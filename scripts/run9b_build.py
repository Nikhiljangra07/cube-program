"""
run9b_build.py — RUN 9B: admission gate = BENCH JUDGE VERBATIM (sonnet_judge) + faceF_9b diet.

Gate: 220 problem-sets (4 generated threads each) scored blind by Sonnet 5 with the
PILOT8 foresight instrument (single session, shuffled, coverage 220/220 or discard).
Admission (frozen in RUNBOOK8): set mean >= 7.5 AND no leak-flagged thread.
Target >= 150 admitted problems; fewer -> STOP and report (top-up decision to Nikhil).

Diet: admitted generated rows + ONE original pos_thread per admitted problem
(deterministic index int(pid,16) % 4), all in prep_v5 worker format (byte-identical
templates). Bench overlap re-verified 0/48 at build.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/run8_build.py

Writes out/run8/gate.jsonl, data/run8/faceF_gen/worker_train.jsonl + manifest.json.
"""
from __future__ import annotations
import asyncio, hashlib, json, os, random, re, statistics, sys
from pathlib import Path

import httpx

import head2head_v5 as H  # noqa: F401
from rejudge_arms import sonnet_judge

ROOT = Path(__file__).resolve().parent.parent
DF = Path.home() / "Desktop/divergence-formula/corpus_run"
D8 = ROOT / "data/run9b"
OUTD = ROOT / "out/run9b"
BENCH = ROOT / "data/bench/problems.jsonl"
MODEL = "claude-sonnet-5"
KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SEM = asyncio.Semaphore(6)
MIN_ADMIT = 140
SET_BAR = 7.5

LANE_DEF_F = ("FORESIGHT: does the thread project a concrete consequence chain multiple "
              "steps deep — move -> reaction -> second-order effect -> end-state at a "
              "time horizon — with each step realistic and specific (not vague 'this may "
              "cause problems')?")

PROMPT = """You are scoring 4 candidate response threads to a decision problem, on ONE dimension only.

PROBLEM: {problem}

THREADS:
{threads}

Score EACH thread 1-10 on this dimension:
{lane_def}
Use the full range: 5-6 = typical competent response, 8+ = the dimension saturates the
text, 9-10 = exceptional. Score the dimension only — not overall quality.

Also flag each thread:
- leak: true if it imports historical/military/classical-era particulars foreign to the problem's own setting
- hedge: true if it fails to commit to one concrete course (lists alternatives, "might/could" without resolution)

Return ONLY JSON: {{"scores":[n,n,n,n],"leak":[b,b,b,b],"hedge":[b,b,b,b]}}"""

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


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        j = json.loads(m.group())
        s, lk, hg = j.get("scores"), j.get("leak"), j.get("hedge")
        if (isinstance(s, list) and len(s) == 4 and all(isinstance(x, int) and 1 <= x <= 10 for x in s)
                and isinstance(lk, list) and len(lk) == 4 and isinstance(hg, list) and len(hg) == 4):
            return {"scores": s, "leak": [bool(x) for x in lk], "hedge": [bool(x) for x in hg]}
    except Exception:
        pass
    return None


async def call(client, prompt):
    async with SEM:
        for a in range(5):
            try:
                r = await client.post("https://api.anthropic.com/v1/messages",
                                      headers={"x-api-key": KEY, "anthropic-version": "2023-06-01",
                                               "content-type": "application/json"},
                                      json={"model": MODEL, "max_tokens": 12000,
                                            "messages": [{"role": "user", "content": prompt}]},
                                      timeout=180)
                r.raise_for_status()
                text = "".join(p.get("text", "") for p in r.json().get("content", [])
                               if p.get("type") == "text").strip()
                j = parse(text)
                if j:
                    return j
            except Exception:
                await asyncio.sleep(3 * (a + 1))
    return None


async def main():
    if not KEY:
        sys.exit("ANTHROPIC_API_KEY not set")
    OUTD.mkdir(parents=True, exist_ok=True)
    by = {}
    for l in (D8 / "threads.jsonl").open():
        r = json.loads(l)
        by.setdefault(r["pid"], {})[r["idx"]] = (r["thread"], r["problem"])
    import hashlib as _h
    srcrows = {}
    SRC = [DF / "corpus_v5_train/passers.jsonl", DF / "corpus_v5_topup/passers.jsonl"]
    for _p in SRC:
        for _l in _p.open():
            _r = json.loads(_l)
            srcrows[_h.md5(_r["problem"].encode()).hexdigest()[:12]] = _r
    sets = []
    for p, th in by.items():
        if len(th) != 4:
            sys.exit(f"incomplete set {p}")
        sets.append({"pid": p, "problem": th[0][1], "threads": [th[i][0] for i in range(4)],
                     "angles": [f"[{a['family']}] {a['directive']}" if isinstance(a, dict) else str(a)
                                for a in srcrows[p]["angles"]]})
    random.Random(98).shuffle(sets)
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

    admitted = [r for r in results if r["judge"]["foresight"] >= 4 and r["judge"]["viability"] >= 3]
    fmean = statistics.mean(r["judge"]["foresight"] for r in results)
    vmean = statistics.mean(r["judge"]["viability"] for r in results)
    print(f"admitted {len(admitted)}/220 (bench-judge foresight>=4 & viability>=3) | "
          f"all-sets foresight {fmean:.2f} viability {vmean:.2f}")
    if len(admitted) < MIN_ADMIT:
        sys.exit(f"ADMISSION SHORTFALL: {len(admitted)} < {MIN_ADMIT} — STOP, top-up decision to Nikhil")

    # ---- build diet ----
    src = {}
    v5_train_rows = [json.loads(l) for l in (DF / "corpus_v5_train/passers.jsonl").open()]
    for r in v5_train_rows + [json.loads(l) for l in (DF / "corpus_v5_topup/passers.jsonl").open()]:
        src[hashlib.md5(r["problem"].encode()).hexdigest()[:12]] = r
    bench = {json.loads(l)["problem"] for l in BENCH.open()}
    gen_by_pid = by
    face_dir = D8 / "faceF_9b"
    face_dir.mkdir(exist_ok=True)
    admit_pids = {r["pid"] for r in admitted}
    n_gen = n_orig = 0
    with (face_dir / "worker_train.jsonl").open("w") as f:
        for pd in sorted(admit_pids):
            row = src[pd]
            if row["problem"] in bench:
                sys.exit(f"BENCH LEAK: {pd}")
            facets = " | ".join(row["facets"][:3])
            for k, ang in enumerate(row["angles"]):
                f.write(json.dumps(chat(WRK_SYS,
                                        WRK_USER.format(problem=row["problem"], facets=facets,
                                                        angle=fam(ang)),
                                        gen_by_pid[pd][k][0])) + "\n")
                n_gen += 1
            oi = int(pd, 16) % 4
            f.write(json.dumps(chat(WRK_SYS,
                                    WRK_USER.format(problem=row["problem"], facets=facets,
                                                    angle=fam(row["angles"][oi])),
                                    str(row["pos_threads"][oi]).strip())) + "\n")
            n_orig += 1
    md5 = hashlib.md5((face_dir / "worker_train.jsonl").read_bytes()).hexdigest()
    manifest = {"admitted_problems": len(admit_pids), "gen_rows": n_gen, "orig_rows": n_orig,
                "total_rows": n_gen + n_orig, "admission": "bench_judge foresight>=4 & viability>=3",
                "admitted_foresight_mean": round(statistics.mean(r["judge"]["foresight"] for r in admitted), 2),
                "worker_md5": md5}
    (face_dir / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    asyncio.run(main())
