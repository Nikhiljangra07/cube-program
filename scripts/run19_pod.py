"""
run19_pod.py — RUN 19 pod job (RUNBOOK19): demand-ladder generation, keep100
only, resume-safe, tiny (~32 gens, one adapter). D5 is never generated here —
it is the cached run-17 L3 arm.

  (setsid nohup python3 run19_pod.py > out/demand19.log 2>&1 < /dev/null &)
Writes /workspace/div/out/demand19_out.jsonl
"""
from __future__ import annotations
import json
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from run13b_pod import BASE
from run15_match_pod import EST, WRK_SYS, gen2

WD = Path("/workspace/div")
OUT = WD / "out/demand19_out.jsonl"


def main():
    (WD / "out").mkdir(exist_ok=True)
    rows = [json.loads(l) for l in (WD / "demand_ladder.jsonl").open()]
    assert len(rows) == 32
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
        max_new = 512 if r["dlevel"] == 4 else 256
        ans = gen2(model, tok, WRK_SYS, r["user"], max_new=max_new)
        inj = False
        if r["dlevel"] == 4 and not EST.search(ans):
            ans2 = gen2(model, tok, WRK_SYS,
                        r["user"] + "\n(Do not omit the final ESTIMATE line.)",
                        max_new=max_new)
            ans, inj = (ans2, False) if EST.search(ans2) else (ans2 + " ESTIMATE: 50%", True)
        f.write(json.dumps({"pid": r["pid"], "dlevel": r["dlevel"], "answer": ans,
                            "est_injected": inj}) + "\n")
        f.flush()
        print(f"[D{r['dlevel']} pid {r['pid']}] done ({len(ans.split())}w)", flush=True)
    f.close()
    print("RUN19 POD COMPLETE", flush=True)


if __name__ == "__main__":
    main()
