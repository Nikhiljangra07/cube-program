"""
run21_score.py — RUN 21 verdict: THE REMATCH, dual-ruler (RUNBOOK21 frozen).
Local; keys stay here.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/run21_score.py --pod HOST:PORT
  python scripts/run21_score.py --mock

Rulers:
  STRICT_ONE : byte-reused, unchanged — the comparability spine.
  STRICT_D   : ⚠ LABELED PROSPECTIVE INSTRUMENT (frozen here, first use this
               run): STRICT_ONE plus a derivation exemption — a number
               explicitly derived from given figures WITH ITS BASIS SHOWN and
               correct arithmetic is grounded. Built by asserted .replace() on
               the exemption sentence so the diff is exactly one clause.
  RULER-T    : computed from STRICT_ONE flaw prose (ruler_t.py verbatim).

32 answers x 2 rulers = 64 reads, cached, SPEND CAP 70.

FROZEN READOUTS:
  PRIMARY (STRICT-D): CUBE clean >= 10/16 AND CUBE >= GEN + 4
  SECONDARY: strict + RULER-T tables; d1_ok / est_injected counts; autopsy.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("ANTHROPIC_API_KEY", "")
from run16b_relabel import STRICT_ONE, acall, valid_one  # byte-reuse  # noqa: E402
from ruler_t import classify  # noqa: E402
import head2head_v5 as H  # noqa: E402

_EXEMPT = ("A final success-estimate percentage line is allowed and does not count "
           "as an invented number.")
_EXEMPT_D = (_EXEMPT + " A number explicitly DERIVED from figures given in the "
             "problem, with its basis shown inline (for example '15 days (July 8 "
             "to July 23)' or '$12,000, the gap between $17,000 and $5,000'), is "
             "also allowed and does not count as invented, PROVIDED the arithmetic "
             "is correct.")
STRICT_D = STRICT_ONE.replace(_EXEMPT, _EXEMPT_D)
assert STRICT_D != STRICT_ONE, "STRICT_D build failed — exemption sentence drifted"

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out/run21"
CACHE = OUT / "judge_cache.jsonl"
PROBS = ROOT / "data/run21/rematch_problems.jsonl"
CAP = 70
MOCK = False
RULERS = {"one": STRICT_ONE, "d": STRICT_D}


def md5(t):
    return hashlib.md5(t.encode()).hexdigest()


def sh(cmd, timeout=600):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


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
    todo = [(r, rk) for r in rows for rk in RULERS
            if f"r21|{rk}|{md5(r['answer'])[:12]}" not in cache]
    print(f"judge: {len(rows)} answers x 2 rulers, "
          f"{len(rows)*2-len(todo)} cached, {len(todo)} new (cap {CAP})")
    if len(todo) > CAP:
        sys.exit("SPEND CAP — abort before billing")
    OUT.mkdir(parents=True, exist_ok=True)
    cf = CACHE.open("a")
    if MOCK:
        for r, rk in todo:
            h = int(md5(r["answer"] + rk), 16)
            v = {"coherent": h % 2 == 0, "flaws": [] if h % 2 == 0 else ["mock flaw"]}
            cf.write(json.dumps({"key": f"r21|{rk}|{md5(r['answer'])[:12]}",
                                 "verdict": v, "_mock": True}) + "\n")
        cf.close()
        return load_cache()
    import httpx

    async def one(client, r, rk):
        text = await acall(client, RULERS[rk].format(problem=probs[r["pid"]],
                                                     answer=r["answer"]))
        j = H.parse_json(text) if text else None
        if valid_one(j):
            cf.write(json.dumps({"key": f"r21|{rk}|{md5(r['answer'])[:12]}",
                                 "verdict": j, "_mock": False}) + "\n")
            cf.flush()
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[one(client, r, rk) for r, rk in todo])
    cf.close()
    return load_cache()


def rulert_clean(v):
    return v["coherent"] or all(
        classify(f if isinstance(f, str) else str(f)) == "ADD" for f in v.get("flaws", []))


def main():
    global MOCK
    ap = argparse.ArgumentParser()
    ap.add_argument("--pod")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    MOCK = args.mock
    probs = {json.loads(l)["pid"]: json.loads(l)["problem"] for l in PROBS.open()}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "rematch21_out.jsonl"
    if not MOCK:
        if not args.pod:
            sys.exit("need --pod HOST:PORT (or --mock)")
        host, port = args.pod.split(":")
        rc, o = sh(f"rsync -a --no-owner --no-group --partial --timeout=90 "
                   f"-e 'ssh -p {port} -o StrictHostKeyChecking=no' "
                   f"root@{host}:/workspace/div/out/rematch21_out.jsonl {OUT}/")
        if rc != 0:
            sys.exit(f"pull failed: {o[-300:]}")
    if MOCK and not path.exists():
        rows = [{"arm": a, "pid": p, "answer": f"Mock {a}{p}. ESTIMATE: 60%",
                 "d1_ok": True, "est_injected": False}
                for p in range(16) for a in ("C", "G")]
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    rows = [json.loads(l) for l in path.open()]
    assert len(rows) == 32, f"expected 32 answers, got {len(rows)}"
    cache = asyncio.run(judge(rows, probs)) or load_cache()
    missing = [(r, rk) for r in rows for rk in RULERS
               if f"r21|{rk}|{md5(r['answer'])[:12]}" not in cache]
    if missing:
        sys.exit(f"COVERAGE INSUFFICIENT: {len(missing)} unjudged — rerun")
    for r in rows:
        r["g1"] = cache[f"r21|one|{md5(r['answer'])[:12]}"]
        r["gd"] = cache[f"r21|d|{md5(r['answer'])[:12]}"]

    print("\n========== RUN 21 — THE REMATCH (dual-ruler) ==========")
    print(f"{'arm':>5} {'strict':>7} {'STRICT-D':>9} {'RULER-T':>8}")
    res = {}
    for a, name in (("C", "CUBE-v2 (staged)"), ("G", "GENERALIST (naked)")):
        rs = [r for r in rows if r["arm"] == a]
        s1 = sum(1 for r in rs if r["g1"]["coherent"])
        sd = sum(1 for r in rs if r["gd"]["coherent"])
        st = sum(1 for r in rs if rulert_clean(r["g1"]))
        res[a] = {"strict": s1, "strict_d": sd, "rulert": st}
        print(f"    {a} {s1:>4}/16 {sd:>6}/16 {st:>5}/16   {name}")
    c, g = res["C"]["strict_d"], res["G"]["strict_d"]
    p = c >= 10 and c >= g + 4
    print(f"\nPRIMARY (STRICT-D: CUBE >= 10/16 AND CUBE >= GEN+4): "
          f"CUBE {c}/16 vs GEN {g}/16 -> "
          f"{'PASS — THE CUBE WINS THE REMATCH' if p else 'FAIL — recorded honestly'}")
    d1ok = sum(1 for r in rows if r["arm"] == "C" and r.get("d1_ok"))
    inj = sum(1 for r in rows if r.get("est_injected"))
    print(f"pipeline integrity: d1 code-check {d1ok}/16 · est injected {inj}")
    (OUT / "rematch_results.json").write_text(json.dumps(
        {"table": res, "primary_pass": p, "d1_ok": d1ok}, indent=1))

    print("\n---------- AUTOPSY (STRICT-D flaws) ----------")
    for r in sorted(rows, key=lambda x: (x["arm"], x["pid"])):
        if r["gd"]["coherent"]:
            continue
        print(f"[{r['arm']} pid {r['pid']:02d}]")
        for fl in r["gd"].get("flaws", []):
            fl = fl if isinstance(fl, str) else json.dumps(fl)
            print(f"    [{classify(fl)}] {fl}")


if __name__ == "__main__":
    main()
