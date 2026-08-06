"""
run13_score.py — RUN 13 local scorer (RUNBOOK13 frozen bars).

Applies the fidelity checker to all four arms of the pulled transcript, prints
the per-arm scoreboard, and evaluates the code-side bars (2, 3, 4-code, 5).
Bars 1 (instrument validity), 4-judge, and 6 (delivery) come from
run13_calibrate.py (Session Q) — this script writes checker_results.json for it.

  python scripts/run13_score.py
"""
from __future__ import annotations
import json, math
from pathlib import Path

from run13_checker import check_speech

ROOT = Path(__file__).resolve().parent.parent
TR = ROOT / "out/run13/run13_transcript.json"
PROBS = ROOT / "data/run13/staged_problems.jsonl"
OUTJ = ROOT / "out/run13/checker_results.json"


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def main():
    t = json.loads(TR.read_text())
    manifests = {json.loads(l)["pid"]: json.loads(l) for l in PROBS.open()}
    arms = ("A", "B", "C", "D")
    res = {a: [] for a in arms}
    for run in t["runs"]:
        pr = manifests[run["pid"]]
        upstream = [pr["problem"], pr["update"], run["audit"], run["read"],
                    run["plan"], run["motion"]]
        for a in arms:
            r = check_speech(run[f"fusion_{a}"], upstream, pr, run["motion"])
            res[a].append({"pid": run["pid"], "flags": r["fidelity_flags"],
                           "verbosity": r["verbosity_flag"], "words": r["words"],
                           "clean": not r["fidelity_flags"],
                           **({"attempts": run["D_attempts"]} if a == "D" else {})})

    print(f"{'arm':<4}{'clean':>7}{'verb-ok':>9}{'words':>7}   flag classes")
    stats = {}
    for a in arms:
        rows = res[a]
        clean = sum(r["clean"] for r in rows)
        vok = sum(1 for r in rows if r["verbosity"] is None)
        wmean = sum(r["words"] for r in rows) / len(rows)
        hist = {}
        for r in rows:
            for k, _ in r["flags"]:
                hist[k] = hist.get(k, 0) + 1
        stats[a] = {"clean": clean, "verb_ok": vok, "hist": hist}
        print(f"{a:<4}{clean:>4}/24{vok:>6}/24{wmean:>7.0f}   {json.dumps(hist)}")

    lo, hi = wilson(stats["A"]["clean"], 24)
    print(f"\nBAR 2 (wall, arm A): clean {stats['A']['clean']}/24 "
          f"({stats['A']['clean']/24:.0%}, 95% CI {lo:.0%}-{hi:.0%}) -> "
          + ("WALL CONFIRMED (<=70%)" if stats["A"]["clean"] / 24 <= 0.70 else
             "WALL QUESTIONED (>=85%)" if stats["A"]["clean"] / 24 >= 0.85 else
             "INDETERMINATE ZONE (70-85%)"))
    for a in ("B", "C"):
        ok = stats[a]["clean"] >= 21 and stats[a]["clean"] >= stats["A"]["clean"] + 4
        print(f"BAR 3 ({a}): clean {stats[a]['clean']}/24 (need >=21 AND >= A+4) -> "
              f"{'PASS' if ok else 'FAIL'}")
    d_ok3 = sum(1 for r in res["D"] if r["clean"] and r["attempts"] <= 3)
    att = [r["attempts"] for r in res["D"]]
    print(f"BAR 4-code (D): clean-within-3 {d_ok3}/24 (need >=22), attempts "
          f"histogram {sorted(set((x, att.count(x)) for x in att))} -> "
          f"{'PASS pending judge leg' if d_ok3 >= 22 else 'FAIL'}")
    for a in arms:
        print(f"BAR 5 verbosity ({a}): {stats[a]['verb_ok']}/24 in 60-200 "
              f"({'ok' if stats[a]['verb_ok'] >= 20 else 'below 20 — reported'})")
    print("\nBARS 1 (instrument), 4-judge, 6 (delivery): run run13_calibrate.py next.")
    OUTJ.write_text(json.dumps(res, indent=1))
    print(f"wrote {OUTJ}")


if __name__ == "__main__":
    main()
