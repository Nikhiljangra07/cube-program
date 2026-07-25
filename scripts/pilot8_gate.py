"""
pilot8_gate.py — PILOT8 stage 3: blind Sonnet lane gate + the 5 frozen reads.

120 sets = (15 problems x 4 conditions x 2 lanes). Each call: the problem + 4 threads of
ONE condition, scored 1-10 on OWN lane only + leak/hedge flags. Judge never sees
passages, condition labels, or TRACE lines. Call order shuffled (seed 8). Coverage must
be 120/120 or the session is discarded whole (program rule).

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/pilot8_gate.py

Writes out/pilot8/gate.jsonl + out/pilot8/summary.json (the frozen reads).
"""
from __future__ import annotations
import asyncio, json, os, random, re, statistics, sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data/pilot8"
OUTD = ROOT / "out/pilot8"
SRC = [Path.home() / "Desktop/divergence-formula/corpus_run/corpus_v5_train/passers.jsonl",
       Path.home() / "Desktop/divergence-formula/corpus_run/corpus_v5_topup/passers.jsonl"]
MODEL = "claude-sonnet-5"
KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SEM = asyncio.Semaphore(6)

LANE_DEF = {
    "F": ("FORESIGHT: does the thread project a concrete consequence chain multiple steps "
          "deep — move -> reaction -> second-order effect -> end-state at a time horizon — "
          "with each step realistic and specific (not vague 'this may cause problems')?"),
    "V": ("VIABILITY: is the strategy execution-complete as stated — exact mechanism "
          "(who/what/when/cost), the binding real-world constraint respected, failure "
          "point + mitigation named — such that a competent operator could run it "
          "tomorrow without further planning?"),
}

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


def build_sets():
    gen = {}
    for l in (D / "threads.jsonl").open():
        r = json.loads(l)
        gen.setdefault((r["lane"], r["cond"], r["pid"]), {})[r["idx"]] = (r["thread"], r["problem"])
    pool = {}
    for p in SRC:
        for l in p.open():
            row = json.loads(l)
            import hashlib
            pool[hashlib.md5(row["problem"].encode()).hexdigest()[:12]] = row
    sets = []
    pids_by_lane = {}
    for (lane, cond, p), th in gen.items():
        pids_by_lane.setdefault(lane, set()).add(p)
        if len(th) != 4:
            print(f"WARN incomplete set {lane}/{cond}/{p}: {len(th)} threads")
            continue
        sets.append({"lane": lane, "cond": cond, "pid": p, "problem": th[0][1],
                     "threads": [th[i][0] for i in range(4)]})
    for lane, pids in pids_by_lane.items():          # P condition from pool originals
        for p in pids:
            row = pool[p]
            sets.append({"lane": lane, "cond": "P", "pid": p, "problem": row["problem"],
                         "threads": row["pos_threads"]})
    random.Random(8).shuffle(sets)
    return sets


async def main():
    if not KEY:
        sys.exit("ANTHROPIC_API_KEY not set")
    OUTD.mkdir(parents=True, exist_ok=True)
    sets = build_sets()
    print(f"{len(sets)} sets to judge (expect 120)")
    results = []
    async with httpx.AsyncClient() as client:
        async def one(s):
            block = "\n\n".join(f"[{i+1}] {t}" for i, t in enumerate(s["threads"]))
            j = await call(client, PROMPT.format(problem=s["problem"], threads=block,
                                                 lane_def=LANE_DEF[s["lane"]]))
            if j:
                results.append({**{k: s[k] for k in ("lane", "cond", "pid")}, **j})
        await asyncio.gather(*[one(s) for s in sets])
    print(f"coverage {len(results)}/{len(sets)}")
    with (OUTD / "gate.jsonl").open("w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    if len(results) < len(sets):
        sys.exit("COVERAGE FAIL — discard session and rerun whole (program rule)")

    # ---- frozen reads ----
    summ = {}
    for lane in ("F", "V"):
        by = {c: [x for r in results if r["lane"] == lane and r["cond"] == c for x in r["scores"]]
              for c in ("G", "U", "X", "P")}
        mean = {c: round(statistics.mean(v), 2) for c, v in by.items()}
        g_leak = [x for r in results if r["lane"] == lane and r["cond"] == "G" for x in r["leak"]]
        g_hedge = [x for r in results if r["lane"] == lane and r["cond"] == "G" for x in r["hedge"]]
        reads = {
            "1_grounding_real": {"G": mean["G"], "U": mean["U"], "need": "G>=U+0.7",
                                 "pass": mean["G"] >= mean["U"] + 0.7},
            "2_passage_specific": {"G": mean["G"], "X": mean["X"], "need": "G>=X+0.5",
                                   "pass": mean["G"] >= mean["X"] + 0.5},
            "3_extremity": {"pct_G_ge8": round(100 * sum(1 for x in by["G"] if x >= 8) / len(by["G"]), 1),
                            "G": mean["G"], "P": mean["P"], "need": ">=50% G>=8 AND G>=P+1.5",
                            "pass": (sum(1 for x in by["G"] if x >= 8) / len(by["G"]) >= 0.5
                                     and mean["G"] >= mean["P"] + 1.5)},
            "4_leak": {"pct": round(100 * sum(g_leak) / len(g_leak), 1), "need": "<=10%",
                       "pass": sum(g_leak) / len(g_leak) <= 0.10},
            "5_decisiveness": {"pct_hedge": round(100 * sum(g_hedge) / len(g_hedge), 1), "need": "<=15%",
                               "pass": sum(g_hedge) / len(g_hedge) <= 0.15},
        }
        summ[lane] = {"means": mean, "reads": reads}
        print(f"\nLANE {lane}: means {mean}")
        for k, v in reads.items():
            print(f"  {k}: {'PASS' if v['pass'] else 'FAIL'}  {v}")
    (OUTD / "summary.json").write_text(json.dumps(summ, indent=1))
    print(f"\n-> {OUTD/'summary.json'}")


if __name__ == "__main__":
    asyncio.run(main())
