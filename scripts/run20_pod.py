"""
run20_pod.py — RUN 20 pod job (RUNBOOK20): 16 staged generations, keep100,
greedy, resume-safe. Tiny (~5 min).

  (setsid nohup python3 run20_pod.py > out/staged20.log 2>&1 < /dev/null &)
Writes /workspace/div/out/staged20_out.jsonl
"""
from __future__ import annotations
import json
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from run13b_pod import BASE
from run15_match_pod import WRK_SYS, gen2

WD = Path("/workspace/div")
OUT = WD / "out/staged20_out.jsonl"


def main():
    (WD / "out").mkdir(exist_ok=True)
    rows = [json.loads(l) for l in (WD / "staged.jsonl").open()]
    assert len(rows) == 16
    done = {(r["pid"], r["dlevel"]) for r in
            (json.loads(l) for l in OUT.open())} if OUT.exists() else set()
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                                 device_map="cuda")
    model = PeftModel.from_pretrained(model, str(WD / "adapters/wrk_keep100_qwen"),
                                      adapter_name="G")
    f = OUT.open("a")
    for r in rows:
        if (r["pid"], r["dlevel"]) in done:
            continue
        ans = gen2(model, tok, WRK_SYS, r["user"], max_new=256)
        f.write(json.dumps({"pid": r["pid"], "dlevel": r["dlevel"],
                            "answer": ans}) + "\n")
        f.flush()
        print(f"[S D{r['dlevel']} pid {r['pid']}] done ({len(ans.split())}w)",
              flush=True)
    f.close()
    print("RUN20 POD COMPLETE", flush=True)


if __name__ == "__main__":
    main()
