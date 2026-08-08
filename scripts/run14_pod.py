"""
run14_pod.py — RUN 14 pod script (RUNBOOK14 frozen). Reuses run13b_pod's frozen
prompts (SEG/FUSE/SYS verbatim import — the loop is mimicked exactly).

  --phase relay    : segments + fusion attempt 1 (keep100) for the 160 training
                     problems -> out/transcript14.json
  --phase repair --round N : regen fusion for pids in feedback14_rN.json
  --phase evalgen  : fresh segments on the 24 EVAL problems + two fusion arms:
                     F14 (adapters/wrk_fusion_14_qwen) and A (keep100)
                     -> out/eval_transcript14.json

  LORA_BASE="Qwen/Qwen3-4B-Instruct-2507" python run14_pod.py --phase relay
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from run13b_pod import ADAPTERS, BASE, FUSE, SEG, SYS, gen, base_prompt, emit  # noqa: F401

WD = Path("/workspace/div")
F14 = WD / "adapters/wrk_fusion_14_qwen"


def load_model(extra_f14=False):
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                                 device_map="cuda")
    model = PeftModel.from_pretrained(model, str(ADAPTERS["F"]), adapter_name="F")
    for k in ("V", "G"):
        model.load_adapter(str(ADAPTERS[k]), adapter_name=k)
    if extra_f14:
        model.load_adapter(str(F14), adapter_name="F14")
    return model, tok


def segments_for(model, tok, pr):
    seg = {}
    for name, seat in (("audit", "V"), ("read", "F"), ("plan", "V"), ("motion", "V")):
        model.set_adapter(seat)
        fmt = dict(problem=pr["problem"], counterparty=pr["counterparty"],
                   update=pr["update"], **seg)
        seg[name], secs = gen(model, tok, SEG[name].format(**fmt))
        emit(stage="segment", seg=name, pid=pr["pid"], secs=round(secs, 1))
    if "ESTIMATE:" not in seg["motion"]:
        fmt = dict(problem=pr["problem"], counterparty=pr["counterparty"],
                   update=pr["update"], **seg)
        seg["motion"], _ = gen(model, tok, SEG["motion"].format(**fmt)
                               + "\n(Your previous attempt omitted the final ESTIMATE line.)")
    return seg


def phase_relay(problems):
    model, tok = load_model()
    runs = []
    t0 = time.time()
    for pr in problems:
        seg = segments_for(model, tok, pr)
        model.set_adapter("G")
        a, secs = gen(model, tok, base_prompt(pr, seg))
        emit(stage="fusion", arm="T1", pid=pr["pid"], attempt=1, secs=round(secs, 1))
        runs.append({"pid": pr["pid"], "arch": pr["arch"], **seg, "fusion_A": a})
        if pr["pid"] % 10 == 0:
            print(f"[{pr['pid']:03d}] done  {round((time.time()-t0)/60,1)}m", flush=True)
    (WD / "out").mkdir(exist_ok=True)
    (WD / "out/transcript14.json").write_text(json.dumps(
        {"base": BASE, "runs": runs}, indent=1))
    print("RUN14 RELAY COMPLETE")


def phase_repair(problems, rnd):
    fb = json.loads((WD / f"feedback14_r{rnd}.json").read_text())
    t = json.loads((WD / "out/transcript14.json").read_text())
    runs = {r["pid"]: r for r in t["runs"]}
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                                 device_map="cuda")
    model = PeftModel.from_pretrained(model, str(ADAPTERS["G"]), adapter_name="G")
    out = {}
    for pid_s, feedback in sorted(fb.items(), key=lambda x: int(x[0])):
        pid = int(pid_s)
        pr = next(p for p in problems if p["pid"] == pid)
        speech, secs = gen(model, tok, base_prompt(pr, runs[pid]) + "\n\n" + feedback)
        out[pid_s] = speech
        emit(stage="fusion", arm="T1", pid=pid, attempt=rnd, secs=round(secs, 1))
    (WD / f"out/attempts14_r{rnd}.json").write_text(json.dumps(out, indent=1))
    print(f"RUN14 REPAIR ROUND {rnd} COMPLETE ({len(out)} speeches)")


def phase_evalgen():
    eval_problems = [json.loads(l) for l in (WD / "staged_problems.jsonl").open()]
    assert len(eval_problems) == 24
    assert (F14 / "adapter_model.safetensors").exists(), "wrk_fusion_14_qwen missing"
    model, tok = load_model(extra_f14=True)
    runs = []
    for pr in eval_problems:
        seg = segments_for(model, tok, pr)
        bp = base_prompt(pr, seg)
        model.set_adapter("F14")
        f14, _ = gen(model, tok, bp)
        model.set_adapter("G")
        a, _ = gen(model, tok, bp)
        runs.append({"pid": pr["pid"], **seg, "fusion_F14": f14, "fusion_A": a})
        print(f"[eval {pr['pid']:02d}] done", flush=True)
    (WD / "out/eval_transcript14.json").write_text(json.dumps({"runs": runs}, indent=1))
    print("RUN14 EVALGEN COMPLETE")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["relay", "repair", "evalgen"])
    ap.add_argument("--round", type=int, default=2)
    args = ap.parse_args()
    if args.phase == "evalgen":
        phase_evalgen()
        return
    problems = [json.loads(l) for l in (WD / "train_problems.jsonl").open()]
    assert len(problems) == 160
    if args.phase == "relay":
        phase_relay(problems)
    else:
        phase_repair(problems, args.round)


if __name__ == "__main__":
    main()
