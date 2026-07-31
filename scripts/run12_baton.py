"""
run12_baton.py — RUN 12 stage 1: the single baton pass (RUNBOOK12 frozen).

The smallest live cube, per the dispatcher doc (§9.3): one problem per type,
full per-segment relay through the coach on one card.

Relay per problem (segments assigned by the coach, adapters hot-swapped):
  seg1 AUDIT   (viability seat)   — what the actor holds, favorable variable
  seg2 READ    (foresight seat)   — counterparty/external reaction 1-2 moves out
  seg3 PLAN    (viability seat)   — plan spending only audited items + friction
  seg4 MOTION  (viability seat)   — coach injects the UPDATE, anchored re-derive
  seg5 FUSION  (generalist seat)  — coach presents all segments, elicits ONE
                                    synthesis ending `ESTIMATE: NN%`
  (fusion runner = keep100 by frozen choice: neutral, closest to base; run-11
   showed the generalist derives correctly when everything is in view)

Also measures: hot-swap identity (greedy outputs byte-identical to fresh-load
reference on segment 1) + swap latency (bar: median < 50ms).

  LORA_BASE="Qwen/Qwen3-4B-Instruct-2507" python run12_baton.py
Writes /workspace/div/out/baton_transcript.json
"""
from __future__ import annotations
import json, os, time
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE = os.environ.get("LORA_BASE", "Qwen/Qwen3-4B-Instruct-2507")
WD = Path("/workspace/div")
ADAPTERS = {"F": WD / "adapters/wrk_faceF_9b_qwen",
            "V": WD / "adapters/wrk_faceV_10_qwen",
            "G": WD / "adapters/wrk_keep100_qwen"}
SYS = "You write one precise, decisive, realistic reasoning thread pursuing a given strategic angle."

SEG = {
    "audit": ("PROBLEM: {problem}\n\nWrite 2-3 cold, analytical sentences that AUDIT this "
              "situation: what the actor actually holds (resources, people, seat/authority, "
              "time — real numbers only if the problem supplies them) and the ONE variable "
              "genuinely in the actor's favor. Audit only — no plan yet."),
    "read": ("PROBLEM: {problem}\n\nAUDIT SO FAR: {audit}\n\nWrite 2-3 cold, analytical "
             "sentences that READ the other parties: the single most likely realistic "
             "reaction or external development one or two moves ahead, and the one "
             "observable signal that would say the read is wrong. Read only — no plan."),
    "plan": ("PROBLEM: {problem}\n\nAUDIT: {audit}\n\nREAD: {read}\n\nWrite 2-3 cold, "
             "analytical sentences that COMMIT to a lawful plan spending ONLY audited "
             "items (who/what/when), positioned for the read above, naming the ONE "
             "friction most likely to stall it and the pre-arranged answer. "
             "Final line, exactly: ESTIMATE: NN%"),
    "motion": ("PROBLEM: {problem}\n\nYOUR PREVIOUS PLAN: {plan}\n\nUPDATE: {update}\n\n"
               "The situation has changed as described in UPDATE. Revise in 2-3 sentences: "
               "what the update changes, the revised plan, and how the estimate responds "
               "and why. Final line, exactly: ESTIMATE: NN%"),
    "fusion": ("PROBLEM: {problem}\n\nTHE AUDIT (what is held): {audit}\n\nTHE READ (what "
               "they will do): {read}\n\nTHE CURRENT PLAN (after one update): {motion}\n\n"
               "Write the FINAL ANSWER as 3-4 cold, decisive sentences that fuse all three: "
               "the committed move, why it survives the read, what it spends, and close "
               "with the success percentage derived from the whole chain — name what earns "
               "it and what caps it. Final line, exactly: ESTIMATE: NN%"),
}

PROBLEMS = [json.loads(l) for l in (WD / "baton_problems.jsonl").open()]


def gen(model, tok, user):
    ids = tok.apply_chat_template([{"role": "system", "content": SYS},
                                   {"role": "user", "content": user}],
                                  add_generation_prompt=True, return_tensors="pt")
    ids = ids["input_ids"] if hasattr(ids, "keys") else ids
    with torch.no_grad():
        out = model.generate(ids.to("cuda"), max_new_tokens=320, do_sample=False,
                             pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()


def main():
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map="cuda")
    model = PeftModel.from_pretrained(model, str(ADAPTERS["F"]), adapter_name="F")
    for k in ("V", "G"):
        model.load_adapter(str(ADAPTERS[k]), adapter_name=k)

    # --- swap latency ---
    lat = []
    for _ in range(20):
        for k in ("F", "V", "G"):
            t0 = time.perf_counter()
            model.set_adapter(k)
            lat.append((time.perf_counter() - t0) * 1000)
    lat.sort()
    print(f"swap latency ms: median {lat[len(lat)//2]:.2f} max {lat[-1]:.2f} (bar < 50)")

    transcript = {"swap_median_ms": lat[len(lat)//2]}
    runs = []
    for pr in PROBLEMS:
        p = pr["problem"]
        model.set_adapter("V"); audit = gen(model, tok, SEG["audit"].format(problem=p))
        model.set_adapter("F"); read = gen(model, tok, SEG["read"].format(problem=p, audit=audit))
        model.set_adapter("V"); plan = gen(model, tok, SEG["plan"].format(problem=p, audit=audit, read=read))
        model.set_adapter("V"); motion = gen(model, tok, SEG["motion"].format(problem=p, plan=plan, update=pr["update"]))
        model.set_adapter("G"); fusion = gen(model, tok, SEG["fusion"].format(problem=p, audit=audit, read=read, motion=motion))
        runs.append({"type": pr["type"], "problem": p, "update": pr["update"],
                     "audit": audit, "read": read, "plan": plan, "motion": motion,
                     "fusion": fusion})
        print(f"[{pr['type']}] relay complete — fusion tail: ...{fusion[-120:]}", flush=True)

    # --- hot-swap identity: seg1 output vs fresh single-adapter load ---
    del model
    torch.cuda.empty_cache()
    m2 = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map="cuda")
    m2 = PeftModel.from_pretrained(m2, str(ADAPTERS["V"]), adapter_name="V")
    fresh = gen(m2, tok, SEG["audit"].format(problem=PROBLEMS[0]["problem"]))
    ident = fresh == runs[0]["audit"]
    print(f"hot-swap identity vs fresh load: {'IDENTICAL' if ident else 'MISMATCH'}")
    transcript.update({"identity_ok": ident, "runs": runs})
    (WD / "out/baton_transcript.json").write_text(json.dumps(transcript, indent=1))
    print("BATON PASS COMPLETE")


if __name__ == "__main__":
    main()
