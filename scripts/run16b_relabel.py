"""
run16b_relabel.py — RUN 16B: single-ruler relabel of CLEAN rows (RUNBOOK16 16B,
frozen). Flawed labels survive (strict ⊇ lenient); only cleans are re-read
under the strict criterion — the same coherence fold the match used.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/run16b_relabel.py          # relabel (cached, capped)
  python scripts/run16b_relabel.py --rebuild  # write v2 train/eval files

Eval cleans: INDIVIDUAL reads (pristine gold). Train cleans: batched <=3
answers of the SAME problem per call. Cache: out/run16/relabel_cache.jsonl.
Spend caps: eval 40 reads, train 80 calls — abort before billing if over.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, os, random, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("ANTHROPIC_API_KEY", "")
import head2head_v5 as H  # parse_json + SEM + key  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D16 = ROOT / "data/run16"
CACHE = ROOT / "out/run16/relabel_cache.jsonl"
CAP_EVAL, CAP_TRAIN = 40, 80

STRICT_ONE = """You are auditing ONE candidate answer to a decision problem for grounding. Be strict.

PROBLEM: {problem}

ANSWER:
{answer}

The answer is INCOHERENT if it contains ANY of: a number, resource, actor, or event not present
in the problem text; a self-contradiction; or a predicted reaction stated as an event that has
already happened. Explicitly conditional predictions ("if they...", "should they...") are allowed.
A final success-estimate percentage line is allowed and does not count as an invented number.

Return ONLY JSON: {{"coherent":true|false,"flaws":["<each violation, briefly>"]}}"""

STRICT_BATCH = """You are auditing {k} INDEPENDENT cases for grounding. Each case has its own PROBLEM and
its own ANSWER. Be strict, and judge each case against ITS OWN problem only.

{cases}

An answer is INCOHERENT if it contains ANY of: a number, resource, actor, or event not present
in ITS problem text; a self-contradiction; or a predicted reaction stated as an event that has
already happened. Explicitly conditional predictions ("if they...", "should they...") are allowed.
A final success-estimate percentage line is allowed and does not count as an invented number.

Return ONLY a JSON array with one object per case, in order:
[{{"idx":1,"coherent":true|false,"flaws":["..."]}}, ...]"""


def md5(t):
    return hashlib.md5(t.encode()).hexdigest()


def load_cache():
    c = {}
    if CACHE.exists():
        for l in CACHE.open():
            r = json.loads(l)
            c[r["key"]] = r["verdict"]
    return c


async def acall(client, prompt):
    async with H.SEM:
        for a in range(5):
            try:
                r = await client.post("https://api.anthropic.com/v1/messages",
                                      headers={"x-api-key": H.ANTHROPIC_KEY,
                                               "anthropic-version": "2023-06-01",
                                               "content-type": "application/json"},
                                      json={"model": "claude-sonnet-5", "max_tokens": 12000,
                                            "messages": [{"role": "user", "content": prompt}]},
                                      timeout=180)
                r.raise_for_status()
                text = "".join(p.get("text", "") for p in r.json().get("content", [])
                               if p.get("type") == "text").strip()
                if text:
                    return text
            except Exception:
                await asyncio.sleep(3 * (a + 1))
    return None


def valid_one(j):
    return (isinstance(j, dict) and isinstance(j.get("coherent"), bool)
            and isinstance(j.get("flaws"), list))


async def relabel():
    rows = [json.loads(l) for l in (D16 / "verifier_real.jsonl").open()]
    cleans = [r for r in rows if r["coherent"]]
    ev = [r for r in cleans if r["split"] == "eval"]
    tr = [r for r in cleans if r["split"] == "train"]
    cache = load_cache()
    ev_todo = [r for r in ev if f"one|{md5(r['answer'])[:12]}" not in cache]
    # train: batches of <=3 cases (problem+answer pairs; problems mostly have a
    # single clean answer, so same-problem grouping degenerates to singletons)
    tr_sorted = sorted(tr, key=lambda r: md5(r["answer"]))
    batches = [tr_sorted[i:i + 3] for i in range(0, len(tr_sorted), 3)]
    b_todo = [b for b in batches
              if any(f"one|{md5(r['answer'])[:12]}" not in cache for r in b)]
    print(f"eval cleans: {len(ev)} ({len(ev_todo)} new, cap {CAP_EVAL}) | "
          f"train cleans: {len(tr)} in {len(batches)} batches ({len(b_todo)} new, "
          f"cap {CAP_TRAIN})")
    if len(ev_todo) > CAP_EVAL or len(b_todo) > CAP_TRAIN:
        sys.exit("SPEND CAP EXCEEDED — abort before billing")
    import httpx
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    cf = CACHE.open("a")

    async def one_eval(client, r):
        text = await acall(client, STRICT_ONE.format(problem=r["problem"],
                                                     answer=r["answer"]))
        j = H.parse_json(text) if text else None
        if valid_one(j):
            cf.write(json.dumps({"key": f"one|{md5(r['answer'])[:12]}",
                                 "verdict": j}) + "\n")
            cf.flush()

    async def one_batch(client, b):
        cases = "\n\n".join(f"CASE {i+1}\nPROBLEM: {r['problem']}\n\nANSWER {i+1}:\n"
                            f"{r['answer']}" for i, r in enumerate(b))
        text = await acall(client, STRICT_BATCH.format(k=len(b), cases=cases))
        j = H.parse_json(text) if text else None
        # parse_json returns dict from first {; for arrays try json direct
        if not isinstance(j, list):
            try:
                s = text[text.index("["):text.rindex("]") + 1]
                j = json.loads(s)
            except Exception:
                j = None
        if isinstance(j, list) and len(j) == len(b) and all(valid_one(x) for x in j):
            for r, v in zip(b, sorted(j, key=lambda x: x.get("idx", 0))):
                cf.write(json.dumps({"key": f"one|{md5(r['answer'])[:12]}",
                                     "verdict": {"coherent": v["coherent"],
                                                 "flaws": v["flaws"]}}) + "\n")
            cf.flush()

    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[one_eval(client, r) for r in ev_todo])
        await asyncio.gather(*[one_batch(client, b) for b in b_todo])
    cf.close()
    cache = load_cache()
    missing = [r for r in cleans if f"one|{md5(r['answer'])[:12]}" not in cache]
    if missing:
        sys.exit(f"COVERAGE INSUFFICIENT: {len(missing)} cleans unlabeled — rerun")
    flipped = sum(1 for r in cleans
                  if not cache[f"one|{md5(r['answer'])[:12]}"]["coherent"])
    print(f"RELABEL COMPLETE: {len(cleans)} cleans re-read under strict ruler, "
          f"{flipped} flipped to FLAGGED, {len(cleans)-flipped} survive as GROUNDED")


def rebuild():
    from run16_corpus import sft_row
    rows = [json.loads(l) for l in (D16 / "verifier_real.jsonl").open()]
    cache = load_cache()
    for r in rows:
        if r["coherent"]:
            v = cache.get(f"one|{md5(r['answer'])[:12]}")
            if v is None:
                sys.exit("missing relabel — run relabel first")
            r["coherent"] = v["coherent"]
            if not v["coherent"]:
                r["flaws"] = v["flaws"] or ["contains an ungrounded claim."]
    # LABELED SPLIT AMENDMENT (RUNBOOK16 16B, pre-v2-training): the strict
    # relabel leaves only 7 clean eval rows — too coarse to measure a 0.70 bar.
    # Move whole clean-bearing problems train->eval (deterministic md5 order)
    # until eval holds >= 20 strict cleans. v16B trains fresh from base, so no
    # row it trains on ever enters eval; problem-level integrity preserved.
    ev_clean = sum(1 for r in rows if r["split"] == "eval" and r["coherent"])
    moved = set()
    for key in sorted({r["split_key"] for r in rows
                       if r["split"] == "train" and r["coherent"]},
                      key=lambda k: hashlib.md5(k.encode()).hexdigest()):
        if ev_clean >= 20:
            break
        for r in rows:
            if r["split_key"] == key:
                r["split"] = "eval"
                if r["coherent"]:
                    ev_clean += 1
        moved.add(key)
    print(f"split amendment: {len(moved)} problems moved train->eval")
    tr = [r for r in rows if r["split"] == "train"]
    ev = [r for r in rows if r["split"] == "eval"]
    n_clean_tr = sum(1 for r in tr if r["coherent"])
    n_clean_ev = sum(1 for r in ev if r["coherent"])
    # synthetics: regenerate ONLY from still-clean train rows (a corruption of a
    # text that is itself flawed would carry a dirty GROUNDED-side twin premise)
    from run16_corpus import corrupt
    syn = []
    for r in tr:
        if r["coherent"]:
            syn.extend(corrupt(r))
    flawed_n = sum(1 for r in tr if not r["coherent"]) + len(syn)
    reps = max(1, round(flawed_n / max(1, n_clean_tr) * 0.6))
    train_sft = []
    for r in tr:
        k = reps if r["coherent"] else 1
        train_sft.extend([sft_row(r["problem"], r["answer"], r["coherent"],
                                  r["flaws"])] * k)
    train_sft += [sft_row(r["problem"], r["answer"], False, r["flaws"]) for r in syn]
    random.Random(162).shuffle(train_sft)
    (D16 / "verifier_train_v2.jsonl").write_text(
        "".join(json.dumps(x) + "\n" for x in train_sft))
    (D16 / "verifier_eval_v2.jsonl").write_text(
        "".join(json.dumps(sft_row(r["problem"], r["answer"], r["coherent"],
                                   r["flaws"])) + "\n" for r in ev))
    print(f"v2 train: {len(train_sft)} rows (clean train {n_clean_tr} x{reps}, "
          f"flawed real {sum(1 for r in tr if not r['coherent'])}, syn {len(syn)})")
    print(f"v2 eval : {len(ev)} rows ({n_clean_ev} clean / {len(ev)-n_clean_ev} flawed)")
    for f in ("verifier_train_v2.jsonl", "verifier_eval_v2.jsonl"):
        print(f"  {f}: md5 {hashlib.md5((D16/f).read_bytes()).hexdigest()}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args()
    if a.rebuild:
        rebuild()
    else:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("ANTHROPIC_API_KEY not set — source load_keys.sh")
        asyncio.run(relabel())
