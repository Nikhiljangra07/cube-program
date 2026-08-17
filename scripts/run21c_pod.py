"""
run21c_pod.py — RUN 21C pod job (RUNBOOK21 21C amendment): cube arm only,
fixed digit screen + prediction-side bar. Built and mock-verified pre-pod.

  (setsid nohup python3 run21c_pod.py > out/rematch21c.log 2>&1 < /dev/null &)
Writes /workspace/div/out/rematch21c_out.jsonl (16 C rows)
"""
from __future__ import annotations
import json, re
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from run13b_pod import BASE
from run15_match_pod import BRIDGE, EST, WRK_SYS, gen2
from run19_demand import D1, D2, D3, parse_params
from run20_stage import ANCHOR, day_count
from run21_pod import ESTQ, PREDQ
from run21b_pod import CONSEQUENCE, REMINDER, commits_to

WD = Path("/workspace/div")
OUT = WD / "out/rematch21c_out.jsonl"

PRED_BAR = (" Do not narrate the {code} track being signed, paid, chosen, or "
            "executed — it is barred.")


def foreign_numbers(problem, text, n_days):
    """21C screen: exempt ONLY a trailing ESTIMATE percent and the
    code-computed day-count; flag every other number absent from problem."""
    body = EST.sub(" ", text)
    probnums = set(re.findall(r"[\d][\d,]*", problem))
    allowed = probnums | {str(n_days), f"{n_days:,}"}
    return [n for n in re.findall(r"[\d][\d,]*", body) if n not in allowed]


def screened_gen(model, tok, user, problem, n_days, max_new):
    text = gen2(model, tok, WRK_SYS, user, max_new=max_new)
    retried = False
    if foreign_numbers(problem, text, n_days):
        text = gen2(model, tok, WRK_SYS,
                    user + "\nUse NO numbers except those written in the problem.",
                    max_new=max_new)
        retried = True
    return text, retried, bool(foreign_numbers(problem, text, n_days))


def main():
    (WD / "out").mkdir(exist_ok=True)
    probs = [json.loads(l) for l in (WD / "rematch_problems.jsonl").open()]
    done = {r["pid"] for r in (json.loads(l) for l in OUT.open())} if OUT.exists() else set()
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                                 device_map="cuda")
    model = PeftModel.from_pretrained(model, str(WD / "adapters/wrk_keep100_qwen"),
                                      adapter_name="G")
    f = OUT.open("a")
    for p in probs:
        if p["pid"] in done:
            continue
        prm = parse_params(p["problem"])
        diff = int(prm["sweet"].replace(",", "")) - int(prm["cap"].replace(",", ""))
        n_days = day_count(prm["d_open"], prm["d_dead"])
        anchor = ANCHOR.format(code=prm["code"], sweet=prm["sweet"], cap=prm["cap"],
                               diff=f"{diff:,}", d_dead=prm["d_dead"],
                               d_open=prm["d_open"], n_days=n_days)
        cons = CONSEQUENCE.format(code=prm["code"], sweet=prm["sweet"],
                                  d_dead=prm["d_dead"])
        atomic = gen2(model, tok, WRK_SYS,
                      f"{p['problem']}\n\nTASK: {D1.format(**prm)}", max_new=256)
        d1_ok = (f"{diff:,}" in atomic or str(diff) in atomic) and str(n_days) in atomic
        judgment = gen2(model, tok, WRK_SYS,
                        f"{p['problem']}\n\nTASK: {D2.format(**prm)}{anchor}",
                        max_new=256)
        pred_user = (f"{p['problem']}\n\nTASK: "
                     f"{PREDQ.format(surname=p['counterparty'])}{anchor}{cons}"
                     f"{PRED_BAR.format(code=prm['code'])}")
        prediction, p_retry, p_fail = screened_gen(model, tok, pred_user,
                                                   p["problem"], n_days, 192)
        choice_user = f"{p['problem']}\n\nTASK: {D3.format(**prm)}{anchor}{cons}"
        choice = gen2(model, tok, WRK_SYS, choice_user, max_new=256)
        guarded = False
        if commits_to(prm["code"], choice):
            choice = gen2(model, tok, WRK_SYS,
                          choice_user + REMINDER.format(code=prm["code"]), max_new=256)
            guarded = True
        guard_fail = commits_to(prm["code"], choice)
        if foreign_numbers(p["problem"], choice, n_days):
            choice2 = gen2(model, tok, WRK_SYS,
                           choice_user + "\nUse NO numbers except those written "
                           "in the problem.", max_new=256)
            if not commits_to(prm["code"], choice2):
                choice = choice2
        est_user = (f"{p['problem']}\n\nTASK: "
                    f"{ESTQ.format(choice=choice, d_dead=prm['d_dead'])}{anchor}{cons}")
        est = gen2(model, tok, WRK_SYS, est_user, max_new=96)
        inj = False
        if not EST.search(est):
            est = gen2(model, tok, WRK_SYS,
                       est_user + "\n(Do not omit the ESTIMATE line.)", max_new=96)
            if not EST.search(est):
                est, inj = est + " ESTIMATE: 50%", True
        final = " ".join([judgment.strip(), prediction.strip(), choice.strip(),
                          BRIDGE, EST.findall(est)[-1]])
        f.write(json.dumps({"arm": "C", "pid": p["pid"], "answer": final,
                            "d1_ok": d1_ok, "est_injected": inj,
                            "screened": p_retry, "screen_fail": p_fail,
                            "guarded": guarded, "guard_fail": guard_fail}) + "\n")
        f.flush()
        print(f"[C pid {p['pid']:02d}] done", flush=True)
    f.close()
    print("RUN21C POD COMPLETE", flush=True)


if __name__ == "__main__":
    main()
