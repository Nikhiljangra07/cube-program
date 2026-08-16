"""
run18_eval.py — RUN 18 pod-side $0 scorer (RUNBOOK18 frozen bars).

Loads ver18_eval.jsonl (messages format), renders the trained gate's verdict on
each row, parses SOUND / FATAL, scores against gold assistant labels.

  FROZEN BARS: recall_fatal >= 0.75  AND  fp_on_sound <= 0.30
  (fp_on_sound is the exact quantity ver_16 failed at 96% in the RULER-T read)

  python run18_eval.py [adapter_dir]     # default adapters/ver_18_qwen
Writes ver18_eval.json next to the log.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from run13b_pod import BASE
from run15_match_pod import gen2

WD = Path("/workspace/div")


def main():
    adapter = sys.argv[1] if len(sys.argv) > 1 else "adapters/ver_18_qwen"
    rows = [json.loads(l) for l in (WD / "ver18_eval.jsonl").open()]
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                                 device_map="cuda")
    model = PeftModel.from_pretrained(model, str(WD / adapter))
    tp = fn = fp = tn = bad = 0
    for i, r in enumerate(rows):
        sys_p, user, gold = (r["messages"][0]["content"], r["messages"][1]["content"],
                             r["messages"][2]["content"])
        out = gen2(model, tok, sys_p, user, max_new=96).upper()
        pred_fatal = out.startswith("FATAL")
        if not (out.startswith("FATAL") or out.startswith("SOUND")):
            bad += 1
            pred_fatal = True  # unparseable counts as a flag (conservative)
        gold_fatal = gold.startswith("FATAL")
        if gold_fatal and pred_fatal:
            tp += 1
        elif gold_fatal:
            fn += 1
        elif pred_fatal:
            fp += 1
        else:
            tn += 1
        print(f"[{i:03d}] gold={'F' if gold_fatal else 'S'} pred={'F' if pred_fatal else 'S'}",
              flush=True)
    recall_fatal = tp / max(tp + fn, 1)
    fp_on_sound = fp / max(fp + tn, 1)
    res = {"n": len(rows), "recall_fatal": round(recall_fatal, 3),
           "fp_on_sound": round(fp_on_sound, 3), "unparseable": bad,
           "tp": tp, "fn": fn, "fp": fp, "tn": tn,
           "bars": "recall_fatal>=0.75 AND fp_on_sound<=0.30",
           "verdict": "PASS" if (recall_fatal >= 0.75 and fp_on_sound <= 0.30) else "FAIL"}
    (WD / "out/ver18_eval.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    print("RUN18 EVAL COMPLETE", flush=True)


if __name__ == "__main__":
    main()
