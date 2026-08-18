"""
run22_pod.py — RUN 22 pod job (RUNBOOK22): the generalized cube-v2 pipeline
on non-template problems, plus the naked baseline. FROZEN BEFORE the holdout
problems exist; zero behavioral edits after first contact (crash-only fixes,
logged in RUNBOOK22).

  (setsid nohup python3 run22_pod.py > out/holdout22.log 2>&1 < /dev/null &)
Reads  /workspace/div/holdout_problems.jsonl   rows {pid, problem}
Writes /workspace/div/out/holdout22_out.jsonl
"""
from __future__ import annotations
import datetime, json, re
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from run13b_pod import BASE
from run15_match_pod import BRIDGE, EST, GEN_SINGLE, WRK_SYS, gen2, with_estimate

WD = Path("/workspace/div")
OUT = WD / "out/holdout22_out.jsonl"

# ---------- frozen prompts ----------
EXTRACT = (
    "TASK: List the concrete facts of this problem, one per line, each in the "
    "form:\nFACT: <the fact, copied as exactly as possible from the problem's "
    "own words>\nInclude every date, deadline, amount of money, numeric limit "
    "or cap, named person or organization, and explicitly stated rule or "
    "constraint. Then list the courses of action the problem poses, one per "
    "line:\nOPTION: <a short name for the course of action, using the "
    "problem's own words>\nDo not add anything that is not written in the "
    "problem.")
COMPARE = (
    "TASK: From the VERIFIED FACTS below, output exactly two lines and "
    "nothing else:\nCOMPARE: <amount A> vs <amount B> — <one short clause on "
    "why this comparison decides the problem>\nSPAN: <date 1> to <date 2> — "
    "<one short clause on why this interval matters>\nUse only amounts and "
    "dates that appear in the facts. If no meaningful comparison or date "
    "pair exists, write NONE on that line.")
JUDGMENT = ("In at most three sentences: name the SINGLE most binding "
            "constraint in this situation, and quote the stated fact that "
            "makes it binding. Do not propose a plan, do not add numbers, "
            "dates, or actors not in the problem.")
PREDQ = ("In one or two sentences: state the counterparty's most likely "
         "reaction as an explicitly conditional prediction ('if... then...'), "
         "and name ONE observable signal that would show the read is wrong. "
         "Do not add numbers, dates, times, or actors not in the problem. Do "
         "not give a plan.")
CHOICE = ("Answer the decision this problem poses by choosing exactly ONE "
          "course of action (one of the OPTIONS if any are listed in the "
          "verified facts, otherwise state your chosen course in one "
          "sentence). Give exactly two reasons, each grounded in a stated "
          "fact. Do not add numbers, dates, times, or actors not in the "
          "problem. Do not commit to any course the verified facts or your "
          "constraint analysis mark as not executable. Do not give a further "
          "plan.")
ESTQ = ("Your decision (already made): {choice}\n\nGiven the verified facts, "
        "output exactly one line: ESTIMATE: NN% — your confidence this path "
        "succeeds.")
BAR_WORDS = re.compile(r"not executable|non-executable|infeasible|cannot be "
                       r"(approved|executed|obtained)|is barred", re.I)
DATE_RE = re.compile(r"(January|February|March|April|May|June|July|August|"
                     r"September|October|November|December)\s+\d{1,2}")
MONTHS = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}


def norm_num(n):
    return n.rstrip(",.")


def nums_in(text):
    return {norm_num(n) for n in re.findall(r"[\d][\d,]*", text)}


def verify_fact(problem, fact):
    """Every number verbatim-present; >=60% of 4+char words present."""
    pnums = nums_in(problem)
    if any(n not in pnums for n in nums_in(fact)):
        return False
    words = [w.lower() for w in re.findall(r"[A-Za-z]{4,}", fact)]
    if not words:
        return True
    hit = sum(1 for w in words if w in problem.lower())
    return hit / len(words) >= 0.6


def parse_money(s):
    m = re.findall(r"[\d][\d,]*", s)
    return int(m[0].replace(",", "")) if m else None


def parse_date(s):
    m = DATE_RE.search(s)
    if not m:
        return None
    return datetime.date(2026, MONTHS[m.group(1)], int(m.group().split()[1]))


def foreign_numbers(problem, text, allowed_extra):
    body = EST.sub(" ", text)
    allowed = nums_in(problem) | {norm_num(str(a)) for a in allowed_extra} \
        | {f"{a:,}" for a in allowed_extra if isinstance(a, int)}
    return [norm_num(n) for n in re.findall(r"[\d][\d,]*", body)
            if norm_num(n) not in allowed]


def commits_to(option, text):
    opt = re.escape(option.strip()[:40])
    if re.search(rf"(choose|choosing|recommend|commit(ting)? to|select|"
                 rf"proceed with|pursue|escalate with) (the )?.{{0,20}}{opt}",
                 text, re.I):
        return True
    first = text.split(".")[0]
    return option.strip().lower()[:25] in first.lower()


def screened_gen(model, tok, user, problem, allowed, max_new):
    text = gen2(model, tok, WRK_SYS, user, max_new=max_new)
    retried = False
    if foreign_numbers(problem, text, allowed):
        text = gen2(model, tok, WRK_SYS,
                    user + "\nUse NO numbers except those written in the problem.",
                    max_new=max_new)
        retried = True
    return text, retried, bool(foreign_numbers(problem, text, allowed))


def main():
    (WD / "out").mkdir(exist_ok=True)
    probs = [json.loads(l) for l in (WD / "holdout_problems.jsonl").open()]
    assert len(probs) == 16, f"expected 16 holdout problems, got {len(probs)}"
    done = {(r["arm"], r["pid"]) for r in
            (json.loads(l) for l in OUT.open())} if OUT.exists() else set()
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                                 device_map="cuda")
    model = PeftModel.from_pretrained(model, str(WD / "adapters/wrk_keep100_qwen"),
                                      adapter_name="G")
    f = OUT.open("a")
    for p in probs:
        pid, text = p["pid"], p["problem"]
        # ---- arm C ----
        if ("C", pid) not in done:
            # 0. extract + verify
            raw = gen2(model, tok, WRK_SYS, f"{text}\n\n{EXTRACT}", max_new=400)
            facts, options, dropped = [], [], 0
            for line in raw.splitlines():
                line = line.strip()
                if line.upper().startswith("FACT:"):
                    ft = line[5:].strip()
                    if verify_fact(text, ft):
                        facts.append(ft)
                    else:
                        dropped += 1
                elif line.upper().startswith("OPTION:"):
                    options.append(line[7:].strip())
            # 1. compare + span (model proposes, code computes)
            fact_block = "\n".join(f"- {ft}" for ft in facts) or "- (none verified)"
            cs = gen2(model, tok, WRK_SYS,
                      f"{text}\n\nVERIFIED FACTS:\n{fact_block}\n\n{COMPARE}",
                      max_new=160)
            comp_line = span_line = ""
            allowed_extra = []
            mm = re.search(r"COMPARE:\s*(.+?)\s+vs\s+(.+?)(—|$)", cs)
            if mm:
                a, b = parse_money(mm.group(1)), parse_money(mm.group(2))
                pn = nums_in(text)
                if (a is not None and b is not None and a != b
                        and (f"{a:,}" in pn or str(a) in pn)
                        and (f"{b:,}" in pn or str(b) in pn)):
                    rel = "EXCEEDS" if a > b else "is LESS THAN"
                    d = abs(a - b)
                    allowed_extra.append(d)
                    comp_line = (f" (i) ${a:,} {rel} ${b:,} by ${d:,} "
                                 f"(machine-checked).")
            ms = re.search(r"SPAN:\s*(.+?)\s+to\s+(.+?)(—|$)", cs)
            if ms:
                d1, d2 = parse_date(ms.group(1)), parse_date(ms.group(2))
                s1, s2 = DATE_RE.search(ms.group(1)), DATE_RE.search(ms.group(2))
                if (d1 and d2 and d1 != d2 and s1 and s2
                        and s1.group() in text and s2.group() in text):
                    nd = abs((d2 - d1).days)
                    allowed_extra.append(nd)
                    span_line = (f" (ii) {nd} days lie between "
                                 f"{ms.group(1).strip()} and {ms.group(2).strip()} "
                                 f"(machine-checked).")
            anchor = ("\n\nVERIFIED FACTS (extracted from the problem and "
                      "machine-checked — rely on them, do not re-derive):\n"
                      + fact_block + "\n" + comp_line + span_line)
            # 2-5. judgment / prediction / choice / estimate
            judgment = gen2(model, tok, WRK_SYS,
                            f"{text}\n\nTASK: {JUDGMENT}{anchor}", max_new=256)
            prediction, p_retry, p_fail = screened_gen(
                model, tok, f"{text}\n\nTASK: {PREDQ}{anchor}", text,
                allowed_extra, 192)
            choice_user = f"{text}\n\nTASK: {CHOICE}{anchor}"
            choice = gen2(model, tok, WRK_SYS, choice_user, max_new=256)
            barred = [o for o in options
                      if BAR_WORDS.search(judgment) and o.lower()[:25] in judgment.lower()
                      and BAR_WORDS.search(
                          judgment[max(0, judgment.lower().find(o.lower()[:25]) - 200):
                                   judgment.lower().find(o.lower()[:25]) + 200])]
            guarded = guard_fail = False
            for o in barred:
                if commits_to(o, choice):
                    choice = gen2(model, tok, WRK_SYS,
                                  choice_user + f"\nREMINDER: '{o}' is not "
                                  f"executable — choose another course.",
                                  max_new=256)
                    guarded = True
                    guard_fail = any(commits_to(x, choice) for x in barred)
                    break
            if foreign_numbers(text, choice, allowed_extra):
                c2 = gen2(model, tok, WRK_SYS,
                          choice_user + "\nUse NO numbers except those written "
                          "in the problem.", max_new=256)
                if not any(commits_to(o, c2) for o in barred):
                    choice = c2
            est_user = f"{text}\n\nTASK: {ESTQ.format(choice=choice)}{anchor}"
            est = gen2(model, tok, WRK_SYS, est_user, max_new=96)
            inj = False
            if not EST.search(est):
                est = gen2(model, tok, WRK_SYS,
                           est_user + "\n(Do not omit the ESTIMATE line.)",
                           max_new=96)
                if not EST.search(est):
                    est, inj = est + " ESTIMATE: 50%", True
            final = " ".join([judgment.strip(), prediction.strip(),
                              choice.strip(), BRIDGE, EST.findall(est)[-1]])
            f.write(json.dumps({"arm": "C", "pid": pid, "answer": final,
                                "n_facts": len(facts), "n_dropped": dropped,
                                "n_options": len(options),
                                "has_compare": bool(comp_line),
                                "has_span": bool(span_line),
                                "guarded": guarded, "guard_fail": guard_fail,
                                "screened": p_retry, "screen_fail": p_fail,
                                "est_injected": inj}) + "\n")
            f.flush()
            print(f"[C pid {pid:02d}] facts {len(facts)} (-{dropped}) "
                  f"cmp={bool(comp_line)} span={bool(span_line)}", flush=True)
        # ---- arm G ----
        if ("G", pid) not in done:
            user = GEN_SINGLE.format(problem=text)
            ans = gen2(model, tok, WRK_SYS, user, max_new=500)
            ans, inj = with_estimate(model, tok, user, ans)
            f.write(json.dumps({"arm": "G", "pid": pid, "answer": ans,
                                "est_injected": inj}) + "\n")
            f.flush()
            print(f"[G pid {pid:02d}] done", flush=True)
    f.close()
    print("RUN22 POD COMPLETE", flush=True)


if __name__ == "__main__":
    main()
