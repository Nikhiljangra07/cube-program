"""
transform_gate.py — RUN 4: the TRANSFORMATION GATE (method 4, strong form).

Turns raw book pages (Clausewitz, data/book/book_pages_train.jsonl) into LANE-dense
training rows — first lane: FORESIGHT. Each page's strategic principle is re-rendered as
one concrete decision-scene in a rotating surface domain (skill-pure, surface-diverse:
the Physics-of-LMs multi-presentation rule). Output rows use the same {"messages":[...]}
shape as the book pages, so the ENTIRE downstream pipeline (loss_band_gate --per-token,
build_masked_dataset keep-0.6, train_mastery, heldout_nll, gen_threads) runs UNCHANGED.

Three-family design (judge-contamination guard, 2026-07-23 Nikhil's call on renderer):
  RENDERER = Kimi K2.6 via OpenRouter ($0.66/$3.41 per M — full book ~$2.50)
  GATE     = Gemini 2.5 Flash (cheap fidelity/anti-collapse check; PASS required)
  JUDGE    = Sonnet 5 (bench only — never writes training data)
Moonshot writes, Google gates, Anthropic judges: no model grades its own homework.

Lane emphasis, not exclusivity (run-3 narrowing-tax lesson): every scene must still
contain live options (multiplicity floor) and a directional close (decisiveness floor) —
foresight is the EMPHASIS (~70% of the reasoning mass), not the totality.

  source ~/Desktop/reasoningEngine/load_keys.sh   # GEMINI_API_KEY — never echo it
  python transform_gate.py --max-pages 5          # pilot
  python transform_gate.py                        # full render (~$5-6, 855 pages)

Resume-safe: pages already present in the output file are skipped (idempotent by
page_idx). Rejected renders are retried once with the gate's reason, then dropped + logged.
"""
from __future__ import annotations
import argparse, asyncio, json, os, re, sys
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "data/book/book_pages_train.jsonl"
OUT_DIR = ROOT / "data/lane_foresight"
RENDER_MODEL = "moonshotai/kimi-k2.6"   # via OpenRouter (no native Moonshot key in vault)
GATE_MODEL = "gemini-2.5-flash"
GEMINI_API = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"
OPENROUTER_API = "https://openrouter.ai/api/v1/chat/completions"

# Protagonist names rotate deterministically by page index — QC gate 3a found K2.6
# collapses to "Maya" for 67% of scenes when left to choose. Diversity is injected, not hoped for.
NAMES = [
    "Arjun", "Wei", "Fatima", "Tomasz", "Amara", "Diego", "Ingrid", "Kenji",
    "Priya", "Omar", "Sofia", "Dmitri", "Zainab", "Marcus", "Yuki", "Thabo",
    "Elena", "Rafael", "Noor", "Henrik", "Kavya", "Jamal", "Astrid", "Chen",
    "Leila", "Pavel", "Rosa", "Tariq", "Mei", "Stefan", "Adaeze", "Lucas",
    "Sana", "Viktor", "Carmen", "Hassan", "Freja", "Ravi", "Dalia", "Owen",
    "Nadia", "Koji", "Ines", "Bogdan", "Amina", "Mateo", "Sigrid", "Deepak",
    "Yasmin", "Anton", "Lucia", "Farid", "Hana", "Emil", "Zola", "Nikhil",
    "Aisha", "Petra", "Joaquin", "Salma", "Erik", "Devi", "Malik", "Greta",
]

# Surface domains rotate deterministically by page index — same principle, many worlds.
DOMAINS = [
    "a small business owner deciding on expansion",
    "a mid-career professional weighing a job change",
    "a startup founder handling a competitor's move",
    "a family negotiating an inheritance decision",
    "a city official managing an infrastructure crisis",
    "a sports team captain in a losing season",
    "a hospital administrator allocating scarce staff",
    "a farmer deciding what to plant amid volatile prices",
    "a union representative in contract talks",
    "an open-source maintainer facing a hostile fork",
    "a restaurant owner during a neighborhood downturn",
    "a graduate student choosing between advisors",
    "an immigrant family timing a move between countries",
    "a small-town mayor courting a big employer",
    "a freelance contractor with one dominant client",
    "a military officer on a peacekeeping deployment",
]

RENDER_PROMPT = """You are converting a passage from a classic treatise on strategy into ONE dense decision-scene for training a reasoning model. The target skill is FORESIGHT: projecting concrete consequences over time.

SOURCE PASSAGE:
---
{page}
---

ASSIGNED SURFACE DOMAIN: {domain}
PROTAGONIST NAME (use exactly this): {name}

Write a scene that embodies the passage's core strategic principle inside the assigned domain. Requirements:

SCENARIO (becomes the user turn, 80-140 words):
- The named protagonist ({name}), concrete stakes (numbers, deadlines, relationships), and ONE live decision point with 2-3 genuinely distinct options.
- No mention of the treatise, war theory, or any author. The principle must live in the situation, not be cited.

PROJECTION (becomes the assistant turn, 220-320 words):
- Project consequences of each live option across at least TWO distinct time horizons (immediate: days-weeks; medium: months; long: years where it matters).
- Include at least ONE second-order effect (a consequence of a consequence).
- Include ONE explicit "what would break this projection" condition.
- End with a directional close: which option the reasoning favors and the single condition that would flip it.
- Dense and concrete throughout: no filler, no hedging boilerplate, no "it depends" without saying on WHAT. Every sentence must carry a fact, a projection, or a tension.

Return ONLY valid JSON, no code fences:
{{"principle": "<the passage's core principle in one sentence>", "scenario": "<the user-turn text>", "projection": "<the assistant-turn text>"}}"""

GATE_PROMPT = """You are a strict quality gate for training data. Given a source passage and a generated scene, verdict PASS or FAIL.

SOURCE PASSAGE:
---
{page}
---

GENERATED principle: {principle}
GENERATED scenario: {scenario}
GENERATED projection: {projection}

FAIL if ANY of these hold:
1. FIDELITY: the stated principle is not actually present in the source passage, or the scene contradicts it.
2. CONCRETENESS: scenario lacks a named actor, concrete stakes, or a real decision point with distinct options.
3. FORESIGHT DENSITY: projection lacks two distinct time horizons, OR lacks a second-order effect, OR lacks a "what breaks this projection" condition.
4. COLLAPSE: generic advice-prose that could have been written without the source passage; meta-text ("this scene illustrates"); treatise/war-theory references leaking into a non-military domain.
5. CLOSE: no directional close (no option favored, or no flip condition).

Return ONLY valid JSON, no code fences:
{{"verdict": "PASS" or "FAIL", "reason": "<one sentence, empty if PASS>"}}"""

SYS = "You are a strategic advisor. Project the concrete consequences of the decision in front of you, then commit to a direction."


def parse_json(text: str):
    text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        i = text.find("{")
        if i < 0:
            return None
        depth, in_str, esc = 0, False, False
        for j, ch in enumerate(text[i:], start=i):
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"' and not esc:
                in_str = not in_str
            elif not in_str:
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[i:j + 1])
                        except json.JSONDecodeError:
                            return None
        return None


async def gemini(client: httpx.AsyncClient, model: str, prompt: str, temp: float) -> str | None:
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temp, "maxOutputTokens": 4096}}
    for attempt in range(3):
        try:
            r = await client.post(GEMINI_API.format(m=model), json=body,
                                  headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]},
                                  timeout=90)
            if r.status_code == 429 or r.status_code >= 500:
                await asyncio.sleep(4 * (attempt + 1))
                continue
            r.raise_for_status()
            parts = r.json()["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts)
        except Exception:
            await asyncio.sleep(4 * (attempt + 1))
    return None


async def openrouter(client: httpx.AsyncClient, model: str, prompt: str, temp: float) -> str | None:
    # reasoning disabled: K2.6 is a reasoning model and its thinking shares max_tokens —
    # without this, long renders come back truncated/empty (same trap as the Sonnet 5 judge).
    body = {"model": model, "temperature": temp, "max_tokens": 4096,
            "reasoning": {"enabled": False},
            "messages": [{"role": "user", "content": prompt}]}
    for attempt in range(3):
        try:
            r = await client.post(OPENROUTER_API, json=body,
                                  headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
                                  timeout=120)
            if r.status_code == 429 or r.status_code >= 500:
                await asyncio.sleep(4 * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception:
            await asyncio.sleep(4 * (attempt + 1))
    return None


async def one_page(client, sem, row, done_ids, out_f, rej_f, lock, counters):
    k = row["page_idx"]
    if k in done_ids:
        return
    page = row["messages"][2]["content"]
    domain = DOMAINS[k % len(DOMAINS)]
    name = NAMES[k % len(NAMES)]
    async with sem:
        feedback, reason = "", "render produced no parseable scene JSON"
        for attempt in range(2):
            raw = await openrouter(client, RENDER_MODEL,
                                   RENDER_PROMPT.format(page=page, domain=domain, name=name) + feedback, 0.9)
            scene = parse_json(raw) if raw else None
            if not scene or not all(scene.get(f) for f in ("principle", "scenario", "projection")):
                feedback = "\n\nPREVIOUS ATTEMPT was not valid JSON with all three fields. Fix that."
                continue
            n_words = len(scene["projection"].split())
            if n_words > 420:
                reason = f"projection too long ({n_words} words; max 420) — bloat, not density"
                feedback = f"\n\nPREVIOUS ATTEMPT FAILED: {reason}\nCompress to 220-320 words. Cut nothing concrete; cut everything else."
                continue
            g_raw = await gemini(client, GATE_MODEL, GATE_PROMPT.format(page=page, **scene), 0.0)
            g = parse_json(g_raw) if g_raw else None
            if g and g.get("verdict") == "PASS":
                out_row = {"messages": [
                    {"role": "system", "content": SYS},
                    {"role": "user", "content": scene["scenario"]},
                    {"role": "assistant", "content": scene["projection"]},
                ], "page_idx": k, "domain": domain, "principle": scene["principle"]}
                async with lock:
                    out_f.write(json.dumps(out_row) + "\n"); out_f.flush()
                    counters["pass"] += 1
                return
            reason = (g or {}).get("reason", "gate call failed")
            feedback = f"\n\nPREVIOUS ATTEMPT FAILED the quality gate: {reason}\nFix exactly that and re-render."
        async with lock:
            rej_f.write(json.dumps({"page_idx": k, "reason": reason}) + "\n"); rej_f.flush()
            counters["drop"] += 1


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pages", type=int, default=0, help="pilot cap; 0 = all")
    ap.add_argument("--concurrency", type=int, default=8)
    args = ap.parse_args()
    for k in ("GEMINI_API_KEY", "OPENROUTER_API_KEY"):
        if not os.environ.get(k):
            sys.exit(f"{k} not set — source the vault loader first.")

    rows = [json.loads(l) for l in SRC.open()]
    if args.max_pages:
        rows = rows[:args.max_pages]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "lane_pages_train.jsonl"
    done_ids = {json.loads(l)["page_idx"] for l in out_path.open()} if out_path.exists() else set()
    print(f"pages={len(rows)} already_done={len(done_ids)} renderer={RENDER_MODEL} gate={GATE_MODEL}")

    counters = {"pass": 0, "drop": 0}
    sem, lock = asyncio.Semaphore(args.concurrency), asyncio.Lock()
    with out_path.open("a") as out_f, (OUT_DIR / "rejected.jsonl").open("a") as rej_f:
        async with httpx.AsyncClient() as client:
            await asyncio.gather(*[one_page(client, sem, r, done_ids, out_f, rej_f, lock, counters)
                                   for r in rows])
    total = len(done_ids) + counters["pass"] + counters["drop"]
    print(json.dumps({"rendered_pass": counters["pass"], "dropped": counters["drop"],
                      "total_on_disk": len(done_ids) + counters["pass"],
                      "drop_rate_pct": round(100 * counters["drop"] / max(1, total), 1)}))


if __name__ == "__main__":
    asyncio.run(main())
