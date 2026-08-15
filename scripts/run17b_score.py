"""
run17b_score.py — RUN 17B verdict: marking bar + the match + verifier rider
(RUNBOOK17B frozen readouts). Local; keys stay here.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/run17b_score.py --pod HOST:PORT   # pull + judge + verdict
  python scripts/run17b_score.py --mock            # $0 offline path test

Gold = STRICT_ONE byte-reused (same ruler as runs 15/16/17). 80 new reads,
cached (out/run17b/judge_cache.jsonl), SPEND CAP 90. Arm B (baseline) is the
run-17 output + run-17 judge cache — $0, never re-billed.

FROZEN READOUTS (RUNBOOK17B):
  PRIMARY  : arm M strict-clean >= 4/40  -> wall relocated to assertion policy
  MATCH    : per-arm per-level clean-rate + flaw totals, reported both ways
  VERIFIER : pooled gold-clean over M+R; if >= 5, FP > 30% -> stagnant-verifier
             thesis CONFIRMED
  AUTOPSY  : every M/R flaw printed with planted tokens for classification
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, os, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("ANTHROPIC_API_KEY", "")
from run16b_relabel import STRICT_ONE, acall, valid_one  # byte-reuse  # noqa: E402
import head2head_v5 as H  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out/run17b"
CACHE = OUT / "judge_cache.jsonl"
PROBS = ROOT / "data/run17/ladder_problems.jsonl"
B_OUT = ROOT / "out/run17/ladder17_out.jsonl"
B_CACHE = ROOT / "out/run17/judge_cache.jsonl"
CAP = 90
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
    todo = [r for r in rows if f"17b|{md5(r['answer'])[:12]}" not in cache]
    print(f"judge: {len(rows)} answers, {len(rows)-len(todo)} cached, {len(todo)} new "
          f"(cap {CAP})")
    if len(todo) > CAP:
        sys.exit("SPEND CAP — abort before billing")
    OUT.mkdir(parents=True, exist_ok=True)
    cf = CACHE.open("a")
    if MOCK:
        for r in todo:
            h = int(md5(r["answer"]), 16)
            v = {"coherent": h % 3 == 0, "flaws": [] if h % 3 == 0 else ["mock flaw"]}
            cf.write(json.dumps({"key": f"17b|{md5(r['answer'])[:12]}",
                                 "verdict": v, "_mock": True}) + "\n")
        cf.close()
        return load_cache(CACHE)
    import httpx

    async def one(client, r):
        p = probs[r["pid"]]["problem"]
        text = await acall(client, STRICT_ONE.format(problem=p, answer=r["answer"]))
        j = H.parse_json(text) if text else None
        if valid_one(j):
            cf.write(json.dumps({"key": f"17b|{md5(r['answer'])[:12]}",
                                 "verdict": j, "_mock": False}) + "\n")
            cf.flush()
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[one(client, r) for r in todo])
    cf.close()
    return load_cache(CACHE)


def planted(problem):
    return "; ".join(re.findall(r"\$[\d,]+|[A-Z][a-z]+ \d{1,2}|\d+ hours", problem))


def main():
    global MOCK
    ap = argparse.ArgumentParser()
    ap.add_argument("--pod")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    MOCK = args.mock
    probs = {json.loads(l)["pid"]: json.loads(l) for l in PROBS.open()}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "ladder17b_out.jsonl"
    if not MOCK:
        if not args.pod:
            sys.exit("need --pod HOST:PORT (or --mock)")
        host, port = args.pod.split(":")
        rc, o = sh(f"rsync -a --no-owner --no-group --partial --timeout=90 "
                   f"-e 'ssh -p {port} -o StrictHostKeyChecking=no' "
                   f"root@{host}:/workspace/div/out/ladder17b_out.jsonl {OUT}/")
        if rc != 0:
            sys.exit(f"pull failed: {o[-300:]}")
    if MOCK and not path.exists():
        rows = []
        for pid, p in probs.items():
            for arm in ("M", "R"):
                rows.append({"arm": arm, "pid": pid, "level": p["level"],
                             "answer": f"Mock {arm} answer {pid}. ESTIMATE: 60%",
                             "est_injected": False, "ver_flagged": pid % 2 == 0})
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    rows = [json.loads(l) for l in path.open()]
    assert len(rows) == 80, f"expected 80 answers (M+R x 40), got {len(rows)}"
    cache = asyncio.run(judge(rows, probs)) or load_cache(CACHE)
    missing = [r for r in rows if f"17b|{md5(r['answer'])[:12]}" not in cache]
    if missing:
        sys.exit(f"COVERAGE INSUFFICIENT: {len(missing)} unjudged — rerun")
    for r in rows:
        r["gold"] = cache[f"17b|{md5(r['answer'])[:12]}"]

    # arm B: run-17 baseline, cached verdicts, $0
    b_rows = [json.loads(l) for l in B_OUT.open()] if B_OUT.exists() else []
    b_cache = load_cache(B_CACHE)
    for r in b_rows:
        r["arm"] = "B"
        r["gold"] = b_cache.get(f"lad|{md5(r['answer'])[:12]}")
    b_rows = [r for r in b_rows if r["gold"]]

    ARMS = {"B": "baseline (run17 keep100)", "M": "keep100 + GROUND",
            "R": "Qwen3-4B-Thinking + GROUND"}
    print("\n========== RUN 17B — MARKING + THE MATCH ==========")
    table = {}
    for arm in ("B", "M", "R"):
        rs = [r for r in (b_rows if arm == "B" else rows) if r["arm"] == arm]
        clean = [r for r in rs if r["gold"]["coherent"]]
        flaws = sum(len(r["gold"].get("flaws", [])) for r in rs)
        per_lv = {lv: sum(1 for r in rs if r["level"] == lv and r["gold"]["coherent"])
                  for lv in (1, 2, 3, 4, 5)}
        table[arm] = {"clean": len(clean), "n": len(rs), "flaws": flaws,
                      "per_level": per_lv}
        lv_s = " ".join(f"L{lv}:{per_lv[lv]}/8" for lv in (1, 2, 3, 4, 5))
        print(f"  {arm} {ARMS[arm]:<28} clean {len(clean):>2}/{len(rs)} "
              f"({len(clean)/max(len(rs),1):.0%})  flaws {flaws:>3}   {lv_s}")

    m_clean = table["M"]["clean"]
    print(f"\nPRIMARY (marking bar, frozen >= 4/40): arm M {m_clean}/40 -> "
          f"{'PASS — wall relocated to ASSERTION POLICY' if m_clean >= 4 else 'FAIL — marking alone does not open the island'}")

    # verifier rider
    pool = [r for r in rows if r["gold"]["coherent"]]
    if len(pool) >= 5:
        fp = sum(1 for r in pool if r.get("ver_flagged")) / len(pool)
        print(f"VERIFIER RIDER: {len(pool)} gold-clean answers pooled (M+R); "
              f"ver_16 false-flag {sum(1 for r in pool if r.get('ver_flagged'))}/{len(pool)} "
              f"({fp:.0%}) -> "
              f"{'STAGNANT-VERIFIER THESIS CONFIRMED (FP > 30%)' if fp > 0.30 else 'verifier survives its first fair test (FP <= 30%)'}")
    else:
        print(f"VERIFIER RIDER: only {len(pool)} gold-clean answers (< 5) — "
              f"unmeasurable, recorded honestly")
    flawed = [r for r in rows if not r["gold"]["coherent"]]
    if flawed:
        rec = sum(1 for r in flawed if r.get("ver_flagged")) / len(flawed)
        print(f"  (recall on flawed, M+R: {rec:.0%})")

    res = {"table": {a: {k: v for k, v in t.items()} for a, t in table.items()},
           "primary_pass": m_clean >= 4,
           "gold_clean_pool": len(pool)}
    (OUT / "match_results.json").write_text(json.dumps(res, indent=1))

    print("\n---------- AUTOPSY DUMP (arms M, R) ----------")
    for r in sorted(rows, key=lambda x: (x["arm"], x["pid"])):
        fl = r["gold"].get("flaws", [])
        if not fl and r["gold"]["coherent"]:
            print(f"[{r['arm']} pid {r['pid']:02d} L{r['level']}] CLEAN"
                  f"{'  (ver FLAGGED)' if r.get('ver_flagged') else ''}")
            continue
        print(f"[{r['arm']} pid {r['pid']:02d} L{r['level']}] "
              f"PLANTED: {planted(probs[r['pid']]['problem'])}")
        for f in fl:
            print(f"    FLAW: {f if isinstance(f, str) else json.dumps(f)}")


if __name__ == "__main__":
    main()
