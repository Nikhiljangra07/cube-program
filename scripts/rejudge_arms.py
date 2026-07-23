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
    # SESSION 4 (2026-07-23): transformation-gate run — all 3 sets generated on the SAME
    # card (RTX 6000 Ada, fresh pod); keep100 + book_C06 regenerated on-card (card-class
    # control). laneF = keep-0.6 band + mastery on the foresight-lane transformed corpus.
    "laneF":     ROOT / "out/eval_laneF_v5_threads.jsonl",
    "keep100":   ROOT / "out/eval_anchor_keep100_v5_threads.jsonl",
    "book_C06":  ROOT / "out/eval_book_C06_v5_threads.jsonl",
    # session-3 set (PRO-6000-generated — do NOT mix into this Ada session):
    # "book_A":    ROOT / "out/eval_book_A_v5_threads.jsonl",
    # "book_B04":  ROOT / "out/eval_book_B04_v5_threads.jsonl",
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
    ns = [v["n"] for v in out.values()]
    print("\n--- READ (RUNBOOK4 frozen criteria) ---")
    if min(ns) < 44:
        print(f"COVERAGE INSUFFICIENT (n={ns}) — do not read signals until all arms >= 44/48")
    lf, k1, c06 = out.get("laneF", {}), out.get("keep100", {}), out.get("book_C06", {})
    if all([lf, k1, c06]):
        # SIGNAL E headline: laneF foresight >= keep100 foresight + 0.25 AND >= 3.25 absolute
        fs, fk = lf["foresight"], k1["foresight"]
        print(f"[run4] SIGNAL E foresight: laneF {fs} vs keep100 {fk} "
              f"(needs >= {round(fk + 0.25, 2)} AND >= 3.25) -> "
              f"{'CLAIMED — checkpoint 1 broken' if (fs >= fk + 0.25 and fs >= 3.25) else 'FAILS — watch continues'}")
        # Narrowing-tax guard
        print(f"[run4] Narrowing-tax guard: laneF overall {lf['overall']} vs keep100 {k1['overall']} "
              f"(floor {round(k1['overall'] - 0.15, 2)}) -> "
              f"{'HOLDS' if lf['overall'] >= k1['overall'] - 0.15 else 'FAILS — purity tax detected'}")
        # Transformation's share: laneF vs book_C06 (same book, same machinery, raw vs transformed)
        do, df = round(lf["overall"] - c06["overall"], 2), round(fs - c06["foresight"], 2)
        active = do >= 0.20 or df >= 0.30
        print(f"[run4] Transformation vs raw: laneF-book_C06 overall {do}, foresight {df} -> "
              f"{'TRANSFORMATION IS THE ACTIVE INGREDIENT' if active else 'within noise of raw book'}")
        # Book value re-check with transformed data
        print(f"[run4] Book value (transformed): laneF {lf['overall']} vs keep100 {k1['overall']} -> "
              f"{'BOOK NOW ADDS VALUE' if lf['overall'] > k1['overall'] else 'still no measurable book value'}")


if __name__ == "__main__":
    asyncio.run(main())
