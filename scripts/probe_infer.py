"""
probe_infer.py — POD-SIDE: answer the 24x2 probes with one arm (base or wrk adapter).

Single-seat inference (the wrk seat is the trained seat; base = no adapter), greedy,
chat template, max_new_tokens 320. Writes out/probe_answers_<label>.jsonl.

  python probe_infer.py --label base
  python probe_infer.py --label laneF --adapter adapters/wrk_laneF
"""
from __future__ import annotations
import argparse, json, os
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

BASE = os.environ.get("LORA_BASE", "ibm-granite/granite-4.0-micro")
PROBES = Path("/workspace/div/probes/probes.jsonl")
OUTD = Path("/workspace/div/out")

SYS = "You are a sharp analytical advisor. Answer directly and concretely."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--adapter", default=None)
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                                 device_map="cuda")
    if args.adapter:
        model = PeftModel.from_pretrained(model, args.adapter)
    model.eval()

    rows = [json.loads(l) for l in PROBES.open()]
    OUTD.mkdir(parents=True, exist_ok=True)
    out_p = OUTD / f"probe_answers_{args.label}.jsonl"
    with out_p.open("w") as f:
        for r in rows:
            rec = {"id": r["id"]}
            for kind, q in (("recall", r["recall_q"]), ("manip", r["manip_q"])):
                msgs = [{"role": "system", "content": SYS},
                        {"role": "user", "content": q}]
                ids = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                              return_tensors="pt").to("cuda")
                with torch.no_grad():
                    gen = model.generate(ids, max_new_tokens=320, do_sample=False,
                                         pad_token_id=tok.eos_token_id)
                rec[kind] = tok.decode(gen[0][ids.shape[1]:], skip_special_tokens=True).strip()
            f.write(json.dumps(rec) + "\n")
            print(f"{args.label} {r['id']} ok", flush=True)
    print(f"PROBES DONE {args.label} -> {out_p}")


if __name__ == "__main__":
    main()
