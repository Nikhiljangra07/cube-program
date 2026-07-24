"""
build_probes.py — Test 2: the recall-vs-manipulation probe sets (photograph vs usable
knowledge). LOCAL, no GPU. Judge/drafter = Sonnet 5 via NATIVE Anthropic key.

Design (frozen in PROBES.md):
- 24 principles stratified-sampled across lane_pages_train.jsonl page_idx range
  (843 foresight-lane scenes, each carrying the Clausewitz principle it was rendered from).
- Per principle, Sonnet 5 drafts:
    RECALL probe  — direct doctrine question; answering = stating the principle. Must not
                    mention any scene surface (names, companies) and must not itself contain
                    the principle's key clause.
    MANIP probe   — novel two-path decision scenario whose correct resolution REQUIRES the
                    principle's mechanism; the probe must not state the principle. Asks for
                    choice + consequence-based why.
- Code validation: JSON schema, length bounds, n-gram leakage check (no 5-gram of the
  principle text may appear in either probe), scene-name ban list.
- Output: data/probes/probes.jsonl (24 rows x {id, page_idx, principle, recall_q, manip_q})
  + a flat review file for human readback.

  source ~/Desktop/reasoningEngine/load_keys.sh   # loads ANTHROPIC_API_KEY (never echo)
  python scripts/build_probes.py
"""
from __future__ import annotations
import json, os, random, re, sys, time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
LANE = ROOT / "data/lane_foresight/lane_pages_train.jsonl"
OUTD = ROOT / "data/probes"
N_PROBES = 24
MODEL = "claude-sonnet-5"
KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# scene-surface names that must never appear in probes (transform-gate injection pool leak guard)
BANNED_SURFACE = re.compile(
    r"\b(Priya|Okonkwo|Meridian|Voss|Chen|Marta|Anya|Elena|Dmitri|Ingrid|Kwame|Yuki|Rohan"
    r"|Amara|Santiago|Freya|Tariq|Mei|Zainab|Bjorn|Leila|Kenji|Aisha|Mateo|Nadia)\b", re.I)

PROMPT = """You are building a precise evaluation probe pair from one strategic principle.

PRINCIPLE (extracted from a classic treatise on war/strategy):
{principle}

Produce exactly two probes as JSON:

1. "recall_q" — a direct doctrine question such that correctly answering it means STATING
   this principle. Phrase it as a question about strategic theory (you may say "in classical
   strategic theory" or "according to Clausewitzian doctrine"). It must NOT contain the
   principle's own key clauses (the answer must not be embedded in the question). One
   sentence, max 35 words.

2. "manip_q" — a NOVEL concrete decision scenario (business, personal, or institutional —
   NOT military) with two named paths (Path 1 / Path 2), where picking correctly REQUIRES
   applying this principle's mechanism. The scenario must NOT state the principle or use its
   distinctive vocabulary. End with: "Which path, and what happens if you choose wrong?"
   Max 110 words. The wrong path must be superficially attractive.

Also include "manip_key" — one sentence: which path is correct and the principle-derived
consequence of the wrong one (this is the grading key, never shown to the tested model).

Return ONLY JSON: {{"recall_q": "...", "manip_q": "...", "manip_key": "..."}}"""


def sonnet(prompt: str, retries: int = 4) -> str | None:
    for a in range(retries):
        try:
            r = httpx.post("https://api.anthropic.com/v1/messages",
                           headers={"x-api-key": KEY, "anthropic-version": "2023-06-01",
                                    "content-type": "application/json"},
                           json={"model": MODEL, "max_tokens": 8000,
                                 "messages": [{"role": "user", "content": prompt}]},
                           timeout=120)
            r.raise_for_status()
            d = r.json()
            text = "".join(p.get("text", "") for p in d.get("content", [])
                           if p.get("type") == "text").strip()
            if text:
                return text
        except Exception as e:
            print(f"  [retry {a}: {type(e).__name__}]", flush=True)
            time.sleep(2 * (a + 1))
    return None


def parse_json(text: str) -> dict | None:
    m = re.search(r"\{", text)
    if not m:
        return None
    depth, i, in_str, esc = 0, m.start(), False, False
    for j in range(m.start(), len(text)):
        c = text[j]
        if esc: esc = False; continue
        if c == "\\": esc = True; continue
        if c == '"': in_str = not in_str; continue
        if in_str: continue
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[i:j + 1])
                except Exception:
                    return None
    return None


def ngrams(text: str, n: int = 5) -> set[tuple]:
    ws = re.findall(r"[a-z']+", text.lower())
    return {tuple(ws[i:i + n]) for i in range(len(ws) - n + 1)}


def validate(row: dict, principle: str) -> list[str]:
    errs = []
    for k in ("recall_q", "manip_q", "manip_key"):
        if not isinstance(row.get(k), str) or len(row[k]) < 20:
            errs.append(f"{k} missing/short")
    if errs:
        return errs
    if len(row["recall_q"].split()) > 45: errs.append("recall_q too long")
    if len(row["manip_q"].split()) > 140: errs.append("manip_q too long")
    leak = ngrams(principle)
    if leak & ngrams(row["recall_q"]): errs.append("principle 5-gram leaked into recall_q")
    if leak & ngrams(row["manip_q"]): errs.append("principle 5-gram leaked into manip_q")
    for k in ("recall_q", "manip_q"):
        m = BANNED_SURFACE.search(row[k])
        if m: errs.append(f"scene surface name '{m.group()}' in {k}")
    if "path 1" not in row["manip_q"].lower() or "path 2" not in row["manip_q"].lower():
        errs.append("manip_q missing Path 1/Path 2")
    return errs


def main():
    if not KEY:
        sys.exit("ANTHROPIC_API_KEY not set — source load_keys.sh first")
    rows = [json.loads(l) for l in LANE.open()]
    # stratified: sort by page_idx, take the longest principle in each of 24 equal buckets
    rows.sort(key=lambda r: r["page_idx"])
    buckets = [rows[i * len(rows) // N_PROBES:(i + 1) * len(rows) // N_PROBES]
               for i in range(N_PROBES)]
    picks = [max(b, key=lambda r: len(r.get("principle", ""))) for b in buckets if b]
    print(f"{len(picks)} principles picked (stratified across page_idx 0..{rows[-1]['page_idx']})")

    OUTD.mkdir(parents=True, exist_ok=True)
    out, review = [], []
    for i, r in enumerate(picks):
        principle = r["principle"].strip()
        got = None
        for attempt in range(3):
            text = sonnet(PROMPT.format(principle=principle))
            j = parse_json(text or "")
            if not j:
                print(f"[{i:02d}] parse fail, attempt {attempt}"); continue
            errs = validate(j, principle)
            if errs:
                print(f"[{i:02d}] invalid ({'; '.join(errs)}), attempt {attempt}"); continue
            got = j; break
        if not got:
            print(f"[{i:02d}] GIVING UP — probe dropped"); continue
        row = {"id": f"P{i:02d}", "page_idx": r["page_idx"], "principle": principle,
               "recall_q": got["recall_q"], "manip_q": got["manip_q"],
               "manip_key": got["manip_key"]}
        out.append(row)
        review.append(f"== {row['id']} (page {row['page_idx']})\nPRINCIPLE: {principle}\n"
                      f"RECALL: {row['recall_q']}\nMANIP: {row['manip_q']}\n"
                      f"KEY: {row['manip_key']}\n")
        print(f"[{i:02d}] ok", flush=True)

    with (OUTD / "probes.jsonl").open("w") as f:
        for row in out:
            f.write(json.dumps(row) + "\n")
    (OUTD / "probes_review.txt").write_text("\n".join(review))
    print(f"\nWROTE {len(out)} probe pairs -> {OUTD}/probes.jsonl (+ probes_review.txt)")


if __name__ == "__main__":
    main()
