"""
run15_match_pod.py — RUN 15 stage-2 pod script: THE MATCH night job (RUNBOOK15).

One detached process runs every GPU phase sequentially, resume-safe (JSONL
append + done-key skip). NO API keys ever touch this machine — all judging is
driver-side. Designed to run with the laptop asleep:

  (setsid nohup python run15_match_pod.py > out/match.log 2>&1 < /dev/null &)

Phases (each skipped when complete):
  dossier   24 problems  : CUBE relay (V audit -> F read -> V plan -> coach
                           assembly) + GENERALIST single (keep100, one pass)
  inventory 32 problems  : CUBE relay + ABLATE relay (keep100 in the V seat)
                           + GENERALIST single
  motion    32 twins     : CUBE native loop (prior = its inventory plan seg,
                           V-seat motion revision) + GENERALIST run-11 protocol
                           (PLAN_USER prior + REVISE_USER revision, keep100)
  general   48 problems  : dec_qwen decomposes ONCE per problem; CUBE routes
                           each angle via dispatcher v1 (run12_router.route on
                           problem+angle); GENERALIST writes all 4 with keep100
  refs      (only if refs_models.json present): each reference model answers
                           dossier+inventory with the same GEN_SINGLE prompt

Frozen operational choices (RUNBOOK15 stage-2 addendum):
  - read-target string for unmanifested problems: "the other parties in this
    problem" (dossier/inventory carry no counterparty field)
  - coach assembly (single-answer legs, zero free prose added):
    [AUDIT] + [READ] + [PLAN minus estimate] + [fixed digit-free BRIDGE] +
    [ESTIMATE line verbatim]. Missing estimate after 1 retry -> inject
    "ESTIMATE: 50%" and flag est_injected (judged as-is, honestly).
  - decompose once per problem, same facets/angles feed BOTH general-leg arms.
"""
from __future__ import annotations
import json, os, re, sys, time
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from run13b_pod import ADAPTERS as WORKER_ADAPTERS, BASE, SEG, emit
from run11_common import WRK_SYS, REVISE_USER
from run12_router import route

WD = Path("/workspace/div")
OUT = WD / "out"
ADAPTERS = dict(WORKER_ADAPTERS)
ADAPTERS["D"] = WD / "adapters/dec_qwen"
COUNTERPARTY = "the other parties in this problem"
EST = re.compile(r"ESTIMATE:\s*\d{1,3}\s*%")
BRIDGE = ("If the other side responds as the read anticipates, the plan is "
          "already positioned for it; if not, nothing in the commitment "
          "depends on that prediction.")

# GENERALIST single-answer prompt (frozen): the union of the three segment
# demands in one pass — same model, same information, same asks, no machine.
GEN_SINGLE = (
    "PROBLEM: {problem}\n\nWrite a single reasoning thread (6-9 sentences, cold "
    "and analytical) that: AUDITS what the actor actually holds (resources, "
    "people, authority, time — real numbers only if the problem supplies them) "
    "and names the ONE variable genuinely in the actor's favor; READS the other "
    "parties — the single most likely realistic reaction one or two moves ahead "
    "and the one observable signal that would say the read is wrong; COMMITS to "
    "a lawful plan spending ONLY audited items (who/what/when), positioned for "
    "that read, naming the ONE friction most likely to stall it and the "
    "pre-arranged answer. Final line, exactly: ESTIMATE: NN%")

# PLAN_USER byte-copied from run11_pod_gen2.py (the Eval D2 generalist prior).
PLAN_USER = ("PROBLEM: {problem}\n\nWrite a single reasoning thread (4-6 sentences, cold and "
             "analytical) that plans this with ONLY what the actor actually holds: audit the "
             "concrete resources, people, seat, and time; name the ONE variable in the actor's "
             "favor; commit to a lawful plan spending only audited items (who/what/when); name "
             "the ONE most likely friction and its pre-arranged answer. "
             "Final line, exactly: ESTIMATE: NN%")

# Decomposer + general-leg worker prompts byte-copied from dav_eval_v5.py
# (train == eval discipline; sets comparable to every prior v5 bench read).
DEC_SYS = "You refract a hard decision problem into four categorically distinct strategic angles."
DEC_USER = ("PROBLEM: {problem}\n\nGive the three key FACETS any complete answer must engage, then FOUR "
            "genuinely distinct strategic ANGLES for approaching the whole problem. Each angle must be a "
            "categorically different KIND of move (a distinct family) leading to a different action — sharp "
            "alternatives, not rephrasings.\nFormat exactly:\n"
            "FACETS: <f1> | <f2> | <f3>\nANGLES:\n1) [FAMILY] <angle>\n2) [FAMILY] <angle>\n"
            "3) [FAMILY] <angle>\n4) [FAMILY] <angle>")
WRK_USER = ("PROBLEM: {problem}\nFACETS: {facets}\nANGLE: {angle}\n\nWrite a single reasoning thread (two or "
            "three sentences, cold and analytical) that COMMITS to THIS angle as a concrete, realistic, VIABLE "
            "strategy that resolves the whole problem in a distinct way — name the actual first move (who does "
            "what, to whom, by when) and the one most likely downstream consequence it is betting on. It must be "
            "lawful, executable, and unmistakably a different KIND of move than the other families would choose.")


def parse_decomp(text):
    facets, angles = [], []
    m = re.search(r"FACETS:\s*(.+)", text)
    if m:
        facets = [x.strip() for x in re.split(r"\||;", m.group(1).splitlines()[0]) if x.strip()][:3]
    for n in range(1, 5):
        a = re.search(rf"{n}\)\s*(.+)", text)
        if a:
            angles.append(a.group(1).strip())
    return facets, angles[:4]


def gen2(model, tok, system, user, max_new=400):
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt")
    ids = ids["input_ids"] if hasattr(ids, "keys") else ids
    with torch.no_grad():
        out = model.generate(ids.to("cuda"), max_new_tokens=max_new, do_sample=False,
                             pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()


def with_estimate(model, tok, user, text):
    """One retry with a nudge if the tagged estimate is missing (run13b law)."""
    if EST.search(text):
        return text, False
    text2 = gen2(model, tok, WRK_SYS, user + "\n(Do not omit the final ESTIMATE line.)")
    if EST.search(text2):
        return text2, False
    return text2 + " ESTIMATE: 50%", True   # inject + flag; judged as-is


def assemble_match(audit, read, plan):
    est_line = EST.findall(plan)[-1]        # last occurrence (run-11 law)
    body = EST.sub(" ", plan).strip()
    return " ".join([audit.strip(), read.strip(), body, BRIDGE, est_line])


def relay(model, tok, problem, v_seat):
    """audit(v_seat) -> read(F) -> plan(v_seat); returns segs + assembled answer."""
    seg = {}
    model.set_adapter(v_seat)
    seg["audit"] = gen2(model, tok, WRK_SYS, SEG["audit"].format(problem=problem))
    model.set_adapter("F")
    seg["read"] = gen2(model, tok, WRK_SYS, SEG["read"].format(
        problem=problem, audit=seg["audit"], counterparty=COUNTERPARTY))
    model.set_adapter(v_seat)
    plan_user = SEG["plan"].format(problem=problem, audit=seg["audit"], read=seg["read"])
    plan = gen2(model, tok, WRK_SYS, plan_user)
    seg["plan"], seg["est_injected"] = with_estimate(model, tok, plan_user, plan)
    seg["answer"] = assemble_match(seg["audit"], seg["read"], seg["plan"])
    return seg


def jsonl_done(path, keyf):
    done = set()
    if path.exists():
        for l in path.open():
            done.add(keyf(json.loads(l)))
    return done


def load_workers():
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                                 device_map="cuda")
    model = PeftModel.from_pretrained(model, str(ADAPTERS["F"]), adapter_name="F")
    for k in ("V", "G", "D"):
        model.load_adapter(str(ADAPTERS[k]), adapter_name=k)
    return model, tok


def phase_dossier(model, tok):
    probs = [json.loads(l) for l in (WD / "match_dossier.jsonl").open()]
    out = OUT / "match_dossier_out.jsonl"
    done = jsonl_done(out, lambda r: r["idx"])
    f = out.open("a")
    for i, pr in enumerate(probs):
        if i in done:
            continue
        t0 = time.time()
        cube = relay(model, tok, pr["problem"], "V")
        model.set_adapter("G")
        g = gen2(model, tok, WRK_SYS, GEN_SINGLE.format(problem=pr["problem"]), max_new=500)
        g, g_inj = with_estimate(model, tok, GEN_SINGLE.format(problem=pr["problem"]), g)
        f.write(json.dumps({"idx": i, "problem": pr["problem"], "cube": cube,
                            "gen": g, "gen_est_injected": g_inj}) + "\n")
        f.flush()
        emit(stage="dossier", idx=i, secs=round(time.time() - t0, 1))
        print(f"[dossier {i:02d}/24] done", flush=True)
    f.close()
    print("PHASE DOSSIER COMPLETE", flush=True)


def phase_inventory(model, tok):
    probs = [json.loads(l) for l in (WD / "match_inventory.jsonl").open()]
    out = OUT / "match_inventory_out.jsonl"
    done = jsonl_done(out, lambda r: r["idx"])
    f = out.open("a")
    for i, pr in enumerate(probs):
        if i in done:
            continue
        t0 = time.time()
        cube = relay(model, tok, pr["problem"], "V")
        ablate = relay(model, tok, pr["problem"], "G")
        model.set_adapter("G")
        g = gen2(model, tok, WRK_SYS, GEN_SINGLE.format(problem=pr["problem"]), max_new=500)
        g, g_inj = with_estimate(model, tok, GEN_SINGLE.format(problem=pr["problem"]), g)
        f.write(json.dumps({"idx": i, "problem": pr["problem"], "cube": cube,
                            "ablate": ablate, "gen": g, "gen_est_injected": g_inj}) + "\n")
        f.flush()
        emit(stage="inventory", idx=i, secs=round(time.time() - t0, 1))
        print(f"[inventory {i:02d}/32] done", flush=True)
    f.close()
    print("PHASE INVENTORY COMPLETE", flush=True)


def phase_motion(model, tok):
    twins = [json.loads(l) for l in (WD / "match_twins.jsonl").open()]
    inv_rows = {r["idx"]: r for r in
                (json.loads(l) for l in (OUT / "match_inventory_out.jsonl").open())}
    out = OUT / "match_motion_out.jsonl"
    done = jsonl_done(out, lambda r: (r["arm"], r["kind"], r["base_index"]))
    f = out.open("a")
    # generalist priors (run-11 protocol, keep100, one per base problem)
    gp_path = OUT / "match_motion_priors.jsonl"
    gpriors = {r["base_index"]: r["plan"] for r in
               (json.loads(l) for l in gp_path.open())} if gp_path.exists() else {}
    gpf = gp_path.open("a")
    model.set_adapter("G")
    for i in sorted({t["base_index"] for t in twins}):
        if i in gpriors:
            continue
        problem = inv_rows[i]["problem"]
        plan = gen2(model, tok, WRK_SYS, PLAN_USER.format(problem=problem))
        plan, _ = with_estimate(model, tok, PLAN_USER.format(problem=problem), plan)
        gpriors[i] = plan
        gpf.write(json.dumps({"base_index": i, "plan": plan}) + "\n")
        gpf.flush()
        print(f"[motion prior {i:02d}] done", flush=True)
    gpf.close()
    for tw in twins:
        i = tw["base_index"]
        problem = inv_rows[i]["problem"]
        # CUBE: prior = its own inventory plan segment, V-seat native motion
        if ("cube", tw["kind"], i) not in done:
            prior = inv_rows[i]["cube"]["plan"]
            model.set_adapter("V")
            rev = gen2(model, tok, WRK_SYS, SEG["motion"].format(
                problem=problem, plan=prior, update=tw["update"]))
            f.write(json.dumps({"arm": "cube", "kind": tw["kind"], "base_index": i,
                                "prior": prior, "update": tw["update"],
                                "revision": rev}) + "\n")
            f.flush()
        # GENERALIST: run-11 REVISE_USER protocol verbatim
        if ("gen", tw["kind"], i) not in done:
            model.set_adapter("G")
            rev = gen2(model, tok, WRK_SYS, REVISE_USER.format(
                problem=problem, prior=gpriors[i], update=tw["update"]))
            f.write(json.dumps({"arm": "gen", "kind": tw["kind"], "base_index": i,
                                "prior": gpriors[i], "update": tw["update"],
                                "revision": rev}) + "\n")
            f.flush()
        print(f"[motion {tw['kind']} {i:02d}] done", flush=True)
    f.close()
    print("PHASE MOTION COMPLETE", flush=True)


def phase_general(model, tok):
    probs = [json.loads(l) for l in (WD / "match_general.jsonl").open()]
    out = OUT / "match_general_out.jsonl"
    done = jsonl_done(out, lambda r: r["idx"])
    f = out.open("a")
    for i, pr in enumerate(probs):
        if i in done:
            continue
        t0 = time.time()
        p = pr["problem"]
        model.set_adapter("D")
        facets = angles = None
        for _ in range(2):   # one retry on malformed decomposition
            dtext = gen2(model, tok, DEC_SYS, DEC_USER.format(problem=p), max_new=600)
            facets, angles = parse_decomp(dtext)
            if len(angles) == 4 and len(facets) >= 1:
                break
        if len(angles) < 4 or len(facets) < 1:
            f.write(json.dumps({"idx": i, "problem": p, "fail": "decomp"}) + "\n")
            f.flush()
            print(f"[general {i:02d}/48] DECOMP FAIL", flush=True)
            continue
        seats = [route(p + " " + a) for a in angles]
        cube_threads, gen_threads_ = [], []
        for a, seat in zip(angles, seats):
            model.set_adapter(seat)
            cube_threads.append(gen2(model, tok, WRK_SYS, WRK_USER.format(
                problem=p, facets=" | ".join(facets), angle=a), max_new=256))
        model.set_adapter("G")
        for a in angles:
            gen_threads_.append(gen2(model, tok, WRK_SYS, WRK_USER.format(
                problem=p, facets=" | ".join(facets), angle=a), max_new=256))
        f.write(json.dumps({"idx": i, "problem": p, "facets": facets, "angles": angles,
                            "seats": seats, "cube_threads": cube_threads,
                            "gen_threads": gen_threads_}) + "\n")
        f.flush()
        emit(stage="general", idx=i, seats="".join(seats),
             secs=round(time.time() - t0, 1))
        print(f"[general {i:02d}/48] seats={''.join(seats)}", flush=True)
    f.close()
    print("PHASE GENERAL COMPLETE", flush=True)


def strip_thinking(text):
    if "</think>" in text:
        text = text.rsplit("</think>", 1)[1]
    if "final<|message|>" in text:          # gpt-oss harmony format
        text = text.rsplit("final<|message|>", 1)[1]
    return text.strip()


def phase_refs():
    cfg = WD / "refs_models.json"
    if not cfg.exists():
        print("PHASE REFS SKIPPED (no refs_models.json)", flush=True)
        return
    models = json.loads(cfg.read_text())
    probs = ([("dossier", json.loads(l)["problem"]) for l in (WD / "match_dossier.jsonl").open()] +
             [("inventory", json.loads(l)["problem"]) for l in (WD / "match_inventory.jsonl").open()])
    for mid in models:
        tag = mid.split("/")[-1].replace(".", "_")
        out = OUT / f"match_refs_{tag}.jsonl"
        done = jsonl_done(out, lambda r: (r["leg"], r["idx"]))
        if len(done) >= len(probs):
            print(f"[refs {tag}] already complete", flush=True)
            continue
        print(f"[refs] loading {mid}", flush=True)
        try:
            tok = AutoTokenizer.from_pretrained(mid)
            model = AutoModelForCausalLM.from_pretrained(mid, torch_dtype="auto",
                                                         device_map="cuda")
        except Exception as e:
            print(f"[refs {tag}] LOAD FAILED ({e}) — skipping model", flush=True)
            continue
        f = out.open("a")
        idx_by_leg = {"dossier": 0, "inventory": 0}
        for leg, p in probs:
            i = idx_by_leg[leg]
            idx_by_leg[leg] += 1
            if (leg, i) in done:
                continue
            msgs = [{"role": "system", "content": WRK_SYS},
                    {"role": "user", "content": GEN_SINGLE.format(problem=p)}]
            ids = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                          return_tensors="pt")
            ids = ids["input_ids"] if hasattr(ids, "keys") else ids
            with torch.no_grad():
                o = model.generate(ids.to("cuda"), max_new_tokens=2048, do_sample=False,
                                   pad_token_id=tok.eos_token_id)
            text = strip_thinking(tok.decode(o[0][ids.shape[1]:], skip_special_tokens=True))
            f.write(json.dumps({"leg": leg, "idx": i, "model": mid, "answer": text}) + "\n")
            f.flush()
            print(f"[refs {tag}] {leg} {i:02d}", flush=True)
        f.close()
        del model
        torch.cuda.empty_cache()
        print(f"[refs {tag}] COMPLETE", flush=True)
    print("PHASE REFS COMPLETE", flush=True)


def main():
    OUT.mkdir(exist_ok=True)
    n_dos = sum(1 for _ in (WD / "match_dossier.jsonl").open())
    n_inv = sum(1 for _ in (WD / "match_inventory.jsonl").open())
    n_twin = sum(1 for _ in (WD / "match_twins.jsonl").open())
    n_gen = sum(1 for _ in (WD / "match_general.jsonl").open())
    assert (n_dos, n_inv, n_twin, n_gen) == (24, 32, 32, 48), \
        f"bench shape wrong: {(n_dos, n_inv, n_twin, n_gen)}"
    model, tok = load_workers()
    phase_dossier(model, tok)
    phase_inventory(model, tok)
    phase_motion(model, tok)
    phase_general(model, tok)
    del model
    torch.cuda.empty_cache()
    phase_refs()
    print("RUN15 MATCH NIGHT JOB COMPLETE", flush=True)


if __name__ == "__main__":
    main()
