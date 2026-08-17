"""
run21_pod.py — RUN 21 pod job (RUNBOOK21): THE REMATCH — the staged cube-v2
pipeline vs the naked generalist, same weights, 16 fresh problems, resume-safe.

Arm C (cube-v2), five demand-matched calls per problem, all keep100:
  1. atomic   : D1 verbatim (code-checked against computed truth; greedy, so
                no regen — failures counted, anchor always carries code truth)
  2. judgment : D2 + VERIFIED-FACTS anchor
  3. prediction: bounded conditional-reaction + signal question + anchor
  4. choice   : D3 + anchor
  5. estimate : one-line ESTIMATE call anchored on the made choice
  final = [judgment] [prediction] [choice] [BRIDGE (fixed, digit-free)]
          [estimate line]   — coach law: verbatim carriage, no re-narration.

Arm G (generalist): GEN_SINGLE verbatim single pass + with_estimate law.

  (setsid nohup python3 run21_pod.py > out/rematch21.log 2>&1 < /dev/null &)
Writes /workspace/div/out/rematch21_out.jsonl
"""
from __future__ import annotations
import json
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from run13b_pod import BASE
from run15_match_pod import BRIDGE, EST, GEN_SINGLE, WRK_SYS, gen2, with_estimate
from run19_demand import D1, D2, D3, parse_params
from run20_stage import ANCHOR, day_count

WD = Path("/workspace/div")
OUT = WD / "out/rematch21_out.jsonl"

PREDQ = ("In one or two sentences: state {surname}'s most likely reaction as an "
         "explicitly conditional prediction ('if... then...'), and name ONE "
         "observable signal that would show the read is wrong. Do not add "
         "numbers, dates, times, or actors not in the problem. Do not give a plan.")
ESTQ = ("Your decision (already made): {choice}\n\nGiven the verified facts, "
        "output exactly one line: ESTIMATE: NN% — your confidence this path "
        "succeeds by {d_dead}.")


def main():
    (WD / "out").mkdir(exist_ok=True)
    probs = [json.loads(l) for l in (WD / "rematch_problems.jsonl").open()]
    assert len(probs) == 16
    done = {(r["arm"], r["pid"]) for r in
            (json.loads(l) for l in OUT.open())} if OUT.exists() else set()
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                                 device_map="cuda")
    model = PeftModel.from_pretrained(model, str(WD / "adapters/wrk_keep100_qwen"),
                                      adapter_name="G")
    f = OUT.open("a")
    for p in probs:
        prm = parse_params(p["problem"])
        diff = int(prm["sweet"].replace(",", "")) - int(prm["cap"].replace(",", ""))
        n_days = day_count(prm["d_open"], prm["d_dead"])
        anchor = ANCHOR.format(code=prm["code"], sweet=prm["sweet"], cap=prm["cap"],
                               diff=f"{diff:,}", d_dead=prm["d_dead"],
                               d_open=prm["d_open"], n_days=n_days)
        # ---- arm C ----
        if ("C", p["pid"]) not in done:
            atomic = gen2(model, tok, WRK_SYS,
                          f"{p['problem']}\n\nTASK: {D1.format(**prm)}", max_new=256)
            d1_ok = (f"{diff:,}" in atomic or str(diff) in atomic) and str(n_days) in atomic
            judgment = gen2(model, tok, WRK_SYS,
                            f"{p['problem']}\n\nTASK: {D2.format(**prm)}{anchor}",
                            max_new=256)
            prediction = gen2(model, tok, WRK_SYS,
                              f"{p['problem']}\n\nTASK: "
                              f"{PREDQ.format(surname=p['counterparty'])}{anchor}",
                              max_new=192)
            choice = gen2(model, tok, WRK_SYS,
                          f"{p['problem']}\n\nTASK: {D3.format(**prm)}{anchor}",
                          max_new=256)
            est_user = (f"{p['problem']}\n\nTASK: "
                        f"{ESTQ.format(choice=choice, d_dead=prm['d_dead'])}{anchor}")
            est = gen2(model, tok, WRK_SYS, est_user, max_new=96)
            inj = False
            if not EST.search(est):
                est = gen2(model, tok, WRK_SYS,
                           est_user + "\n(Do not omit the ESTIMATE line.)", max_new=96)
                if not EST.search(est):
                    est, inj = est + " ESTIMATE: 50%", True
            est_line = EST.findall(est)[-1]
            final = " ".join([judgment.strip(), prediction.strip(), choice.strip(),
                              BRIDGE, est_line])
            f.write(json.dumps({"arm": "C", "pid": p["pid"], "answer": final,
                                "pieces": {"atomic": atomic, "judgment": judgment,
                                           "prediction": prediction, "choice": choice,
                                           "est": est},
                                "d1_ok": d1_ok, "est_injected": inj}) + "\n")
            f.flush()
            print(f"[C pid {p['pid']:02d}] done (d1_ok={d1_ok})", flush=True)
        # ---- arm G ----
        if ("G", p["pid"]) not in done:
            user = GEN_SINGLE.format(problem=p["problem"])
            ans = gen2(model, tok, WRK_SYS, user, max_new=500)
            ans, inj = with_estimate(model, tok, user, ans)
            f.write(json.dumps({"arm": "G", "pid": p["pid"], "answer": ans,
                                "est_injected": inj}) + "\n")
            f.flush()
            print(f"[G pid {p['pid']:02d}] done", flush=True)
    f.close()
    print("RUN21 POD COMPLETE", flush=True)


if __name__ == "__main__":
    main()
