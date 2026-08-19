"""
run23_pod.py — RUN 23 pod job (RUNBOOK23): Qwen3-4B-Thinking-2507 naked
one-pass on the run-22 frozen holdout. No adapter, no harness. Frozen
pre-run; C-arm answers/verdicts are immutable run-22 cache.

  (setsid nohup python3 run23_pod.py > out/thinking23.log 2>&1 < /dev/null &)
Reads  /workspace/div/holdout_problems.jsonl
Writes /workspace/div/out/thinking23_out.jsonl
"""
from __future__ import annotations
import json
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from run15_match_pod import EST, GEN_SINGLE, WRK_SYS

BASE_T = "Qwen/Qwen3-4B-Thinking-2507"
WD = Path("/workspace/div")
OUT = WD / "out/thinking23_out.jsonl"


def gen_think(model, tok, user, max_new):
    msgs = [{"role": "system", "content": WRK_SYS},
            {"role": "user", "content": user}]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                  return_tensors="pt").to(model.device)
    out = model.generate(ids, max_new_tokens=max_new, do_sample=True,
                         temperature=0.6, top_p=0.95, top_k=20,
                         pad_token_id=tok.eos_token_id)
    gen = out[0][ids.shape[1]:]
    return tok.decode(gen, skip_special_tokens=True), int(gen.shape[0])


def main():
    (WD / "out").mkdir(exist_ok=True)
    probs = [json.loads(l) for l in (WD / "holdout_problems.jsonl").open()]
    assert len(probs) == 16, f"expected 16 holdout problems, got {len(probs)}"
    done = {r["pid"] for r in (json.loads(l) for l in OUT.open())} \
        if OUT.exists() else set()
    tok = AutoTokenizer.from_pretrained(BASE_T)
    model = AutoModelForCausalLM.from_pretrained(
        BASE_T, torch_dtype=torch.bfloat16, device_map="cuda")
    f = OUT.open("a")
    for p in probs:
        pid, text = p["pid"], p["problem"]
        if pid in done:
            continue
        user = GEN_SINGLE.format(problem=text)
        raw, total = gen_think(model, tok, user, 9000)
        leaked = False
        if "</think>" not in raw:                 # 17B leak fix: one retry
            raw, total = gen_think(model, tok, user, 13000)
            leaked = "</think>" not in raw        # judged as-is if still open
        ans = raw.split("</think>")[-1].strip()
        inj = False
        if not EST.search(ans):                   # with_estimate law
            raw2, n2 = gen_think(
                model, tok,
                user + "\n(End your answer with one line 'ESTIMATE: NN%'.)",
                9000)
            total += n2
            a2 = raw2.split("</think>")[-1].strip()
            if EST.search(a2):
                ans = a2
            else:
                ans, inj = ans + " ESTIMATE: 50%", True
        f.write(json.dumps({"arm": "R", "pid": pid, "answer": ans,
                            "gen_tokens": total, "leaked": leaked,
                            "est_injected": inj}) + "\n")
        f.flush()
        print(f"[R pid {pid:02d}] tokens {total} leaked={leaked}", flush=True)
    f.close()
    print("RUN23 POD COMPLETE", flush=True)


if __name__ == "__main__":
    main()
