"""
judge_run9.py — SESSIONS H / H2 (run 9 base swap to Qwen3-4B-Instruct-2507):
faceF_gen_q + anchor keep100_q, one card (multiple_teal_mole, 2026-07-26).
Sonnet 5, one session per invocation. Reads = RUNBOOK8 frozen: FACE BAR (foresight >=
anchor+0.20 AND overall >= anchor-0.15), CUBE MEMBER READ (>= anchor-0.15), oracle over
{faceF_gen, faceG} reported-not-licensing.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/judge_run9.py            # session H  -> out/run9/rejudge_summary.json
  python scripts/judge_run9.py --s2       # session H2 -> out/run9/rejudge_summary_s2.json
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
FILES = {"faceF_gen": ROOT / "out/run9/eval_faceF_gen_q_v5_threads.jsonl",
         "keep100": ROOT / "out/run9/eval_anchor_keep100_q_v5_threads.jsonl"}


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

    (ROOT / "out/run9").mkdir(parents=True, exist_ok=True)
    (ROOT / f"out/run9/rejudge_summary{SUF}.json").write_text(json.dumps(out, indent=2))
    (ROOT / f"out/run9/per_problem{SUF}.json").write_text(json.dumps(per_problem, indent=2))

    ns = [v["n"] for v in out.values()]
    print(f"\n--- READ (RUNBOOK8 frozen criteria, session {'H2' if S2 else 'H'}) ---")
    if min(ns) < 44:
        print(f"COVERAGE INSUFFICIENT (n={ns}) — discard session and rerun whole")
        return
    k = out["keep100"]
    f = out["faceF_gen"]
    lane_need = round(k["foresight"] + 0.20, 3)
    floor = round(k["overall"] - 0.15, 3)
    lane_ok = f["foresight"] >= k["foresight"] + 0.20
    floor_ok = f["overall"] >= k["overall"] - 0.15
    print(f"[run9] R3 FACE faceF_gen_qwen: foresight {f['foresight']} vs anchor {k['foresight']} "
          f"(needs >= {lane_need}) {'OK' if lane_ok else 'FAIL'}; "
          f"overall {f['overall']} vs floor {floor} {'OK' if floor_ok else 'FAIL'} "
          f"-> {'PASS' if lane_ok and floor_ok else 'FAIL'}")
    # R2 anchor read (reported): cross-model vs granite anchor (annotated cross-session)
    print(f"[run9] R2 ANCHOR (reported): qwen anchor overall {k['overall']} foresight {k['foresight']} "
          f"vs granite-run8 3.57 / 2.92 (cross-session, annotated)")
    if k["foresight"] > 4.3:
        print("[run9] WARNING: anchor foresight > 4.3 — lane bar collides with scale ceiling (annotate loudly)")


if __name__ == "__main__":
    asyncio.run(main())
