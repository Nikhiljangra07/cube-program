"""
run11_pod_gen.py — RUN 11 pod stage: Eval D revisions, 3 arms x 32 twins (RUNBOOK11).

Runs ON POD after training + base-thread gens. Builds revision inputs on-pod:
priors per arm = that arm's OWN base-problem threads (faceVD_11 from fresh c16 gen;
faceV_10 + keep100 from uploaded run-10 qC files), preferring threads with a
parseable estimate. Greedy decoding. Writes /workspace/div/out/evalD_raw.jsonl.

  LORA_BASE="Qwen/Qwen3-4B-Instruct-2507" python run11_pod_gen.py
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
PRIOR_FILES = {"faceVD_11": WD / "out/eval_faceVD_11_qc16_v5_threads.jsonl",
               "faceV_10": WD / "priors/eval_faceV_10_qC_v5_threads.jsonl",
               "keep100": WD / "priors/eval_anchor_10_qC_v5_threads.jsonl"}
PCT = re.compile(r"(\d{1,3})(?:\s*(?:-|–|to)\s*(\d{1,3}))?\s*%")
ESTLINE = re.compile(r"ESTIMATE:\s*(\d{1,3})\s*%", re.M)


def prior_est(t):
    m = ESTLINE.findall(t)
    if m:
        return float(m[-1])
    f = PCT.findall(t)
    if f:
        a, b = f[-1]
        return (int(a) + int(b)) / 2 if b else float(a)
    return None


def pick_prior(threads):
    scored = [(t, prior_est(t)) for t in threads]
    with_est = [x for x in scored if x[1] is not None]
    return with_est[0] if with_est else (threads[0], None)


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

    out_f = (WD / "out/evalD_raw.jsonl").open("w")
    done = 0
    for arm in ADAPTERS:
        priors_by_problem = {r["problem"]: r for r in
                             (json.loads(l) for l in PRIOR_FILES[arm].open())}
        model.set_adapter(arm)
        for tw in twins:
            base_problem = inv[tw["base_index"]]["problem"]
            pr = priors_by_problem.get(base_problem)
            if not pr or not pr.get("threads"):
                out_f.write(json.dumps({"arm": arm, "kind": tw["kind"],
                                        "base_index": tw["base_index"], "error": "no prior"}) + "\n")
                continue
            prior, old_est = pick_prior(pr["threads"])
            msgs = [{"role": "system", "content": WRK_SYS},
                    {"role": "user", "content": REVISE_USER.format(
                        problem=base_problem, prior=prior, update=tw["update"])}]
            ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt")
            ids = ids["input_ids"] if hasattr(ids, "keys") else ids
            with torch.no_grad():
                out = model.generate(ids.to("cuda"), max_new_tokens=384, do_sample=False,
                                     pad_token_id=tok.eos_token_id)
            text = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()
            out_f.write(json.dumps({"arm": arm, "kind": tw["kind"], "base_index": tw["base_index"],
                                    "old_est": old_est, "update": tw["update"],
                                    "revision": text}) + "\n")
            out_f.flush()
            done += 1
            if done % 12 == 0:
                print(f"  {done}/96", flush=True)
    out_f.close()
    print(f"EVALD GEN DONE: {done} revisions -> {WD/'out/evalD_raw.jsonl'}")


if __name__ == "__main__":
    main()
