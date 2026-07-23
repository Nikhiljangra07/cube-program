"""
verify_renderer.py — RUN-4 PRE-FLIGHT: which renderer serves the transformation gate best,
Kimi K2.6 or Kimi K3? (Nikhil, 2026-07-23: "full precision, no rush — verify again.")

Protocol (frozen before running):
  1. Render pages 0-19 of the Clausewitz book with BOTH models (pages 0-4 reuse the
     existing pilots; 5-19 rendered fresh here). Same prompts, same gate, same length guard.
  2. Every paired page is judged blind by TWO judge families — Gemini 2.5 Pro and
     Claude Sonnet 5 — each judging TWICE with A/B positions swapped (4 verdicts/page).
     Both candidates are Moonshot models, so neither judge has a family in the race.
  3. Criteria: concreteness, consequence-chain depth, non-genericness, density.
     "Ignore length; longer is not better."
  4. Read: per-judge tallies + position-consistency. A page counts for a model only if
     that model wins BOTH orders under that judge (position-consistent win); split
     verdicts count as ties. Overall verdict = pooled position-consistent wins.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python verify_renderer.py            # renders what's missing, then judges, ~$4 all-in
"""
from __future__ import annotations
import asyncio, json, os, random, re, sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
import transform_gate as TG

ROOT = Path(__file__).resolve().parent.parent
LANE = ROOT / "data/lane_foresight"
N_PAGES = 20
MODELS = {"K2.6": "moonshotai/kimi-k2.6", "K3": "moonshotai/kimi-k3"}
PILOT = {"K2.6": LANE / "pilot_k26.jsonl", "K3": LANE / "pilot_k3.jsonl"}

JUDGE_PROMPT = """You are comparing two candidate training examples for teaching a small model FORESIGHT (consequence projection). Same source situation, two renderings.

CANDIDATE A:
scenario: {sa}
projection: {pa}

CANDIDATE B:
scenario: {sb}
projection: {pb}

Judge ONLY on: (1) concreteness (specific numbers, names, stakes), (2) depth of consequence chains (second-order effects, distinct time horizons), (3) non-genericness (could NOT have been written without a real strategic principle behind it), (4) density (no filler sentence). Ignore length; longer is not better.

Return ONLY JSON: {{"winner": "A" or "B" or "TIE", "reason": "<one sentence>"}}"""


async def render_missing(client, model_key):
    """Render pages 0..N_PAGES-1 with one model into its pilot file (resume by page_idx)."""
    path = PILOT[model_key]
    done = {json.loads(l)["page_idx"] for l in path.open()} if path.exists() else set()
    rows = [json.loads(l) for l in (ROOT / "data/book/book_pages_train.jsonl").open()][:N_PAGES]
    todo = [r for r in rows if r["page_idx"] not in done]
    if not todo:
        return 0
    sem = asyncio.Semaphore(4)
    n_ok = 0
    lock = asyncio.Lock()

    async def one(row):
        nonlocal n_ok
        k = row["page_idx"]
        page = row["messages"][2]["content"]
        domain = TG.DOMAINS[k % len(TG.DOMAINS)]
        async with sem:
            feedback = ""
            for _ in range(2):
                raw = await TG.openrouter(client, MODELS[model_key],
                                          TG.RENDER_PROMPT.format(page=page, domain=domain) + feedback, 0.9)
                scene = TG.parse_json(raw) if raw else None
                if not scene or not all(scene.get(f) for f in ("principle", "scenario", "projection")):
                    feedback = "\n\nPREVIOUS ATTEMPT was not valid JSON with all three fields. Fix that."
                    continue
                if len(scene["projection"].split()) > 420:
                    feedback = "\n\nPREVIOUS ATTEMPT too long. Compress to 220-320 words; cut nothing concrete."
                    continue
                g_raw = await TG.gemini(client, TG.GATE_MODEL, TG.GATE_PROMPT.format(page=page, **scene), 0.0)
                g = TG.parse_json(g_raw) if g_raw else None
                if g and g.get("verdict") == "PASS":
                    out = {"messages": [
                        {"role": "system", "content": TG.SYS},
                        {"role": "user", "content": scene["scenario"]},
                        {"role": "assistant", "content": scene["projection"]},
                    ], "page_idx": k, "domain": domain, "principle": scene["principle"]}
                    async with lock:
                        with path.open("a") as f:
                            f.write(json.dumps(out) + "\n")
                        n_ok += 1
                    return
            print(f"  [{model_key}] page {k}: DROPPED after retries", flush=True)

    await asyncio.gather(*[one(r) for r in todo])
    return n_ok


async def gemini_judge(client, prompt):
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.0, "maxOutputTokens": 16384}}
    for att in range(4):
        try:
            r = await client.post(TG.GEMINI_API.format(m="gemini-2.5-pro"), json=body,
                                  headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, timeout=180)
            d = r.json()
            parts = d.get("candidates", [{}])[0].get("content", {}).get("parts")
            if not parts:
                await asyncio.sleep(15 * (att + 1)); continue
            return TG.parse_json("".join(p.get("text", "") for p in parts))
        except Exception:
            await asyncio.sleep(15 * (att + 1))
    return None


async def sonnet_judge(client, prompt):
    body = {"model": "claude-sonnet-5", "max_tokens": 12000,
            "messages": [{"role": "user", "content": prompt}]}
    for att in range(4):
        try:
            r = await client.post("https://api.anthropic.com/v1/messages", json=body,
                                  headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                                           "anthropic-version": "2023-06-01"}, timeout=240)
            if r.status_code in (429,) or r.status_code >= 500:
                await asyncio.sleep(20 * (att + 1)); continue
            r.raise_for_status()
            txt = "".join(b.get("text", "") for b in r.json()["content"] if b.get("type") == "text")
            if not txt.strip():
                await asyncio.sleep(10); continue
            return TG.parse_json(txt)
        except Exception:
            await asyncio.sleep(20 * (att + 1))
    return None


async def main():
    for k in ("GEMINI_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY"):
        if not os.environ.get(k):
            sys.exit(f"{k} not set — source the vault loader first.")
    async with httpx.AsyncClient() as client:
        print("=== RENDER missing pages", flush=True)
        for mk in MODELS:
            n = await render_missing(client, mk)
            print(f"  {mk}: +{n} new renders", flush=True)

        a = {json.loads(l)["page_idx"]: json.loads(l) for l in PILOT["K2.6"].open()}
        b = {json.loads(l)["page_idx"]: json.loads(l) for l in PILOT["K3"].open()}
        pages = sorted(set(a) & set(b))
        print(f"=== JUDGE {len(pages)} paired pages x 2 judges x 2 orders", flush=True)

        results = []  # (page, judge, order, winner_model)

        async def judge_one(pg, judge_name, judge_fn, order):
            r26, r3 = a[pg], b[pg]
            first, second = (("K2.6", r26), ("K3", r3)) if order == 0 else (("K3", r3), ("K2.6", r26))
            prompt = JUDGE_PROMPT.format(
                sa=first[1]["messages"][1]["content"], pa=first[1]["messages"][2]["content"],
                sb=second[1]["messages"][1]["content"], pb=second[1]["messages"][2]["content"])
            v = await judge_fn(client, prompt)
            if not v:
                return (pg, judge_name, order, None)
            w = v.get("winner")
            name = "TIE" if w == "TIE" else (first[0] if w == "A" else second[0])
            return (pg, judge_name, order, name)

        sem = asyncio.Semaphore(3)

        async def guarded(coro_args):
            async with sem:
                res = await judge_one(*coro_args)
                print(f"  page {res[0]:>2} {res[1]:>7} order{res[2]}: {res[3]}", flush=True)
                return res

        tasks = [(pg, jn, jf, o) for pg in pages
                 for jn, jf in (("gemini", gemini_judge), ("sonnet", sonnet_judge))
                 for o in (0, 1)]
        results = await asyncio.gather(*[guarded(t) for t in tasks])

    # Position-consistent read: a judge's vote on a page counts only if the same model
    # wins BOTH orders; otherwise it's a tie (position bias or genuine parity).
    from collections import defaultdict
    votes = defaultdict(dict)
    for pg, jn, order, name in results:
        votes[(pg, jn)][order] = name
    tally = {"K2.6": 0, "K3": 0, "TIE": 0, "no-verdict": 0}
    per_judge = {"gemini": {"K2.6": 0, "K3": 0, "TIE": 0}, "sonnet": {"K2.6": 0, "K3": 0, "TIE": 0}}
    for (pg, jn), o in votes.items():
        w0, w1 = o.get(0), o.get(1)
        if w0 is None or w1 is None:
            tally["no-verdict"] += 1
        elif w0 == w1 and w0 in ("K2.6", "K3"):
            tally[w0] += 1; per_judge[jn][w0] += 1
        else:
            tally["TIE"] += 1; per_judge[jn]["TIE"] += 1
    out = {"pages": len(pages), "pooled_position_consistent": tally, "per_judge": per_judge}
    print(json.dumps(out, indent=2))
    (ROOT / "out/renderer_verification.json").write_text(json.dumps(
        {"results": [{"page": p, "judge": j, "order": o, "winner": w} for p, j, o, w in results],
         "summary": out}, indent=2))
    print("WROTE out/renderer_verification.json")


if __name__ == "__main__":
    asyncio.run(main())
