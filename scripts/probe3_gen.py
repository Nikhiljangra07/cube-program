"""
probe3_gen.py — PROBE 3 pod stage: elicited-derivation revisions (RUNBOOK10 frozen).

Runs ON POD. Loads Qwen base + both adapters (faceV_10 subject, keep100 reference),
generates one greedy revision per input row. Self-contained; no harness imports.

  LORA_BASE="Qwen/Qwen3-4B-Instruct-2507" python probe3_gen.py

Reads  /workspace/p3/probe3_inputs.jsonl
Writes /workspace/p3/probe3_raw.jsonl
"""
from __future__ import annotations
import json, os
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE = os.environ.get("LORA_BASE", "Qwen/Qwen3-4B-Instruct-2507")
WD = Path("/workspace/p3")
ADAPTERS = {"faceV_10": "/workspace/p3/adapters/wrk_faceV_10_qwen",
            "keep100": "/workspace/p3/adapters/wrk_keep100_qwen"}

SYS = "You write one precise, decisive, realistic reasoning thread pursuing a given strategic angle."
USER = ("PROBLEM: {problem}\n\nYOUR PREVIOUS PLAN: {prior}\n\nUPDATE: {boost}\n\n"
        "The situation has changed as described in UPDATE. Revise your plan in 3-4 "
        "sentences, cold and analytical: (1) state what the update changes for your "
        "plan, (2) give the revised plan, (3) end with your revised success estimate "
        "in digits with a % sign, derived from the updated situation.")


def main():
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map="cuda")
    first = True
    for arm, path in ADAPTERS.items():
        if first:
            model = PeftModel.from_pretrained(model, path, adapter_name=arm)
            first = False
        else:
            model.load_adapter(path, adapter_name=arm)
    rows = [json.loads(l) for l in (WD / "probe3_inputs.jsonl").open()]
    out_f = (WD / "probe3_raw.jsonl").open("w")
    done = 0
    for r in rows:
        model.set_adapter(r["arm"])
        msgs = [{"role": "system", "content": SYS},
                {"role": "user", "content": USER.format(problem=r["problem"], prior=r["prior"],
                                                        boost=r["boost"])}]
        ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt")
        ids = ids["input_ids"] if hasattr(ids, "keys") else ids  # 4.57 vs 5.x
        with torch.no_grad():
            out = model.generate(ids.to("cuda"), max_new_tokens=384, do_sample=False,
                                 pad_token_id=tok.eos_token_id)
        text = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()
        out_f.write(json.dumps({**{k: r[k] for k in ("pair", "arm", "thread_idx", "old_est", "boost")},
                                "revision": text}) + "\n")
        out_f.flush()
        done += 1
        if done % 8 == 0:
            print(f"  {done}/{len(rows)}", flush=True)
    out_f.close()
    print(f"PROBE3 GEN DONE: {done}/{len(rows)} -> {WD/'probe3_raw.jsonl'}")


if __name__ == "__main__":
    main()
