"""
judge_run7.py — SESSION F (run 7 face factory II): 4 cube members + keep100 anchor, all
generated on pod C (RTX PRO 6000 Blackwell, 2026-07-25). Sonnet 5 single session.
Reads = RUNBOOK7 frozen: per-face bar, ORACLE CEILING over the 4 cube members, verdict
grid. Inputs/outputs under out/run7/ only.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/judge_run7.py
"""
from __future__ import annotations
import asyncio, json
from pathlib import Path

import numpy as np
import httpx

import head2head_v5 as H
from rejudge_arms import sonnet_judge, agg

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CUBE = ["faceF", "faceD", "faceV", "faceG"]
LANE = {"faceF": "foresight", "faceD": "distinctness", "faceV": "viability"}
FILES = {**{a: ROOT / f"out/run7/eval_{a}_v5_threads.jsonl" for a in CUBE},
         "keep100": ROOT / "out/run7/eval_anchor_keep100_v5_threads.jsonl"}


async def main():
    for label, p in FILES.items():
        if not p.exists():
            raise SystemExit(f"missing thread file for '{label}': {p}")
    out, per_problem = {}, {}
    async with httpx.AsyncClient() as client:
        for label, path in FILES.items():
            rows = [json.loads(l) for l in path.open()]
            res = []

            async def one(r):
                j = await sonnet_judge(client, r["problem"], r["angles"], r["threads"])
                res.append({"problem": r["problem"], "judge": j})

            await asyncio.gather(*[one(r) for r in rows if r.get("threads")])
            out[label] = agg(res)
            per_problem[label] = {r["problem"]: r["judge"]["mean"]
                                  for r in res if r.get("judge")}
            print(f"{label:8s} {json.dumps(out[label])}", flush=True)

    (ROOT / "out/run7").mkdir(parents=True, exist_ok=True)
    (ROOT / "out/run7/rejudge_summary.json").write_text(json.dumps(out, indent=2))
    (ROOT / "out/run7/per_problem.json").write_text(json.dumps(per_problem, indent=2))

    ns = [v["n"] for v in out.values()]
    print("\n--- READ (RUNBOOK7 frozen criteria) ---")
    if min(ns) < 44:
        print(f"COVERAGE INSUFFICIENT (n={ns}) — do not read signals until all arms >= 44/48")
        return
    k = out["keep100"]
    # 1. FACE BAR
    passes = []
    for a, lane in LANE.items():
        own, ko = out[a][lane], k[lane]
        ok_lane = own >= ko + 0.20
        ok_over = out[a]["overall"] >= k["overall"] - 0.15
        ok = ok_lane and ok_over
        passes.append(ok)
        print(f"[run7] FACE {a} ({lane}): own {own} vs anchor {ko} "
              f"(needs >= {round(ko+0.20,2)}) {'OK' if ok_lane else 'FAIL'}; "
              f"overall {out[a]['overall']} vs floor {round(k['overall']-0.15,2)} "
              f"{'OK' if ok_over else 'FAIL'} -> {'PASS' if ok else 'FAIL'}")
    print(f"[run7] faceG (cube generalist): overall {out['faceG']['overall']} "
          f"vs anchor {k['overall']} (no lane bar — its job is the fallback seat)")
    # 2. ORACLE CEILING over the 4 cube members
    common = set.intersection(*[set(per_problem[a]) for a in CUBE + ["keep100"]])
    oracle = float(np.mean([max(per_problem[a][p] for a in CUBE) for p in common]))
    km = float(np.mean([per_problem["keep100"][p] for p in common]))
    print(f"[run7] ORACLE CEILING (n={len(common)}): oracle {oracle:.2f} vs keep100 {km:.2f} "
          f"-> {'HEADROOM (>= +0.20): dispatcher licensed' if oracle >= km + 0.20 else ('DEAD (< +0.10): no routing gain possible' if oracle < km + 0.10 else 'MARGINAL (+0.10..0.20): judgment call')}")
    # routing pattern preview
    from collections import Counter
    wins = Counter(max(CUBE, key=lambda a: per_problem[a][p]) for p in common)
    print(f"[run7] per-problem best-arm counts: {dict(wins)}")
    # 3. verdict grid
    npass = sum(passes)
    if npass >= 2 and oracle >= km + 0.20:
        print("[run7] VERDICT: >=2 faces + headroom -> BUILD DISPATCHER (stage 2)")
    elif npass >= 2:
        print("[run7] VERDICT: faces real but no oracle headroom -> cube redundant on this bench")
    else:
        print("[run7] VERDICT: <2 faces pass -> carved behavioral faces null; lane corpora must be GENERATED")


if __name__ == "__main__":
    asyncio.run(main())
