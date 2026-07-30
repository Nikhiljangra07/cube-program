"""
run11_pod_gen2.py — EVAL D v2 (protocol amendment, thresholds unchanged): priors
with tagged estimates. For each arm and each of the 16 base problems, generate ONE
base plan with the tagged-line instruction (greedy), then the 32 revisions per arm
against that plan. Fixes the v1 coverage gap (static-prompt priors carried no
estimate -> 12-16/32 pairs unscorable for every arm). Bars, twins, and the revise
instruction are byte-identical to v1.

  LORA_BASE="Qwen/Qwen3-4B-Instruct-2507" python run11_pod_gen2.py
Writes /workspace/div/out/evalD2_raw.jsonl (+ evalD2_priors.jsonl)
"""
from __future__ import annotations
import json, os, re
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from run11_common import WRK_SYS, REVISE_USER

BASE = os.environ.get("LORA_BASE", "Qwen/Qwen3-4B-Instruct-2507")
WD = Path("/workspace/div")
ADAPTERS = {"faceVD_11": WD / "adapters/wrk_faceVD_11_qwen",
            "faceV_10": WD / "adapters/wrk_faceV_10_qwen",
            "keep100": WD / "adapters/wrk_keep100_qwen"}
ESTLINE = re.compile(r"ESTIMATE:\s*(\d{1,3})(?:\s*-\s*(\d{1,3}))?\s*%", re.M)

PLAN_USER = ("PROBLEM: {problem}\n\nWrite a single reasoning thread (4-6 sentences, cold and "
             "analytical) that plans this with ONLY what the actor actually holds: audit the "
             "concrete resources, people, seat, and time; name the ONE variable in the actor's "
             "favor; commit to a lawful plan spending only audited items (who/what/when); name "
             "the ONE most likely friction and its pre-arranged answer. "
             "Final line, exactly: ESTIMATE: NN%")


def est(t):
    m = ESTLINE.findall(t)
    if not m:
        return None
    a, b = m[-1]
    return (int(a) + int(b)) / 2 if b else float(a)


def gen(model, tok, msgs):
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt")
    ids = ids["input_ids"] if hasattr(ids, "keys") else ids
    with torch.no_grad():
        out = model.generate(ids.to("cuda"), max_new_tokens=384, do_sample=False,
                             pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()


def main():
    inv = [json.loads(l) for l in (WD / "bench_data_c/eval_problems.jsonl").open()]
    boosts = [json.loads(l) for l in (WD / "twins/boost_twins.jsonl").open()]
    nerfs = [json.loads(l) for l in (WD / "twins/nerf_twins.jsonl").open()]
    twins = ([{"kind": "boost", **t, "update": t["boost"]} for t in boosts] +
             [{"kind": "nerf", **t, "update": t["nerf"]} for t in nerfs])

    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map="cuda")
    first = True
    for arm, path in ADAPTERS.items():
        if first:
            model = PeftModel.from_pretrained(model, str(path), adapter_name=arm)
            first = False
        else:
            model.load_adapter(str(path), adapter_name=arm)

    priors_f = (WD / "out/evalD2_priors.jsonl").open("w")
    out_f = (WD / "out/evalD2_raw.jsonl").open("w")
    done = 0
    for arm in ADAPTERS:
        model.set_adapter(arm)
        priors = {}
        for i in range(16):
            problem = inv[i]["problem"]
            # up to 3 attempts to get a tagged prior (greedy is deterministic, so
            # retry with a nudge suffix if the first lacks the line)
            plan = gen(model, tok, [{"role": "system", "content": WRK_SYS},
                                    {"role": "user", "content": PLAN_USER.format(problem=problem)}])
            if est(plan) is None:
                plan = gen(model, tok, [{"role": "system", "content": WRK_SYS},
                                        {"role": "user", "content": PLAN_USER.format(problem=problem)
                                         + "\n(Do not omit the final ESTIMATE line.)"}])
            priors[i] = plan
            priors_f.write(json.dumps({"arm": arm, "base_index": i, "plan": plan,
                                       "est": est(plan)}) + "\n")
            priors_f.flush()
        for tw in twins:
            i = tw["base_index"]
            plan = priors[i]
            text = gen(model, tok, [{"role": "system", "content": WRK_SYS},
                                    {"role": "user", "content": REVISE_USER.format(
                                        problem=inv[i]["problem"], prior=plan, update=tw["update"])}])
            out_f.write(json.dumps({"arm": arm, "kind": tw["kind"], "base_index": i,
                                    "old_est": est(plan), "update": tw["update"],
                                    "revision": text}) + "\n")
            out_f.flush()
            done += 1
            if done % 16 == 0:
                print(f"  {done}/96", flush=True)
    out_f.close(); priors_f.close()
    print(f"EVALD2 GEN DONE: {done} revisions -> {WD/'out/evalD2_raw.jsonl'}")


if __name__ == "__main__":
    main()
