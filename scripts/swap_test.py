"""
swap_test.py — POD-SIDE mechanics test: does peft multi-adapter hot-swapping garble
granite-4.0-micro, and how fast is a swap?

The landmine on record (dav_eval_v5.py): peft 0.19.1 multi-adapter switching garbles
granite — every eval loads a separate model instance per seat as the workaround. The
Rubik's-cube dispatcher needs in-process swapping, so this test decides build-vs-blocked.

Protocol (greedy, fixed prompt, so outputs are deterministic per model state):
1. REFERENCE: load base+faceF alone -> generate; load base+faceG alone -> generate.
2. MULTI: one base, load_adapter faceF + faceG, set_adapter to switch F->G->F,
   generating after each switch.
3. VERDICT per adapter: multi-adapter output == its single-load reference (exact match)?
   Any mismatch = garbling reproduced. Swap latency = median set_adapter wall time.
"""
from __future__ import annotations
import json, os, statistics, time

import torch
import peft
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

BASE = os.environ.get("LORA_BASE", "ibm-granite/granite-4.0-micro")
A1, A2 = "adapters/wrk_faceF", "adapters/wrk_faceG"
PROMPT = ("PROBLEM: A regional bakery chain must decide whether to expand into a rival "
          "city now or consolidate its home market for a year.\nGive your recommendation "
          "in two sentences.")


def gen(model, tok):
    msgs = [{"role": "user", "content": PROMPT}]
    enc = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt")
    ids = (enc if torch.is_tensor(enc) else enc["input_ids"]).to("cuda")
    with torch.no_grad():
        out = model.generate(ids, max_new_tokens=120, do_sample=False,
                             pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()


def fresh(adapter, tok):
    m = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                             device_map="cuda")
    m = PeftModel.from_pretrained(m, adapter)
    m.eval()
    text = gen(m, tok)
    del m
    torch.cuda.empty_cache()
    return text

def main():
    print(f"peft {peft.__version__}")
    tok = AutoTokenizer.from_pretrained(BASE)

    ref = {}
    for name, path in (("faceF", A1), ("faceG", A2)):
        ref[name] = fresh(path, tok)
        print(f"REF {name}: {ref[name][:100]!r}")

    m = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                             device_map="cuda")
    m = PeftModel.from_pretrained(m, A1, adapter_name="faceF")
    m.load_adapter(A2, adapter_name="faceG")
    m.eval()

    seq = ["faceF", "faceG", "faceF", "faceG", "faceF"]
    lat, results = [], []
    for name in seq:
        t0 = time.perf_counter()
        m.set_adapter(name)
        lat.append(time.perf_counter() - t0)
        text = gen(m, tok)
        results.append({"adapter": name, "match_ref": text == ref[name],
                        "text_head": text[:100]})
        print(f"SWAP->{name}: match={text == ref[name]} | {text[:80]!r}")

    verdict = {
        "peft_version": peft.__version__,
        "all_match": all(r["match_ref"] for r in results),
        "mismatches": [r["adapter"] for r in results if not r["match_ref"]],
        "swap_latency_ms_median": round(statistics.median(lat) * 1000, 2),
        "swap_latency_ms_max": round(max(lat) * 1000, 2),
        "results": results,
    }
    print("\nVERDICT " + json.dumps(verdict, indent=2))
    with open("out/swap_verdict.json", "w") as f:
        json.dump(verdict, f, indent=2)


if __name__ == "__main__":
    main()
