"""
run19_demand.py — RUN 19 demand-ladder builder (RUNBOOK19, $0).

The flip of run 17: supply FIXED (the 8 six-fact L3 problems, byte-reused from
data/run17/ladder_problems.jsonl), DEMAND varied across five levels. D5 (full
GEN_SINGLE demand) is the cached run-17 L3 arm — 0/8 strict-clean, $0 anchor.
Only D1–D4 are generated (32 answers).

  D1 ATOMIC     : extraction + one derivation-with-basis (cap check, day count)
  D2 JUDGMENT   : name the binding constraint, quote the fact — no plan
  D3 CHOICE     : pick one option, exactly two fact-grounded reasons — no plan
  D4 PLAN-LITE  : three steps, ONLY stated specifics, [TBD] for absent ones
  D5 FULL       : GEN_SINGLE verbatim (run 17 cache)

Planted parameters are parsed back out of the fixed problem templates
(cap, option price, dates) — parse is asserted complete on all 8 problems.

  python scripts/run19_demand.py   # writes data/run19/demand_ladder.jsonl + md5
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/run19/demand_ladder.jsonl"

D1 = ("Answer from the stated facts only, in at most three sentences: "
      "(a) Does the {code} track price of ${sweet} exceed the ${cap} single-expense "
      "sign-off threshold — yes or no, and by how much? "
      "(b) How many days lie between {d_open} and the {d_dead} hard deadline? "
      "Show the basis for any number you derive. Do not add any other facts.")
D2 = ("In at most three sentences: name the SINGLE most binding constraint in this "
      "situation, and quote the stated fact that makes it binding. Do not propose "
      "a plan, do not add numbers, dates, or actors not in the problem.")
D3 = ("Answer the DECISION NOW question by choosing exactly ONE of the two options. "
      "Give exactly two reasons, each grounded in a stated fact of the problem. "
      "Do not add numbers, dates, times, or actors not in the problem. Do not give "
      "a further plan.")
D4 = ("Give a three-step plan for the DECISION NOW question. Use ONLY numbers, "
      "dates, and people stated in the problem; wherever a needed specific is not "
      "supplied, write [TBD] instead of inventing one. "
      "Final line, exactly: ESTIMATE: NN%")


def parse_params(p):
    cap = re.search(r"above \$([\d,]*\d) requires sign-off", p).group(1)
    m = re.search(r"the (\w+) track — \w+ holds the terms open until "
                  r"([A-Z][a-z]+ \d+) for \$([\d,]*\d)", p)
    code, d_open, sweet = m.group(1), m.group(2), m.group(3)
    d_dead = re.search(r"Hard deadline: ([A-Z][a-z]+ \d+);", p).group(1)
    return dict(cap=cap, code=code, d_open=d_open, sweet=sweet, d_dead=d_dead)


def main():
    probs = [json.loads(l) for l in (ROOT / "data/run17/ladder_problems.jsonl").open()
             if json.loads(l)["level"] == 3]
    assert len(probs) == 8 and [p["pid"] for p in probs] == list(range(16, 24))
    rows = []
    for p in probs:
        prm = parse_params(p["problem"])
        for dlevel, tmpl in ((1, D1), (2, D2), (3, D3), (4, D4)):
            q = tmpl.format(**prm)
            rows.append({"pid": p["pid"], "dlevel": dlevel,
                         "problem": p["problem"],
                         "user": f"{p['problem']}\n\nTASK: {q}"})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r) + "\n" for r in rows))
    md5 = hashlib.md5(OUT.read_bytes()).hexdigest()
    print(f"{len(rows)} demand rows (8 problems x D1-D4) -> {OUT}\nmd5 {md5}")


if __name__ == "__main__":
    main()
