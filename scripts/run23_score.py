"""
run23_score.py — RUN 23 verdict: cube (immutable run-22 cached verdicts) vs
Qwen3-4B-Thinking-2507 naked, on the frozen holdout (RUNBOOK23).

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/run23_score.py --pod HOST:PORT
  python scripts/run23_score.py --mock

Only arm R is judged (48 reads, cap 55). Arms C/G verdicts MUST come from
the run-22 cache — re-judging them is forbidden (one-directional blindness).
PRIMARY: RULER-T clean count, C vs R (WIN >, TIE =, LOSS <).
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("ANTHROPIC_API_KEY", "")
from run16b_relabel import acall  # noqa: E402
from run21_score import RULERS  # noqa: E402
from run22_score import QDIMS, QUAL, rulert_clean, valid_qual, valid_ruler  # noqa: E402
from ruler_t import classify  # noqa: E402
import head2head_v5 as H  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT22 = ROOT / "out/run22"
OUT = ROOT / "out/run23"
CACHE = OUT / "judge_cache.jsonl"
PROBS = ROOT / "data/run22/holdout_problems.jsonl"
CAP = 55
MOCK = False
CUBE_CAP_TOKENS = 1360  # arm-C stage max_new sum: 400+160+256+192+256+96


def md5(t):
    return hashlib.md5(t.encode()).hexdigest()


def key(r, k):
    return f"{'r23' if r['arm'] == 'R' else 'r22'}|{k}|{md5(r['answer'])[:12]}"


def sh(cmd, timeout=600):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def load_cache():
    c = {}
    for path in (OUT22 / "judge_cache.jsonl", CACHE):
        if path.exists():
            for l in path.open():
                rec = json.loads(l)
                if bool(rec.get("_mock")) == MOCK:
                    c[rec["key"]] = rec["verdict"]
    return c


async def judge(rows, probs):
    cache = load_cache()
    kinds = list(RULERS) + ["q"]
    todo = [(r, k) for r in rows for k in kinds if key(r, k) not in cache]
    stale = [(r, k) for r, k in todo if r["arm"] != "R"]
    if stale and not MOCK:
        sys.exit(f"C/G verdicts missing from run-22 cache ({len(stale)}) — "
                 "re-judging them is forbidden (RUNBOOK23)")
    print(f"judge: {len(todo)} new reads (cap {CAP}), "
          f"{len(rows)*3-len(todo)} cached")
    if not MOCK and len(todo) > CAP:
        sys.exit("SPEND CAP — abort before billing")
    OUT.mkdir(parents=True, exist_ok=True)
    cf = CACHE.open("a")
    if MOCK:
        for r, k in todo:
            h = int(md5(r["answer"] + k), 16)
            v = ({d: (h >> i) % 5 + 1 for i, d in enumerate(QDIMS)} if k == "q"
                 else {"coherent": h % 2 == 0,
                       "flaws": [] if h % 2 == 0 else ["mock flaw"]})
            cf.write(json.dumps({"key": key(r, k), "verdict": v,
                                 "_mock": True}) + "\n")
        cf.close()
        return load_cache()
    import httpx

    async def one(client, r, k):
        tmpl = QUAL if k == "q" else RULERS[k]
        text = await acall(client, tmpl.format(problem=probs[r["pid"]],
                                               answer=r["answer"]))
        j = H.parse_json(text) if text else None
        if (valid_qual(j) if k == "q" else valid_ruler(j)):
            cf.write(json.dumps({"key": key(r, k), "verdict": j,
                                 "_mock": False}) + "\n")
            cf.flush()
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[one(client, r, k) for r, k in todo])
    cf.close()
    return load_cache()


def main():
    global MOCK
    ap = argparse.ArgumentParser()
    ap.add_argument("--pod")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    MOCK = args.mock
    probs = {json.loads(l)["pid"]: json.loads(l)["problem"] for l in PROBS.open()}
    OUT.mkdir(parents=True, exist_ok=True)
    rpath = OUT / "thinking23_out.jsonl"
    if not MOCK:
        if not args.pod:
            sys.exit("need --pod HOST:PORT (or --mock)")
        host, port = args.pod.split(":")
        rc, o = sh(f"rsync -a --no-owner --no-group --partial --timeout=90 "
                   f"-e 'ssh -p {port} -o StrictHostKeyChecking=no' "
                   f"root@{host}:/workspace/div/out/thinking23_out.jsonl {OUT}/")
        if rc != 0:
            sys.exit(f"pull failed: {o[-300:]}")
    if MOCK and not rpath.exists():
        rpath.write_text("".join(json.dumps(
            {"arm": "R", "pid": p, "answer": f"Mock R{p}. ESTIMATE: 60%",
             "gen_tokens": 5000, "leaked": False}) + "\n" for p in range(16)))
    rows = [json.loads(l) for l in (OUT22 / "holdout22_out.jsonl").open()]
    rrows = [json.loads(l) for l in rpath.open()]
    assert len(rrows) == 16, f"expected 16 R answers, got {len(rrows)}"
    rows += rrows
    cache = asyncio.run(judge(rows, probs)) or load_cache()
    missing = [(r, k) for r in rows for k in ("one", "d", "q")
               if key(r, k) not in cache]
    if missing:
        sys.exit(f"COVERAGE INSUFFICIENT: {len(missing)} unjudged — rerun")
    for r in rows:
        r["g1"], r["gd"], r["q"] = (cache[key(r, "one")], cache[key(r, "d")],
                                    cache[key(r, "q")])

    print("\n========== RUN 23 — CUBE vs REASONING MODEL ==========")
    print(f"{'arm':>5} {'strict':>7} {'STRICT-D':>9} {'RULER-T':>8}  quality (cf/pq/aq/cal)")
    res = {}
    for a, name in (("C", "CUBE-v2 (instruct+harness)"),
                    ("R", "Qwen3-4B-THINKING naked"),
                    ("G", "instruct naked (context)")):
        rs = [r for r in rows if r["arm"] == a]
        s1 = sum(1 for r in rs if r["g1"]["coherent"])
        sd = sum(1 for r in rs if r["gd"]["coherent"])
        st = sum(1 for r in rs if rulert_clean(r["g1"]))
        qm = {d: sum(r["q"][d] for r in rs) / len(rs) for d in QDIMS}
        res[a] = {"strict": s1, "strict_d": sd, "rulert": st,
                  "qual": {d: round(qm[d], 2) for d in QDIMS}}
        print(f"    {a} {s1:>4}/16 {sd:>6}/16 {st:>5}/16  "
              + "/".join(f"{qm[d]:.2f}" for d in QDIMS) + f"   {name}")
    c, r_ = res["C"]["rulert"], res["R"]["rulert"]
    verdict = "WIN" if c > r_ else ("TIE" if c == r_ else "LOSS")
    print(f"\nPRIMARY (RULER-T, cube vs Thinking): {c} vs {r_} -> {verdict}")
    cf_pred = res["C"]["qual"]["constraint_fidelity"] >= res["R"]["qual"]["constraint_fidelity"]
    print(f"registered prediction (cube >= thinking on constraint_fidelity): "
          f"{'HELD' if cf_pred else 'FAILED'}")
    toks = [r.get("gen_tokens", 0) for r in rrows]
    leaks = sum(1 for r in rrows if r.get("leaked"))
    print(f"efficiency: Thinking {sum(toks)/len(toks):.0f} tokens/answer "
          f"(min {min(toks)}, max {max(toks)}, leaked {leaks}) vs cube "
          f"stage-budget ceiling {CUBE_CAP_TOKENS}")
    (OUT / "run23_results.json").write_text(json.dumps(
        {"table": res, "primary": verdict, "cf_prediction_held": cf_pred,
         "thinking_tokens_avg": round(sum(toks) / len(toks), 1)}, indent=1))

    print("\n---------- AUTOPSY (STRICT-D flaws, arm R only) ----------")
    for r in sorted(rrows, key=lambda x: x["pid"]):
        if r["gd"]["coherent"]:
            continue
        print(f"[R pid {r['pid']:02d}]")
        for fl in r["gd"].get("flaws", []):
            fl = fl if isinstance(fl, str) else json.dumps(fl)
            print(f"    [{classify(fl)}] {fl}")


if __name__ == "__main__":
    main()
