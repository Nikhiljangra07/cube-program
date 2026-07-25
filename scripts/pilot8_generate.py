"""
pilot8_generate.py — PILOT8 stage 2: 360 threads via DeepSeek V4 Pro.

30 seed-8 problems from the pool (prep_v5 last-20 holdout excluded): first 15 -> lane F,
last 15 -> lane V. Conditions per problem: G (own-lane passage), U (no passage,
length-matched), X (wrong-lane passage, same index). 4 threads/problem (one per angle,
workers blind to each other). Every prompt demands 4-6 sentences + TRACE line.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/pilot8_generate.py

Writes data/pilot8/threads.jsonl. Resume-safe by (lane, cond, pid, thread_idx).
"""
from __future__ import annotations
import asyncio, hashlib, json, os, random, sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data/pilot8"
OUT = D / "threads.jsonl"
SRC = [Path.home() / "Desktop/divergence-formula/corpus_run/corpus_v5_train/passers.jsonl",
       Path.home() / "Desktop/divergence-formula/corpus_run/corpus_v5_topup/passers.jsonl"]
MODEL = "deepseek/deepseek-v4-pro"
OR_URL = "https://openrouter.ai/api/v1/chat/completions"
KEY = os.environ.get("OPENROUTER_API_KEY", "")
SEM = asyncio.Semaphore(10)
N_PER_LANE = 15
SEED = 8

BORROW = {
    "F": ("The exemplar shows how consequences CHAIN: a move triggers a reaction, the "
          "reaction shifts the ground, the shift decides the endgame. Borrow that "
          "DEPTH-OF-CHAIN — never its era, events, people, or subject matter."),
    "V": ("The exemplar shows reasoning that survives contact with reality: named "
          "mechanisms, real costs, binding constraints, what breaks and what covers it. "
          "Borrow that EXECUTION-COMPLETENESS — never its era, events, people, or "
          "subject matter."),
}

TASK = {
    "F": ("Write a single thread (4-6 sentences, cold and analytical) that COMMITS to this "
          "angle as a concrete, lawful, executable strategy — name the first move with "
          "who/what/when — then project its consequence chain THREE TO FOUR STEPS DEEP: "
          "move -> most likely counter-reaction or system response -> second-order effect "
          "-> where this leaves you at a named time horizon. Every step must follow "
          "realistically from the last; no fantasy chains, no branching hedges ('it might "
          "X or Y') — commit to the most likely path and name the ONE signal that would "
          "falsify it.\n"
          "Final line, exactly: TRACE: <the chain skeleton in <=15 words>"),
    "V": ("Write a single thread (4-6 sentences, cold and analytical) that COMMITS to this "
          "angle and makes it EXECUTION-COMPLETE: the exact mechanism (who does what, to "
          "whom, by when, at what cost in money or time), the binding constraint that most "
          "limits it (budget, authority, law, capacity) and how the plan fits inside it, "
          "the most likely failure point, and the concrete mitigation already built in. "
          "Every element must be realistic and lawful — a competent operator could run "
          "this tomorrow without further planning.\n"
          "Final line, exactly: TRACE: <mechanism + constraint + failure point in <=15 words>"),
}

HEAD = ("You are writing ONE reasoning thread for a decision dilemma. You see ONLY your "
        "assigned angle; you are blind to the other threads.\n\n")
EXEMPLAR = ("STRUCTURAL EXEMPLAR (study the SHAPE of its reasoning, not its content):\n"
            "---\n{passage}\n---\n{borrow}\n\n")
BODY = ("PROBLEM: {problem}\nKEY FACETS: {facets}\nYOUR ANGLE [{family}]: {angle}\n\n"
        "{task}\n"
        "HARD RULES: no reference to the exemplar or any historical/military/classical "
        "content (unless the problem itself is set there); modern voice matching the "
        "problem's own world; no restating the angle. Output ONLY the thread + TRACE line.")


def pid(problem: str) -> str:
    return hashlib.md5(problem.encode()).hexdigest()[:12]


def load_problems():
    train = [json.loads(l) for l in SRC[0].open()]
    topup = [json.loads(l) for l in SRC[1].open()]
    pool = train[:-20] + topup  # exclude prep_v5 last-20 holdout
    rng = random.Random(SEED)
    sample = rng.sample(pool, N_PER_LANE * 2)
    return {"F": sample[:N_PER_LANE], "V": sample[N_PER_LANE:]}


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
    passages = {ln: json.load((D / f"passages_{ln}.json").open())["passages"] for ln in ("F", "V")}
    probs = load_problems()
    done = set()
    if OUT.exists():
        for l in OUT.open():
            r = json.loads(l)
            done.add((r["lane"], r["cond"], r["pid"], r["idx"]))
        print(f"resume: {len(done)} threads present")

    jobs = []
    for lane in ("F", "V"):
        other = "V" if lane == "F" else "F"
        for i, row in enumerate(probs[lane]):
            p = pid(row["problem"])
            facets = "; ".join(row["facets"])
            for cond in ("G", "U", "X"):
                if cond == "G":
                    ex = EXEMPLAR.format(passage=passages[lane][i % 8]["text"], borrow=BORROW[lane])
                elif cond == "X":
                    ex = EXEMPLAR.format(passage=passages[other][i % 8]["text"], borrow=BORROW[lane])
                else:
                    ex = ""
                for k, ang in enumerate(row["angles"]):
                    if (lane, cond, p, k) in done:
                        continue
                    prompt = HEAD + ex + BODY.format(problem=row["problem"], facets=facets,
                                                     family=ang["family"], angle=ang["directive"],
                                                     task=TASK[lane])
                    jobs.append((lane, cond, p, k, ang["family"], row["problem"], prompt))
    print(f"{len(jobs)} threads to generate")

    out_f = OUT.open("a")
    lock = asyncio.Lock()
    n_ok = n_fail = 0

    async with httpx.AsyncClient() as client:
        async def one(job):
            nonlocal n_ok, n_fail
            lane, cond, p, k, fam, problem, prompt = job
            msg = await gen(client, prompt)
            async with lock:
                if msg:
                    body, _, trace = msg.partition("TRACE:")
                    out_f.write(json.dumps({"lane": lane, "cond": cond, "pid": p, "idx": k,
                                            "family": fam, "problem": problem,
                                            "thread": body.strip(), "trace": trace.strip()}) + "\n")
                    out_f.flush(); n_ok += 1
                else:
                    n_fail += 1
                if (n_ok + n_fail) % 40 == 0:
                    print(f"  {n_ok} ok / {n_fail} fail", flush=True)
        await asyncio.gather(*[one(j) for j in jobs])
    out_f.close()
    print(f"DONE: {n_ok} ok, {n_fail} fail -> {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
