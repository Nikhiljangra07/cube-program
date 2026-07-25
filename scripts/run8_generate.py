"""
run8_generate.py — RUN 8 stage 1a: scaled foresight corpus, prompt-only.

Re-derives the run-7 face-F carve (identical code path to build_faces.py; verified
against the frozen manifest md5 11910a55…) and generates 4 lane-extreme threads per
problem with PILOT8's F-prompt v1 verbatim (no passage — grounding falsified).
DeepSeek V4 Pro, temp 0.75, workers blind to each other, resume-safe.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/run8_generate.py

Writes data/run8/threads.jsonl (+ data/run8/problems_F.json, the frozen 220 list).
"""
from __future__ import annotations
import asyncio, hashlib, json, os, sys
from pathlib import Path

import httpx
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DF = Path.home() / "Desktop/divergence-formula/corpus_run"
RESCORED = ROOT / "data/faces/rescored.jsonl"
BENCH = ROOT / "data/bench/problems.jsonl"
D8 = ROOT / "data/run8"
OUT = D8 / "threads.jsonl"
MODEL = "deepseek/deepseek-v4-pro"
OR_URL = "https://openrouter.ai/api/v1/chat/completions"
KEY = os.environ.get("OPENROUTER_API_KEY", "")
SEM = asyncio.Semaphore(10)
TOP_N = 220
DIMS = ("foresight", "distinctness", "viability")

# ---- PILOT8 F-prompt v1, verbatim ----
TASK_F = (
    "Write a single thread (4-6 sentences, cold and analytical) that COMMITS to this "
    "angle as a concrete, lawful, executable strategy — name the first move with "
    "who/what/when — then project its consequence chain THREE TO FOUR STEPS DEEP: "
    "move -> most likely counter-reaction or system response -> second-order effect "
    "-> where this leaves you at a named time horizon. Every step must follow "
    "realistically from the last; no fantasy chains, no branching hedges ('it might "
    "X or Y') — commit to the most likely path and name the ONE signal that would "
    "falsify it.\n"
    "Final line, exactly: TRACE: <the chain skeleton in <=15 words>")
HEAD = ("You are writing ONE reasoning thread for a decision dilemma. You see ONLY your "
        "assigned angle; you are blind to the other threads.\n\n")
BODY = ("PROBLEM: {problem}\nKEY FACETS: {facets}\nYOUR ANGLE [{family}]: {angle}\n\n"
        "{task}\n"
        "HARD RULES: no historical/military/classical content (unless the problem itself "
        "is set there); modern voice matching the problem's own world; no restating the "
        "angle. Output ONLY the thread + TRACE line.")


def pid(problem: str) -> str:
    return hashlib.md5(problem.encode()).hexdigest()[:12]


def derive_carve():
    src = {}
    v5_train_rows = [json.loads(l) for l in (DF / "corpus_v5_train/passers.jsonl").open()]
    for r in v5_train_rows + [json.loads(l) for l in (DF / "corpus_v5_topup/passers.jsonl").open()]:
        src[r["problem"]] = r
    prep_holdout = {r["problem"] for r in v5_train_rows[-20:]}
    bench = {json.loads(l)["problem"] for l in BENCH.open()}
    rows = [json.loads(l) for l in RESCORED.open()]
    pool = [r for r in rows if r["problem"] not in prep_holdout and r["problem"] not in bench]
    S = {d: np.array([r["rescore"][d] for r in pool]) for d in DIMS}
    Z = {d: (S[d] - S[d].mean()) / S[d].std() for d in DIMS}
    contrast = Z["foresight"] - (Z["distinctness"] + Z["viability"]) / 2
    idx = list(np.argsort(-contrast)[:TOP_N])
    probs = [pool[i]["problem"] for i in idx]
    # identity check vs run-7 frozen artifact: rebuild face_F worker file bytes
    import io
    WRK_SYS = ("You write one precise, decisive, realistic reasoning thread pursuing a given "
               "strategic angle.")
    WRK_USER = ("PROBLEM: {problem}\nFACETS: {facets}\nANGLE: {angle}\n\nWrite a single reasoning "
                "thread (two or three sentences, cold and analytical) that COMMITS to THIS angle as "
                "a concrete, realistic, VIABLE strategy that resolves the whole problem in a "
                "distinct way — name the actual first move (who does what, to whom, by when) and "
                "the one most likely downstream consequence it is betting on. It must be lawful, "
                "executable, and unmistakably a different KIND of move than the other families "
                "would choose.")
    def fam(a):
        if isinstance(a, dict):
            f = str(a.get("family", "")).strip(); dd = str(a.get("directive", "")).strip()
            return f"[{f}] {dd}" if f else dd
        return str(a)
    buf = io.StringIO()
    for p in probs:
        r = src[p]
        for a, t in zip(r["angles"], r["pos_threads"]):
            buf.write(json.dumps({"messages": [
                {"role": "system", "content": WRK_SYS},
                {"role": "user", "content": WRK_USER.format(problem=r["problem"],
                                                            facets=" | ".join(r["facets"][:3]),
                                                            angle=fam(a))},
                {"role": "assistant", "content": str(t).strip()}]}) + "\n")
    md5 = hashlib.md5(buf.getvalue().encode()).hexdigest()
    ref = json.load((ROOT / "data/faces/carve_manifest.json").open())["F"]["md5"]
    if md5 != ref:
        sys.exit(f"CARVE IDENTITY FAIL: rebuilt {md5} != frozen {ref}")
    print(f"carve identity OK ({md5}) — 220 problems match run-7 face-F exactly")
    return probs, src


async def gen(client, prompt):
    async with SEM:
        for a in range(4):
            try:
                r = await client.post(OR_URL, headers={"Authorization": f"Bearer {KEY}"},
                                      json={"model": MODEL, "max_tokens": 2600, "temperature": 0.75,
                                            "messages": [{"role": "user", "content": prompt}]},
                                      timeout=120)
                r.raise_for_status()
                msg = (r.json()["choices"][0]["message"]["content"] or "").strip()
                if msg and "TRACE:" in msg:
                    return msg
            except Exception:
                await asyncio.sleep(2 * (a + 1))
    return None


async def main():
    if not KEY:
        sys.exit("OPENROUTER_API_KEY not set")
    D8.mkdir(parents=True, exist_ok=True)
    probs, src = derive_carve()
    (D8 / "problems_F.json").write_text(json.dumps(
        {"n": len(probs), "pids": [pid(p) for p in probs]}, indent=0))
    done = set()
    if OUT.exists():
        for l in OUT.open():
            r = json.loads(l)
            done.add((r["pid"], r["idx"]))
        print(f"resume: {len(done)} threads present")
    jobs = []
    for p in probs:
        row = src[p]
        pd = pid(p)
        facets = "; ".join(row["facets"])
        for k, ang in enumerate(row["angles"]):
            if (pd, k) in done:
                continue
            jobs.append((pd, k, p, HEAD + BODY.format(problem=p, facets=facets,
                                                      family=ang["family"],
                                                      angle=ang["directive"], task=TASK_F)))
    print(f"{len(jobs)} threads to generate (target 880)")
    out_f = OUT.open("a")
    lock = asyncio.Lock()
    n_ok = n_fail = 0
    async with httpx.AsyncClient() as client:
        async def one(job):
            nonlocal n_ok, n_fail
            pd, k, problem, prompt = job
            msg = await gen(client, prompt)
            async with lock:
                if msg:
                    body, _, trace = msg.partition("TRACE:")
                    out_f.write(json.dumps({"pid": pd, "idx": k, "problem": problem,
                                            "thread": body.strip(), "trace": trace.strip()}) + "\n")
                    out_f.flush(); n_ok += 1
                else:
                    n_fail += 1
                if (n_ok + n_fail) % 80 == 0:
                    print(f"  {n_ok} ok / {n_fail} fail", flush=True)
        await asyncio.gather(*[one(j) for j in jobs])
    out_f.close()
    total = sum(1 for _ in OUT.open())
    print(f"DONE: {n_ok} new, {n_fail} fail, {total} total on disk -> {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
