"""
run17b_fix.py — RUN 17B repair pass (RUNBOOK17B amendment, run-15 refs-fix
precedent): rival answers that hit max_new 4096 mid-thinking never closed
</think>, so the stored "answer" is raw deliberation. Judging those would
sandbag the rival and invalidate the match.

  detection : arm R row with > 1200 words (clean finals run ~100-600w;
              leaked deliberations run 2600w+)
  repair    : regenerate, same seed law (1700+pid), max_new 9000;
              if still unclosed, one retry (seed 2700+pid, max_new 13000);
              if STILL unclosed, keep best text and mark leak=true (honest)
  estimate  : run-13b law — one nudged retry, then inject ESTIMATE: 50% + flag
  verifier  : repaired rows get 'ver' cleared and re-rendered by ver_16_qwen

  (setsid nohup python3 run17b_fix.py > out/ladder17b_fix.log 2>&1 < /dev/null &)
Rewrites /workspace/div/out/ladder17b_out.jsonl in place (backup .pre_fix).
"""
from __future__ import annotations
import json, shutil
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from run13b_pod import BASE
from run15_match_pod import EST, GEN_SINGLE, WRK_SYS, gen2
from run17_pod import VER_SYS, VER_USER
from run17b_pod import GROUND, RIVAL

WD = Path("/workspace/div")
OUT = WD / "out/ladder17b_out.jsonl"
LEAK_WORDS = 1200


def gen_think_raw(model, tok, system, user, max_new):
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt")
    ids = ids["input_ids"] if hasattr(ids, "keys") else ids
    with torch.no_grad():
        out = model.generate(ids.to("cuda"), max_new_tokens=max_new, do_sample=True,
                             temperature=0.6, top_p=0.95, top_k=20,
                             pad_token_id=tok.eos_token_id)
    raw = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=False)
    closed = "</think>" in raw
    fin = raw.split("</think>")[-1]
    for t in {tok.eos_token, "<|im_end|>", "<|endoftext|>", tok.pad_token}:
        if t:
            fin = fin.replace(t, "")
    return fin.strip(), closed


def main():
    rows = [json.loads(l) for l in OUT.open()]
    shutil.copy(OUT, str(OUT) + ".pre_fix")
    bad = [r for r in rows if r["arm"] == "R"
           and len(r["answer"].split()) > LEAK_WORDS]
    print(f"repair targets: {len(bad)} leaked rival rows", flush=True)
    if bad:
        probs = {json.loads(l)["pid"]: json.loads(l)
                 for l in (WD / "ladder_problems.jsonl").open()}
        tok = AutoTokenizer.from_pretrained(RIVAL)
        model = AutoModelForCausalLM.from_pretrained(RIVAL, torch_dtype=torch.bfloat16,
                                                     device_map="cuda")
        for r in bad:
            user = GEN_SINGLE.format(problem=probs[r["pid"]]["problem"]) + GROUND
            torch.manual_seed(1700 + r["pid"])
            ans, closed = gen_think_raw(model, tok, WRK_SYS, user, 9000)
            if not closed:
                torch.manual_seed(2700 + r["pid"])
                ans, closed = gen_think_raw(model, tok, WRK_SYS, user, 13000)
            inj = False
            if closed and not EST.search(ans):
                torch.manual_seed(3700 + r["pid"])
                ans2, c2 = gen_think_raw(model, tok, WRK_SYS,
                                         user + "\n(Do not omit the final ESTIMATE line.)",
                                         9000)
                if c2 and EST.search(ans2):
                    ans = ans2
                else:
                    ans, inj = ans + " ESTIMATE: 50%", True
            r["answer"] = ans
            r["est_injected"] = inj
            r["leak"] = not closed
            r.pop("ver", None)
            r.pop("ver_flagged", None)
            print(f"[fix R L{r['level']} pid {r['pid']:02d}] "
                  f"{'closed' if closed else 'STILL-LEAKED'} ({len(ans.split())}w)",
                  flush=True)
        OUT.write_text("".join(json.dumps(x) + "\n" for x in rows))
        del model
        torch.cuda.empty_cache()
    print("PHASE FIX COMPLETE", flush=True)

    rows = [json.loads(l) for l in OUT.open()]
    if any("ver" not in r for r in rows):
        probs = {json.loads(l)["pid"]: json.loads(l)
                 for l in (WD / "ladder_problems.jsonl").open()}
        tok = AutoTokenizer.from_pretrained(BASE)
        model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                                     device_map="cuda")
        model = PeftModel.from_pretrained(model, str(WD / "adapters/ver_16_qwen"))
        for r in rows:
            if "ver" in r:
                continue
            user = VER_USER.format(problem=probs[r["pid"]]["problem"],
                                   answer=r["answer"])
            out = gen2(model, tok, VER_SYS, user, max_new=96)
            r["ver"] = out[:300]
            r["ver_flagged"] = out.upper().startswith("FLAGGED")
            print(f"[re-ver {r['arm']} L{r['level']} pid {r['pid']:02d}] "
                  f"{'FLAG' if r['ver_flagged'] else 'clean'}", flush=True)
        OUT.write_text("".join(json.dumps(x) + "\n" for x in rows))
    print("RUN17B FIX COMPLETE", flush=True)


if __name__ == "__main__":
    main()
