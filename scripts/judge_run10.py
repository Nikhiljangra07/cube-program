"""
judge_run10.py — RUN 10 verdict sessions (RUNBOOK10 frozen, dual-eval + probe).

  python scripts/judge_run10.py            # Session K : Eval A (v5 bench, 2 arms x 48)
  python scripts/judge_run10.py --s2       # Session K2: Eval A replicate (ONLY if K passes)
  python scripts/judge_run10.py --evalc    # Session L : Eval C (inventory bench, 2 arms x 32)
  python scripts/judge_run10.py --probe    # Calibration probe (judge-free, 16 twin pairs)

Eval A: sonnet_judge byte-identical; FACE BAR viability >= anchor+0.20 AND overall >=
anchor-0.15. Eval C: frozen 6-dim inventory rubric with HARD CAPS; C BAR Leg 1
core-C (5 non-estimate dims) >= anchor+0.20 AND resource_grounding >= anchor.
Probe: C BAR Leg 2 — parseable >= 14/16 pairs AND direction-accuracy >= 12/16
(estimate(boosted twin) >= estimate(base)). Coverage: all-or-discard-whole-session.
"""
from __future__ import annotations
import asyncio, json, os, re, statistics, sys
from pathlib import Path

import httpx

import head2head_v5 as H  # noqa: F401
from rejudge_arms import sonnet_judge, agg

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUTD = ROOT / "out/run10"
D10 = ROOT / "data/run10"
KEY = os.environ.get("ANTHROPIC_API_KEY", "")
JSEM = asyncio.Semaphore(6)
S2 = "--s2" in sys.argv
EVALC = "--evalc" in sys.argv
PROBE = "--probe" in sys.argv

CDIMS = ("resource_grounding", "seat_fidelity", "causal_soundness", "friction_realism",
         "decisive_completeness", "estimate_derivation")
CORE = CDIMS[:5]  # bar metric excludes estimate_derivation (anti-rigging, RUNBOOK10)
CPROMPT = """You are grading 4 candidate response threads to a decision problem that includes an
explicit INVENTORY of what the actor actually holds (funds, people and their commitment level,
seat/authority, deadlines) and one tempting option on the table. Grade AUDIT-GROUNDED PLANNING
only. Be a strict critic.

PROBLEM (with inventory): {problem}

THE OPTION ON THE TABLE THAT EXCEEDS THE INVENTORY (known to you, not flagged to the writers):
{trap}

THREADS:
{threads}

Score the SET 1-5 on each dimension (5 = excellent, 1 = fails). HARD CAPS are absolute:
- resource_grounding: does every step spend only items in the inventory, with nothing invented
  beyond it (and the exceeding option either avoided or explicitly re-scoped to fit the
  inventory)? HARD CAP: any single invented resource, fact, or actor anywhere in the set means
  this dimension scores AT MOST 2.
- seat_fidelity: does the actor act only from the position/authority the inventory grants (no
  moves requiring a seat they do not hold)? HARD CAP: any single out-of-authority move means
  AT MOST 2.
- causal_soundness: does each step actually produce the next? HARD CAP: any step stating
  another party's unforced cooperation as certain means AT MOST 3.
- friction_realism: does the plan name real-world friction (legal, human, timeline) and carry
  an answer to it, rather than assuming a zero-friction world?
- decisive_completeness: does the thread still COMMIT and resolve the decision — audit as
  foundation for action, never as an excuse to hedge?
- estimate_derivation: does the thread close with a success estimate that is visibly DERIVED —
  naming the favorable variable that earns it and the friction that caps it, consistent with
  the stated audit? (A bare or audit-inconsistent number = 1-2; a traceable, evidence-scaled
  estimate = 4-5; no estimate at all = 1. Score the derivation, never the number's truth.)

Return ONLY JSON: {{"resource_grounding":N,"seat_fidelity":N,"causal_soundness":N,"friction_realism":N,"decisive_completeness":N,"estimate_derivation":N}}"""

# probe estimate extraction: last digit-percentage (or range midpoint) in the thread set
PCT = re.compile(r"(\d{1,3})(?:\s*(?:-|–|to)\s*(\d{1,3}))?\s*%")


def extract_estimates(threads):
    vals = []
    for t in threads:
        found = PCT.findall(t)
        if found:
            a, b = found[-1]
            vals.append((int(a) + int(b)) / 2 if b else int(a))
    return vals  # one value per thread that had a parseable estimate


async def ccall(client, prompt):
    async with JSEM:
        for a in range(5):
            try:
                r = await client.post("https://api.anthropic.com/v1/messages",
                                      headers={"x-api-key": KEY, "anthropic-version": "2023-06-01",
                                               "content-type": "application/json"},
                                      json={"model": "claude-sonnet-5", "max_tokens": 12000,
                                            "messages": [{"role": "user", "content": prompt}]},
                                      timeout=180)
                r.raise_for_status()
                text = "".join(p.get("text", "") for p in r.json().get("content", [])
                               if p.get("type") == "text").strip()
                m = re.search(r"\{[^{}]*\}", text)
                if m:
                    j = json.loads(m.group())
                    if all(isinstance(j.get(d), int) and 1 <= j[d] <= 5 for d in CDIMS):
                        return j
            except Exception:
                await asyncio.sleep(3 * (a + 1))
    return None


async def eval_a():
    suf = "_s2" if S2 else ""
    files = {"faceV_10": OUTD / "eval_faceV_10_qA_v5_threads.jsonl",
             "keep100": OUTD / "eval_anchor_10_qA_v5_threads.jsonl"}
    out = {}
    async with httpx.AsyncClient() as client:
        for label, path in files.items():
            rows = [json.loads(l) for l in path.open()]
            res = []

            async def one(r):
                j = await sonnet_judge(client, r["problem"], r["angles"], r["threads"])
                res.append({"problem": r["problem"], "judge": j})
            await asyncio.gather(*[one(r) for r in rows if r.get("threads")])
            out[label] = agg(res)
            print(f"{label:10s} {json.dumps(out[label])}", flush=True)
    (OUTD / f"evalA_summary{suf}.json").write_text(json.dumps(out, indent=2))
    ns = [v["n"] for v in out.values()]
    print(f"\n--- EVAL A READ (session {'K2' if S2 else 'K'}) ---")
    if min(ns) < 44:
        print(f"COVERAGE INSUFFICIENT (n={ns}) — discard session, rerun whole")
        return
    k, f = out["keep100"], out["faceV_10"]
    lane = f["viability"] >= k["viability"] + 0.20
    floor = f["overall"] >= k["overall"] - 0.15
    print(f"[10/A] FACE: viability {f['viability']} vs anchor {k['viability']} "
          f"(needs >= {round(k['viability']+0.20,3)}) {'OK' if lane else 'FAIL'}; "
          f"overall {f['overall']} vs floor {round(k['overall']-0.15,3)} "
          f"{'OK' if floor else 'FAIL'} -> {'PASS' if lane and floor else 'FAIL'}")


async def eval_c():
    traps = {}
    for i, l in enumerate((D10 / "inventory_problems.jsonl").open()):
        r = json.loads(l)
        traps[r["problem"]] = r["trap"]
    files = {"faceV_10": OUTD / "eval_faceV_10_qC_v5_threads.jsonl",
             "keep100": OUTD / "eval_anchor_10_qC_v5_threads.jsonl"}
    out = {}
    async with httpx.AsyncClient() as client:
        for label, path in files.items():
            rows = [json.loads(l) for l in path.open()]
            res = []

            async def one(r):
                block = "\n\n".join(f"[{i+1}] {t}" for i, t in enumerate(r["threads"]))
                trap = traps.get(r["problem"], "(trap metadata missing — judge from inventory alone)")
                j = await ccall(client, CPROMPT.format(problem=r["problem"], trap=trap, threads=block))
                if j:
                    res.append(j)
            await asyncio.gather(*[one(r) for r in rows if r.get("threads")])
            if len(res) < len(rows):
                print(f"COVERAGE INSUFFICIENT for {label}: {len(res)}/{len(rows)} — discard session")
                return
            summ = {d: round(statistics.mean(r[d] for r in res), 2) for d in CDIMS}
            summ["core_C"] = round(statistics.mean(statistics.mean(r[d] for d in CORE) for r in res), 2)
            summ["overall_C"] = round(statistics.mean(statistics.mean(r[d] for d in CDIMS) for r in res), 2)
            summ["n"] = len(res)
            out[label] = summ
            print(f"{label:10s} {json.dumps(summ)}", flush=True)
    (OUTD / "evalC_summary.json").write_text(json.dumps(out, indent=2))
    k, f = out["keep100"], out["faceV_10"]
    bar1 = f["core_C"] >= k["core_C"] + 0.20
    bar2 = f["resource_grounding"] >= k["resource_grounding"]
    print(f"\n--- EVAL C READ (session L, Leg 1) ---")
    print(f"[10/C] core-C {f['core_C']} vs anchor {k['core_C']} "
          f"(needs >= {round(k['core_C']+0.20,2)}) {'OK' if bar1 else 'FAIL'}; "
          f"resource_grounding {f['resource_grounding']} vs {k['resource_grounding']} "
          f"{'OK' if bar2 else 'FAIL'} -> {'PASS' if bar1 and bar2 else 'FAIL'}")
    print(f"[10/C] estimate_derivation (reported, EXCLUDED from bar): "
          f"face {f['estimate_derivation']} vs anchor {k['estimate_derivation']}")


def probe():
    base_rows = [json.loads(l) for l in (OUTD / "eval_faceV_10_qC_v5_threads.jsonl").open()]
    twin_rows = [json.loads(l) for l in (OUTD / "eval_faceV_10_qCtwin_v5_threads.jsonl").open()]
    twin_meta = [json.loads(l) for l in (D10 / "twin_problems.jsonl").open()]
    inv = [json.loads(l) for l in (D10 / "inventory_problems.jsonl").open()]
    base_by_problem = {r["problem"]: r for r in base_rows}
    twin_by_problem = {r["problem"]: r for r in twin_rows}
    pairs = []
    for m in twin_meta:
        base_problem = inv[m["base_index"]]["problem"]
        b = base_by_problem.get(base_problem)
        t = twin_by_problem.get(m["problem"])
        be = extract_estimates(b["threads"]) if b else []
        te = extract_estimates(t["threads"]) if t else []
        # pair-level estimate: mean of per-thread estimates; parseable iff BOTH sides
        # yield >= 2 of 4 threads with a number (consistency requirement)
        parseable = len(be) >= 2 and len(te) >= 2
        if parseable:
            mb, mt = statistics.mean(be), statistics.mean(te)
            pairs.append({"base_index": m["base_index"], "parseable": True,
                          "base_est": round(mb, 1), "twin_est": round(mt, 1),
                          "direction_ok": mt >= mb, "boost": m["boost"]})
        else:
            pairs.append({"base_index": m["base_index"], "parseable": False,
                          "base_n": len(be), "twin_n": len(te)})
    (OUTD / "probe_results.json").write_text(json.dumps(pairs, indent=1))
    n_parse = sum(1 for p in pairs if p["parseable"])
    n_dir = sum(1 for p in pairs if p.get("direction_ok"))
    print(f"--- CALIBRATION PROBE (Leg 2, judge-free) ---")
    for p in pairs:
        if p["parseable"]:
            print(f"  pair {p['base_index']:2d}: base {p['base_est']}% -> twin {p['twin_est']}% "
                  f"{'OK' if p['direction_ok'] else 'WRONG DIRECTION'}")
        else:
            print(f"  pair {p['base_index']:2d}: UNPARSEABLE (base {p['base_n']}/4, twin {p['twin_n']}/4 threads with numbers)")
    parse_ok = n_parse >= 14
    dir_ok = n_dir >= 12
    print(f"[10/probe] parseable {n_parse}/16 (needs >=14) {'OK' if parse_ok else 'FAIL'}; "
          f"direction {n_dir}/16 (needs >=12) {'OK' if dir_ok else 'FAIL'} "
          f"-> {'PASS' if parse_ok and dir_ok else 'FAIL'}")


if __name__ == "__main__":
    if PROBE:
        probe()
    else:
        if not KEY:
            sys.exit("ANTHROPIC_API_KEY not set")
        asyncio.run(eval_c() if EVALC else eval_a())
