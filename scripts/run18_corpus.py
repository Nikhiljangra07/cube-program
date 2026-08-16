"""
run18_corpus.py — RUN 18 corpus: the fatal-flaw gate, labels mined for $0
(RUNBOOK18). Every label derives from an already-paid Sonnet read; the RULER-T
classifier (ruler_t.py, frozen) maps flaw prose -> SOUND / FATAL.

Label-trust rules (frozen):
  STRICT-COMPLETE reads (full classification, both classes):
    - the 208 STRICT_ONE relabels (out/run16/relabel_cache.jsonl), which
      override the original label of any joined verifier_real row
    - verifier_real rows with source == 'match' (strict folded criterion)
    - the 120 ladder reads (run 17 arm B + run 17B arms M/R)
  LENIENT reads (run13b / run14 / run15smoke originals, no relabel):
    - FATAL only if their flaw prose already shows a T1 marker (precision-safe);
      otherwise EXCLUDED (a lenient read may have missed a fatal flaw, so
      "sounds clean" cannot be trusted from it)

Splits: verifier_real rows keep their run-16 problem-level split verbatim;
ladder answers split by pid (< 28 train, >= 28 eval — 12 problems x 3 arms).
SOUND rows oversampled x3 in train (run-16 anti-all-flag lesson).

  python scripts/run18_corpus.py   # writes data/run18/ver18_{train,eval}.jsonl
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ruler_t import classify  # frozen taxonomy  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D18 = ROOT / "data/run18"

VER18_SYS = ("You are a strict plan auditor. Given a PROBLEM and a RESPONSE, decide "
             "whether the RESPONSE commits any FATAL flaw.")
VER18_USER = (
    "PROBLEM: {problem}\n\nRESPONSE: {answer}\n\n"
    "FATAL flaws are: contradicting itself; mis-stating a fact given in the "
    "PROBLEM; violating a stated constraint (for example spending above a stated "
    "sign-off cap); arithmetic or date errors; treating an already-observed event "
    "as future, or a prediction as an accomplished fact. Proposing new specifics "
    "(amounts, dates, times, names) is NOT fatal as long as nothing given is "
    "contradicted. If the RESPONSE contains no fatal flaw, output exactly: SOUND. "
    "Otherwise output: FATAL: <one sentence naming the clearest fatal flaw>.")


def md5(t):
    return hashlib.md5(t.encode()).hexdigest()


def row(problem, answer, label, reason):
    tgt = "SOUND" if label == "SOUND" else f"FATAL: {reason}"
    return {"messages": [
        {"role": "system", "content": VER18_SYS},
        {"role": "user", "content": VER18_USER.format(problem=problem, answer=answer)},
        {"role": "assistant", "content": tgt}]}


def label_from_flaws(flaws):
    fl = [f if isinstance(f, str) else str(f) for f in flaws]
    cls = [classify(f) for f in fl]
    fatal_fl = [f for f, c in zip(fl, cls) if c != "ADD"]
    return ("FATAL", fatal_fl[0]) if fatal_fl else ("SOUND", "")


def main():
    relabel = {}
    for l in (ROOT / "out/run16/relabel_cache.jsonl").open():
        r = json.loads(l)
        relabel[r["key"]] = r["verdict"]

    train, evalr = [], []
    stats = {"strict": 0, "lenient_fatal": 0, "excluded": 0}

    # ---- source 1: the 621 real pairs ----
    for l in (ROOT / "data/run16/verifier_real.jsonl").open():
        r = json.loads(l)
        rel = relabel.get(f"one|{md5(r['answer'])[:12]}")
        if rel is not None:
            lab, reason = label_from_flaws(rel.get("flaws", []))
            if rel.get("coherent"):
                lab, reason = "SOUND", ""
            stats["strict"] += 1
        elif r["source"] == "match":
            flaws = r["flaws"] if isinstance(r["flaws"], list) else json.loads(r["flaws"].replace("'", '"')) if r["flaws"] not in ("[]", "") else []
            lab, reason = label_from_flaws(flaws)
            stats["strict"] += 1
        else:
            flaws = r["flaws"] if isinstance(r["flaws"], list) else []
            fatal_fl = [f for f in flaws if classify(str(f)) in ("T1",)]
            if not fatal_fl:
                stats["excluded"] += 1
                continue
            lab, reason = "FATAL", str(fatal_fl[0])
            stats["lenient_fatal"] += 1
        out = row(r["problem"], r["answer"], lab, reason)
        (train if r["split"] == "train" else evalr).append((lab, out))

    # ---- source 2: the 120 ladder reads (all strict) ----
    probs = {json.loads(l)["pid"]: json.loads(l)
             for l in (ROOT / "data/run17/ladder_problems.jsonl").open()}
    for out_path, cache_path, prefix in (
            ("out/run17/ladder17_out.jsonl", "out/run17/judge_cache.jsonl", "lad|"),
            ("out/run17b/ladder17b_out.jsonl", "out/run17b/judge_cache.jsonl", "17b|")):
        cache = {}
        for l in (ROOT / cache_path).open():
            c = json.loads(l)
            if not c.get("_mock"):
                cache[c["key"]] = c["verdict"]
        for l in (ROOT / out_path).open():
            r = json.loads(l)
            v = cache.get(f"{prefix}{md5(r['answer'])[:12]}")
            if v is None:
                continue
            lab, reason = ("SOUND", "") if v["coherent"] else label_from_flaws(v.get("flaws", []))
            stats["strict"] += 1
            out = row(probs[r["pid"]]["problem"], r["answer"], lab, reason)
            (train if r["pid"] < 28 else evalr).append((lab, out))

    # ---- assemble: oversample SOUND x3 in train ----
    D18.mkdir(parents=True, exist_ok=True)
    tr_rows = []
    for lab, o in train:
        tr_rows.extend([o] * (3 if lab == "SOUND" else 1))
    ev_rows = [o for _, o in evalr]
    (D18 / "ver18_train.jsonl").write_text("".join(json.dumps(o) + "\n" for o in tr_rows))
    (D18 / "ver18_eval.jsonl").write_text("".join(json.dumps(o) + "\n" for o in ev_rows))

    def counts(pairs):
        s = sum(1 for lab, _ in pairs if lab == "SOUND")
        return f"{len(pairs)} rows ({s} SOUND / {len(pairs)-s} FATAL)"
    print("label trust:", stats)
    print("train (pre-oversample):", counts(train), f"-> {len(tr_rows)} rows on disk")
    print("eval:", counts(evalr))
    ev_sound = sum(1 for lab, _ in evalr if lab == "SOUND")
    assert ev_sound >= 12, f"eval SOUND too thin ({ev_sound}) — extend eval split"
    for name in ("ver18_train.jsonl", "ver18_eval.jsonl"):
        print(name, "md5", hashlib.md5((D18 / name).read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
