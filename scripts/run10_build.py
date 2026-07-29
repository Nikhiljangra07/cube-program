"""
run10_build.py — RUN 10: admission gate = BENCH JUDGE VERBATIM (sonnet_judge) + faceV_10 diet.

Gate: 220 problem-sets (4 generated threads each) scored blind by Sonnet 5 with the
byte-identical v5 bench judge (single session, shuffled, coverage 220/220 or discard).
Admission (frozen in RUNBOOK10): set viability >= 4 AND foresight >= 3 — the legs of
9b's gate swapped for the V lane; the foresight leg blocks plans that audit well but
ignore the counterparty entirely.
Target >= 140 admitted problems; fewer -> STOP and report (watch item 5: if foresight
is the binding failure, the pre-authorized fix is one line in TASK_V step 4).

Diet: admitted generated rows (thread body, TRACE stripped at generation) + ONE
original pos_thread per admitted problem (deterministic index int(pid,16) % 4), all
in prep_v5 worker format (byte-identical templates). Bench overlap re-verified at build.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/run10_build.py

Writes out/run10/gate.jsonl, data/run10/faceV_10/worker_train.jsonl + manifest.json.
"""
from __future__ import annotations
import asyncio, hashlib, json, os, random, statistics, sys
from pathlib import Path

import httpx

import head2head_v5 as H  # noqa: F401
from rejudge_arms import sonnet_judge

ROOT = Path(__file__).resolve().parent.parent
DF = Path.home() / "Desktop/divergence-formula/corpus_run"
D10 = ROOT / "data/run10"
OUTD = ROOT / "out/run10"
BENCH = ROOT / "data/bench/problems.jsonl"
KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MIN_ADMIT = 140

WRK_SYS = ("You write one precise, decisive, realistic reasoning thread pursuing a given "
           "strategic angle.")
WRK_USER = ("PROBLEM: {problem}\nFACETS: {facets}\nANGLE: {angle}\n\nWrite a single reasoning "
            "thread (two or three sentences, cold and analytical) that COMMITS to THIS angle as "
            "a concrete, realistic, VIABLE strategy that resolves the whole problem in a "
            "distinct way — name the actual first move (who does what, to whom, by when) and "
            "the one most likely downstream consequence it is betting on. It must be lawful, "
            "executable, and unmistakably a different KIND of move than the other families "
            "would choose.")


def fam(a):
    if isinstance(a, dict):
        f = str(a.get("family", "")).strip(); d = str(a.get("directive", "")).strip()
        return f"[{f}] {d}" if f else d
    return str(a)


def chat(s, u, a):
    return {"messages": [{"role": "system", "content": s}, {"role": "user", "content": u},
                         {"role": "assistant", "content": a}]}


async def main():
    if not KEY:
        sys.exit("ANTHROPIC_API_KEY not set")
    OUTD.mkdir(parents=True, exist_ok=True)
    by = {}
    for l in (D10 / "threads.jsonl").open():
        r = json.loads(l)
        by.setdefault(r["pid"], {})[r["idx"]] = (r["thread"], r["problem"])
    srcrows = {}
    SRC = [DF / "corpus_v5_train/passers.jsonl", DF / "corpus_v5_topup/passers.jsonl"]
    for _p in SRC:
        for _l in _p.open():
            _r = json.loads(_l)
            srcrows[hashlib.md5(_r["problem"].encode()).hexdigest()[:12]] = _r
    sets = []
    for p, th in by.items():
        if len(th) != 4:
            sys.exit(f"incomplete set {p}")
        sets.append({"pid": p, "problem": th[0][1], "threads": [th[i][0] for i in range(4)],
                     "angles": [fam(a) for a in srcrows[p]["angles"]]})
    random.Random(107).shuffle(sets)
    print(f"{len(sets)} sets to gate (expect 220)")

    results = []
    async with httpx.AsyncClient() as client:
        async def one(st):
            j = await sonnet_judge(client, st["problem"], st["angles"], st["threads"])
            if j:
                results.append({"pid": st["pid"], "judge": j})
                if len(results) % 50 == 0:
                    print(f"  {len(results)} gated", flush=True)
        await asyncio.gather(*[one(s) for s in sets])
    print(f"coverage {len(results)}/{len(sets)}")
    with (OUTD / "gate.jsonl").open("w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    if len(results) < len(sets):
        sys.exit("COVERAGE FAIL — discard session and rerun whole")

    admitted = [r for r in results if r["judge"]["viability"] >= 4 and r["judge"]["foresight"] >= 3]
    vmean = statistics.mean(r["judge"]["viability"] for r in results)
    fmean = statistics.mean(r["judge"]["foresight"] for r in results)
    v_only = sum(1 for r in results if r["judge"]["viability"] >= 4)
    f_only = sum(1 for r in results if r["judge"]["foresight"] >= 3)
    print(f"admitted {len(admitted)}/220 (bench-judge viability>=4 & foresight>=3) | "
          f"all-sets viability {vmean:.2f} foresight {fmean:.2f} | "
          f"legs alone: viability>=4: {v_only}, foresight>=3: {f_only}")
    if len(admitted) < MIN_ADMIT:
        sys.exit(f"ADMISSION SHORTFALL: {len(admitted)} < {MIN_ADMIT} — STOP, report binding leg to Nikhil")

    # ---- build diet ----
    bench = {json.loads(l)["problem"] for l in BENCH.open()}
    face_dir = D10 / "faceV_10"
    face_dir.mkdir(exist_ok=True)
    admit_pids = {r["pid"] for r in admitted}
    n_gen = n_orig = 0
    with (face_dir / "worker_train.jsonl").open("w") as f:
        for pd in sorted(admit_pids):
            row = srcrows[pd]
            if row["problem"] in bench:
                sys.exit(f"BENCH LEAK: {pd}")
            facets = " | ".join(row["facets"][:3])
            for k, ang in enumerate(row["angles"]):
                f.write(json.dumps(chat(WRK_SYS,
                                        WRK_USER.format(problem=row["problem"], facets=facets,
                                                        angle=fam(ang)),
                                        by[pd][k][0])) + "\n")
                n_gen += 1
            oi = int(pd, 16) % 4
            f.write(json.dumps(chat(WRK_SYS,
                                    WRK_USER.format(problem=row["problem"], facets=facets,
                                                    angle=fam(row["angles"][oi])),
                                    str(row["pos_threads"][oi]).strip())) + "\n")
            n_orig += 1
    md5 = hashlib.md5((face_dir / "worker_train.jsonl").read_bytes()).hexdigest()
    manifest = {"admitted_problems": len(admit_pids), "gen_rows": n_gen, "orig_rows": n_orig,
                "total_rows": n_gen + n_orig, "admission": "bench_judge viability>=4 & foresight>=3",
                "admitted_viability_mean": round(statistics.mean(r["judge"]["viability"] for r in admitted), 2),
                "admitted_foresight_mean": round(statistics.mean(r["judge"]["foresight"] for r in admitted), 2),
                "worker_md5": md5}
    (face_dir / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    asyncio.run(main())
