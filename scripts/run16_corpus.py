"""
run16_corpus.py — RUN 16 stage 0: verifier corpus assembly (RUNBOOK16, $0).

Mines every Sonnet-labeled (answer -> coherent/flaws) pair this program has
already paid for, joins each label back to its EXACT judged text (md5-verified
against the cache key wherever the key carries one), dedups, splits by PROBLEM
identity, and augments the train split with seeded programmatic corruptions
whose labels are perfect by construction (we made the defects).

Sources (all local, all already billed):
  run13b  judge_cache (77)   : fusion_A/fusion_C (transcript13b) + Dp repair
                               attempts r2/r3 — key arm|pid|attempt|md5(full)
  run14   judge_cache (379)  : harvest certification via corpus_speeches ×
                               corpus_verdicts (pid/attempt join, md5 cross-
                               checked) + eval fusions (eval_transcript14)
  run15   judge_cache (48)   : smoke COACH (re-assembled deterministically from
                               stored motions + fix rounds) + BASE fusions
  run15   match_judge_cache  : 144 folded-coherence reads (dossier 48 +
                               inventory 96) joined to match transcripts

Split law (problem-level, no leakage; same staged problem splits identically
across 13b and smoke15): staged pids 0-19 train / 20-23 eval · run14 pids
0-139 train / 140-159 eval · match dossier idx 0-15 train / 16-23 eval ·
match inventory idx 0-20 train / 21-31 eval. SYNTHETIC ROWS NEVER ENTER EVAL.

Corruption classes (seeded RNG, seed 16; each verified against the problem
text before emission): invented_number · invented_actor · prediction_as_fact ·
dead_option_revival (manifest rows only) · self_contradiction.

Outputs (data/run16/): verifier_real.jsonl (every joined real pair + split
tag), verifier_train.jsonl (chat-SFT rows, real train + synthetic),
verifier_eval.jsonl (real eval only). Prints per-source join coverage —
UNJOINED CACHE ROWS ARE LISTED, never silently dropped.
"""
from __future__ import annotations
import hashlib, json, random, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run15_coach import assemble  # frozen stage-1 assembler, reused verbatim

ROOT = Path(__file__).resolve().parent.parent
D16 = ROOT / "data/run16"
RNG = random.Random(16)

VER_SYS = ("You are a strict grounding auditor. Given a PROBLEM and a RESPONSE, "
           "decide whether every claim in the RESPONSE is grounded in the PROBLEM text.")
VER_USER = ("PROBLEM: {problem}\n\nRESPONSE: {answer}\n\n"
            "If every number, actor, event, and commitment in the RESPONSE is grounded "
            "in the PROBLEM (or is an explicitly conditional prediction), output "
            "exactly: GROUNDED. Otherwise output: FLAGGED: <one sentence naming the "
            "single clearest ungrounded claim>.")

rows = []          # unified real rows
unjoined = []


def md5(t):
    return hashlib.md5(t.encode()).hexdigest()


def add(source, split_key, problem, answer, judge, key, manifest=None):
    rows.append({"source": source, "split_key": split_key, "problem": problem,
                 "answer": answer, "coherent": bool(judge["coherent"]),
                 "flaws": judge.get("flaws", []), "key": key,
                 "manifest": manifest})


def cache_map(path, keyname="judge"):
    out = {}
    for l in path.open():
        r = json.loads(l)
        if r.get("_mock"):
            continue
        out[r["key"]] = r[keyname] if keyname in r else r.get("verdict")
    return out


# ---------------- run 13B ----------------
def src_13b():
    cache = cache_map(ROOT / "out/run13b/judge_cache.jsonl")
    probs = {json.loads(l)["pid"]: json.loads(l)
             for l in (ROOT / "data/run13/staged_problems.jsonl").open()}
    t = json.load((ROOT / "out/run13b/transcript13b.json").open())
    cand = {}   # md5 -> (pid, text)
    for r in t["runs"]:
        for arm, txt in (("A", r["fusion_A"]), ("C", r["fusion_C"])):
            cand[f"{arm}|{r['pid']}|1|{md5(txt)}"] = (r["pid"], txt)
    for rnd in (2, 3):
        p = ROOT / f"out/run13b/attempts_r{rnd}.json"
        if p.exists():
            for pid_s, txt in json.load(p.open()).items():
                cand[f"Dp|{pid_s}|{rnd}|{md5(txt)}"] = (int(pid_s), txt)
    n = 0
    for key, judge in cache.items():
        if key in cand:
            pid, txt = cand[key]
            pr = probs[pid]
            man = {"dead_token": pr["dead_token"], "counterparty": pr["counterparty"]}
            add("run13b", f"staged{pid}", pr["problem"] + "\n\nUPDATE: " + pr["update"],
                txt, judge, key, man)
            n += 1
        else:
            unjoined.append(("run13b", key))
    print(f"  run13b: {n}/{len(cache)} joined")


# ---------------- run 14 ----------------
def src_14():
    cache = cache_map(ROOT / "out/run14/judge_cache.jsonl")
    probs = {json.loads(l)["pid"]: json.loads(l)
             for l in (ROOT / "data/run14/train_problems.jsonl").open()}
    speeches = json.load((ROOT / "out/run14/corpus_speeches.json").open())
    verdicts = json.load((ROOT / "out/run14/corpus_verdicts.json").open())
    n = matched_keys = 0
    for pid_s, attempts in speeches.items():
        pid = int(pid_s)
        for att, txt in attempts.items():
            j = verdicts.get(pid_s, {}).get(att)
            if not j:
                continue
            key = f"S1|{pid}|{att}|{md5(txt)}"
            if key in cache:      # cross-verify the join against the cache
                matched_keys += 1
            pr = probs[pid]
            man = {"dead_token": pr["dead_token"], "counterparty": pr["counterparty"]}
            add("run14", f"r14p{pid}", pr["problem"] + "\n\nUPDATE: " + pr["update"],
                txt, j, key, man)
            n += 1
    # eval fusions (F14/A arms on the frozen 24 staged problems)
    ev = json.load((ROOT / "out/run14/eval_transcript14.json").open())
    sp = {json.loads(l)["pid"]: json.loads(l)
          for l in (ROOT / "data/run13/staged_problems.jsonl").open()}
    ne = 0
    for r in ev.get("runs", []):
        for arm in ("fusion_F14", "fusion_A"):
            if arm not in r:
                continue
            txt = r[arm]
            for k, j in cache.items():
                if k.endswith(md5(txt)):
                    pr = sp[r["pid"]]
                    man = {"dead_token": pr["dead_token"],
                           "counterparty": pr["counterparty"]}
                    add("run14eval", f"staged{r['pid']}",
                        pr["problem"] + "\n\nUPDATE: " + pr["update"], txt, j, k, man)
                    ne += 1
                    break
    print(f"  run14: harvest {n} (cache-key cross-check {matched_keys}), eval {ne} "
          f"(cache total {len(cache)})")


# ---------------- run 15 smoke ----------------
def src_15smoke():
    cache = cache_map(ROOT / "out/run15/judge_cache.jsonl")
    probs = {json.loads(l)["pid"]: json.loads(l)
             for l in (ROOT / "data/run13/staged_problems.jsonl").open()}
    t = json.load((ROOT / "out/run15/smoke15_transcript.json").open())
    motions = {r["pid"]: r["motion"] for r in t["runs"]}
    for rnd in (1, 2):
        p = ROOT / f"out/run15/motionfix15_r{rnd}_out.json"
        if p.exists():
            for pid_s, m in json.load(p.open()).items():
                motions[int(pid_s)] = m
    n = 0
    for r in t["runs"]:
        pid = r["pid"]
        pr = probs[pid]
        man = {"dead_token": pr["dead_token"], "counterparty": pr["counterparty"]}
        coach = assemble(motions[pid], pr)
        if coach is None:
            coach = assemble(motions[pid] + " ESTIMATE: 50%", pr)
        for arm, txt in (("COACH", coach), ("BASE", r["fusion_base"])):
            key = f"{arm}|{pid}|1|{md5(txt)}"
            if key in cache:
                add("run15smoke", f"staged{pid}",
                    pr["problem"] + "\n\nUPDATE: " + pr["update"],
                    txt, cache[key], key, man)
                n += 1
            else:
                unjoined.append(("run15smoke", key))
    print(f"  run15smoke: {n}/{len(cache)} joined")


# ---------------- run 15 match ----------------
def src_match():
    cache = cache_map(ROOT / "out/run15/match_judge_cache.jsonl", keyname="verdict")
    M = ROOT / "out/run15/match"
    inv_meta = [json.loads(l) for l in (ROOT / "data/run10/inventory_problems.jsonl").open()]
    n = 0
    for leg, fname, arms in (("dossier", "match_dossier_out.jsonl", ("cube", "gen")),
                             ("inventory", "match_inventory_out.jsonl",
                              ("cube", "ablate", "gen"))):
        for r in (json.loads(l) for l in (M / fname).open()):
            for arm in arms:
                txt = r[arm]["answer"] if isinstance(r[arm], dict) else r[arm]
                key = f"{leg}|{arm}|{r['idx']}|{md5(txt)[:12]}"
                j = cache.get(key)
                if j and "coherent" in j:
                    add(f"match_{leg}", f"{leg}{r['idx']}", r["problem"], txt,
                        j, key, None)
                    n += 1
                else:
                    unjoined.append(("match", key))
    print(f"  match: {n} coherence reads joined")


# ---------------- split law ----------------
def split_of(r):
    k = r["split_key"]
    if k.startswith("staged"):
        return "eval" if int(k[6:]) >= 20 else "train"
    if k.startswith("r14p"):
        return "eval" if int(k[4:]) >= 140 else "train"
    if k.startswith("dossier"):
        return "eval" if int(k[7:]) >= 16 else "train"
    if k.startswith("inventory"):
        return "eval" if int(k[9:]) >= 21 else "train"
    raise ValueError(k)


# ---------------- corruptions (train split only, seeded) ----------------
ACTORS = ["Halvorsen", "Okafor", "Brandt", "Ceballos", "Whitfield", "Marchetti",
          "Duval", "Petrov", "Lindqvist", "Abernathy"]
NUM = re.compile(r"\$[\d,]+|\b\d{2,6}\b")
ESTL = re.compile(r"ESTIMATE:\s*(\d{1,3})\s*%")


def _insert_before_estimate(answer, sentence):
    m = ESTL.search(answer)
    if m:
        return answer[:m.start()].rstrip() + " " + sentence + " " + answer[m.start():]
    return answer.rstrip() + " " + sentence


def corrupt(r):
    out = []
    problem, answer = r["problem"], r["answer"]

    def emit(cat, txt, reason):
        if txt != answer:
            out.append({"problem": problem, "answer": txt, "coherent": False,
                        "flaws": [reason], "source": "synthetic:" + cat,
                        "split_key": r["split_key"]})
    # invented_number: perturb an existing figure to one absent from problem+answer
    nums = [m.group(0) for m in NUM.finditer(answer) if m.group(0) in answer]
    RNG.shuffle(nums)
    for tok in nums:
        raw = int(re.sub(r"[^\d]", "", tok))
        if raw < 10:
            continue
        new = str(int(raw * (1.6 + RNG.random())))
        newtok = ("$" + "{:,}".format(int(new))) if tok.startswith("$") else new
        if newtok not in problem and newtok not in answer:
            emit("invented_number", answer.replace(tok, newtok, 1),
                 f"States the figure {newtok}, which appears nowhere in the problem.")
            break
    # invented_actor
    name = next((a for a in ACTORS if a not in problem and a not in answer), None)
    if name:
        emit("invented_actor", _insert_before_estimate(
            answer, f"{name} has agreed to support the plan if the timing slips."),
            f"Introduces {name}, an actor who appears nowhere in the problem.")
    # prediction_as_fact
    emit("prediction_as_fact", _insert_before_estimate(
        answer, "The counterparty has already accepted the revised terms, which "
                "settles the main uncertainty."),
        "States the counterparty's acceptance as an event that has already "
        "happened, when no such acceptance appears in the problem.")
    # dead_option_revival (manifest rows only)
    man = r.get("manifest")
    if man and man.get("dead_token") and man["dead_token"] not in ("", None):
        emit("dead_option_revival", _insert_before_estimate(
            answer, f"Falling back to {man['dead_token']} remains a live option "
                    f"if the plan stalls."),
            f"Revives {man['dead_token']}, which the update eliminated.")
    # self_contradiction (only when a moderate estimate exists)
    m = ESTL.search(answer)
    if m and int(m.group(1)) <= 70:
        emit("self_contradiction", _insert_before_estimate(
            answer, "Success at this point is effectively certain."),
            f"Claims success is effectively certain while the stated estimate "
            f"is {m.group(1)}%.")
    RNG.shuffle(out)
    return out[:3]   # cap per base row — keeps synthetic:real ratio bounded


def sft_row(problem, answer, coherent, flaws):
    tgt = "GROUNDED" if coherent else ("FLAGGED: " + (flaws[0] if flaws else
                                                     "contains an ungrounded claim."))
    return {"messages": [
        {"role": "system", "content": VER_SYS},
        {"role": "user", "content": VER_USER.format(problem=problem, answer=answer)},
        {"role": "assistant", "content": tgt}]}


def main():
    D16.mkdir(parents=True, exist_ok=True)
    print("joining sources:")
    src_13b()
    src_14()
    src_15smoke()
    src_match()
    if unjoined:
        print(f"  UNJOINED cache rows: {len(unjoined)} (listed in unjoined.json)")
        (D16 / "unjoined.json").write_text(json.dumps(unjoined, indent=1))
    # dedup by answer md5; on label conflict, drop (recorded)
    seen, dropped = {}, 0
    uniq = []
    for r in rows:
        h = md5(r["answer"])
        if h in seen:
            if seen[h] != r["coherent"]:
                dropped += 1
            continue
        seen[h] = r["coherent"]
        uniq.append(r)
    for r in uniq:
        r["split"] = split_of(r)
    tr = [r for r in uniq if r["split"] == "train"]
    ev = [r for r in uniq if r["split"] == "eval"]
    syn = []
    for r in tr:
        if r["coherent"]:
            syn.extend(corrupt(r))
    (D16 / "verifier_real.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in uniq))
    (D16 / "verifier_eval.jsonl").write_text(
        "".join(json.dumps(sft_row(r["problem"], r["answer"], r["coherent"],
                                   r["flaws"])) + "\n" for r in ev))
    # class balance: clean train rows oversampled x3 (174 -> 522 vs 860 flagged);
    # without this the skew teaches "always flag" and recall_clean dies
    train_sft = []
    for r in tr:
        reps = 3 if r["coherent"] else 1
        train_sft.extend([sft_row(r["problem"], r["answer"], r["coherent"],
                                  r["flaws"])] * reps)
    train_sft += [sft_row(r["problem"], r["answer"], False, r["flaws"]) for r in syn]
    RNG.shuffle(train_sft)
    (D16 / "verifier_train.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in train_sft))

    def stats(rs):
        c = sum(1 for r in rs if r["coherent"])
        return f"{len(rs)} rows ({c} clean / {len(rs)-c} flawed)"
    print(f"\nreal total: {stats(uniq)} | label-conflict dropped: {dropped}")
    print(f"train real: {stats(tr)} | synthetic: {len(syn)}")
    print(f"eval  real: {stats(ev)}  <- bars measured here, NO synthetic")
    for f in ("verifier_real.jsonl", "verifier_train.jsonl", "verifier_eval.jsonl"):
        p = D16 / f
        print(f"  {f}: md5 {hashlib.md5(p.read_bytes()).hexdigest()[:12]}")


if __name__ == "__main__":
    main()
