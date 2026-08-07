"""
run13b_pod.py — RUN 13B pod script (RUNBOOK13B frozen). Two phases, one pod.

  --phase relay   : full fresh dataset — segments (V/F/V/V) + fusion A (keep100)
                    + fusion C (Qwen3-14B, non-thinking) for all 24 problems.
                    Writes out/transcript13b.json. Emits out/pod_events.jsonl.
  --phase repair --round N : reads feedback_rN.json {pid: feedback_text},
                    regenerates the D' speech for ONLY those pids (keep100,
                    base fusion prompt + feedback appended, greedy).
                    Writes out/attempts_rN.json.

Keys never touch this machine — all judging happens on the driver side.

  LORA_BASE="Qwen/Qwen3-4B-Instruct-2507" python run13b_pod.py --phase relay
"""
from __future__ import annotations
import argparse, json, os, time
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE = os.environ.get("LORA_BASE", "Qwen/Qwen3-4B-Instruct-2507")
BIG = os.environ.get("RUN13_BIG", "Qwen/Qwen3-14B")
WD = Path("/workspace/div")
ADAPTERS = {"F": WD / "adapters/wrk_faceF_9b_qwen",
            "V": WD / "adapters/wrk_faceV_10_qwen",
            "G": WD / "adapters/wrk_keep100_qwen"}
SYS = "You write one precise, decisive, realistic reasoning thread pursuing a given strategic angle."

SEG = {
    "audit": ("PROBLEM: {problem}\n\nWrite 2-3 cold, analytical sentences that AUDIT this "
              "situation: what the actor actually holds (resources, people, authority, time "
              "— real numbers only if the problem supplies them) and the ONE variable "
              "genuinely in the actor's favor. Audit only — no plan yet."),
    "read": ("PROBLEM: {problem}\n\nAUDIT SO FAR: {audit}\n\nWrite 2-3 cold, analytical "
             "sentences that READ {counterparty}: the single most likely realistic reaction "
             "or external development one or two moves ahead, and the one observable signal "
             "that would say the read is wrong. Read only — no plan."),
    "plan": ("PROBLEM: {problem}\n\nAUDIT: {audit}\n\nREAD: {read}\n\nWrite 2-3 cold, "
             "analytical sentences that COMMIT to a lawful plan spending ONLY audited items "
             "(who/what/when), positioned for the read above, naming the ONE friction most "
             "likely to stall it and the pre-arranged answer. "
             "Final line, exactly: ESTIMATE: NN%"),
    "motion": ("PROBLEM: {problem}\n\nYOUR PREVIOUS PLAN: {plan}\n\nUPDATE: {update}\n\n"
               "The situation has changed as described in UPDATE. Revise in 2-3 sentences: "
               "what the update changes, the revised plan, and how the estimate responds "
               "and why. FACT DISCIPLINE: only the PROBLEM and the UPDATE have happened; "
               "every predicted reaction remains unconfirmed — never state one as an "
               "event. Final line, exactly: ESTIMATE: NN%"),
}

FUSE = ("PROBLEM: {problem}\n\nUPDATE (this HAS happened): {update}\n\n"
        "AUDIT: {audit}\n\nREAD (a PREDICTION of what {counterparty} may do — none of it "
        "has happened): {read}\n\nCURRENT PLAN (already revised for the UPDATE): {motion}\n\n"
        "Write the final answer as ONE speech of 90-160 words: the situation as it now "
        "stands, the committed plan, how the plan is positioned IF the predicted reaction "
        "comes, and why the estimate is what it is. FACT DISCIPLINE: only the PROBLEM and "
        "the UPDATE have happened; keep every element of the READ conditional. Every number "
        "must come from the texts above — never introduce a new one. Anything the UPDATE "
        "eliminated is gone — mention it only to note it is gone. End with the CURRENT "
        "PLAN's estimate unchanged, final line exactly: ESTIMATE: NN%")

EV = (WD / "out/pod_events.jsonl")


def emit(**kw):
    EV.parent.mkdir(exist_ok=True)
    with EV.open("a") as f:
        f.write(json.dumps(kw) + "\n")


def gen(model, tok, user, big=False, max_new=400):
    msgs = [{"role": "system", "content": SYS}, {"role": "user", "content": user}]
    kw = {"add_generation_prompt": True, "return_tensors": "pt"}
    if big:
        kw["enable_thinking"] = False
    ids = tok.apply_chat_template(msgs, **kw)
    ids = ids["input_ids"] if hasattr(ids, "keys") else ids
    t0 = time.time()
    with torch.no_grad():
        out = model.generate(ids.to("cuda"), max_new_tokens=max_new, do_sample=False,
                             pad_token_id=tok.eos_token_id)
    text = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()
    return text, time.time() - t0


def base_prompt(pr, seg):
    return FUSE.format(problem=pr["problem"], update=pr["update"], audit=seg["audit"],
                       read=seg["read"], motion=seg["motion"],
                       counterparty=pr["counterparty"])


def phase_relay(problems):
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                                 device_map="cuda")
    model = PeftModel.from_pretrained(model, str(ADAPTERS["F"]), adapter_name="F")
    for k in ("V", "G"):
        model.load_adapter(str(ADAPTERS[k]), adapter_name=k)
    runs = []
    for pr in problems:
        p, seg = pr["problem"], {}
        for name, seat in (("audit", "V"), ("read", "F"), ("plan", "V"), ("motion", "V")):
            model.set_adapter(seat)
            fmt = dict(problem=p, counterparty=pr["counterparty"], update=pr["update"], **seg)
            seg[name], secs = gen(model, tok, SEG[name].format(**fmt))
            emit(stage="segment", seg=name, pid=pr["pid"], secs=round(secs, 1),
                 words=len(seg[name].split()))
        if "ESTIMATE:" not in seg["motion"]:
            fmt = dict(problem=p, counterparty=pr["counterparty"], update=pr["update"], **seg)
            seg["motion"], _ = gen(model, tok, SEG["motion"].format(**fmt)
                                   + "\n(Your previous attempt omitted the final ESTIMATE line.)")
        model.set_adapter("G")
        a, secs = gen(model, tok, base_prompt(pr, seg))
        emit(stage="fusion", arm="A", pid=pr["pid"], attempt=1, secs=round(secs, 1),
             words=len(a.split()))
        runs.append({"pid": pr["pid"], "arch": pr["arch"], **seg, "fusion_A": a})
        print(f"[{pr['pid']:02d}] segments+A done", flush=True)

    del model
    torch.cuda.empty_cache()
    print("loading big spokesman:", BIG, flush=True)
    btok = AutoTokenizer.from_pretrained(BIG)
    big = AutoModelForCausalLM.from_pretrained(BIG, torch_dtype=torch.bfloat16,
                                               device_map="cuda")
    for pr, run in zip(problems, runs):
        run["fusion_C"], secs = gen(big, btok, base_prompt(pr, run), big=True)
        emit(stage="fusion", arm="C", pid=pr["pid"], attempt=1, secs=round(secs, 1),
             words=len(run["fusion_C"].split()))
        print(f"[{pr['pid']:02d}] C done", flush=True)
    (WD / "out").mkdir(exist_ok=True)
    (WD / "out/transcript13b.json").write_text(json.dumps(
        {"base": BASE, "big": BIG, "runs": runs}, indent=1))
    print("RUN13B RELAY COMPLETE")


def phase_repair(problems, rnd):
    fb = json.loads((WD / f"feedback_r{rnd}.json").read_text())
    t = json.loads((WD / "out/transcript13b.json").read_text())
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
        emit(stage="fusion", arm="Dp", pid=pid, attempt=rnd, secs=round(secs, 1),
             words=len(speech.split()))
        print(f"[{pid:02d}] repair r{rnd} done", flush=True)
    (WD / f"out/attempts_r{rnd}.json").write_text(json.dumps(out, indent=1))
    print(f"RUN13B REPAIR ROUND {rnd} COMPLETE ({len(out)} speeches)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["relay", "repair"])
    ap.add_argument("--round", type=int, default=2)
    args = ap.parse_args()
    problems = [json.loads(l) for l in (WD / "staged_problems.jsonl").open()]
    assert len(problems) == 24
    if args.phase == "relay":
        phase_relay(problems)
    else:
        phase_repair(problems, args.round)


if __name__ == "__main__":
    main()
