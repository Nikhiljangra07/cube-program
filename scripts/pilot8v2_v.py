"""
pilot8v2_v.py — PILOT8 addendum: viability worker prompt v2, prompt-only, V lane only.

Pilot 8 falsified grounding (G≈U≈X) and showed the worker prompt is the lever. Foresight
cleared extremity prompt-only; viability missed the mean margin (+1.12 vs +1.5). This
re-pilot tests V-prompt v2 (hard-number mechanism density) on the SAME 15 V problems,
no passage, then gates U2 + P fresh in ONE blind Sonnet session (single-session
comparison rule — pilot-8 P scores are not reused).

Frozen reads (registered here before generation):
  A. EXTREMITY-V2: mean(U2) >= mean(P) + 1.5 AND >=50% of U2 threads >= 8.
  B. LEAK <= 10%; C. HEDGE <= 15%.
  A+B+C pass -> RUNBOOK8 freezes with F-prompt v1 + V-prompt v2, prompt-only.
  A fails -> one more iteration allowed; two failures -> V face dropped from run 8
  (cube proceeds F-only) — no endless prompt fishing.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/pilot8v2_v.py            # generate + gate + reads

Writes data/pilot8/threads_v2.jsonl + out/pilot8/summary_v2.json.
"""
from __future__ import annotations
import asyncio, hashlib, json, os, random, re, statistics, sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data/pilot8"
OUTD = ROOT / "out/pilot8"
SRC = [Path.home() / "Desktop/divergence-formula/corpus_run/corpus_v5_train/passers.jsonl",
       Path.home() / "Desktop/divergence-formula/corpus_run/corpus_v5_topup/passers.jsonl"]
GEN_MODEL = "deepseek/deepseek-v4-pro"
OR_URL = "https://openrouter.ai/api/v1/chat/completions"
OR_KEY = os.environ.get("OPENROUTER_API_KEY", "")
J_MODEL = "claude-sonnet-5"
J_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SEM = asyncio.Semaphore(10)
JSEM = asyncio.Semaphore(6)
N_PER_LANE = 15
SEED = 8

TASK_V2 = (
    "Write a single thread (5-7 sentences, cold and analytical) that COMMITS to this "
    "angle and makes it EXECUTION-COMPLETE at operator level: (1) the exact mechanism — "
    "who does what, to whom, in what order, with AT LEAST TWO hard numbers (a cost, "
    "amount, percentage, or headcount AND a deadline or duration); (2) the binding "
    "constraint that most limits the plan (budget, authority, law, capacity) with the "
    "number at which it binds; (3) the most likely failure point and the concrete "
    "mitigation PRE-BUILT into the plan (not a fallback list); (4) the first "
    "irreversible commitment and what walking it back would cost. Nothing vague "
    "survives: every actor a named role, every instrument specific, every step "
    "executable tomorrow without further planning. It must be lawful and realistic.\n"
    "Final line, exactly: TRACE: <mechanism + constraint + failure point in <=15 words>")

HEAD = ("You are writing ONE reasoning thread for a decision dilemma. You see ONLY your "
        "assigned angle; you are blind to the other threads.\n\n")
BODY = ("PROBLEM: {problem}\nKEY FACETS: {facets}\nYOUR ANGLE [{family}]: {angle}\n\n"
        "{task}\n"
        "HARD RULES: no historical/military/classical content (unless the problem itself "
        "is set there); modern voice matching the problem's own world; no restating the "
        "angle. Output ONLY the thread + TRACE line.")

LANE_DEF_V = ("VIABILITY: is the strategy execution-complete as stated — exact mechanism "
              "(who/what/when/cost), the binding real-world constraint respected, failure "
              "point + mitigation named — such that a competent operator could run it "
              "tomorrow without further planning?")

JPROMPT = """You are scoring 4 candidate response threads to a decision problem, on ONE dimension only.

PROBLEM: {problem}

THREADS:
{threads}

Score EACH thread 1-10 on this dimension:
{lane_def}
Use the full range: 5-6 = typical competent response, 8+ = the dimension saturates the
text, 9-10 = exceptional. Score the dimension only — not overall quality.

Also flag each thread:
- leak: true if it imports historical/military/classical-era particulars foreign to the problem's own setting
- hedge: true if it fails to commit to one concrete course (lists alternatives, "might/could" without resolution)

Return ONLY JSON: {{"scores":[n,n,n,n],"leak":[b,b,b,b],"hedge":[b,b,b,b]}}"""


def pid(problem: str) -> str:
    return hashlib.md5(problem.encode()).hexdigest()[:12]


def v_problems():
    train = [json.loads(l) for l in SRC[0].open()]
    topup = [json.loads(l) for l in SRC[1].open()]
    pool = train[:-20] + topup
    rng = random.Random(SEED)
    sample = rng.sample(pool, N_PER_LANE * 2)
    return sample[N_PER_LANE:]          # identical V-lane sample to pilot 8


async def gen(client, prompt):
    async with SEM:
        for a in range(4):
            try:
                r = await client.post(OR_URL, headers={"Authorization": f"Bearer {OR_KEY}"},
                                      json={"model": GEN_MODEL, "max_tokens": 2600,
                                            "temperature": 0.75,
                                            "messages": [{"role": "user", "content": prompt}]},
                                      timeout=120)
                r.raise_for_status()
                msg = (r.json()["choices"][0]["message"]["content"] or "").strip()
                if msg and "TRACE:" in msg:
                    return msg
            except Exception:
                await asyncio.sleep(2 * (a + 1))
    return None


def jparse(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        j = json.loads(m.group())
        s, lk, hg = j.get("scores"), j.get("leak"), j.get("hedge")
        if (isinstance(s, list) and len(s) == 4 and all(isinstance(x, int) and 1 <= x <= 10 for x in s)
                and isinstance(lk, list) and len(lk) == 4 and isinstance(hg, list) and len(hg) == 4):
            return {"scores": s, "leak": [bool(x) for x in lk], "hedge": [bool(x) for x in hg]}
    except Exception:
        pass
    return None


async def judge(client, prompt):
    async with JSEM:
        for a in range(5):
            try:
                r = await client.post("https://api.anthropic.com/v1/messages",
                                      headers={"x-api-key": J_KEY, "anthropic-version": "2023-06-01",
                                               "content-type": "application/json"},
                                      json={"model": J_MODEL, "max_tokens": 12000,
                                            "messages": [{"role": "user", "content": prompt}]},
                                      timeout=180)
                r.raise_for_status()
                text = "".join(p.get("text", "") for p in r.json().get("content", [])
                               if p.get("type") == "text").strip()
                j = jparse(text)
                if j:
                    return j
            except Exception:
                await asyncio.sleep(3 * (a + 1))
    return None


async def main():
    if not OR_KEY or not J_KEY:
        sys.exit("keys not loaded")
    probs = v_problems()
    tfile = D / "threads_v2.jsonl"

    # ---- generate U2 (resume-safe) ----
    done = set()
    if tfile.exists():
        for l in tfile.open():
            r = json.loads(l)
            done.add((r["pid"], r["idx"]))
    jobs = []
    for row in probs:
        p = pid(row["problem"])
        facets = "; ".join(row["facets"])
        for k, ang in enumerate(row["angles"]):
            if (p, k) in done:
                continue
            jobs.append((p, k, row["problem"],
                         HEAD + BODY.format(problem=row["problem"], facets=facets,
                                            family=ang["family"], angle=ang["directive"],
                                            task=TASK_V2)))
    print(f"{len(jobs)} V2 threads to generate")
    out_f = tfile.open("a")
    lock = asyncio.Lock()
    async with httpx.AsyncClient() as client:
        async def one(job):
            p, k, problem, prompt = job
            msg = await gen(client, prompt)
            async with lock:
                if msg:
                    body, _, trace = msg.partition("TRACE:")
                    out_f.write(json.dumps({"pid": p, "idx": k, "problem": problem,
                                            "thread": body.strip(), "trace": trace.strip()}) + "\n")
                    out_f.flush()
        await asyncio.gather(*[one(j) for j in jobs])
    out_f.close()
    rows = [json.loads(l) for l in tfile.open()]
    print(f"{len(rows)} V2 threads on disk (expect 60)")
    if len(rows) < 60:
        sys.exit("generation incomplete")

    # ---- gate: U2 + P, fresh single session ----
    by = {}
    for r in rows:
        by.setdefault(r["pid"], {})[r["idx"]] = (r["thread"], r["problem"])
    sets = [{"cond": "U2", "pid": p, "problem": th[0][1],
             "threads": [th[i][0] for i in range(4)]} for p, th in by.items()]
    for row in probs:
        sets.append({"cond": "P", "pid": pid(row["problem"]), "problem": row["problem"],
                     "threads": row["pos_threads"]})
    random.Random(82).shuffle(sets)
    print(f"{len(sets)} sets to judge (expect 30)")
    results = []
    async with httpx.AsyncClient() as client:
        async def jone(s):
            block = "\n\n".join(f"[{i+1}] {t}" for i, t in enumerate(s["threads"]))
            j = await judge(client, JPROMPT.format(problem=s["problem"], threads=block,
                                                   lane_def=LANE_DEF_V))
            if j:
                results.append({"cond": s["cond"], "pid": s["pid"], **j})
        await asyncio.gather(*[jone(s) for s in sets])
    print(f"coverage {len(results)}/{len(sets)}")
    if len(results) < len(sets):
        sys.exit("COVERAGE FAIL — discard session and rerun whole")

    OUTD.mkdir(parents=True, exist_ok=True)
    with (OUTD / "gate_v2.jsonl").open("w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    u2 = [x for r in results if r["cond"] == "U2" for x in r["scores"]]
    pp = [x for r in results if r["cond"] == "P" for x in r["scores"]]
    lk = [x for r in results if r["cond"] == "U2" for x in r["leak"]]
    hg = [x for r in results if r["cond"] == "U2" for x in r["hedge"]]
    mu, mp = statistics.mean(u2), statistics.mean(pp)
    reads = {
        "A_extremity_v2": {"U2": round(mu, 2), "P": round(mp, 2),
                           "pct_ge8": round(100 * sum(1 for x in u2 if x >= 8) / len(u2), 1),
                           "need": "U2>=P+1.5 AND >=50% >=8",
                           "pass": mu >= mp + 1.5 and sum(1 for x in u2 if x >= 8) / len(u2) >= 0.5},
        "B_leak": {"pct": round(100 * sum(lk) / len(lk), 1), "pass": sum(lk) / len(lk) <= 0.10},
        "C_hedge": {"pct": round(100 * sum(hg) / len(hg), 1), "pass": sum(hg) / len(hg) <= 0.15},
    }
    (OUTD / "summary_v2.json").write_text(json.dumps(reads, indent=1))
    for k, v in reads.items():
        print(f"{k}: {'PASS' if v['pass'] else 'FAIL'}  {v}")


if __name__ == "__main__":
    asyncio.run(main())
