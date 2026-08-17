"""
run20_score.py — RUN 20 verdict: staged vs unstaged (RUNBOOK20 frozen
readouts). Local; keys stay here.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/run20_score.py --pod HOST:PORT
  python scripts/run20_score.py --mock

Gold = STRICT_ONE byte-reused, judged against the FULL problem text (anchor is
harness text, not model output — but judged as part of the answer? NO: the
judge sees problem + the model's ANSWER only, same as every prior run).
16 reads, cached, SPEND CAP 24. Baseline = run-19 D2/D3 cached verdicts ($0).

FROZEN READOUTS:
  PRIMARY : staged D2 >= 6/8 AND staged D3 >= 6/8 strict-clean
  SECONDARY: RULER-T per level; lift vs run-19 baseline (D2 5/8, D3 3/8);
             constraint-conflation count (T1 flaws touching the sign-off cap)
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
OUT = ROOT / "out/run20"
CACHE = OUT / "judge_cache.jsonl"
CAP = 24
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
    todo = [r for r in rows if f"s20|{md5(r['answer'])[:12]}" not in cache]
    print(f"judge: {len(rows)} answers, {len(rows)-len(todo)} cached, {len(todo)} new "
          f"(cap {CAP})")
    if len(todo) > CAP:
        sys.exit("SPEND CAP — abort before billing")
    OUT.mkdir(parents=True, exist_ok=True)
    cf = CACHE.open("a")
    if MOCK:
        for r in todo:
            h = int(md5(r["answer"]), 16)
            v = {"coherent": h % 2 == 0, "flaws": [] if h % 2 == 0 else ["mock flaw"]}
            cf.write(json.dumps({"key": f"s20|{md5(r['answer'])[:12]}",
                                 "verdict": v, "_mock": True}) + "\n")
        cf.close()
        return load_cache(CACHE)
    import httpx

    async def one(client, r):
        text = await acall(client, STRICT_ONE.format(problem=probs[r["pid"]],
                                                     answer=r["answer"]))
        j = H.parse_json(text) if text else None
        if valid_one(j):
            cf.write(json.dumps({"key": f"s20|{md5(r['answer'])[:12]}",
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
    probs = {json.loads(l)["pid"]: json.loads(l)["problem"]
             for l in (ROOT / "data/run17/ladder_problems.jsonl").open()
             if json.loads(l)["level"] == 3}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "staged20_out.jsonl"
    if not MOCK:
        if not args.pod:
            sys.exit("need --pod HOST:PORT (or --mock)")
        host, port = args.pod.split(":")
        rc, o = sh(f"rsync -a --no-owner --no-group --partial --timeout=90 "
                   f"-e 'ssh -p {port} -o StrictHostKeyChecking=no' "
                   f"root@{host}:/workspace/div/out/staged20_out.jsonl {OUT}/")
        if rc != 0:
            sys.exit(f"pull failed: {o[-300:]}")
    if MOCK and not path.exists():
        rows = [{"pid": p, "dlevel": d, "answer": f"Mock staged {p}/{d}."}
                for p in range(16, 24) for d in (2, 3)]
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    rows = [json.loads(l) for l in path.open()]
    assert len(rows) == 16, f"expected 16, got {len(rows)}"
    cache = asyncio.run(judge(rows, probs)) or load_cache(CACHE)
    missing = [r for r in rows if f"s20|{md5(r['answer'])[:12]}" not in cache]
    if missing:
        sys.exit(f"COVERAGE INSUFFICIENT: {len(missing)} unjudged — rerun")
    for r in rows:
        r["gold"] = cache[f"s20|{md5(r['answer'])[:12]}"]

    # baseline: run-19 D2/D3 cached
    c19 = load_cache(ROOT / "out/run19/judge_cache.jsonl")
    base = []
    for l in (ROOT / "out/run19/demand19_out.jsonl").open():
        r = json.loads(l)
        if r["dlevel"] in (2, 3):
            v = c19.get(f"d19|{md5(r['answer'])[:12]}")
            if v:
                base.append({"pid": r["pid"], "dlevel": r["dlevel"], "gold": v})

    print("\n========== RUN 20 — STAGED vs UNSTAGED ==========")
    print(f"{'level':>6} {'unstaged':>9} {'staged':>7}   (strict | RULER-T staged)")
    res = {}
    for d in (2, 3):
        b = [r for r in base if r["dlevel"] == d]
        s = [r for r in rows if r["dlevel"] == d]
        bs = sum(1 for r in b if r["gold"]["coherent"])
        ss = sum(1 for r in s if r["gold"]["coherent"])
        st = sum(1 for r in s if rulert_clean(r["gold"]))
        res[d] = {"unstaged": bs, "staged": ss, "staged_rulert": st}
        print(f"    D{d} {bs:>6}/8 {ss:>5}/8   ({st}/8 RULER-T)")
    p = res[2]["staged"] >= 6 and res[3]["staged"] >= 6
    cap_flaws = sum(1 for r in rows for f in r["gold"].get("flaws", [])
                    if classify(str(f)) == "T1" and ("sign-off" in str(f) or "threshold" in str(f) or "cap" in str(f)))
    print(f"\nPRIMARY (staged D2>=6/8 AND D3>=6/8 strict): "
          f"{'PASS — the chain is complete' if p else 'FAIL — recorded honestly'}")
    print(f"constraint-conflation T1 flaws touching the cap: {cap_flaws} "
          f"(run-19 unstaged had 6)")
    (OUT / "staged_results.json").write_text(json.dumps(
        {"table": res, "primary_pass": p, "cap_conflation_flaws": cap_flaws}, indent=1))

    print("\n---------- AUTOPSY (staged flaws) ----------")
    for r in sorted(rows, key=lambda x: (x["dlevel"], x["pid"])):
        if r["gold"]["coherent"]:
            continue
        print(f"[S D{r['dlevel']} pid {r['pid']}]")
        for f in r["gold"].get("flaws", []):
            f = f if isinstance(f, str) else json.dumps(f)
            print(f"    [{classify(f)}] {f}")


if __name__ == "__main__":
    main()
