"""
rejudge_arms.py — SINGLE-SESSION judge over all four arms (local; keys via the vault symlink).

JUDGE = Claude Sonnet 5 (Nikhil's call, 2026-07-21), temp 0, byte-identical JUDGE_PROMPT +
thread formatting + JSON parsing from head2head_v5.py — only the model behind the prompt
changed. NOTE: absolute scores are NOT comparable to the historical Gemini-judged numbers
in WORKING_PAPER (§12 measured ~0.9 judge-family skew); comparability here comes from all
four arms being judged by the SAME judge in the SAME session:

  base       — untrained granite-4.0-micro   (threads already on disk, from the v5 bench run)
  v5full     — v5 SFT, full corpus ~1.05M tk (threads already on disk — THE baseline)
  dense60    — v5 SFT, learnable-band ~60% tk (new)
  rand60     — v5 SFT, random ~60% tk         (new control)

  export GEMINI_API_KEY=...   # from ~/Desktop/reasoningEngine/.env — do NOT echo it
  python rejudge_arms.py

Reads thread files from ../data/bench and ../out; writes ../out/rejudge_summary.json.
Cost: 4 x 48 judge calls ≈ $2-3. Non-destructive, safe to re-run.
"""
from __future__ import annotations
import asyncio, json
from pathlib import Path

import numpy as np
import httpx

import head2head_v5 as H

JUDGE_MODEL = "claude-sonnet-5"


async def sonnet_call(client, prompt, max_tokens=12000):
    # Sonnet 5 is a thinking model: thinking tokens count toward max_tokens, so the budget
    # must be VERY generous or the JSON never arrives (4000 still lost 20/48 on one arm).
    # NOTE: `temperature` is deprecated/rejected on Sonnet 5 — omit it (judge is one session
    # regardless; exact decoding determinism is no longer a controllable knob on this family).
    body = {"model": JUDGE_MODEL, "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]}
    async with H.SEM:
        for a in range(4):
            try:
                r = await client.post("https://api.anthropic.com/v1/messages",
                                      headers={"x-api-key": H.ANTHROPIC_KEY,
                                               "anthropic-version": "2023-06-01",
                                               "content-type": "application/json"},
                                      json=body, timeout=120)
                r.raise_for_status()
                d = r.json()
                text = "".join(p.get("text", "") for p in d.get("content", [])
                               if p.get("type") == "text").strip()
                if not text:
                    print(f"    [judge empty: stop={d.get('stop_reason')}]", flush=True)
                    continue  # retry — empty text (thinking ate the budget or refusal)
                return text
            except Exception:
                await asyncio.sleep(2 * (a + 1))
    return None


async def sonnet_judge(client, problem, angles, threads):
    # identical formatting + parsing to H.judge — only the model call differs
    block = "\n".join(f"{i+1}. [{H.fam_of(a)}] {t}" for i, (a, t) in enumerate(zip(angles, threads)))
    out = await sonnet_call(client, H.JUDGE_PROMPT.format(problem=problem, threads=block))
    j = H.parse_json(out)
    if not j:
        return None
    try:
        s = {d: int(j[d]) for d in H.DIMS}
    except Exception:
        return None
    s["mean"] = round(sum(s[d] for d in H.DIMS) / 6, 2)
    return s


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FILES = {
    "base":    ROOT / "data/bench/eval_bench_base_v5_threads.jsonl",
    "v5full":  ROOT / "data/bench/eval_bench_sft_v5_threads.jsonl",
    "dense60": ROOT / "out/eval_bench_dense60_v5_threads.jsonl",
    "rand60":  ROOT / "out/eval_bench_rand60_v5_threads.jsonl",
}


def agg(rows):
    ok = [r for r in rows if r.get("judge")]
    a = {d: round(float(np.mean([r["judge"][d] for r in ok])), 2) for d in H.DIMS}
    a["overall"] = round(float(np.mean([r["judge"]["mean"] for r in ok])), 2)
    a["dist>=4%"] = round(100 * float(np.mean([r["judge"]["distinctness"] >= 4 for r in ok])), 1)
    a["n"] = len(ok)
    return a


async def main():
    for label, p in FILES.items():
        if not p.exists():
            raise SystemExit(f"missing thread file for '{label}': {p}")
    out = {}
    async with httpx.AsyncClient() as client:
        for label, path in FILES.items():
            rows = [json.loads(l) for l in path.open()]
            res = []

            async def one(r):
                j = await sonnet_judge(client, r["problem"], r["angles"], r["threads"])
                res.append({"problem": r["problem"], "judge": j})

            await asyncio.gather(*[one(r) for r in rows if r.get("threads")])
            out[label] = agg(res)
            print(f"{label:8s} {json.dumps(out[label])}", flush=True)

    summary = ROOT / "out/rejudge_summary.json"
    summary.write_text(json.dumps(out, indent=2))
    print(f"\nWROTE {summary}")
    d, r, f = out.get("dense60", {}), out.get("rand60", {}), out.get("v5full", {})
    if d and r and f:
        ns = [out[k]["n"] for k in ("base", "v5full", "dense60", "rand60")]
        print("\n--- READ (PLAN.md §5) ---")
        if min(ns) < 44:
            print(f"COVERAGE INSUFFICIENT (n={ns}) — do not read signals until all arms >= 44/48")
        a_holds = abs(d["overall"] - f["overall"]) <= 0.15
        b_holds = (d["overall"] - r["overall"]) >= 0.20
        print(f"Signal A (efficiency): dense60 {d['overall']} vs v5full {f['overall']} -> "
              f"{'HOLDS' if a_holds else 'FAILS'}")
        print(f"Signal B (selection):  dense60 {d['overall']} vs rand60 {r['overall']} "
              f"(delta {round(d['overall'] - r['overall'], 2)}) -> "
              f"{'HOLDS' if b_holds else 'FAILS'}")


if __name__ == "__main__":
    asyncio.run(main())
