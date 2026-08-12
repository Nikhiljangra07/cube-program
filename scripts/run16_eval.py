"""
run16_eval.py — RUN 16 stage 1 verdict: verifier accuracy on held-out REAL
Sonnet-labeled pairs (RUNBOOK16 frozen bars; code-only scoring, $0, no keys).

Runs on the pod after training:
  LORA_BASE="Qwen/Qwen3-4B-Instruct-2507" python run16_eval.py \
      --adapter adapters/ver_16_qwen --data verifier_eval.jsonl

FROZEN BARS (both required):
  recall_flawed >= 0.75   (of 75 real flawed pairs, catch >= 57)
  recall_clean  >= 0.70   (of 34 real clean pairs, pass >= 24)
Reference points (reported): code-checker semantic recall was 0.20 (run 13);
an all-flag baseline scores recall_clean = 0.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

import os
BASE = os.environ.get("LORA_BASE", "Qwen/Qwen3-4B-Instruct-2507")
WD = Path("/workspace/div")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--data", default="verifier_eval.jsonl")
    args = ap.parse_args()
    rows = [json.loads(l) for l in (WD / args.data).open()]
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                                 device_map="cuda")
    model = PeftModel.from_pretrained(model, str(WD / args.adapter))
    res = []
    for i, r in enumerate(rows):
        msgs = r["messages"][:2]
        gold_flagged = r["messages"][2]["content"].startswith("FLAGGED")
        ids = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                      return_tensors="pt")
        ids = ids["input_ids"] if hasattr(ids, "keys") else ids
        with torch.no_grad():
            o = model.generate(ids.to("cuda"), max_new_tokens=96, do_sample=False,
                               pad_token_id=tok.eos_token_id)
        out = tok.decode(o[0][ids.shape[1]:], skip_special_tokens=True).strip()
        pred_flagged = out.upper().startswith("FLAGGED")
        pred_grounded = out.upper().startswith("GROUNDED")
        res.append({"i": i, "gold_flagged": gold_flagged,
                    "pred_flagged": pred_flagged,
                    "malformed": not (pred_flagged or pred_grounded),
                    "out": out[:200]})
        if (i + 1) % 20 == 0:
            print(f"  {i+1}/{len(rows)}", flush=True)
    flawed = [r for r in res if r["gold_flagged"]]
    clean = [r for r in res if not r["gold_flagged"]]
    rf = sum(1 for r in flawed if r["pred_flagged"]) / len(flawed)
    rc = sum(1 for r in clean if not r["pred_flagged"] and not r["malformed"]) / len(clean)
    mal = sum(1 for r in res if r["malformed"])
    summary = {"n": len(res), "n_flawed": len(flawed), "n_clean": len(clean),
               "recall_flawed": round(rf, 3), "recall_clean": round(rc, 3),
               "malformed": mal,
               "bars": "recall_flawed >= 0.75 AND recall_clean >= 0.70",
               "STAGE1": "PASS" if rf >= 0.75 and rc >= 0.70 else "FAIL"}
    (WD / "out/ver16_eval.json").write_text(json.dumps(
        {"summary": summary, "rows": res}, indent=1))
    print(json.dumps(summary, indent=1))
    print("RUN16 EVAL COMPLETE")


if __name__ == "__main__":
    main()
