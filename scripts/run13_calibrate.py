"""
run13_calibrate.py — RUN 13 Session Q: judge calibration of the fidelity checker
(RUNBOOK13 frozen). The CHECKER is on trial here, then arm D's judge leg.

Stratified, deterministic sample: 10 checker-flagged + 10 checker-clean speeches
from arms A/B/C (sorted by (arm,pid), first N of each stratum) + 6 arm-D finals
(pids 0-5). Sonnet reads each BLIND to the checker verdict.

Judge discipline: claude-sonnet-5, NO temperature param, max_tokens 12000,
retry-on-empty, coverage all-or-discard-whole-session.

INSTRUMENT VALIDITY BAR: agreement >= 80% on the 20 AND miss rate <= 2/10
(checker-clean the judge finds incoherent). D judge leg: >= 5/6 coherent.

  source ~/Desktop/reasoningEngine/load_keys.sh && python scripts/run13_calibrate.py
"""
from __future__ import annotations
import asyncio, json, os, re, sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
TR = ROOT / "out/run13/run13_transcript.json"
CK = ROOT / "out/run13/checker_results.json"
PROBS = ROOT / "data/run13/staged_problems.jsonl"
OUTJ = ROOT / "out/run13/calibration.json"
KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SEM = asyncio.Semaphore(4)

PROMPT = """You are auditing the FINAL SPEECH of a multi-part reasoning relay for factual
fidelity. The segments below are the speech's only permitted sources. Be a strict critic.

PROBLEM (happened): {problem}
UPDATE (happened): {update}
AUDIT segment: {audit}
READ segment (a PREDICTION — none of it has happened): {read}
CURRENT PLAN segment (revised for the update): {motion}

FINAL SPEECH UNDER AUDIT:
{speech}

Judge ONLY fidelity and delivery, not strategy quality:
- coherent = false if the speech states any predicted event as having happened, uses any
  number absent from the sources, revives anything the UPDATE eliminated (except to note
  it is gone), or contradicts the sources. Otherwise true.
- flaws: list each violation in one short sentence (empty list if none).
- delivery: 1-5 — is it a readable, complete, decisive final answer (5 = excellent)?

Return ONLY JSON: {{"coherent": true/false, "flaws": ["..."], "delivery": N}}"""


async def judge(client, item):
    async with SEM:
        for a in range(4):
            try:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": KEY, "anthropic-version": "2023-06-01",
                             "content-type": "application/json"},
                    json={"model": "claude-sonnet-5", "max_tokens": 12000,
                          "messages": [{"role": "user", "content": PROMPT.format(**item)}]},
                    timeout=180)
                resp.raise_for_status()
                text = "".join(p.get("text", "") for p in resp.json().get("content", [])
                               if p.get("type") == "text")
                m = re.search(r"\{.*\}", text, re.S)
                if m:
                    j = json.loads(m.group())
                    if isinstance(j.get("coherent"), bool) and "delivery" in j:
                        return j
            except Exception:
                await asyncio.sleep(3 * (a + 1))
    return None


def build_sample():
    t = json.loads(TR.read_text())
    ck = json.loads(CK.read_text())
    manifests = {json.loads(l)["pid"]: json.loads(l) for l in PROBS.open()}
    runs = {r["pid"]: r for r in t["runs"]}
    flagged, clean = [], []
    for arm in ("A", "B", "C"):
        for row in ck[arm]:
            (clean if row["clean"] else flagged).append((arm, row["pid"]))
    flagged.sort(); clean.sort()
    picks = [("cal_flagged", a, p) for a, p in flagged[:10]] + \
            [("cal_clean", a, p) for a, p in clean[:10]] + \
            [("d_leg", "D", p) for p in sorted(runs)[:6]]
    items = []
    for stratum, arm, pid in picks:
        r, man = runs[pid], manifests[pid]
        items.append({"stratum": stratum, "arm": arm, "pid": pid,
                      "checker_clean": next(x["clean"] for x in ck[arm] if x["pid"] == pid),
                      "problem": man["problem"], "update": man["update"],
                      "audit": r["audit"], "read": r["read"], "motion": r["motion"],
                      "speech": r[f"fusion_{arm}"]})
    return items


async def main():
    if not KEY:
        sys.exit("ANTHROPIC_API_KEY not set — source ~/Desktop/reasoningEngine/load_keys.sh")
    items = build_sample()
    n_f = sum(1 for i in items if i["stratum"] == "cal_flagged")
    n_c = sum(1 for i in items if i["stratum"] == "cal_clean")
    print(f"Session Q sample: {n_f} flagged + {n_c} clean + "
          f"{sum(1 for i in items if i['stratum'] == 'd_leg')} D finals")
    async with httpx.AsyncClient() as client:
        verdicts = await asyncio.gather(*[judge(client, i) for i in items])
    if any(v is None for v in verdicts):
        sys.exit("COVERAGE INCOMPLETE — all-or-discard: session Q discarded, rerun whole.")
    for i, v in zip(items, verdicts):
        i["judge"] = v
    cal = [i for i in items if i["stratum"].startswith("cal_")]
    agree = sum(1 for i in cal if i["checker_clean"] == i["judge"]["coherent"])
    miss = sum(1 for i in cal if i["stratum"] == "cal_clean" and not i["judge"]["coherent"])
    false_alarm = sum(1 for i in cal if i["stratum"] == "cal_flagged" and i["judge"]["coherent"])
    n_cal = len(cal)
    valid = (agree / n_cal >= 0.80) and (miss <= 2)
    print(f"\nBAR 1 INSTRUMENT: agreement {agree}/{n_cal} ({agree/n_cal:.0%}, need >=80%), "
          f"miss {miss}/{n_c} (need <=2), false-alarm {false_alarm}/{n_f} -> "
          f"{'VALID' if valid else 'INSTRUMENT FAILURE — no arm claims'}")
    d = [i for i in items if i["stratum"] == "d_leg"]
    d_ok = sum(1 for i in d if i["judge"]["coherent"])
    print(f"BAR 4-judge (D finals): {d_ok}/{len(d)} coherent (need >=5) -> "
          f"{'PASS' if d_ok >= 5 else 'FAIL'}")
    by_arm = {}
    for i in items:
        by_arm.setdefault(i["arm"], []).append(i["judge"]["delivery"])
    for a, ds in sorted(by_arm.items()):
        print(f"BAR 6 delivery ({a}, n={len(ds)}): mean {sum(ds)/len(ds):.2f}")
    OUTJ.write_text(json.dumps(
        {"items": [{k: v for k, v in i.items()
                    if k in ("stratum", "arm", "pid", "checker_clean", "judge")}
                   for i in items],
         "agreement": agree, "n_cal": n_cal, "miss": miss, "false_alarm": false_alarm,
         "instrument_valid": valid, "d_coherent": d_ok}, indent=1))
    print(f"wrote {OUTJ}")


if __name__ == "__main__":
    asyncio.run(main())
