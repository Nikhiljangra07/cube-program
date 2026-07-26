"""
judge_run8.py — SESSIONS G / G2 (run 8 generated foresight face): faceF_gen + faceG_r8
+ anchor keep100_r8, all generated on one card (costly_emerald_basilisk, 2026-07-25).
Sonnet 5, one session per invocation. Reads = RUNBOOK8 frozen: FACE BAR (foresight >=
anchor+0.20 AND overall >= anchor-0.15), CUBE MEMBER READ (>= anchor-0.15), oracle over
{faceF_gen, faceG} reported-not-licensing.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/judge_run8.py            # session G  -> out/run8/rejudge_summary.json
  python scripts/judge_run8.py --s2       # session G2 -> out/run8/rejudge_summary_s2.json
"""
from __future__ import annotations
import asyncio, json, sys
from pathlib import Path

import httpx

import head2head_v5 as H  # noqa: F401  (import parity with judge_run7)
from rejudge_arms import sonnet_judge, agg

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
S2 = "--s2" in sys.argv
SUF = "_s2" if S2 else ""
FILES = {"faceF_gen": ROOT / "out/run8/eval_faceF_gen_v5_threads.jsonl",
         "faceG": ROOT / "out/run8/eval_faceG_r8_v5_threads.jsonl",
         "keep100": ROOT / "out/run8/eval_anchor_keep100_r8_v5_threads.jsonl"}


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
            print(f"{label:10s} {json.dumps(out[label])}", flush=True)

    (ROOT / "out/run8").mkdir(parents=True, exist_ok=True)
    (ROOT / f"out/run8/rejudge_summary{SUF}.json").write_text(json.dumps(out, indent=2))
    (ROOT / f"out/run8/per_problem{SUF}.json").write_text(json.dumps(per_problem, indent=2))

    ns = [v["n"] for v in out.values()]
    print(f"\n--- READ (RUNBOOK8 frozen criteria, session {'G2' if S2 else 'G'}) ---")
    if min(ns) < 44:
        print(f"COVERAGE INSUFFICIENT (n={ns}) — discard session and rerun whole")
        return
    k = out["keep100"]
    f = out["faceF_gen"]
    g = out["faceG"]
    lane_need = round(k["foresight"] + 0.20, 3)
    floor = round(k["overall"] - 0.15, 3)
    lane_ok = f["foresight"] >= k["foresight"] + 0.20
    floor_ok = f["overall"] >= k["overall"] - 0.15
    print(f"[run8] FACE faceF_gen: foresight {f['foresight']} vs anchor {k['foresight']} "
          f"(needs >= {lane_need}) {'OK' if lane_ok else 'FAIL'}; "
          f"overall {f['overall']} vs floor {floor} {'OK' if floor_ok else 'FAIL'} "
          f"-> {'PASS' if lane_ok and floor_ok else 'FAIL'}")
    print(f"[run8] CUBE faceG: overall {g['overall']} vs floor {floor} "
          f"{'OK' if g['overall'] >= floor else 'FAIL'}")
    # oracle over the 2 cube members (reported, not licensing)
    common = set(per_problem["faceF_gen"]) & set(per_problem["faceG"]) & set(per_problem["keep100"])
    oracle = sum(max(per_problem["faceF_gen"][p], per_problem["faceG"][p]) for p in common) / len(common)
    kk = sum(per_problem["keep100"][p] for p in common) / len(common)
    best = {"faceF_gen": 0, "faceG": 0}
    for p in common:
        best["faceF_gen" if per_problem["faceF_gen"][p] >= per_problem["faceG"][p] else "faceG"] += 1
    print(f"[run8] ORACLE(2) n={len(common)}: {oracle:.2f} vs keep100 {kk:.2f} "
          f"(+{oracle-kk:.2f}) | best-arm counts {best}  [reported only]")


if __name__ == "__main__":
    asyncio.run(main())
