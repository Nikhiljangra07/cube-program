"""
run22_score.py — RUN 22 verdict: the locked holdout, dual-ruler + blind
quality rubric (RUNBOOK22 frozen readouts). Local; keys stay here.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/run22_score.py --pod HOST:PORT
  python scripts/run22_score.py --mock

Rulers: STRICT_ONE + STRICT_D byte-reused from run21_score (problem-text
generic). NEW: QUAL — 4-dim 1-5 blind quality read (audit finding #1),
same read for both arms, judge never sees arm labels.
32 answers x 3 reads = 96, cached, SPEND CAP 105.

FROZEN (RUNBOOK22): PRIMARY = STRICT-D CUBE >= 6/16 AND CUBE >= GEN+4.
Registered prediction: cube >= gen on constraint_fidelity. No other bars.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("ANTHROPIC_API_KEY", "")
from run16b_relabel import acall  # noqa: E402
from run21_score import RULERS  # STRICT_ONE + STRICT_D byte-reuse  # noqa: E402
from ruler_t import classify  # noqa: E402
import head2head_v5 as H  # noqa: E402

QUAL = """You are grading ONE answer to a strategic decision problem. Score 1-5 on
each dimension. Be strict; 3 = adequate.

PROBLEM: {problem}

ANSWER:
{answer}

Dimensions:
- constraint_fidelity: are stated limits (deadlines, caps, resources) respected
  and correctly applied?
- prediction_quality: is the counterparty read plausible, conditional, and
  falsifiable?
- action_quality: is the chosen course concrete, executable within the stated
  constraints, and well-grounded?
- calibration: does the final estimate follow from the analysis (not a
  reflexive round number)?

Return ONLY JSON: {{"constraint_fidelity":n,"prediction_quality":n,"action_quality":n,"calibration":n}}"""

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out/run22"
CACHE = OUT / "judge_cache.jsonl"
PROBS = ROOT / "data/run22/holdout_problems.jsonl"
CAP = 105
MOCK = False
QDIMS = ("constraint_fidelity", "prediction_quality", "action_quality", "calibration")


def md5(t):
    return hashlib.md5(t.encode()).hexdigest()


def sh(cmd, timeout=600):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def valid_ruler(j):
    return isinstance(j, dict) and isinstance(j.get("coherent"), bool) \
        and isinstance(j.get("flaws"), list)


def valid_qual(j):
    return isinstance(j, dict) and all(
        isinstance(j.get(d), (int, float)) and 1 <= j[d] <= 5 for d in QDIMS)


def load_cache():
    c = {}
    if CACHE.exists():
        for l in CACHE.open():
            r = json.loads(l)
            if bool(r.get("_mock")) == MOCK:
                c[r["key"]] = r["verdict"]
    return c


async def judge(rows, probs):
    cache = load_cache()
    kinds = list(RULERS) + ["q"]
    todo = [(r, k) for r in rows for k in kinds
            if f"r22|{k}|{md5(r['answer'])[:12]}" not in cache]
    print(f"judge: {len(rows)} answers x 3 reads, "
          f"{len(rows)*3-len(todo)} cached, {len(todo)} new (cap {CAP})")
    if len(todo) > CAP:
        sys.exit("SPEND CAP — abort before billing")
    OUT.mkdir(parents=True, exist_ok=True)
    cf = CACHE.open("a")
    if MOCK:
        for r, k in todo:
            h = int(md5(r["answer"] + k), 16)
            v = ({d: (h >> i) % 5 + 1 for i, d in enumerate(QDIMS)} if k == "q"
                 else {"coherent": h % 2 == 0,
                       "flaws": [] if h % 2 == 0 else ["mock flaw"]})
            cf.write(json.dumps({"key": f"r22|{k}|{md5(r['answer'])[:12]}",
                                 "verdict": v, "_mock": True}) + "\n")
        cf.close()
        return load_cache()
    import httpx

    async def one(client, r, k):
        tmpl = QUAL if k == "q" else RULERS[k]
        text = await acall(client, tmpl.format(problem=probs[r["pid"]],
                                               answer=r["answer"]))
        j = H.parse_json(text) if text else None
        if (valid_qual(j) if k == "q" else valid_ruler(j)):
            cf.write(json.dumps({"key": f"r22|{k}|{md5(r['answer'])[:12]}",
                                 "verdict": j, "_mock": False}) + "\n")
            cf.flush()
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[one(client, r, k) for r, k in todo])
    cf.close()
    return load_cache()


def rulert_clean(v):
    return v["coherent"] or all(
        classify(f if isinstance(f, str) else str(f)) == "ADD"
        for f in v.get("flaws", []))


def main():
    global MOCK
    ap = argparse.ArgumentParser()
    ap.add_argument("--pod")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    MOCK = args.mock
    probs = {json.loads(l)["pid"]: json.loads(l)["problem"] for l in PROBS.open()}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "holdout22_out.jsonl"
    if not MOCK:
        if not args.pod:
            sys.exit("need --pod HOST:PORT (or --mock)")
        host, port = args.pod.split(":")
        rc, o = sh(f"rsync -a --no-owner --no-group --partial --timeout=90 "
                   f"-e 'ssh -p {port} -o StrictHostKeyChecking=no' "
                   f"root@{host}:/workspace/div/out/holdout22_out.jsonl {OUT}/")
        if rc != 0:
            sys.exit(f"pull failed: {o[-300:]}")
    if MOCK and not path.exists():
        rows = [{"arm": a, "pid": p, "answer": f"Mock {a}{p}. ESTIMATE: 60%"}
                for p in range(16) for a in ("C", "G")]
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    rows = [json.loads(l) for l in path.open()]
    assert len(rows) == 32, f"expected 32 answers, got {len(rows)}"
    cache = asyncio.run(judge(rows, probs)) or load_cache()
    missing = [(r, k) for r in rows for k in ("one", "d", "q")
               if f"r22|{k}|{md5(r['answer'])[:12]}" not in cache]
    if missing:
        sys.exit(f"COVERAGE INSUFFICIENT: {len(missing)} unjudged — rerun")
    for r in rows:
        r["g1"] = cache[f"r22|one|{md5(r['answer'])[:12]}"]
        r["gd"] = cache[f"r22|d|{md5(r['answer'])[:12]}"]
        r["q"] = cache[f"r22|q|{md5(r['answer'])[:12]}"]

    print("\n========== RUN 22 — THE LOCKED HOLDOUT ==========")
    print(f"{'arm':>5} {'strict':>7} {'STRICT-D':>9} {'RULER-T':>8}  quality (cf/pq/aq/cal)")
    res = {}
    for a, name in (("C", "CUBE-v2 generalized"), ("G", "GENERALIST naked")):
        rs = [r for r in rows if r["arm"] == a]
        s1 = sum(1 for r in rs if r["g1"]["coherent"])
        sd = sum(1 for r in rs if r["gd"]["coherent"])
        st = sum(1 for r in rs if rulert_clean(r["g1"]))
        qm = {d: sum(r["q"][d] for r in rs) / len(rs) for d in QDIMS}
        res[a] = {"strict": s1, "strict_d": sd, "rulert": st,
                  "qual": {d: round(qm[d], 2) for d in QDIMS}}
        print(f"    {a} {s1:>4}/16 {sd:>6}/16 {st:>5}/16  "
              + "/".join(f"{qm[d]:.2f}" for d in QDIMS) + f"   {name}")
    c, g = res["C"]["strict_d"], res["G"]["strict_d"]
    p = c >= 6 and c >= g + 4
    print(f"\nPRIMARY (STRICT-D: CUBE >= 6/16 AND >= GEN+4): CUBE {c} vs GEN {g} -> "
          f"{'PASS — THE ARCHITECTURE GENERALIZES' if p else 'FAIL — recorded honestly'}")
    cf_pred = res["C"]["qual"]["constraint_fidelity"] >= res["G"]["qual"]["constraint_fidelity"]
    print(f"registered prediction (cube >= gen on constraint_fidelity): "
          f"{'HELD' if cf_pred else 'FAILED'}")
    crows = [r for r in rows if r["arm"] == "C"]
    if crows and "n_facts" in crows[0]:
        print("pipeline: facts/problem avg %.1f (dropped avg %.1f) · compare %d/16 · "
              "span %d/16 · guard %d (fail %d) · screen %d (fail %d)" % (
                  sum(r["n_facts"] for r in crows) / len(crows),
                  sum(r.get("n_dropped", 0) for r in crows) / len(crows),
                  sum(1 for r in crows if r.get("has_compare")),
                  sum(1 for r in crows if r.get("has_span")),
                  sum(1 for r in crows if r.get("guarded")),
                  sum(1 for r in crows if r.get("guard_fail")),
                  sum(1 for r in crows if r.get("screened")),
                  sum(1 for r in crows if r.get("screen_fail"))))
    (OUT / "holdout_results.json").write_text(json.dumps(
        {"table": res, "primary_pass": p, "cf_prediction_held": cf_pred}, indent=1))

    print("\n---------- AUTOPSY (STRICT-D flaws, both arms) ----------")
    for r in sorted(rows, key=lambda x: (x["arm"], x["pid"])):
        if r["gd"]["coherent"]:
            continue
        print(f"[{r['arm']} pid {r['pid']:02d}]")
        for fl in r["gd"].get("flaws", []):
            fl = fl if isinstance(fl, str) else json.dumps(fl)
            print(f"    [{classify(fl)}] {fl}")


if __name__ == "__main__":
    main()
