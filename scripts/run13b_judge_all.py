"""
run13b_judge_all.py — RUN 13B judge-everything fallback (RUNBOOK13B bar 1).

Fired because the precision spot-audit failed (<= quota-1 confirmed): the code
shortcut is revoked. Every speech in every round now gets a judge verdict
(cached ones are free); cleanliness is then decided BY THE JUDGE ALONE, with
code flags demoted to advisory. Rewrites round*.json in place (adds judge to
previously unjudged rows), recomputes results.json, and marks it judge_all.

  source ~/Desktop/reasoningEngine/load_keys.sh && python scripts/run13b_judge_all.py
"""
from __future__ import annotations
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run13b_judge as J  # noqa: E402
from run13b_drive import wilson  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out/run13b"


def main():
    t = json.loads((OUT / "transcript13b.json").read_text())
    runs = {r["pid"]: r for r in t["runs"]}
    man = {json.loads(l)["pid"]: json.loads(l)
           for l in (ROOT / "data/run13/staged_problems.jsonl").open()}
    att = {2: {}, 3: {}}
    for rnd in (2, 3):
        p = OUT / f"attempts_r{rnd}.json"
        if p.exists():
            att[rnd] = json.loads(p.read_text())

    def speech_of(row):
        if row["attempt"] == 1:
            return runs[row["pid"]][f"fusion_{'A' if row['arm'] in ('A', 'Dp') else row['arm']}"]
        return att[row["attempt"]][str(row["pid"])]

    files = {"round1": json.loads((OUT / "round1.json").read_text())}
    files["round2"] = json.loads((OUT / "round2.json").read_text())
    files["round3"] = json.loads((OUT / "round3.json").read_text())
    all_rows = files["round1"]["rows"] + files["round2"]["rows"] + files["round3"]["rows"]
    need = [r for r in all_rows if r["judge"] is None]
    print(f"judge-everything: {len(need)} unjudged rows")
    items = []
    for r in need:
        run, pr = runs[r["pid"]], man[r["pid"]]
        items.append({"arm": r["arm"], "pid": r["pid"], "attempt": r["attempt"],
                      "problem": pr["problem"], "update": pr["update"],
                      "audit": run["audit"], "read": run["read"],
                      "motion": run["motion"], "speech": speech_of(r)})
    if items:
        verdicts = J.certify_batch(items)
        billed = sum(1 for v in verdicts if not v.get("cached"))
        print(f"reads billed: {billed} (rest cached)")
        for r, v in zip(need, verdicts):
            r["judge"] = v
    (OUT / "round1.json").write_text(json.dumps(files["round1"], indent=1))
    (OUT / "round2.json").write_text(json.dumps({"rows": files["round2"]["rows"]}, indent=1))
    (OUT / "round3.json").write_text(json.dumps({"rows": files["round3"]["rows"]}, indent=1))

    # ---- recompute: judge decides; code advisory ----
    def jclean(r):
        return r["judge"] is not None and r["judge"]["coherent"]

    rows_a = [r for r in files["round1"]["rows"] if r["arm"] == "A"]
    rows_c = [r for r in files["round1"]["rows"] if r["arm"] == "C"]
    # D' clean-within-3: ANY attempt judged coherent (attempt 1 = arm A speech)
    attempts_by_pid = {r["pid"]: [dict(r, arm="Dp")] for r in rows_a}
    for rnd in (2, 3):
        for r in files[f"round{rnd}"]["rows"]:
            attempts_by_pid[r["pid"]].append(r)
    d_clean_at = {}
    for pid, rows in attempts_by_pid.items():
        d_clean_at[pid] = next((r["attempt"] for r in rows if jclean(r)), None)
    d_k = sum(1 for a in d_clean_at.values() if a is not None)

    a_k, c_k = sum(map(jclean, rows_a)), sum(map(jclean, rows_c))
    lo, hi = wilson(a_k, 24)

    def dmean(rows):
        ds = [r["judge"]["delivery"] for r in rows if r["judge"]]
        return round(sum(ds) / len(ds), 2) if ds else None

    res = {
        "mode": "judge_all (code shortcut revoked by bar 1)",
        "bar1_spot_audit": json.loads((OUT / "results.json").read_text())["bar1_spot_audit"],
        "bar2_wall_A": {"clean": a_k, "n": 24, "rate": round(a_k / 24, 3),
                        "ci95": [round(lo, 3), round(hi, 3)]},
        "bar3_C": {"clean": c_k, "pass": c_k >= 18 and c_k >= a_k + 8},
        "bar4_Dp": {"clean_within_3": d_k, "pass": d_k >= 20,
                    "clean_at_attempt": {str(a): sum(1 for x in d_clean_at.values() if x == a)
                                         for a in (1, 2, 3)},
                    "never_clean": sum(1 for x in d_clean_at.values() if x is None)},
        "bar6_delivery": {"A": dmean(rows_a), "C": dmean(rows_c),
                          "Dp": dmean([attempts_by_pid[p][-1] for p in attempts_by_pid])},
        "code_advisory": {"false_alarm_note": "spot-audit 4/6; code flags advisory only"},
    }
    (OUT / "results.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
