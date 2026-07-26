"""
anthropic_batch.py — shared Message Batches helper (50% off vs direct API).

Contract: batch_call_map(prompts: {custom_id: prompt_str}, model, max_tokens)
  -> {custom_id: response_text}
Submits ONE batch, polls until ended, collects results, then runs a DIRECT-API retry
pass for any failed/empty ids (same model + prompt — transport-only difference), so
callers keep the existing all-or-discard coverage discipline unchanged.

Catches handled here: async polling (24h SLA, usually minutes), out-of-order results
(matched by custom_id), straggler retries (second pass), collection guaranteed before
return. Science unchanged: same model, same prompts, same blind single-submission
semantics — only the transport (and the price) differs.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/anthropic_batch.py --smoke     # 4-call end-to-end test (~$0.01)
"""
from __future__ import annotations
import asyncio, json, os, sys, time

import httpx

API = "https://api.anthropic.com/v1"
KEY = os.environ.get("ANTHROPIC_API_KEY", "")
HDRS = {"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}
POLL_S = 20
DIRECT_SEM = asyncio.Semaphore(6)


def _text(message: dict) -> str:
    return "".join(p.get("text", "") for p in message.get("content", [])
                   if p.get("type") == "text").strip()


async def _direct(client, prompt, model, max_tokens, retries=5):
    async with DIRECT_SEM:
        for a in range(retries):
            try:
                r = await client.post(f"{API}/messages", headers=HDRS,
                                      json={"model": model, "max_tokens": max_tokens,
                                            "messages": [{"role": "user", "content": prompt}]},
                                      timeout=180)
                r.raise_for_status()
                t = _text(r.json())
                if t:
                    return t
            except Exception:
                await asyncio.sleep(3 * (a + 1))
    return None


async def batch_call_map(prompts: dict, model: str, max_tokens: int,
                         label: str = "batch") -> dict:
    """One batch + direct retry pass. Returns {custom_id: text}; missing ids failed twice."""
    if not KEY:
        sys.exit("ANTHROPIC_API_KEY not set")
    reqs = [{"custom_id": cid,
             "params": {"model": model, "max_tokens": max_tokens,
                        "messages": [{"role": "user", "content": p}]}}
            for cid, p in prompts.items()]
    out: dict = {}
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{API}/messages/batches", headers=HDRS,
                              json={"requests": reqs}, timeout=120)
        r.raise_for_status()
        b = r.json()
        bid = b["id"]
        print(f"[{label}] batch {bid} submitted: {len(reqs)} requests", flush=True)
        t0 = time.time()
        while True:
            await asyncio.sleep(POLL_S)
            r = await client.get(f"{API}/messages/batches/{bid}", headers=HDRS, timeout=60)
            r.raise_for_status()
            b = r.json()
            c = b.get("request_counts", {})
            if b.get("processing_status") == "ended":
                print(f"[{label}] ended in {time.time()-t0:.0f}s: {c}", flush=True)
                break
            if time.time() - t0 > 6 * 3600:
                # collect what exists, retry pass covers the rest
                print(f"[{label}] WARN: 6h poll ceiling hit, canceling remainder", flush=True)
                await client.post(f"{API}/messages/batches/{bid}/cancel", headers=HDRS, timeout=60)
        # collect (guaranteed before return)
        url = b.get("results_url")
        if url:
            rr = await client.get(url, headers=HDRS, timeout=300)
            rr.raise_for_status()
            for line in rr.text.splitlines():
                row = json.loads(line)
                res = row.get("result", {})
                if res.get("type") == "succeeded":
                    t = _text(res.get("message", {}))
                    if t:
                        out[row["custom_id"]] = t
        missing = [cid for cid in prompts if cid not in out]
        if missing:
            print(f"[{label}] retry pass (direct API) for {len(missing)} stragglers", flush=True)
            texts = await asyncio.gather(*[_direct(client, prompts[cid], model, max_tokens)
                                           for cid in missing])
            for cid, t in zip(missing, texts):
                if t:
                    out[cid] = t
    print(f"[{label}] coverage {len(out)}/{len(prompts)}", flush=True)
    return out


async def _smoke():
    prompts = {f"smoke-{i}": f'Return ONLY JSON: {{"n": {i}, "sq": <the square of {i}>}}'
               for i in range(1, 5)}
    res = await batch_call_map(prompts, "claude-sonnet-5", 200, label="smoke")
    ok = 0
    for cid, t in sorted(res.items()):
        try:
            j = json.loads(t[t.index("{"):t.rindex("}") + 1])
            good = j["sq"] == j["n"] ** 2
        except Exception:
            good = False
        ok += good
        print(f"  {cid}: {t[:60]!r} {'OK' if good else 'BAD'}")
    print(f"SMOKE {'PASS' if ok == 4 else 'FAIL'} ({ok}/4)")


if __name__ == "__main__":
    if "--smoke" in sys.argv:
        asyncio.run(_smoke())
    else:
        print(__doc__)
