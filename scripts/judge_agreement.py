"""
judge_agreement.py — MINI-STUDY (MINISTUDY_JUDGE.md, frozen): second-family
judge validity read. Gemini 2.5 Pro via OpenRouter re-reads all 48 holdout
answers with the byte-identical STRICT_ONE ruler; agreement + kappa vs the
cached Sonnet verdicts. Local only, no GPU, no Anthropic spend.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/judge_agreement.py
"""
from __future__ import annotations
import asyncio, hashlib, json, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run21_score import RULERS  # noqa: E402
from ruler_t import classify  # noqa: E402
import head2head_v5 as H  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out/agreement"
CACHE = OUT / "gemini_cache.jsonl"
PROBS = ROOT / "data/run22/holdout_problems.jsonl"
MODEL = "google/gemini-2.5-pro"
CAP = 60


def md5(t):
    return hashlib.md5(t.encode()).hexdigest()


def valid(j):
    return isinstance(j, dict) and isinstance(j.get("coherent"), bool) \
        and isinstance(j.get("flaws"), list)


def rulert_clean(v):
    return v["coherent"] or all(
        classify(f if isinstance(f, str) else str(f)) == "ADD"
        for f in v.get("flaws", []))


def load_rows():
    rows = [json.loads(l) for l in (ROOT / "out/run22/holdout22_out.jsonl").open()]
    rows += [json.loads(l) for l in (ROOT / "out/run23/thinking23_out.jsonl").open()]
    assert len(rows) == 48, f"expected 48 answers, got {len(rows)}"
    return rows


def sonnet_verdicts(rows):
    cache = {}
    for p in (ROOT / "out/run22/judge_cache.jsonl",
              ROOT / "out/run23/judge_cache.jsonl"):
        for l in p.open():
            rec = json.loads(l)
            if not rec.get("_mock"):
                cache[rec["key"]] = rec["verdict"]
    out = {}
    for r in rows:
        pre = "r23" if r["arm"] == "R" else "r22"
        out[(r["arm"], r["pid"])] = cache[f"{pre}|one|{md5(r['answer'])[:12]}"]
    return out


def gem_cache():
    c = {}
    if CACHE.exists():
        for l in CACHE.open():
            rec = json.loads(l)
            c[rec["key"]] = rec["verdict"]
    return c


async def judge(rows, probs):
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key.strip():
        sys.exit("OPENROUTER_API_KEY missing — source load_keys.sh")
    cache = gem_cache()
    todo = [r for r in rows if f"g|{md5(r['answer'])[:12]}" not in cache]
    print(f"gemini: {len(todo)} new reads, {len(rows)-len(todo)} cached (cap {CAP})")
    if len(todo) > CAP:
        sys.exit("SPEND CAP — abort before billing")
    OUT.mkdir(parents=True, exist_ok=True)
    import httpx
    cf = CACHE.open("a")
    sem = asyncio.Semaphore(6)

    async def one(client, r):
        prompt = RULERS["one"].format(problem=probs[r["pid"]], answer=r["answer"])
        for _ in range(3):
            async with sem:
                try:
                    resp = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={"Authorization": f"Bearer {key}"},
                        json={"model": MODEL, "max_tokens": 4096,
                              "messages": [{"role": "user", "content": prompt}]},
                        timeout=120)
                    text = resp.json()["choices"][0]["message"]["content"]
                except Exception:
                    continue
            j = H.parse_json(text) if text else None
            if valid(j):
                cf.write(json.dumps({"key": f"g|{md5(r['answer'])[:12]}",
                                     "verdict": j}) + "\n")
                cf.flush()
                return
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[one(client, r) for r in todo])
    cf.close()
    return gem_cache()


def kappa(pairs):
    n = len(pairs)
    po = sum(1 for a, b in pairs if a == b) / n
    pa = sum(1 for a, _ in pairs if a) / n
    pb = sum(1 for _, b in pairs if b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return po, (po - pe) / (1 - pe) if pe < 1 else 1.0


def main():
    probs = {json.loads(l)["pid"]: json.loads(l)["problem"] for l in PROBS.open()}
    rows = load_rows()
    son = sonnet_verdicts(rows)
    gem = asyncio.run(judge(rows, probs)) or gem_cache()
    missing = [r for r in rows if f"g|{md5(r['answer'])[:12]}" not in gem]
    if missing:
        sys.exit(f"COVERAGE INSUFFICIENT: {len(missing)} unjudged — rerun")

    strict_pairs, rt_pairs, disagreements = [], [], []
    for r in rows:
        s = son[(r["arm"], r["pid"])]
        g = gem[f"g|{md5(r['answer'])[:12]}"]
        strict_pairs.append((s["coherent"], g["coherent"]))
        sc, gc = rulert_clean(s), rulert_clean(g)
        rt_pairs.append((sc, gc))
        if sc != gc:
            disagreements.append((r["arm"], r["pid"], sc, gc, s, g))

    print("\n========== JUDGE VALIDITY MINI-STUDY ==========")
    po1, k1 = kappa(strict_pairs)
    po2, k2 = kappa(rt_pairs)
    print(f"strict-coherent : agreement {po1:.1%}  kappa {k1:.2f}")
    print(f"RULER-T-clean   : agreement {po2:.1%}  kappa {k2:.2f}")
    band = ("SUPPORTED (>=80%)" if po2 >= 0.80 else
            "PARTIAL (60-79%)" if po2 >= 0.60 else "FLAGGED (<60%)")
    print(f"frozen interpretation: judge validity {band}")
    for a in ("C", "R", "G"):
        srt = sum(1 for r in rows if r["arm"] == a
                  and rulert_clean(son[(r["arm"], r["pid"])]))
        grt = sum(1 for r in rows if r["arm"] == a
                  and rulert_clean(gem[f"g|{md5(r['answer'])[:12]}"]))
        print(f"  arm {a}: RULER-T clean — Sonnet {srt}/16, Gemini {grt}/16")
    (OUT / "agreement_results.json").write_text(json.dumps(
        {"strict_agreement": round(po1, 4), "strict_kappa": round(k1, 3),
         "rulert_agreement": round(po2, 4), "rulert_kappa": round(k2, 3),
         "band": band}, indent=1))
    print("\n---------- DISAGREEMENTS (RULER-T-clean) ----------")
    for arm, pid, sc, gc, s, g in disagreements:
        print(f"[{arm} pid {pid:02d}] Sonnet clean={sc} vs Gemini clean={gc}")
        print(f"  Sonnet flaws: {json.dumps(s.get('flaws', []))[:400]}")
        print(f"  Gemini flaws: {json.dumps(g.get('flaws', []))[:400]}")


if __name__ == "__main__":
    main()
