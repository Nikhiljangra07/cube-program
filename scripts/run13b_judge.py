"""
run13b_judge.py — RUN 13B judge session R: certification + cache (RUNBOOK13B).

The certifier prompt is BYTE-REUSED from run13_calibrate.py (program law: the
verdict instrument is quoted verbatim). Judge discipline: claude-sonnet-5, NO
temperature param, max_tokens 12000, retry-on-empty. Cache law (run 11): every
verdict cached keyed (arm, pid, attempt, md5(speech)) — reruns never re-bill.

Import surface: certify_batch(items) -> list of judge dicts (parallel, cached).
Each item: {arm, pid, attempt, problem, update, audit, read, motion, speech}.
Offline mode for dry runs: RUN13B_MOCK_JUDGE=1 returns deterministic canned
verdicts (never valid for a real session).
"""
from __future__ import annotations
import asyncio, hashlib, json, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "out/run13b/judge_cache.jsonl"
KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MOCK = os.environ.get("RUN13B_MOCK_JUDGE") == "1"
SEM_N = 4

# byte-reused from run13_calibrate.py (session Q) — the frozen instrument
PROMPT = """You are auditing the FINAL SPEECH of a multi-part reasoning relay for factual
fidelity. The segments below are the speech's only permitted sources. Be a strict critic.

PROBLEM (happened): {problem}
UPDATE (happened): {update}
AUDIT segment: {audit}
READ segment (a PREDICTION — none of it has happened): {read}
CURRENT PLAN segment (revised for the update): {motion}

FINAL SPEECH UNDER AUDIT:
{speech}

Judge ONLY fidelity and delivery, not strategy quality:
- coherent = false if the speech states any predicted event as having happened, uses any
  number absent from the sources, revives anything the UPDATE eliminated (except to note
  it is gone), or contradicts the sources. Otherwise true.
- flaws: list each violation in one short sentence (empty list if none).
- delivery: 1-5 — is it a readable, complete, decisive final answer (5 = excellent)?

Return ONLY JSON: {{"coherent": true/false, "flaws": ["..."], "delivery": N}}"""


def ckey(item):
    h = hashlib.md5(item["speech"].encode()).hexdigest()
    return f"{item['arm']}|{item['pid']}|{item['attempt']}|{h}"


def load_cache():
    if not CACHE.exists():
        return {}
    return {r["key"]: r["judge"] for r in map(json.loads, CACHE.open())}


def save_cache_line(key, judge):
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with CACHE.open("a") as f:
        f.write(json.dumps({"key": key, "judge": judge}) + "\n")


async def _judge_one(client, sem, item):
    async with sem:
        for a in range(4):
            try:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": KEY, "anthropic-version": "2023-06-01",
                             "content-type": "application/json"},
                    json={"model": "claude-sonnet-5", "max_tokens": 12000,
                          "messages": [{"role": "user", "content": PROMPT.format(
                              problem=item["problem"], update=item["update"],
                              audit=item["audit"], read=item["read"],
                              motion=item["motion"], speech=item["speech"])}]},
                    timeout=180)
                resp.raise_for_status()
                text = "".join(p.get("text", "") for p in resp.json().get("content", [])
                               if p.get("type") == "text")
                m = re.search(r"\{.*\}", text, re.S)
                if m:
                    j = json.loads(m.group())
                    if isinstance(j.get("coherent"), bool) and "delivery" in j:
                        return j
            except Exception:
                await asyncio.sleep(3 * (a + 1))
    return None


def _mock_judge(item):
    # deterministic offline stand-in: incoherent iff the speech contains the
    # token "MOCKFLAW"; used ONLY by the dry-run harness
    bad = "MOCKFLAW" in item["speech"]
    return {"coherent": not bad,
            "flaws": (["mock semantic flaw for dry-run"] if bad else []),
            "delivery": 4, "_mock": True}


def certify_batch(items):
    """Returns verdicts aligned with items; raises on any coverage gap
    (all-or-discard law). Cached verdicts are free and marked cached=True."""
    cache = load_cache()
    results = [None] * len(items)
    todo = []
    for i, it in enumerate(items):
        k = ckey(it)
        # mock verdicts must never serve a real session (and vice versa)
        if k in cache and bool(cache[k].get("_mock")) == MOCK:
            results[i] = {**cache[k], "cached": True}
        else:
            todo.append((i, it, k))
    if todo:
        if MOCK:
            fresh = [_mock_judge(it) for _, it, _ in todo]
        else:
            if not KEY:
                sys.exit("ANTHROPIC_API_KEY not set")
            import httpx

            async def run():
                sem = asyncio.Semaphore(SEM_N)
                async with httpx.AsyncClient() as client:
                    return await asyncio.gather(
                        *[_judge_one(client, sem, it) for _, it, _ in todo])
            fresh = asyncio.run(run())
        if any(v is None for v in fresh):
            sys.exit("SESSION R COVERAGE INCOMPLETE — all-or-discard: rerun this phase "
                     "(cached verdicts are kept; only missing ones re-bill).")
        for (i, it, k), v in zip(todo, fresh):
            save_cache_line(k, v)
            results[i] = {**v, "cached": False}
    return results
