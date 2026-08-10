"""
run15_pod.py — RUN 15 stage-1 pod script (RUNBOOK15 frozen).

  --phase smoke    : fresh segments + BASELINE free fusion (keep100) for the
                     24 frozen eval problems -> out/smoke15_transcript.json
  --phase motionfix --round N : regenerate MOTION only, for pids listed in
                     motionfix15_rN.json (V seat, feedback appended)

  LORA_BASE="Qwen/Qwen3-4B-Instruct-2507" python run15_pod.py --phase smoke
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from run13b_pod import ADAPTERS, BASE, SEG, base_prompt, emit, gen
from run14_pod import load_model, segments_for

WD = Path("/workspace/div")


def phase_smoke():
    problems = [json.loads(l) for l in (WD / "staged_problems.jsonl").open()]
    assert len(problems) == 24
    model, tok = load_model()
    runs = []
    for pr in problems:
        seg = segments_for(model, tok, pr)
        model.set_adapter("G")
        base, _ = gen(model, tok, base_prompt(pr, seg))
        runs.append({"pid": pr["pid"], **seg, "fusion_base": base})
        print(f"[{pr['pid']:02d}] smoke relay done", flush=True)
    (WD / "out").mkdir(exist_ok=True)
    (WD / "out/smoke15_transcript.json").write_text(json.dumps({"runs": runs}, indent=1))
    print("RUN15 SMOKE RELAY COMPLETE")


def phase_motionfix(rnd):
    problems = {json.loads(l)["pid"]: json.loads(l)
                for l in (WD / "staged_problems.jsonl").open()}
    fb = json.loads((WD / f"motionfix15_r{rnd}.json").read_text())
    t = json.loads((WD / "out/smoke15_transcript.json").read_text())
    runs = {r["pid"]: r for r in t["runs"]}
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                                 device_map="cuda")
    model = PeftModel.from_pretrained(model, str(ADAPTERS["V"]), adapter_name="V")
    out = {}
    for pid_s, feedback in sorted(fb.items(), key=lambda x: int(x[0])):
        pid = int(pid_s)
        pr, run = problems[pid], runs[pid]
        prompt = SEG["motion"].format(problem=pr["problem"], plan=run["plan"],
                                      update=pr["update"]) + "\n\n" + feedback
        out[pid_s], _ = gen(model, tok, prompt)
        print(f"[{pid:02d}] motionfix r{rnd} done", flush=True)
    (WD / f"out/motionfix15_r{rnd}_out.json").write_text(json.dumps(out, indent=1))
    print(f"RUN15 MOTIONFIX ROUND {rnd} COMPLETE ({len(out)})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["smoke", "motionfix"])
    ap.add_argument("--round", type=int, default=1)
    args = ap.parse_args()
    if args.phase == "smoke":
        phase_smoke()
    else:
        phase_motionfix(args.round)


if __name__ == "__main__":
    main()
