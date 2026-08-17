"""
run21b_score.py — RUN 21B verdict (RUNBOOK21 21B amendment). Judges ONLY the
16 regenerated C answers x 2 rulers (32 reads, cap 40); arm G's run-21 answers
and cached verdicts stand. Same cache file and key space as run 21 — if a
regenerated answer is byte-identical to run 21's, its verdicts are cache hits.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/run21b_score.py --pod HOST:PORT

Bars carried over VERBATIM: STRICT-D CUBE >= 10/16 AND CUBE >= GEN + 4.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("ANTHROPIC_API_KEY", "")
import run21_score as R  # byte-reuse: rulers, cache, judge, rulert  # noqa: E402
from ruler_t import classify  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out/run21"


def md5(t):
    return hashlib.md5(t.encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pod", required=True)
    args = ap.parse_args()
    probs = {json.loads(l)["pid"]: json.loads(l)["problem"] for l in R.PROBS.open()}
    host, port = args.pod.split(":")
    rc, o = R.sh(f"rsync -a --no-owner --no-group --partial --timeout=90 "
                 f"-e 'ssh -p {port} -o StrictHostKeyChecking=no' "
                 f"root@{host}:/workspace/div/out/rematch21b_out.jsonl {OUT}/")
    if rc != 0:
        sys.exit(f"pull failed: {o[-300:]}")
    c_rows = [json.loads(l) for l in (OUT / "rematch21b_out.jsonl").open()]
    assert len(c_rows) == 16
    g_rows = [json.loads(l) for l in (OUT / "rematch21_out.jsonl").open()
              if json.loads(l)["arm"] == "G"]
    R.CAP = 40
    cache = asyncio.run(R.judge(c_rows, probs)) or R.load_cache()
    for rows in (c_rows, g_rows):
        for r in rows:
            r["g1"] = cache[f"r21|one|{md5(r['answer'])[:12]}"]
            r["gd"] = cache[f"r21|d|{md5(r['answer'])[:12]}"]

    print("\n========== RUN 21B — THE GUARDED REMATCH ==========")
    print(f"{'arm':>5} {'strict':>7} {'STRICT-D':>9} {'RULER-T':>8}")
    res = {}
    for a, rows, name in (("C", c_rows, "CUBE-v2 + guard/screen"),
                          ("G", g_rows, "GENERALIST (run-21 cached)")):
        s1 = sum(1 for r in rows if r["g1"]["coherent"])
        sd = sum(1 for r in rows if r["gd"]["coherent"])
        st = sum(1 for r in rows if R.rulert_clean(r["g1"]))
        res[a] = {"strict": s1, "strict_d": sd, "rulert": st}
        print(f"    {a} {s1:>4}/16 {sd:>6}/16 {st:>5}/16   {name}")
    c, g = res["C"]["strict_d"], res["G"]["strict_d"]
    p = c >= 10 and c >= g + 4
    print(f"\nPRIMARY (carried over: CUBE >= 10/16 AND >= GEN+4, STRICT-D): "
          f"CUBE {c}/16 vs GEN {g}/16 -> "
          f"{'PASS — ABSOLUTE BAR FALLS, THE THESIS CLOSES AT 4B' if p else 'FAIL — recorded honestly'}")
    print(f"delta vs run 21: CUBE STRICT-D {res['C']['strict_d']} (was 6), "
          f"strict {res['C']['strict']} (was 3), RULER-T {res['C']['rulert']} (was 6)")
    print("pipeline: d1_ok %d/16 · guard retries %d (fails %d) · "
          "screen retries %d (fails %d) · est injected %d" % (
              sum(1 for r in c_rows if r["d1_ok"]),
              sum(1 for r in c_rows if r["guarded"]),
              sum(1 for r in c_rows if r["guard_fail"]),
              sum(1 for r in c_rows if r["screened"]),
              sum(1 for r in c_rows if r["screen_fail"]),
              sum(1 for r in c_rows if r["est_injected"])))
    (OUT / "rematch21b_results.json").write_text(json.dumps(
        {"table": res, "primary_pass": p}, indent=1))

    print("\n---------- AUTOPSY (STRICT-D flaws, guarded cube) ----------")
    for r in sorted(c_rows, key=lambda x: x["pid"]):
        if r["gd"]["coherent"]:
            continue
        print(f"[C pid {r['pid']:02d}]")
        for fl in r["gd"].get("flaws", []):
            fl = fl if isinstance(fl, str) else json.dumps(fl)
            print(f"    [{classify(fl)}] {fl}")


if __name__ == "__main__":
    main()
