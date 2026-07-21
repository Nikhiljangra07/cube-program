"""
rejudge_arms.py — SINGLE-SESSION Gemini 2.5 Pro judge over all four arms (local, needs GEMINI_API_KEY).

The §12 lesson (session wobble ±0.05, judge-family skew ~0.9): never compare scores from
different judging sessions. This re-judges everything in ONE session with the byte-identical
JUDGE_PROMPT from head2head_v5.py (temp 0):

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
                j = await H.judge(client, r["problem"], r["angles"], r["threads"])
                res.append({"problem": r["problem"], "judge": j})

            await asyncio.gather(*[one(r) for r in rows if r.get("threads")])
            out[label] = agg(res)
            print(f"{label:8s} {json.dumps(out[label])}", flush=True)

    summary = ROOT / "out/rejudge_summary.json"
    summary.write_text(json.dumps(out, indent=2))
    print(f"\nWROTE {summary}")
    d, r, f = out.get("dense60", {}), out.get("rand60", {}), out.get("v5full", {})
    if d and r and f:
        print("\n--- READ (PLAN.md §5) ---")
        print(f"Signal A (efficiency): dense60 overall {d['overall']} vs v5full {f['overall']} "
              f"(within 0.15 = holds)")
        print(f"Signal B (selection):  dense60 overall {d['overall']} vs rand60 {r['overall']} "
              f"(dense - rand >= 0.20 = holds)")


if __name__ == "__main__":
    asyncio.run(main())
