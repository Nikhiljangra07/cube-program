"""
run11_nerfs.py — RUN 11 stage 0: 16 NERF twins for Eval D (RUNBOOK11 frozen).

For each of the 16 frozen twin base problems (Eval C, md5 ea0707a5), DeepSeek
authors ONE strictly-weakening dated update (resource removed / friction added /
deadline tightened — exactly one change, no silver linings). Twin construction is
DETERMINISTIC: the nerf is appended as one UPDATE inventory line to the
byte-identical base problem — same law as the boost twins (run10_inventory.py).

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/run11_nerfs.py

Writes data/run11/nerf_twins.jsonl (16 rows: problem/base_index/nerf), md5-frozen.
"""
from __future__ import annotations
import asyncio, hashlib, json, os, re, sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
D10 = ROOT / "data/run10"
D11 = ROOT / "data/run11"
OUT = D11 / "nerf_twins.jsonl"
MODEL = "deepseek/deepseek-v4-pro"
OR_URL = "https://openrouter.ai/api/v1/chat/completions"
KEY = os.environ.get("OPENROUTER_API_KEY", "")
SEM = asyncio.Semaphore(8)
N = 16

PROMPT = (
    "Below is a decision problem with an explicit inventory of what the actor holds.\n\n"
    "PROBLEM: {problem}\n\n"
    "Write ONE sentence, phrased as a dated UPDATE, that STRICTLY WEAKENS the actor's "
    "position in exactly ONE way — either removes/reduces one concrete inventory item "
    "(money, a person's availability, an approval) or adds one new named friction "
    "(a cost increase, a delay, a veto, a deadline moved EARLIER). Rules: exactly one "
    "change; no silver linings or compensations; concrete numbers where natural; must "
    "target something actually in the inventory or timeline; no crimes, no melodrama.\n"
    'Return STRICT JSON only: {{"nerf":"<the update sentence>"}}'
)


async def gen(client, i, problem):
    async with SEM:
        for a in range(5):
            try:
                r = await client.post(OR_URL, headers={"Authorization": f"Bearer {KEY}"},
                                      json={"model": MODEL, "max_tokens": 8000, "temperature": 0.8,
                                            "messages": [{"role": "user",
                                                          "content": PROMPT.format(problem=problem)}]},
                                      timeout=180)
                r.raise_for_status()
                msg = (r.json()["choices"][0]["message"]["content"] or "").strip()
                m = re.search(r"\{.*\}", msg, re.S)
                j = json.loads(m.group()) if m else None
                if j and isinstance(j.get("nerf"), str) and len(j["nerf"].strip()) > 20:
                    return i, j["nerf"].strip()
            except Exception:
                await asyncio.sleep(2 * (a + 1))
    return i, None


def render_twin(base_problem, nerf):
    # same deterministic law as boost twins: one appended UPDATE inventory item
    return base_problem.replace(" ON THE TABLE:", f" (7) UPDATE: {nerf} ON THE TABLE:", 1)


async def main():
    if not KEY:
        sys.exit("OPENROUTER_API_KEY not set")
    D11.mkdir(parents=True, exist_ok=True)
    inv = [json.loads(l) for l in (D10 / "inventory_problems.jsonl").open()]
    bases = [(i, inv[i]["problem"]) for i in range(N)]
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[gen(client, i, p) for i, p in bases])
    ok = {i: nerf for i, nerf in results if nerf}
    print(f"{len(ok)}/{N} nerfs generated")
    if len(ok) < N:
        sys.exit(f"INCOMPLETE — missing {[i for i in range(N) if i not in ok]}; rerun")
    with OUT.open("w") as f:
        for i in range(N):
            f.write(json.dumps({"problem": render_twin(inv[i]["problem"], ok[i]),
                                "base_index": i, "nerf": ok[i]}) + "\n")
    # determinism byte-check
    rows = [json.loads(l) for l in OUT.open()]
    for r in rows:
        expect = render_twin(inv[r["base_index"]]["problem"], r["nerf"])
        assert r["problem"] == expect, f"TWIN MISMATCH {r['base_index']}"
    print(f"determinism: {len(rows)}/16 OK")
    print(f"FROZEN: {OUT} md5 {hashlib.md5(OUT.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    asyncio.run(main())
