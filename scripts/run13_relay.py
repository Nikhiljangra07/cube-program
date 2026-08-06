"""
run13_relay.py — RUN 13 pod script: fusion wall test, 4 spokesman arms (RUNBOOK13).

Per staged problem (24, md5-checked upstream): one greedy relay on the trained
seats — audit(V) -> read(F) -> plan(V) -> motion(V, absorbs UPDATE) — segments
SHARED across arms. Then four fusion arms:
  A  baseline   free fusion on keep100 (fact-discipline prompt)
  B  few-shot   A's prompt + 2 hand-written exemplar speeches
  D  detect+fix A's speech -> checker -> deterministic feedback retry (<=3 total)
  C  bigger     Qwen3-14B, no adapter, non-thinking chat mode, A's prompt

  LORA_BASE="Qwen/Qwen3-4B-Instruct-2507" python run13_relay.py
Writes /workspace/div/out/run13_transcript.json
"""
from __future__ import annotations
import json, os, time
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from run13_checker import check_speech, feedback

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

# two hand-written exemplar speeches (arm B) — written by us, not by any model
EXEMPLARS = """Here are two examples of the required speech discipline.

EXAMPLE 1 — inputs (abbreviated): budget $31,000 revised down from $35,000 by the update;
operator Dana, 10 hours weekly; counterparty Whitfield observed delaying twice; the Osprey
add-on was eliminated by the update; prediction: Whitfield may demand a shorter window;
current plan: proceed without the add-on, use Dana's 10 hours for verification. ESTIMATE: 60%
SPEECH: The update settles the terrain: the Osprey add-on is gone, and the working budget
is $31,000, not $35,000. The plan proceeds on what remains — Dana's 10 weekly hours go to
verification, and the commitment stays inside the $31,000 now confirmed. If Whitfield
presses for a shorter window, as the read anticipates, the verification work is
front-loaded so the deadline still holds; nothing in the plan depends on his cooperation.
The estimate reflects a plan spending only confirmed resources against one unresolved
friction — Whitfield's timing — which is prepared for but not controlled. ESTIMATE: 60%

EXAMPLE 2 — inputs (abbreviated): reserve $22,500; deadline September 12; counterparty
Iwu observed courting a second buyer; the Kestrel hold was withdrawn by the update;
prediction: Iwu could invite a rival bid to raise price; current plan: set a final offer
by September 5 and hold the reserve. ESTIMATE: 45%
SPEECH: With the Kestrel hold withdrawn, there is no protected window — the decision now
rests on the $22,500 reserve and the September 12 deadline alone. The plan commits to a
final offer by September 5, keeping the reserve intact rather than chasing terms that no
longer exist. Should Iwu invite a rival bid, as the read suggests he might, the early
final offer forces his hand before a bidding contest can form; if he instead goes quiet,
the deadline discipline loses nothing. The estimate stays where the revised plan put it:
a workable position, but one where the counterparty holds the pacing. ESTIMATE: 45%

Now produce the speech for the actual inputs below, with the same discipline.

"""


def gen(model, tok, user, big=False, max_new=400):
    msgs = [{"role": "system", "content": SYS}, {"role": "user", "content": user}]
    kw = {"add_generation_prompt": True, "return_tensors": "pt"}
    if big:
        kw["enable_thinking"] = False
    ids = tok.apply_chat_template(msgs, **kw)
    ids = ids["input_ids"] if hasattr(ids, "keys") else ids
    with torch.no_grad():
        out = model.generate(ids.to("cuda"), max_new_tokens=max_new, do_sample=False,
                             pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()


def upstream_of(pr, s):
    return [pr["problem"], pr["update"], s["audit"], s["read"], s["plan"], s["motion"]]


def main():
    problems = [json.loads(l) for l in (WD / "staged_problems.jsonl").open()]
    assert len(problems) == 24, f"expected 24 staged problems, got {len(problems)}"
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                                 device_map="cuda")
    model = PeftModel.from_pretrained(model, str(ADAPTERS["F"]), adapter_name="F")
    for k in ("V", "G"):
        model.load_adapter(str(ADAPTERS[k]), adapter_name=k)

    runs = []
    t0 = time.time()
    for pr in problems:
        p = pr["problem"]
        model.set_adapter("V")
        audit = gen(model, tok, SEG["audit"].format(problem=p))
        model.set_adapter("F")
        read = gen(model, tok, SEG["read"].format(problem=p, audit=audit,
                                                  counterparty=pr["counterparty"]))
        model.set_adapter("V")
        plan = gen(model, tok, SEG["plan"].format(problem=p, audit=audit, read=read))
        motion = gen(model, tok, SEG["motion"].format(problem=p, plan=plan,
                                                      update=pr["update"]))
        if "ESTIMATE:" not in motion:  # one nudge, then proceed (checker will flag)
            motion = gen(model, tok, SEG["motion"].format(problem=p, plan=plan,
                                                          update=pr["update"])
                         + "\n(Your previous attempt omitted the final ESTIMATE line.)")
        seg = {"audit": audit, "read": read, "plan": plan, "motion": motion}
        base_prompt = FUSE.format(problem=p, update=pr["update"], audit=audit, read=read,
                                  motion=motion, counterparty=pr["counterparty"])
        model.set_adapter("G")
        a = gen(model, tok, base_prompt)
        b = gen(model, tok, EXEMPLARS + base_prompt)
        # arm D: detect-and-repair from A, deterministic feedback, <=3 attempts total
        d_attempts, d_speech = [a], a
        for _ in range(2):
            r = check_speech(d_speech, upstream_of(pr, seg), pr, motion)
            if not r["fidelity_flags"]:
                break
            d_speech = gen(model, tok, base_prompt + "\n\n" + feedback(r["fidelity_flags"]))
            d_attempts.append(d_speech)
        runs.append({"pid": pr["pid"], "arch": pr["arch"], **seg,
                     "fusion_A": a, "fusion_B": b,
                     "fusion_D": d_speech, "D_attempts": len(d_attempts)})
        print(f"[{pr['pid']:02d}] relay+A/B/D done  {time.time()-t0:.0f}s "
              f"(D attempts {len(d_attempts)})", flush=True)

    del model
    torch.cuda.empty_cache()
    print("loading big spokesman:", BIG, flush=True)
    btok = AutoTokenizer.from_pretrained(BIG)
    big = AutoModelForCausalLM.from_pretrained(BIG, torch_dtype=torch.bfloat16,
                                               device_map="cuda")
    for pr, run in zip(problems, runs):
        base_prompt = FUSE.format(problem=pr["problem"], update=pr["update"],
                                  audit=run["audit"], read=run["read"],
                                  motion=run["motion"], counterparty=pr["counterparty"])
        run["fusion_C"] = gen(big, btok, base_prompt, big=True)
        print(f"[{pr['pid']:02d}] C done", flush=True)

    (WD / "out").mkdir(exist_ok=True)
    (WD / "out/run13_transcript.json").write_text(json.dumps(
        {"base": BASE, "big": BIG, "runs": runs}, indent=1))
    print(f"RUN13 RELAY COMPLETE  {time.time()-t0:.0f}s  -> out/run13_transcript.json")


if __name__ == "__main__":
    main()
