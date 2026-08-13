"""
run17_score.py — RUN 17 verdict: the capacity curve + verifier tracking
(RUNBOOK17 frozen readouts). Local; keys stay here.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/run17_score.py --pod HOST:PORT   # pull + judge + curves
  python scripts/run17_score.py --mock            # $0 offline path test

Gold = strict single-ruler coherence read (STRICT_ONE byte-reused from
run16b_relabel.py — the same criterion as the match and run 16). 40 reads,
cached (out/run17/judge_cache.jsonl), SPEND CAP 50.

FROZEN READOUTS:
  capacity curve : gold clean-rate per level; ENVELOPE-70 = highest level with
                   clean-rate >= 70%; ENVELOPE-50 likewise (8 problems/level ->
                   one problem = 12.5 points; reported with counts).
  verifier bars  : at levels where gold clean-rate >= 50%: false-flag rate on
                   gold-clean answers <= 30%  ->  "gate-viable within envelope";
                   flaw recall reported at every level.
  sanity guard   : if L3 (match-like load) clean-rate >> the match's 5.4%, the
                   load hypothesis is confounded by style — record honestly.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("ANTHROPIC_API_KEY", "")
from run16b_relabel import STRICT_ONE, acall, valid_one  # byte-reuse  # noqa: E402
import head2head_v5 as H  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out/run17"
CACHE = OUT / "judge_cache.jsonl"
PROBS = ROOT / "data/run17/ladder_problems.jsonl"
CAP = 50
MOCK = False


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
    todo = [r for r in rows if f"lad|{md5(r['answer'])[:12]}" not in cache]
    print(f"judge: {len(rows)} answers, {len(rows)-len(todo)} cached, {len(todo)} new "
          f"(cap {CAP})")
    if len(todo) > CAP:
        sys.exit("SPEND CAP — abort before billing")
    OUT.mkdir(parents=True, exist_ok=True)
    cf = CACHE.open("a")
    if MOCK:
        for r in todo:
            h = int(md5(r["answer"]), 16)
            v = {"coherent": (h + r["level"]) % (r["level"] + 1) == 0, "flaws": []}
            cf.write(json.dumps({"key": f"lad|{md5(r['answer'])[:12]}",
                                 "verdict": v, "_mock": True}) + "\n")
        cf.close()
        return load_cache()
    import httpx

    async def one(client, r):
        p = probs[r["pid"]]["problem"]
        text = await acall(client, STRICT_ONE.format(problem=p, answer=r["answer"]))
        j = H.parse_json(text) if text else None
        if valid_one(j):
            cf.write(json.dumps({"key": f"lad|{md5(r['answer'])[:12]}",
                                 "verdict": j, "_mock": False}) + "\n")
            cf.flush()
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[one(client, r) for r in todo])
    cf.close()
    return load_cache()


def main():
    global MOCK
    ap = argparse.ArgumentParser()
    ap.add_argument("--pod")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    MOCK = args.mock
    probs = {json.loads(l)["pid"]: json.loads(l) for l in PROBS.open()}
    OUT.mkdir(parents=True, exist_ok=True)
    if not MOCK:
        if not args.pod:
            sys.exit("need --pod HOST:PORT (or --mock)")
        host, port = args.pod.split(":")
        rc, o = sh(f"rsync -a --no-owner --no-group --partial --timeout=90 "
                   f"-e 'ssh -p {port} -o StrictHostKeyChecking=no' "
                   f"root@{host}:/workspace/div/out/ladder17_out.jsonl {OUT}/")
        if rc != 0:
            sys.exit(f"pull failed: {o[-300:]}")
    path = OUT / "ladder17_out.jsonl"
    if MOCK and not path.exists():
        rows = []
        for pid, p in probs.items():
            rows.append({"pid": pid, "level": p["level"],
                         "answer": f"Mock answer {pid} referencing the facts. ESTIMATE: 60%",
                         "est_injected": False, "ver_flagged": pid % 3 == 0})
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    rows = [json.loads(l) for l in path.open()]
    assert len(rows) == 40, f"expected 40 answers, got {len(rows)}"
    cache = asyncio.run(judge(rows, probs)) or load_cache()
    missing = [r for r in rows if f"lad|{md5(r['answer'])[:12]}" not in cache]
    if missing:
        sys.exit(f"COVERAGE INSUFFICIENT: {len(missing)} unjudged — rerun")
    for r in rows:
        r["gold"] = cache[f"lad|{md5(r['answer'])[:12]}"]

    print("\n========== RUN 17 — THE CAPACITY CURVE ==========")
    print(f"{'level':>5} {'facts':>5} {'clean':>9} {'ver flag%':>9} "
          f"{'FP(on clean)':>13} {'recall(flawed)':>14}")
    env70 = env50 = 0
    table = {}
    for lv in (1, 2, 3, 4, 5):
        rs = [r for r in rows if r["level"] == lv]
        clean = [r for r in rs if r["gold"]["coherent"]]
        flawed = [r for r in rs if not r["gold"]["coherent"]]
        rate = len(clean) / len(rs)
        flag = sum(1 for r in rs if r.get("ver_flagged")) / len(rs)
        fp = (sum(1 for r in clean if r.get("ver_flagged")) / len(clean)
              if clean else None)
        rec = (sum(1 for r in flawed if r.get("ver_flagged")) / len(flawed)
               if flawed else None)
        nf = {1: 2, 2: 4, 3: 6, 4: 8, 5: 10}[lv]
        if rate >= 0.70:
            env70 = lv
        if rate >= 0.50:
            env50 = lv
        table[lv] = {"n": len(rs), "clean": len(clean), "clean_rate": round(rate, 3),
                     "ver_flag_rate": round(flag, 3),
                     "fp_on_clean": round(fp, 3) if fp is not None else None,
                     "recall_on_flawed": round(rec, 3) if rec is not None else None}
        print(f"   L{lv} {nf:>5} {len(clean):>2}/8 ({rate:>4.0%}) {flag:>8.0%} "
              f"{('%d/%d' % (sum(1 for r in clean if r.get('ver_flagged')), len(clean))) if clean else '   —':>13} "
              f"{('%d/%d' % (sum(1 for r in flawed if r.get('ver_flagged')), len(flawed))) if flawed else '   —':>14}")
    gate_levels = [lv for lv in table if table[lv]["clean_rate"] >= 0.5]
    gate_ok = all(table[lv]["fp_on_clean"] is not None
                  and table[lv]["fp_on_clean"] <= 0.30 for lv in gate_levels) \
        if gate_levels else False
    res = {"table": table, "envelope_70": env70, "envelope_50": env50,
           "gate_levels": gate_levels,
           "verifier_gate_viable_within_envelope": gate_ok,
           "sanity_L3_vs_match": f"L3 {table[3]['clean_rate']} vs match 0.054"}
    (OUT / "ladder_results.json").write_text(json.dumps(res, indent=1))
    print(f"\nENVELOPE-70: L{env70} ({'none' if not env70 else str({1:2,2:4,3:6,4:8,5:10}[env70])+' facts'})"
          f" | ENVELOPE-50: L{env50}")
    print(f"verifier within envelope (levels {gate_levels}): "
          f"{'GATE-VIABLE' if gate_ok else 'NOT gate-viable'} (FP<=30% bar)")
    print(f"sanity: {res['sanity_L3_vs_match']} (>>0.054 would confound load with style)")


if __name__ == "__main__":
    main()
