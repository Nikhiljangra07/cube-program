"""
pilot8_passages.py — PILOT8 stage 1: passage selection.

Chunks the 6 source books (~1,100 words/chunk), samples 20 evenly-spaced chunks per book
(60 per lane), has DeepSeek V4 Pro score each 1-10 for lane density, keeps top 8 per lane.
Generator-family selects its own food; the Sonnet gate never sees passages.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/pilot8_passages.py

Writes data/pilot8/passages_F.json / passages_V.json (top 8, md5'd) + chunk_scores.jsonl.
"""
from __future__ import annotations
import asyncio, hashlib, json, os, re, sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
LIB = Path.home() / "Desktop/lora-corpus-source/english"
OUTD = ROOT / "data/pilot8"
MODEL = "deepseek/deepseek-v4-pro"
OR_URL = "https://openrouter.ai/api/v1/chat/completions"
KEY = os.environ.get("OPENROUTER_API_KEY", "")
SEM = asyncio.Semaphore(10)

BOOKS = {
    "F": [LIB / "diplomacy-and-war/clausewitz-on-war.txt",
          LIB / "diplomacy-and-war/thucydides-peloponnesian-war.txt",
          LIB / "greek-classics/plutarch-lives.txt"],
    "V": [LIB / "roman-classics/cicero-on-duties.txt",
          LIB / "political-philosophy/aristotle-nicomachean.txt",
          LIB / "economics/bagehot-lombard-street.txt"],
}
CHUNK_WORDS = 1100
PER_BOOK = 20
TOP_PER_LANE = 8

LANE_DEF = {
    "F": ("multi-step CONSEQUENCE reasoning: a move triggers a reaction, the reaction "
          "shifts the ground, the shift decides the endgame — chains of cause and effect "
          "projected several steps deep, second-order effects, how a choice's consequence "
          "lands two moves later"),
    "V": ("EXECUTION-REALISTIC reasoning: named mechanisms, real costs and resources, "
          "binding constraints, what actually breaks in practice and what covers it — "
          "reasoning that survives contact with reality, fitted to the particular case"),
}

PROMPT = """Score this passage from a classic text for ONE property only.

PROPERTY: density of {lane_def}

PASSAGE:
---
{chunk}
---

Score 1-10: 10 = nearly every paragraph exhibits the property intensely and could serve
as a structural exemplar of it; 5 = the property appears but diluted by narrative or
digression; 1 = absent. Judge the REASONING STRUCTURE on display, not the topic.

Return ONLY JSON: {{"score": n, "why": "<=12 words"}}"""


def chunks_of(path: Path):
    words = re.sub(r"\s+", " ", path.read_text(errors="ignore")).split(" ")
    # skip Gutenberg header/footer ~5% each end
    lo, hi = int(len(words) * 0.05), int(len(words) * 0.95)
    words = words[lo:hi]
    n = max(1, len(words) // CHUNK_WORDS)
    all_chunks = [" ".join(words[i * CHUNK_WORDS:(i + 1) * CHUNK_WORDS]) for i in range(n)]
    if len(all_chunks) <= PER_BOOK:
        return list(enumerate(all_chunks))
    step = len(all_chunks) / PER_BOOK
    return [(int(i * step), all_chunks[int(i * step)]) for i in range(PER_BOOK)]


async def score(client, lane, book, idx, chunk):
    p = PROMPT.format(lane_def=LANE_DEF[lane], chunk=chunk[:9000])
    async with SEM:
        for a in range(4):
            try:
                r = await client.post(OR_URL, headers={"Authorization": f"Bearer {KEY}"},
                                      json={"model": MODEL, "max_tokens": 2000, "temperature": 0.0,
                                            "messages": [{"role": "user", "content": p}]}, timeout=90)
                r.raise_for_status()
                msg = (r.json()["choices"][0]["message"]["content"] or "").strip()
                m = re.search(r"\{[^{}]*\}", msg)
                j = json.loads(m.group()) if m else None
                if j and isinstance(j.get("score"), int) and 1 <= j["score"] <= 10:
                    return {"lane": lane, "book": book.stem, "chunk_idx": idx,
                            "score": j["score"], "why": str(j.get("why", "")), "text": chunk}
            except Exception:
                await asyncio.sleep(2 * (a + 1))
    return None


async def main():
    if not KEY:
        sys.exit("OPENROUTER_API_KEY not set")
    OUTD.mkdir(parents=True, exist_ok=True)
    tasks = []
    async with httpx.AsyncClient() as client:
        for lane, books in BOOKS.items():
            for b in books:
                if not b.exists():
                    sys.exit(f"missing book: {b}")
                for idx, ch in chunks_of(b):
                    tasks.append(score(client, lane, b, idx, ch))
        print(f"{len(tasks)} chunks to score")
        results = [r for r in await asyncio.gather(*tasks) if r]
    print(f"{len(results)} scored")
    with (OUTD / "chunk_scores.jsonl").open("w") as f:
        for r in results:
            f.write(json.dumps({k: v for k, v in r.items() if k != "text"}) + "\n")
    for lane in ("F", "V"):
        pool = sorted([r for r in results if r["lane"] == lane],
                      key=lambda r: -r["score"])[:TOP_PER_LANE]
        out = {"lane": lane,
               "passages": [{"book": p["book"], "chunk_idx": p["chunk_idx"], "score": p["score"],
                             "md5": hashlib.md5(p["text"].encode()).hexdigest()[:12],
                             "text": p["text"]} for p in pool]}
        path = OUTD / f"passages_{lane}.json"
        path.write_text(json.dumps(out, indent=1))
        print(f"lane {lane}: top{TOP_PER_LANE} scores {[p['score'] for p in pool]} "
              f"books {sorted(set(p['book'] for p in pool))} -> {path}")


if __name__ == "__main__":
    asyncio.run(main())
