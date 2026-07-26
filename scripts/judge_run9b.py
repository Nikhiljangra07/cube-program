"""
judge_run9b.py — RUN 9B verdict sessions (RUNBOOK9B frozen, dual-eval).

  python scripts/judge_run9b.py            # Session I : Eval A (v5 bench, 2 arms x 48)
  python scripts/judge_run9b.py --s2       # Session I2: Eval A replicate (ONLY if I passes)
  python scripts/judge_run9b.py --evalb    # Session J : Eval B (dossier bench, 2 arms x 24)

Eval A: sonnet_judge byte-identical; FACE BAR foresight >= anchor+0.20 AND overall >=
anchor-0.15. Eval B: the frozen 5-dim dossier rubric; B BAR overall-B >= anchor+0.20
AND evidence_grounding >= anchor. Coverage: all sets judged or session discarded whole.
"""
from __future__ import annotations
import asyncio, json, os, re, statistics, sys
from pathlib import Path

import httpx

import head2head_v5 as H  # noqa: F401
from rejudge_arms import sonnet_judge, agg

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUTD = ROOT / "out/run9b"
KEY = os.environ.get("ANTHROPIC_API_KEY", "")
JSEM = asyncio.Semaphore(6)
S2 = "--s2" in sys.argv
EVALB = "--evalb" in sys.argv

BDIMS = ("prediction_specificity", "evidence_grounding", "calibration", "positioning", "falsifiability")
BPROMPT = """You are grading 4 candidate response threads to a decision problem that includes a
DOSSIER of observed counterparty behavior. Grade EVIDENCE-FED FORESIGHT only. Be a strict critic.

PROBLEM (with dossier): {problem}

THREADS:
{threads}

Score the SET 1-5 on each dimension (5 = excellent, 1 = fails):
- prediction_specificity: do threads name the counterparty's likely NEXT 1-3 moves concretely
  (who does what, when) rather than vague "they may resist"?
- evidence_grounding: is every prediction traceable to specific dossier observations (cite-able
  to an observed behavior), with nothing invented beyond the evidence?
- calibration: does confidence scale with evidence strength — acknowledging the innocent
  reading where the dossier supports it, not treating every signal as hostile?
- positioning: do the plans EXPLOIT the predictions (pre-positioned counters, timed moves)
  rather than merely stating them?
- falsifiability: do threads name observable signals that would disconfirm their read?

Return ONLY JSON: {{"prediction_specificity":N,"evidence_grounding":N,"calibration":N,"positioning":N,"falsifiability":N}}"""


async def bcall(client, prompt):
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
                    if all(isinstance(j.get(d), int) and 1 <= j[d] <= 5 for d in BDIMS):
                        return j
            except Exception:
                await asyncio.sleep(3 * (a + 1))
    return None


async def eval_a():
    suf = "_s2" if S2 else ""
    files = {"faceF_9b": OUTD / "eval_faceF_9b_qA_v5_threads.jsonl",
             "keep100": OUTD / "eval_anchor_9b_qA_v5_threads.jsonl"}
    out, per = {}, {}
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
    print(f"\n--- EVAL A READ (session {'I2' if S2 else 'I'}) ---")
    if min(ns) < 44:
        print(f"COVERAGE INSUFFICIENT (n={ns}) — discard session, rerun whole")
        return
    k, f = out["keep100"], out["faceF_9b"]
    lane = f["foresight"] >= k["foresight"] + 0.20
    floor = f["overall"] >= k["overall"] - 0.15
    print(f"[9b/A] FACE: foresight {f['foresight']} vs anchor {k['foresight']} "
          f"(needs >= {round(k['foresight']+0.20,3)}) {'OK' if lane else 'FAIL'}; "
          f"overall {f['overall']} vs floor {round(k['overall']-0.15,3)} "
          f"{'OK' if floor else 'FAIL'} -> {'PASS' if lane and floor else 'FAIL'}")


async def eval_b():
    files = {"faceF_9b": OUTD / "eval_faceF_9b_qB_v5_threads.jsonl",
             "keep100": OUTD / "eval_anchor_9b_qB_v5_threads.jsonl"}
    out = {}
    async with httpx.AsyncClient() as client:
        for label, path in files.items():
            rows = [json.loads(l) for l in path.open()]
            res = []

            async def one(r):
                block = "\n\n".join(f"[{i+1}] {t}" for i, t in enumerate(r["threads"]))
                j = await bcall(client, BPROMPT.format(problem=r["problem"], threads=block))
                if j:
                    res.append(j)
            await asyncio.gather(*[one(r) for r in rows if r.get("threads")])
            if len(res) < len(rows):
                print(f"COVERAGE INSUFFICIENT for {label}: {len(res)}/{len(rows)} — discard session")
                return
            summ = {d: round(statistics.mean(r[d] for r in res), 2) for d in BDIMS}
            summ["overall_B"] = round(statistics.mean(statistics.mean(r[d] for d in BDIMS) for r in res), 2)
            summ["n"] = len(res)
            out[label] = summ
            print(f"{label:10s} {json.dumps(summ)}", flush=True)
    (OUTD / "evalB_summary.json").write_text(json.dumps(out, indent=2))
    k, f = out["keep100"], out["faceF_9b"]
    bar1 = f["overall_B"] >= k["overall_B"] + 0.20
    bar2 = f["evidence_grounding"] >= k["evidence_grounding"]
    print(f"\n--- EVAL B READ (session J) ---")
    print(f"[9b/B] overall_B {f['overall_B']} vs anchor {k['overall_B']} "
          f"(needs >= {round(k['overall_B']+0.20,2)}) {'OK' if bar1 else 'FAIL'}; "
          f"evidence_grounding {f['evidence_grounding']} vs {k['evidence_grounding']} "
          f"{'OK' if bar2 else 'FAIL'} -> {'PASS' if bar1 and bar2 else 'FAIL'}")


if __name__ == "__main__":
    if not KEY:
        sys.exit("ANTHROPIC_API_KEY not set")
    asyncio.run(eval_b() if EVALB else eval_a())
