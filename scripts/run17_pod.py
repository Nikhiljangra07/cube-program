"""
run17_pod.py — RUN 17 pod job (RUNBOOK17): capacity-ladder generation + verifier
inference, one detached process, resume-safe. No API keys ever on this machine.

  phase 1: keep100 (generalist) answers each of the 40 ladder problems with the
           match's GEN_SINGLE prompt verbatim (greedy, max_new 500 — identical
           decoding at every level; load is the only variable)
  phase 2: ver_16_qwen (the archived v1 verifier, best clean-recall variant)
           renders GROUNDED/FLAGGED on every answer with the run-16 prompt
           verbatim

  (setsid nohup python run17_pod.py > out/ladder17.log 2>&1 < /dev/null &)
Writes /workspace/div/out/ladder17_out.jsonl
"""
from __future__ import annotations
import json
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from run13b_pod import BASE
from run15_match_pod import GEN_SINGLE, gen2, with_estimate, WRK_SYS

WD = Path("/workspace/div")
OUT = WD / "out/ladder17_out.jsonl"

VER_SYS = ("You are a strict grounding auditor. Given a PROBLEM and a RESPONSE, "
           "decide whether every claim in the RESPONSE is grounded in the PROBLEM text.")
VER_USER = ("PROBLEM: {problem}\n\nRESPONSE: {answer}\n\n"
            "If every number, actor, event, and commitment in the RESPONSE is grounded "
            "in the PROBLEM (or is an explicitly conditional prediction), output "
            "exactly: GROUNDED. Otherwise output: FLAGGED: <one sentence naming the "
            "single clearest ungrounded claim>.")


def jsonl_rows(path):
    return [json.loads(l) for l in path.open()] if path.exists() else []


def main():
    (WD / "out").mkdir(exist_ok=True)
    probs = [json.loads(l) for l in (WD / "ladder_problems.jsonl").open()]
    assert len(probs) == 40
    done = {r["pid"]: r for r in jsonl_rows(OUT)}

    # ---- phase 1: generalist answers ----
    if any(p["pid"] not in done for p in probs):
        tok = AutoTokenizer.from_pretrained(BASE)
        model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                                     device_map="cuda")
        model = PeftModel.from_pretrained(model, str(WD / "adapters/wrk_keep100_qwen"),
                                          adapter_name="G")
        f = OUT.open("a")
        for p in probs:
            if p["pid"] in done:
                continue
            user = GEN_SINGLE.format(problem=p["problem"])
            ans = gen2(model, tok, WRK_SYS, user, max_new=500)
            ans, inj = with_estimate(model, tok, user, ans)
            row = {"pid": p["pid"], "level": p["level"], "answer": ans,
                   "est_injected": inj}
            f.write(json.dumps(row) + "\n")
            f.flush()
            done[p["pid"]] = row
            print(f"[gen L{p['level']} pid {p['pid']:02d}] done", flush=True)
        f.close()
        del model
        torch.cuda.empty_cache()
    print("PHASE GEN COMPLETE", flush=True)

    # ---- phase 2: verifier verdicts ----
    rows = jsonl_rows(OUT)
    if any("ver" not in r for r in rows):
        tok = AutoTokenizer.from_pretrained(BASE)
        model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                                     device_map="cuda")
        model = PeftModel.from_pretrained(model, str(WD / "adapters/ver_16_qwen"))
        probs_by = {p["pid"]: p for p in probs}
        for r in rows:
            if "ver" in r:
                continue
            user = VER_USER.format(problem=probs_by[r["pid"]]["problem"],
                                   answer=r["answer"])
            out = gen2(model, tok, VER_SYS, user, max_new=96)
            r["ver"] = out[:300]
            r["ver_flagged"] = out.upper().startswith("FLAGGED")
            print(f"[ver L{r['level']} pid {r['pid']:02d}] "
                  f"{'FLAG' if r['ver_flagged'] else 'clean'}", flush=True)
        OUT.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print("PHASE VERIFY COMPLETE", flush=True)
    print("RUN17 LADDER POD COMPLETE", flush=True)


if __name__ == "__main__":
    main()
