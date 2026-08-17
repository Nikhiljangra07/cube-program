"""
run19_score.py — RUN 19 verdict: the demand curve (RUNBOOK19 frozen readouts).
Local; keys stay here.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/run19_score.py --pod HOST:PORT
  python scripts/run19_score.py --mock

Gold = STRICT_ONE byte-reused, judged against the FULL problem text (the same
ruler as runs 15-18). 32 new reads (D1-D4), cached, SPEND CAP 40. D5 = the
cached run-17 L3 verdicts ($0 anchor, 0/8 strict-clean).

FROZEN READOUTS:
  PRIMARY : D1 AND D2 strict-clean >= 6/8 each -> demand-matching thesis
            validated (registered prediction: monotone rise D5 -> D1)
  SECONDARY: RULER-T clean per level (ruler_t.py verbatim); D4 [TBD]
            compliance; full autopsy dump
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("ANTHROPIC_API_KEY", "")
from run16b_relabel import STRICT_ONE, acall, valid_one  # byte-reuse  # noqa: E402
from ruler_t import classify  # noqa: E402
import head2head_v5 as H  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out/run19"
CACHE = OUT / "judge_cache.jsonl"
LADDER = ROOT / "data/run19/demand_ladder.jsonl"
CAP = 40
MOCK = False


def md5(t):
    return hashlib.md5(t.encode()).hexdigest()


def sh(cmd, timeout=600):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def load_cache(path):
    c = {}
    if path.exists():
        for l in path.open():
            r = json.loads(l)
            if bool(r.get("_mock")) == MOCK:
                c[r["key"]] = r["verdict"]
    return c


async def judge(rows, probs):
    cache = load_cache(CACHE)
    todo = [r for r in rows if f"d19|{md5(r['answer'])[:12]}" not in cache]
    print(f"judge: {len(rows)} answers, {len(rows)-len(todo)} cached, {len(todo)} new "
          f"(cap {CAP})")
    if len(todo) > CAP:
        sys.exit("SPEND CAP — abort before billing")
    OUT.mkdir(parents=True, exist_ok=True)
    cf = CACHE.open("a")
    if MOCK:
        for r in todo:
            h = int(md5(r["answer"]), 16)
            v = {"coherent": (h + r["dlevel"]) % 3 == 0, "flaws": ["mock flaw"] if (h + r["dlevel"]) % 3 else []}
            cf.write(json.dumps({"key": f"d19|{md5(r['answer'])[:12]}",
                                 "verdict": v, "_mock": True}) + "\n")
        cf.close()
        return load_cache(CACHE)
    import httpx

    async def one(client, r):
        text = await acall(client, STRICT_ONE.format(problem=probs[r["pid"]],
                                                     answer=r["answer"]))
        j = H.parse_json(text) if text else None
        if valid_one(j):
            cf.write(json.dumps({"key": f"d19|{md5(r['answer'])[:12]}",
                                 "verdict": j, "_mock": False}) + "\n")
            cf.flush()
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[one(client, r) for r in todo])
    cf.close()
    return load_cache(CACHE)


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
    probs = {json.loads(l)["pid"]: json.loads(l)["problem"] for l in LADDER.open()}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "demand19_out.jsonl"
    if not MOCK:
        if not args.pod:
            sys.exit("need --pod HOST:PORT (or --mock)")
        host, port = args.pod.split(":")
        rc, o = sh(f"rsync -a --no-owner --no-group --partial --timeout=90 "
                   f"-e 'ssh -p {port} -o StrictHostKeyChecking=no' "
                   f"root@{host}:/workspace/div/out/demand19_out.jsonl {OUT}/")
        if rc != 0:
            sys.exit(f"pull failed: {o[-300:]}")
    if MOCK and not path.exists():
        rows = [{"pid": p, "dlevel": d, "answer": f"Mock {p}/{d}. ESTIMATE: 60%",
                 "est_injected": False}
                for p in range(16, 24) for d in (1, 2, 3, 4)]
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    rows = [json.loads(l) for l in path.open()]
    assert len(rows) == 32, f"expected 32, got {len(rows)}"
    cache = asyncio.run(judge(rows, probs)) or load_cache(CACHE)
    missing = [r for r in rows if f"d19|{md5(r['answer'])[:12]}" not in cache]
    if missing:
        sys.exit(f"COVERAGE INSUFFICIENT: {len(missing)} unjudged — rerun")
    for r in rows:
        r["gold"] = cache[f"d19|{md5(r['answer'])[:12]}"]

    # D5 anchor: run-17 L3 cached
    d5 = []
    c17 = {}
    for l in (ROOT / "out/run17/judge_cache.jsonl").open():
        c = json.loads(l)
        if not c.get("_mock"):
            c17[c["key"]] = c["verdict"]
    for l in (ROOT / "out/run17/ladder17_out.jsonl").open():
        r = json.loads(l)
        if r["level"] == 3:
            v = c17.get(f"lad|{md5(r['answer'])[:12]}")
            if v:
                d5.append({"pid": r["pid"], "dlevel": 5, "answer": r["answer"], "gold": v})
    allr = rows + d5

    print("\n========== RUN 19 — THE DEMAND CURVE ==========")
    print(f"{'level':>6} {'strict':>8} {'RULER-T':>8}   demand")
    NAMES = {1: "atomic extract/derive", 2: "single judgment", 3: "bounded choice",
             4: "plan-lite ([TBD] allowed)", 5: "full plan (run-17 anchor)"}
    res = {}
    for d in (1, 2, 3, 4, 5):
        rs = [r for r in allr if r["dlevel"] == d]
        s = sum(1 for r in rs if r["gold"]["coherent"])
        t = sum(1 for r in rs if rulert_clean(r["gold"]))
        res[d] = {"n": len(rs), "strict": s, "rulert": t}
        print(f"    D{d} {s:>5}/{len(rs)} {t:>5}/{len(rs)}   {NAMES[d]}")
    p = res[1]["strict"] >= 6 and res[2]["strict"] >= 6
    print(f"\nPRIMARY (D1>=6/8 AND D2>=6/8 strict): "
          f"{'PASS — demand-matching thesis VALIDATED' if p else 'FAIL — recorded honestly'}")
    tbd = sum(1 for r in rows if r["dlevel"] == 4 and "[TBD]" in r["answer"])
    print(f"D4 [TBD] compliance: {tbd}/8 answers used the escape hatch")
    (OUT / "demand_results.json").write_text(json.dumps(
        {"curve": res, "primary_pass": p, "d4_tbd": tbd}, indent=1))

    print("\n---------- AUTOPSY (D1-D4 flaws) ----------")
    for r in sorted(rows, key=lambda x: (x["dlevel"], x["pid"])):
        fl = r["gold"].get("flaws", [])
        if r["gold"]["coherent"]:
            continue
        print(f"[D{r['dlevel']} pid {r['pid']}]")
        for f in fl:
            f = f if isinstance(f, str) else json.dumps(f)
            print(f"    [{classify(f)}] {f}")


if __name__ == "__main__":
    main()
