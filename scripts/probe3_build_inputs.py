"""
probe3_build_inputs.py — PROBE 3 stage 0 (local, $0): assemble revision-prompt inputs.

For each of the 16 twin pairs and each arm (faceV_10, keep100): pick up to 2 of the
arm's own base-problem threads (preferring threads with a parseable digit estimate;
old estimate recorded), pair with the frozen boost. Writes data/run10/probe3_inputs.jsonl.
"""
from __future__ import annotations
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTD = ROOT / "out/run10"
D10 = ROOT / "data/run10"
PCT = re.compile(r"(\d{1,3})(?:\s*(?:-|–|to)\s*(\d{1,3}))?\s*%")


def last_pct(t):
    found = PCT.findall(t)
    if not found:
        return None
    a, b = found[-1]
    return (int(a) + int(b)) / 2 if b else float(a)


def main():
    inv = [json.loads(l) for l in (D10 / "inventory_problems.jsonl").open()]
    twins = [json.loads(l) for l in (D10 / "twin_problems.jsonl").open()]
    arms = {
        "faceV_10": {r["problem"]: r for r in (json.loads(l) for l in (OUTD / "eval_faceV_10_qC_v5_threads.jsonl").open())},
        "keep100": {r["problem"]: r for r in (json.loads(l) for l in (OUTD / "eval_anchor_10_qC_v5_threads.jsonl").open())},
    }
    rows = []
    for m in twins:
        base_problem = inv[m["base_index"]]["problem"]
        for arm, by in arms.items():
            r = by.get(base_problem)
            if not r:
                continue
            scored = [(i, t, last_pct(t)) for i, t in enumerate(r["threads"])]
            with_est = [x for x in scored if x[2] is not None]
            chosen = (with_est + [x for x in scored if x[2] is None])[:2]
            for i, t, est in chosen:
                rows.append({"pair": m["base_index"], "arm": arm, "thread_idx": i,
                             "problem": base_problem, "prior": t, "old_est": est,
                             "boost": m["boost"]})
    out = D10 / "probe3_inputs.jsonl"
    with out.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    n_est = sum(1 for r in rows if r["old_est"] is not None)
    print(f"{len(rows)} revision jobs ({n_est} with old estimate) -> {out}")


if __name__ == "__main__":
    main()
