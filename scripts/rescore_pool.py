"""
rescore_pool.py — RUN 7 curation: blind 1-10 re-scoring of the 964-problem v5 pool.

The original gate scores are 1-5 integers truncated by the pass gate (multiplicity all-5,
foresight 3/4 only) — too coarse to carve lane subsets with real contrast. This pass
re-scores every problem's 4 pos_threads as a set on a 1-10 scale, three lanes only
(the carveable ones): foresight, distinctness, viability. Judge = Sonnet 5, blind,
single pass, one call per problem.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/rescore_pool.py
Writes data/faces/rescored.jsonl: original row + "rescore" {foresight, distinctness,
viability} on 1-10. Non-destructive; resume-safe by problem hash.
"""
from __future__ import annotations
import asyncio, hashlib, json, os, re, sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
SRC = [
    Path.home() / "Desktop/divergence-formula/corpus_run/corpus_v5_train/passers.jsonl",
    Path.home() / "Desktop/divergence-formula/corpus_run/corpus_v5_topup/passers.jsonl",
]
OUTD = ROOT / "data/faces"
OUT = OUTD / "rescored.jsonl"
MODEL = "claude-sonnet-5"
KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SEM = asyncio.Semaphore(8)

PROMPT = """Score this set of 4 candidate responses to a decision problem. Use the FULL 1-10
range — you are re-scoring an already-decent pool, so differentiate aggressively: 5-6 is
the pool's typical row, 9-10 only for standouts, 1-4 for weak-for-this-pool.

PROBLEM: {problem}

RESPONSES:
{threads}

Score the SET (not each response) on exactly three dimensions:
- foresight (1-10): do responses project concrete downstream consequences, second-order
  effects, time horizons, failure conditions?
- distinctness (1-10): are the 4 responses genuinely different strategies (not one idea
  reworded)? Do they occupy different regions of the solution space?
- viability (1-10): are the responses executable as stated — specific, resourced,
  realistic — rather than directionally correct hand-waving?

Return ONLY JSON: {{"foresight": n, "distinctness": n, "viability": n}}"""


def pid(problem: str) -> str:
    return hashlib.md5(problem.encode()).hexdigest()[:12]


def parse_json(text):
    m = re.search(r"\{[^{}]*\}", text)
    if not m:
        return None
    try:
        return json.loads(m.group())
    except Exception:
        return None


async def call(client, prompt, retries=4):
    async with SEM:
        for a in range(retries):
            try:
                r = await client.post("https://api.anthropic.com/v1/messages",
                                      headers={"x-api-key": KEY,
                                               "anthropic-version": "2023-06-01",
                                               "content-type": "application/json"},
                                      json={"model": MODEL, "max_tokens": 4000,
                                            "messages": [{"role": "user", "content": prompt}]},
                                      timeout=120)
                r.raise_for_status()
                d = r.json()
                text = "".join(p.get("text", "") for p in d.get("content", [])
                               if p.get("type") == "text").strip()
                j = parse_json(text)
                if j and all(isinstance(j.get(k), int) and 1 <= j[k] <= 10
                             for k in ("foresight", "distinctness", "viability")):
                    return j
            except Exception:
                await asyncio.sleep(2 * (a + 1))
    return None


async def main():
    if not KEY:
        sys.exit("ANTHROPIC_API_KEY not set")
    rows = []
    for p in SRC:
        rows += [json.loads(l) for l in p.open()]
    print(f"{len(rows)} problems loaded from {len(SRC)} pools")
    OUTD.mkdir(parents=True, exist_ok=True)
    done = set()
    if OUT.exists():
        for l in OUT.open():
            done.add(json.loads(l)["pid"])
        print(f"resume: {len(done)} already scored")
    todo = [r for r in rows if pid(r["problem"]) not in done]

    out_f = OUT.open("a")
    n_ok = n_fail = 0
    lock = asyncio.Lock()

    async with httpx.AsyncClient() as client:
        async def one(r):
            nonlocal n_ok, n_fail
            threads = "\n\n".join(f"[{i+1}] {t}" for i, t in enumerate(r["pos_threads"]))
            j = await call(client, PROMPT.format(problem=r["problem"], threads=threads))
            async with lock:
                if j:
                    out_f.write(json.dumps({"pid": pid(r["problem"]),
                                            "source": r["source"], "setting": r.get("setting"),
                                            "problem": r["problem"],
                                            "orig_judge": r["pos_judge"],
                                            "rescore": j}) + "\n")
                    out_f.flush()
                    n_ok += 1
                else:
                    n_fail += 1
                if (n_ok + n_fail) % 50 == 0:
                    print(f"  {n_ok} ok / {n_fail} fail", flush=True)

        await asyncio.gather(*[one(r) for r in todo])
    out_f.close()
    print(f"DONE: {n_ok} scored, {n_fail} failed -> {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
