"""
judge_run5.py — SESSION H (run 5 headroom): fedH + anchor_keep100, both generated on pod A
(RTX PRO 6000 Blackwell, 2026-07-24). Sonnet 5 single session; reads = RUNBOOK5 frozen.
Isolated from run-4 files: inputs/outputs live under out/run5/ only.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/judge_run5.py
"""
from __future__ import annotations
import asyncio, json
from pathlib import Path

import httpx

import head2head_v5 as H
from rejudge_arms import sonnet_judge, agg

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FILES = {
    "fedH":    ROOT / "out/run5/eval_fedH_v5_threads.jsonl",
    "keep100": ROOT / "out/run5/eval_anchor_keep100_v5_threads.jsonl",
}


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

    summary = ROOT / "out/run5/rejudge_summary.json"
    summary.write_text(json.dumps(out, indent=2))
    print(f"\nWROTE {summary}")
    ns = [v["n"] for v in out.values()]
    print("\n--- READ (RUNBOOK5 frozen criteria) ---")
    if min(ns) < 44:
        print(f"COVERAGE INSUFFICIENT (n={ns}) — do not read signals until all arms >= 44/48")
    f, k = out["fedH"], out["keep100"]
    floor = round(k["overall"] - 0.15, 2)
    cat = round(k["overall"] - 0.30, 2)
    print(f"[run5] NO-FORGETTING GUARD: fedH overall {f['overall']} vs keep100 {k['overall']} "
          f"(floor {floor}) -> {'HOLDS' if f['overall'] >= floor else 'FAILS'}")
    print(f"[run5] CATASTROPHIC CHECK: fedH {f['overall']} vs {cat} -> "
          f"{'CATASTROPHIC INTERFERENCE' if f['overall'] < cat else 'no catastrophe'}")
    if f["overall"] > k["overall"] + 0.15:
        print("[run5] BONUS ANOMALY: fedH BEATS keep100 by >0.15 — re-verify before claiming")
    print("[run5] (1a telemetry: 886/886 mastered @504/555, mean 4.48 visits — HOLDS, from train log)")
    print("[run5] (1b NLL: instrument invalidated by control — bookC06 shows same inflation on "
          "clausewitz heldout (+2.14) as fedH on fed heldout (+1.93); verdict rests on 1a + guard)")


if __name__ == "__main__":
    asyncio.run(main())
