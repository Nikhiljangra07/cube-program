"""
build_faces.py — RUN 7 stage 0: carve the three face subsets and emit worker-format
training files, byte-compatible with prep_v5.py's worker contract.

Carve (frozen endpoint, RUNBOOK7): contrast score z(own) − mean z(others) on the blind
1-10 rescores; top 220 problems per lane. Strict quartile carve documented as failing the
200-minimum for D (56) and V (81); stepwise slack only reached size where the constraint
became vacuous — contrast ranking adopted as the documented loosening endpoint.

Leak guards: (1) prep_v5's 20 held-out problems (last 20 rows of corpus_v5_train) are
excluded from every face — the keep100 generalist never trained on them, faces must not
either; (2) any problem string appearing in the 48-problem bench is excluded (none
expected — bench is OOD — but verified, not assumed).

Outputs per face under data/faces/face_{F,D,V}/:
  worker_train.jsonl   (4 rows per problem, WRK_SYS/WRK_USER template from prep_v5)
  manifest.json        (carve stats: size, lane means, overlaps, exclusions)

  python scripts/build_faces.py
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DF = Path.home() / "Desktop/divergence-formula/corpus_run"
RESCORED = ROOT / "data/faces/rescored.jsonl"
BENCH = ROOT / "data/bench/problems.jsonl"
OUTD = ROOT / "data/faces"
TOP_N = 220
DIMS = {"F": "foresight", "D": "distinctness", "V": "viability"}

# byte-identical to round2_kit/prep_v5.py
WRK_SYS = "You write one precise, decisive, realistic reasoning thread pursuing a given strategic angle."
WRK_USER = ("PROBLEM: {problem}\nFACETS: {facets}\nANGLE: {angle}\n\nWrite a single reasoning thread (two or "
            "three sentences, cold and analytical) that COMMITS to THIS angle as a concrete, realistic, VIABLE "
            "strategy that resolves the whole problem in a distinct way — name the actual first move (who does "
            "what, to whom, by when) and the one most likely downstream consequence it is betting on. It must be "
            "lawful, executable, and unmistakably a different KIND of move than the other families would choose.")


def fam(a):
    if isinstance(a, dict):
        f = str(a.get("family", "")).strip(); d = str(a.get("directive", "")).strip()
        return f"[{f}] {d}" if f else d
    return str(a)


def chat(s, u, a):
    return {"messages": [{"role": "system", "content": s}, {"role": "user", "content": u},
                         {"role": "assistant", "content": a}]}


def main():
    # source rows (threads live here), keyed by problem
    src = {}
    v5_train_rows = [json.loads(l) for l in (DF / "corpus_v5_train/passers.jsonl").open()]
    for r in v5_train_rows + [json.loads(l) for l in (DF / "corpus_v5_topup/passers.jsonl").open()]:
        src[r["problem"]] = r
    prep_holdout = {r["problem"] for r in v5_train_rows[-20:]}  # prep_v5 --holdout 20
    bench = {json.loads(l)["problem"] for l in BENCH.open()}

    rows = [json.loads(l) for l in RESCORED.open()]
    excluded = [r for r in rows if r["problem"] in prep_holdout or r["problem"] in bench]
    pool = [r for r in rows if r["problem"] not in prep_holdout and r["problem"] not in bench]
    bench_hits = sum(1 for r in rows if r["problem"] in bench)
    print(f"pool={len(pool)} (excluded {len(excluded)}: {len(excluded)-bench_hits} prep-holdout, "
          f"{bench_hits} bench overlap)")

    S = {d: np.array([r["rescore"][d] for r in pool]) for d in DIMS.values()}
    Z = {d: (S[d] - S[d].mean()) / S[d].std() for d in DIMS.values()}

    sel = {}
    for key, d in DIMS.items():
        others = [o for o in DIMS.values() if o != d]
        contrast = Z[d] - (Z[others[0]] + Z[others[1]]) / 2
        sel[key] = list(np.argsort(-contrast)[:TOP_N])

    manifests = {}
    for key, d in DIMS.items():
        face_dir = OUTD / f"face_{key}"
        face_dir.mkdir(parents=True, exist_ok=True)
        probs = [pool[i]["problem"] for i in sel[key]]
        n_rows = 0
        with (face_dir / "worker_train.jsonl").open("w") as f:
            for p in probs:
                r = src[p]
                for a, t in zip(r["angles"], r["pos_threads"]):
                    f.write(json.dumps(chat(WRK_SYS, WRK_USER.format(
                        problem=r["problem"], facets=" | ".join(r["facets"][:3]),
                        angle=fam(a)), str(t).strip())) + "\n")
                    n_rows += 1
        idx = sel[key]
        manifests[key] = {
            "lane": d, "problems": len(probs), "worker_rows": n_rows,
            "own_lane_mean": round(float(S[d][idx].mean()), 2),
            "pool_mean": round(float(S[d].mean()), 2),
            "other_lane_means": {o: round(float(S[o][idx].mean()), 2)
                                 for o in DIMS.values() if o != d},
            "md5": hashlib.md5((face_dir / "worker_train.jsonl").read_bytes()).hexdigest(),
        }

    for a in DIMS:
        for b in DIMS:
            if a < b:
                ov = len(set(sel[a]) & set(sel[b]))
                manifests.setdefault("overlaps", {})[f"{a}&{b}"] = f"{ov} ({100*ov/TOP_N:.0f}%)"
    manifests["exclusions"] = {"prep_holdout": len(excluded) - bench_hits, "bench_overlap": bench_hits}
    (OUTD / "carve_manifest.json").write_text(json.dumps(manifests, indent=2))
    print(json.dumps(manifests, indent=2))


if __name__ == "__main__":
    main()
