"""
build_arms.py — build the two arms at MATCHED token mass (local, no GPU, no keys).

Inputs: the source training jsonl + its loss_band_gate.py score file.
Arms (per dataset — run once for worker, once for decomposer):

  dense60  — the LEARNABLE BAND: rows sorted by base-model mean_nll; token mass is
             trimmed from both ends until the target fraction remains, dropping
             easy-end mass and hard-end mass at EASY_BIAS:1 (default 3:1 — the easy
             end carries the least gradient; the extreme hard end is likelier noise).
  rand60   — CONTROL: random rows (seed 42) to the same token mass. If dense60 only
             ties rand60, the gate did nothing and "any 60% subset works" — the honest
             null result. Skipped-score rows are excluded from BOTH arms (same pool).

  python build_arms.py --src data/src/worker_train.jsonl --scores out/worker_scored.jsonl \
      --out-dir data/arms --name worker_train --frac 0.60
  python build_arms.py --src data/src/decomposer_train.jsonl --scores out/decomposer_scored.jsonl \
      --out-dir data/arms --name decomposer_train --frac 0.60

Writes data/arms/dense60/<name>.jsonl, data/arms/rand60/<name>.jsonl and a manifest with
row counts, token masses, and the selected NLL band [lo, hi] for the paper trail.
"""
from __future__ import annotations
import argparse, json, random
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--scores", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--frac", type=float, default=0.60)
    ap.add_argument("--easy-bias", type=float, default=3.0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    src_rows = [json.loads(l) for l in Path(args.src).open()]
    scores = [json.loads(l) for l in Path(args.scores).open()]
    assert len(scores) == len(src_rows), f"score/src length mismatch {len(scores)} vs {len(src_rows)}"

    pool = [s for s in scores if "mean_nll" in s]
    n_skip = len(scores) - len(pool)
    total = sum(s["n_comp_tokens"] for s in pool)
    target = args.frac * total

    # DENSE: trim both ends of the NLL-sorted pool, easy-biased.
    by_nll = sorted(pool, key=lambda s: s["mean_nll"])
    lo, hi = 0, len(by_nll) - 1
    mass = total
    dropped_easy = dropped_hard = 0
    while mass > target and lo < hi:
        if dropped_easy <= args.easy_bias * dropped_hard:
            dropped_easy += by_nll[lo]["n_comp_tokens"]; mass -= by_nll[lo]["n_comp_tokens"]; lo += 1
        else:
            dropped_hard += by_nll[hi]["n_comp_tokens"]; mass -= by_nll[hi]["n_comp_tokens"]; hi -= 1
    dense = by_nll[lo:hi + 1]
    dense_mass = sum(s["n_comp_tokens"] for s in dense)
    band = (by_nll[lo]["mean_nll"], by_nll[hi]["mean_nll"])

    # RAND control: random rows from the SAME pool to the same mass (stop at closest approach).
    rng = random.Random(args.seed)
    shuffled = pool[:]; rng.shuffle(shuffled)
    rand, cum = [], 0
    for s in shuffled:
        if cum >= dense_mass:
            break
        # take the row only if it brings us closer to the target mass
        if abs(cum + s["n_comp_tokens"] - dense_mass) <= abs(cum - dense_mass):
            rand.append(s); cum += s["n_comp_tokens"]
    rand_mass = cum

    out_dir = Path(args.out_dir)
    for arm_name, arm in (("dense60", dense), ("rand60", rand)):
        d = out_dir / arm_name; d.mkdir(parents=True, exist_ok=True)
        keep = sorted(s["idx"] for s in arm)  # preserve original corpus order
        with (d / f"{args.name}.jsonl").open("w") as f:
            for i in keep:
                f.write(json.dumps(src_rows[i]) + "\n")

    manifest = {
        "name": args.name, "frac": args.frac, "easy_bias": args.easy_bias, "seed": args.seed,
        "pool_rows": len(pool), "skipped_rows": n_skip, "pool_tokens": total,
        "dense60": {"rows": len(dense), "tokens": dense_mass,
                    "nll_band": [round(band[0], 4), round(band[1], 4)],
                    "dropped_easy_tokens": dropped_easy, "dropped_hard_tokens": dropped_hard},
        "rand60": {"rows": len(rand), "tokens": rand_mass},
        "mass_match_pct": round(100 * rand_mass / max(dense_mass, 1), 2),
    }
    mpath = out_dir / f"manifest_{args.name}.json"
    mpath.write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))
    print(f"WROTE {out_dir}/dense60/{args.name}.jsonl, {out_dir}/rand60/{args.name}.jsonl, {mpath}")


if __name__ == "__main__":
    main()
