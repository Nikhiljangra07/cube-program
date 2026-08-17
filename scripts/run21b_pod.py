"""
run21b_pod.py — RUN 21B pod job (RUNBOOK21 21B amendment): cube arm ONLY,
regenerated with the constraint guard + digit screen. Arm G untouched.

  (setsid nohup python3 run21b_pod.py > out/rematch21b.log 2>&1 < /dev/null &)
Writes /workspace/div/out/rematch21b_out.jsonl (16 C rows)
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

WD = Path("/workspace/div")
OUT = WD / "out/rematch21b_out.jsonl"

CONSEQUENCE = (" VERIFIED CONSEQUENCE (binding): because the {code} track is not "
               "executable before {d_dead}, you must NOT choose, recommend, or "
               "build the plan on the {code} track or on committing ${sweet}. "
               "Select the alternative path in the DECISION NOW question and "
               "ground your reasons in the remaining stated facts.")
REMINDER = ("\nREMINDER: the {code} track is BARRED — it cannot be executed. "
            "Choose the other option.")


def commits_to(code, text):
    if re.search(rf"(choose|choosing|recommend|commit(ting)? to|select|proceed with|"
                 rf"escalate with|pursue) (the )?{code}", text, re.I):
        return True
    first = text.split(".")[0]
    return code.lower() in first.lower()


def foreign_digits(problem, text):
    probnums = set(re.findall(r"[\d][\d,]*", problem))
    return [n for n in re.findall(r"[\d][\d,]*", text)
            if n not in probnums and not re.fullmatch(r"\d{1,3}%?", n)]


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
        anchor_c = anchor + CONSEQUENCE.format(code=prm["code"], sweet=prm["sweet"],
                                               d_dead=prm["d_dead"])
        atomic = gen2(model, tok, WRK_SYS,
                      f"{p['problem']}\n\nTASK: {D1.format(**prm)}", max_new=256)
        d1_ok = (f"{diff:,}" in atomic or str(diff) in atomic) and str(n_days) in atomic
        judgment = gen2(model, tok, WRK_SYS,
                        f"{p['problem']}\n\nTASK: {D2.format(**prm)}{anchor}",
                        max_new=256)
        # prediction with digit screen
        pred_user = (f"{p['problem']}\n\nTASK: "
                     f"{PREDQ.format(surname=p['counterparty'])}{anchor}")
        prediction = gen2(model, tok, WRK_SYS, pred_user, max_new=192)
        screened = False
        if foreign_digits(p["problem"], prediction):
            prediction = gen2(model, tok, WRK_SYS,
                              pred_user + "\nUse NO numbers at all.", max_new=192)
            screened = True
        screen_fail = bool(foreign_digits(p["problem"], prediction))
        # choice with constraint guard
        choice_user = f"{p['problem']}\n\nTASK: {D3.format(**prm)}{anchor_c}"
        choice = gen2(model, tok, WRK_SYS, choice_user, max_new=256)
        guarded = False
        if commits_to(prm["code"], choice):
            choice = gen2(model, tok, WRK_SYS,
                          choice_user + REMINDER.format(code=prm["code"]), max_new=256)
            guarded = True
        guard_fail = commits_to(prm["code"], choice)
        est_user = (f"{p['problem']}\n\nTASK: "
                    f"{ESTQ.format(choice=choice, d_dead=prm['d_dead'])}{anchor_c}")
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
                            "screened": screened, "screen_fail": screen_fail,
                            "guarded": guarded, "guard_fail": guard_fail}) + "\n")
        f.flush()
        print(f"[C pid {p['pid']:02d}] done (guard={'retry' if guarded else 'ok'}"
              f"{'/FAIL' if guard_fail else ''}, screen="
              f"{'retry' if screened else 'ok'}{'/FAIL' if screen_fail else ''})",
              flush=True)
    f.close()
    print("RUN21B POD COMPLETE", flush=True)


if __name__ == "__main__":
    main()
