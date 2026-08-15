"""
run17b_pod.py — RUN 17B pod job (RUNBOOK17B): the marking test + the rival.
One detached process, resume-safe, no API keys ever on this machine.

  phase 1 (arm M): keep100 + GROUND discipline appended to GEN_SINGLE
                   (greedy, max_new 600 — marking costs tokens)
  phase 2 (arm R): Qwen3-4B-Thinking-2507, same system+user prompt, vendor
                   decoding (temp .6 / top_p .95 / top_k 20, seed 1700+pid);
                   thinking stripped via special-token decode + </think> split
  phase 3        : ver_16_qwen GROUNDED/FLAGGED on all 80 answers
                   (run-16 prompt verbatim)

  (setsid nohup python run17b_pod.py > out/ladder17b.log 2>&1 < /dev/null &)
Writes /workspace/div/out/ladder17b_out.jsonl  rows {arm,pid,level,answer,...}
"""
from __future__ import annotations
import json
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from run13b_pod import BASE
from run15_match_pod import EST, GEN_SINGLE, WRK_SYS, gen2
from run17_pod import VER_SYS, VER_USER

WD = Path("/workspace/div")
OUT = WD / "out/ladder17b_out.jsonl"
RIVAL = "Qwen/Qwen3-4B-Thinking-2507"

GROUND = (
    "\n\nGROUNDING DISCIPLINE (mandatory): every specific in your answer — every "
    "number, date, time, dollar amount, name, and event — must be one of: "
    "(a) QUOTED: it appears in the problem text; "
    "(b) DERIVED: computed from problem facts, with the basis shown inline, "
    "e.g. '15 days (July 8 to July 23)'; "
    "(c) PROPOSED: explicitly marked as your chosen parameter, e.g. 'open at "
    "$45,000 — my proposal, adjustable'. "
    "Never state a specific absent from the problem as settled fact. If the plan "
    "needs a specific the problem does not supply, propose it and mark it."
)


def jsonl_rows(path):
    return [json.loads(l) for l in path.open()] if path.exists() else []


def gen_think(model, tok, system, user, max_new=4096):
    """Vendor-decoding generation for the thinking rival; returns final text
    only. Decode WITH special tokens, split on the last </think> (the gpt-oss
    harmony lesson: skip_special_tokens would merge thinking into the answer)."""
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt")
    ids = ids["input_ids"] if hasattr(ids, "keys") else ids
    with torch.no_grad():
        out = model.generate(ids.to("cuda"), max_new_tokens=max_new, do_sample=True,
                             temperature=0.6, top_p=0.95, top_k=20,
                             pad_token_id=tok.eos_token_id)
    raw = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=False)
    fin = raw.split("</think>")[-1]
    for t in {tok.eos_token, "<|im_end|>", "<|endoftext|>", tok.pad_token}:
        if t:
            fin = fin.replace(t, "")
    return fin.strip()


def rival_with_estimate(model, tok, user, text, pid):
    """Run-13b estimate law, rival edition: one nudged retry, then inject+flag."""
    if EST.search(text):
        return text, False
    torch.manual_seed(3400 + pid)
    text2 = gen_think(model, tok, WRK_SYS,
                      user + "\n(Do not omit the final ESTIMATE line.)")
    if EST.search(text2):
        return text2, False
    return text2 + " ESTIMATE: 50%", True


def main():
    (WD / "out").mkdir(exist_ok=True)
    probs = [json.loads(l) for l in (WD / "ladder_problems.jsonl").open()]
    assert len(probs) == 40
    done = {(r["arm"], r["pid"]) for r in jsonl_rows(OUT)}

    # ---- phase 1: arm M — keep100 + GROUND ----
    if any(("M", p["pid"]) not in done for p in probs):
        tok = AutoTokenizer.from_pretrained(BASE)
        model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                                     device_map="cuda")
        model = PeftModel.from_pretrained(model, str(WD / "adapters/wrk_keep100_qwen"),
                                          adapter_name="G")
        f = OUT.open("a")
        for p in probs:
            if ("M", p["pid"]) in done:
                continue
            user = GEN_SINGLE.format(problem=p["problem"]) + GROUND
            ans = gen2(model, tok, WRK_SYS, user, max_new=600)
            inj = False
            if not EST.search(ans):
                ans2 = gen2(model, tok, WRK_SYS,
                            user + "\n(Do not omit the final ESTIMATE line.)",
                            max_new=600)
                ans, inj = (ans2, False) if EST.search(ans2) else (ans2 + " ESTIMATE: 50%", True)
            f.write(json.dumps({"arm": "M", "pid": p["pid"], "level": p["level"],
                                "answer": ans, "est_injected": inj}) + "\n")
            f.flush()
            print(f"[M L{p['level']} pid {p['pid']:02d}] done", flush=True)
        f.close()
        del model
        torch.cuda.empty_cache()
    print("PHASE M COMPLETE", flush=True)

    # ---- phase 2: arm R — the thinking rival ----
    done = {(r["arm"], r["pid"]) for r in jsonl_rows(OUT)}
    if any(("R", p["pid"]) not in done for p in probs):
        tok = AutoTokenizer.from_pretrained(RIVAL)
        model = AutoModelForCausalLM.from_pretrained(RIVAL, torch_dtype=torch.bfloat16,
                                                     device_map="cuda")
        f = OUT.open("a")
        for p in probs:
            if ("R", p["pid"]) in done:
                continue
            user = GEN_SINGLE.format(problem=p["problem"]) + GROUND
            torch.manual_seed(1700 + p["pid"])
            ans = gen_think(model, tok, WRK_SYS, user)
            ans, inj = rival_with_estimate(model, tok, user, ans, p["pid"])
            f.write(json.dumps({"arm": "R", "pid": p["pid"], "level": p["level"],
                                "answer": ans, "est_injected": inj}) + "\n")
            f.flush()
            print(f"[R L{p['level']} pid {p['pid']:02d}] done ({len(ans.split())}w)",
                  flush=True)
        f.close()
        del model
        torch.cuda.empty_cache()
    print("PHASE R COMPLETE", flush=True)

    # ---- phase 3: verifier on all 80 ----
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
            print(f"[ver {r['arm']} L{r['level']} pid {r['pid']:02d}] "
                  f"{'FLAG' if r['ver_flagged'] else 'clean'}", flush=True)
        OUT.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print("PHASE VERIFY COMPLETE", flush=True)
    print("RUN17B POD COMPLETE", flush=True)


if __name__ == "__main__":
    main()
