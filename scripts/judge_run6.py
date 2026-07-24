"""
judge_run6.py — SESSION S (run 6 exposure sweep): 5 sweep arms + anchor_keep100, all
generated on pod B (RTX PRO 6000 Blackwell, 2026-07-24). Sonnet 5 single session;
reads = RUNBOOK6 frozen. Inputs/outputs live under out/run6/ only.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/judge_run6.py
"""
from __future__ import annotations
import asyncio, json
from pathlib import Path

import httpx

import head2head_v5 as H
from rejudge_arms import sonnet_judge, agg

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
X = {"x025": 1.25, "x05": 2.5, "x1": 5.0, "x2": 10.0, "x4": 20.0}
FILES = {
    **{f"swp_{k}": ROOT / f"out/run6/eval_swp_{k}_v5_threads.jsonl" for k in X},
    "keep100": ROOT / "out/run6/eval_anchor_keep100_v5_threads.jsonl",
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
            print(f"{label:10s} {json.dumps(out[label])}", flush=True)

    summary = ROOT / "out/run6/rejudge_summary.json"
    summary.write_text(json.dumps(out, indent=2))
    print(f"\nWROTE {summary}")
    ns = [v["n"] for v in out.values()]
    print("\n--- READ (RUNBOOK6 frozen criteria) ---")
    if min(ns) < 44:
        print(f"COVERAGE INSUFFICIENT (n={ns}) — do not read signals until all arms >= 44/48")
        return
    ov = {k: out[f"swp_{k}"]["overall"] for k in X}
    anchor = out["keep100"]["overall"]
    curve = " ".join(f"{k}={ov[k]}" for k in X)
    print(f"[run6] curve: {curve} | anchor keep100={anchor}")
    vals = list(ov.values())
    hi, lo = max(vals), min(vals)
    best_k = max(ov, key=ov.get)
    # 1. CURVE SHAPE
    if hi - lo <= 0.15:
        shape = "FLAT — exposure is not a lever on this data"
    elif ov["x4"] >= ov["x05"] + 0.20 and all(v <= ov["x4"] + 0.10 for v in vals):
        shape = "RISING — we have been under-training; our number is HIGHER than 5 epochs"
    elif any(ov[k] >= max(ov["x025"], ov["x4"]) + 0.15 for k in ("x05", "x1", "x2")):
        shape = "PEAK-THEN-FALL — interior peak is our number; memorization burn beyond it"
    elif max(ov["x025"], ov["x05"]) >= ov["x4"] + 0.15 and max(ov["x025"], ov["x05"]) >= ov["x1"]:
        shape = "FALLING — we have been OVER-training"
    else:
        shape = "MIXED/AMBIGUOUS — within-noise wobble, treat as flat-ish"
    print(f"[run6] 1. CURVE SHAPE: {shape}")
    # 2. OUR NUMBER
    for k in X:  # ordered smallest exposure first
        if ov[k] >= hi - 0.10:
            print(f"[run6] 2. OUR NUMBER: {X[k]} exposures/page (arm {k}, ov {ov[k]}; "
                  f"cheapest within 0.10 of best {best_k}={hi})")
            break
    # 3. SATURATION HALF-CONDITION
    sat = abs(ov["x2"] - ov["x1"]) <= 0.15 and abs(ov["x4"] - ov["x1"]) <= 0.15
    print(f"[run6] 3. SATURATION HALF-CONDITION: {'MET — exposure lever exhausted at this scale' if sat else 'not met'}")
    # 4. MEMORIZATION CHECK
    burn = ov["x4"] < ov["x1"] - 0.20
    print(f"[run6] 4. MEMORIZATION CHECK: {'BURN — x4 degrades >0.20 below x1' if burn else 'no over-exposure degradation'}")
    # 5. Narrowing-tax guard
    for k in X:
        if ov[k] < anchor - 0.30:
            print(f"[run6] 5. NARROWING-TAX FLAG: {k} ({ov[k]}) < anchor-0.30 ({round(anchor-0.30,2)})")


if __name__ == "__main__":
    asyncio.run(main())
