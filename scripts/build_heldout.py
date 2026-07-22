"""
build_heldout.py — build the FREE sweep metric's dataset. Local, no GPU, no keys.

The v5 TOPUP set (corpus_v5_topup/passers.jsonl, 484 scenes) was never used to train any
arm — same generator, same gate, same distribution as v5_train. We render its threads
into worker-format messages rows (byte-identical WRK_SYS/WRK_USER templates imported from
dav_eval_v5) and use held-out completion NLL as the objective sweep metric: lower NLL on
unseen same-distribution scenes = the arm learned the skill, not the rows.

  python build_heldout.py --passers ../divergence-formula/corpus_run/corpus_v5_topup/passers.jsonl \
      --out data/src/heldout_worker.jsonl --cap 600
"""
from __future__ import annotations
import argparse, ast, json, random
from pathlib import Path


def _load_templates():
    # dav_eval_v5 imports torch at module level (pod-only), so lift the two template
    # constants out of its SOURCE via AST — byte-identical, no GPU deps needed locally.
    tree = ast.parse((Path(__file__).parent / "dav_eval_v5.py").read_text())
    consts = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in ("WRK_SYS", "WRK_USER"):
            consts[node.targets[0].id] = ast.literal_eval(node.value)
    assert set(consts) == {"WRK_SYS", "WRK_USER"}, f"templates not found: {set(consts)}"
    return consts["WRK_SYS"], consts["WRK_USER"]


WRK_SYS, WRK_USER = _load_templates()


class E:  # keep the E.WRK_* call sites unchanged
    WRK_SYS, WRK_USER = WRK_SYS, WRK_USER


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--passers", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cap", type=int, default=600)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rows = []
    for line in Path(args.passers).open():
        r = json.loads(line)
        facets = r.get("facets") or []
        angles = r.get("angles") or []
        threads = r.get("pos_threads") or []
        for a, t in zip(angles, threads):
            rows.append({"messages": [
                {"role": "system", "content": E.WRK_SYS},
                {"role": "user", "content": E.WRK_USER.format(
                    problem=r["problem"], facets=" | ".join(facets), angle=a)},
                {"role": "assistant", "content": t},
            ]})
    rng = random.Random(args.seed)
    rng.shuffle(rows)
    rows = rows[:args.cap]
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"WROTE {len(rows)} held-out worker rows -> {out}")


if __name__ == "__main__":
    main()
