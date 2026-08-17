"""
run20_stage.py — RUN 20 staged-prompt builder (RUNBOOK20, $0 local).

The chain under test: model answers atomics (run-19 D1, cached) -> CODE
verifies them against deterministic truth (parameters parsed from the fixed
problem templates; calendar arithmetic via datetime) -> verified facts are
normalized into a fixed ANCHOR template (coach law: code carries text) ->
anchor appended to the run-19 D2 and D3 prompts VERBATIM.

If a model D1 answer fails its code check, the anchor still carries the
CODE-computed truth (deterministic arithmetic is the harness's job in the
cube-v2 division of labor) and the failure is counted and printed.

  python scripts/run20_stage.py   # writes data/run20/staged.jsonl + md5
"""
from __future__ import annotations
import datetime, hashlib, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run19_demand import D2, D3, parse_params  # byte-reuse  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/run20/staged.jsonl"

MONTHS = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}

ANCHOR = ("\n\nVERIFIED FACTS (already checked — rely on them, do not re-derive): "
          "(i) The {code} track price of ${sweet} EXCEEDS the ${cap} single-expense "
          "sign-off threshold by ${diff}; the problem states sign-off cannot be "
          "obtained before {d_dead}, so committing ${sweet} before {d_dead} is not "
          "executable. (ii) {n_days} days lie between {d_open} and the {d_dead} "
          "deadline.")


def day_count(d_open, d_dead):
    def parse(d):
        m, day = d.split()
        return datetime.date(2026, MONTHS[m], int(day))
    return (parse(d_dead) - parse(d_open)).days


def main():
    probs = [json.loads(l) for l in (ROOT / "data/run17/ladder_problems.jsonl").open()
             if json.loads(l)["level"] == 3]
    d1 = {r["pid"]: r["answer"] for r in
          (json.loads(l) for l in (ROOT / "out/run19/demand19_out.jsonl").open())
          if r["dlevel"] == 1}
    rows, d1_fail = [], []
    for p in probs:
        prm = parse_params(p["problem"])
        diff = int(prm["sweet"].replace(",", "")) - int(prm["cap"].replace(",", ""))
        n_days = day_count(prm["d_open"], prm["d_dead"])
        # code check of the model's cached D1 answer (content, not judgment)
        a = d1[p["pid"]]
        ok = (f"{diff:,}" in a or str(diff) in a) and str(n_days) in a
        if not ok:
            d1_fail.append(p["pid"])
        anchor = ANCHOR.format(code=prm["code"], sweet=prm["sweet"], cap=prm["cap"],
                               diff=f"{diff:,}", d_dead=prm["d_dead"],
                               d_open=prm["d_open"], n_days=n_days)
        for dlevel, tmpl in ((2, D2), (3, D3)):
            q = tmpl.format(**prm)
            rows.append({"pid": p["pid"], "dlevel": dlevel,
                         "user": f"{p['problem']}\n\nTASK: {q}{anchor}"})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"{len(rows)} staged rows (8 problems x D2,D3) -> {OUT}")
    print(f"model D1 code-check: {8-len(d1_fail)}/8 pass"
          + (f" (failed pids {d1_fail} — anchor carries code truth)" if d1_fail else ""))
    print("md5", hashlib.md5(OUT.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
