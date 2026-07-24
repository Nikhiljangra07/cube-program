"""
probe_grade.py — LOCAL: grade probe answers, blind to arm labels. Sonnet 5 native key.

For each (arm, probe, kind): the judge sees the principle (gold), the question, the answer,
and for manip the manip_key — never the arm name. 0-2 scale per PROBES.md rubric.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/probe_grade.py out/probe_answers_base.jsonl out/probe_answers_laneF.jsonl ...
Writes data/probes/probe_grades.json with per-arm means + per-probe detail.
"""
from __future__ import annotations
import asyncio, json, os, re, sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
PROBES = {r["id"]: r for r in
          (json.loads(l) for l in (ROOT / "data/probes/probes.jsonl").open())}
MODEL = "claude-sonnet-5"
KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SEM = asyncio.Semaphore(8)

RECALL_PROMPT = """Grade this answer 0-2 against the gold principle. Blind test — judge content only.

GOLD PRINCIPLE: {principle}

QUESTION: {q}

ANSWER: {a}

Scale: 0 = the principle is absent or contradicted; 1 = partially/adjacently stated (right
territory, missing the mechanism); 2 = the principle is correctly stated (paraphrase fine —
the MECHANISM must match, not the wording).

Return ONLY JSON: {{"score": 0|1|2, "why": "<one sentence>"}}"""

MANIP_PROMPT = """Grade this answer 0-2 against the grading key. Blind test — judge content only.

SCENARIO QUESTION: {q}

GRADING KEY (which path is correct and why): {key}

UNDERLYING PRINCIPLE: {principle}

ANSWER: {a}

Scale: 0 = picks the wrong path, or no path, or reasoning contradicts the key's mechanism;
1 = right path but generic/weak justification (doesn't use the principle's mechanism);
2 = right path AND the stated consequence matches the key's mechanism.

Return ONLY JSON: {{"score": 0|1|2, "why": "<one sentence>"}}"""


def parse_json(text):
    m = re.search(r"\{.*\}", text, re.S)
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
                                      json={"model": MODEL, "max_tokens": 6000,
                                            "messages": [{"role": "user", "content": prompt}]},
                                      timeout=120)
                r.raise_for_status()
                d = r.json()
                text = "".join(p.get("text", "") for p in d.get("content", [])
                               if p.get("type") == "text").strip()
                j = parse_json(text)
                if j and j.get("score") in (0, 1, 2):
                    return j
            except Exception:
                await asyncio.sleep(2 * (a + 1))
    return None


async def main():
    if not KEY:
        sys.exit("ANTHROPIC_API_KEY not set")
    files = sys.argv[1:]
    if not files:
        sys.exit("usage: probe_grade.py <probe_answers_*.jsonl> ...")
    results = {}
    async with httpx.AsyncClient() as client:
        for fp in files:
            label = re.search(r"probe_answers_(.+)\.jsonl", fp).group(1)
            rows = [json.loads(l) for l in open(fp)]
            detail = []

            async def one(rec):
                p = PROBES[rec["id"]]
                rj = await call(client, RECALL_PROMPT.format(
                    principle=p["principle"], q=p["recall_q"], a=rec["recall"]))
                mj = await call(client, MANIP_PROMPT.format(
                    q=p["manip_q"], key=p["manip_key"], principle=p["principle"],
                    a=rec["manip"]))
                detail.append({"id": rec["id"],
                               "recall": rj["score"] if rj else None,
                               "recall_why": rj["why"] if rj else "JUDGE FAIL",
                               "manip": mj["score"] if mj else None,
                               "manip_why": mj["why"] if mj else "JUDGE FAIL"})

            await asyncio.gather(*[one(r) for r in rows])
            rec_ok = [d["recall"] for d in detail if d["recall"] is not None]
            man_ok = [d["manip"] for d in detail if d["manip"] is not None]
            results[label] = {
                "recall_mean": round(sum(rec_ok) / len(rec_ok), 3) if rec_ok else None,
                "manip_mean": round(sum(man_ok) / len(man_ok), 3) if man_ok else None,
                "n_recall": len(rec_ok), "n_manip": len(man_ok),
                "detail": sorted(detail, key=lambda d: d["id"]),
            }
            print(f"{label:10s} recall={results[label]['recall_mean']} "
                  f"manip={results[label]['manip_mean']} "
                  f"(n={len(rec_ok)}/{len(man_ok)})", flush=True)

    outp = ROOT / "data/probes/probe_grades.json"
    outp.write_text(json.dumps(results, indent=2))
    print(f"\nWROTE {outp}")
    ks = [k for k in results if k != "keep100"]
    if "keep100" in results:
        print("\n--- READ (PROBES.md frozen criteria, Δ vs keep100) ---")
        k = results["keep100"]
        for label in ks:
            r = results[label]
            dr = round(r["recall_mean"] - k["recall_mean"], 3)
            dm = round(r["manip_mean"] - k["manip_mean"], 3)
            stor = "STORAGE" if dr >= 0.30 else "no-storage"
            use = "USABILITY" if dm >= 0.30 else "no-usability"
            print(f"{label:10s} Δrecall={dr:+.3f} ({stor})  Δmanip={dm:+.3f} ({use})")
        if "laneF" in results:
            r = results["laneF"]
            dr = r["recall_mean"] - k["recall_mean"]; dm = r["manip_mean"] - k["manip_mean"]
            if dr >= 0.30 and dm < 0.30:
                v = "PHOTOGRAPH — stored but not usable -> multi-angle 4b indicated"
            elif dr < 0.30 and dm < 0.30:
                v = "NOT STORED — arrangement/exposure issue, read RUN-6 sweep first"
            else:
                v = "STORED AND USABLE — bench shortfall is transfer -> capacity story"
            print(f"[laneF verdict] {v}")


if __name__ == "__main__":
    asyncio.run(main())
