"""
run11_generate.py — RUN 11 stage 1: the delta corpus (RUNBOOK11 frozen).

150 strongest gate-admitted run-10 problems (by gate viability) × 2 directions
(boost + nerf) = 300 sequences. One DeepSeek call per sequence returns STRICT JSON:
  plan     — turn-1 audit-first thread, final line exactly `ESTIMATE: NN%`
  update   — ONE named dated shift in the assigned direction, one change only
  revision — the re-derivation: what changed → revised plan → `ESTIMATE: NN%`
Direction label lives in metadata only. Resume-safe by (pid, direction).

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/run11_generate.py [--pilot]     # pilot = first 15 problems (30 seqs)

Writes data/run11/sequences.jsonl.
"""
from __future__ import annotations
import asyncio, hashlib, json, os, re, sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
DF = Path.home() / "Desktop/divergence-formula/corpus_run"
D11 = ROOT / "data/run11"
OUT = D11 / "sequences.jsonl"
GATE = ROOT / "out/run10/gate.jsonl"
MODEL = "deepseek/deepseek-v4-pro"
OR_URL = "https://openrouter.ai/api/v1/chat/completions"
KEY = os.environ.get("OPENROUTER_API_KEY", "")
SEM = asyncio.Semaphore(10)
N_PROBLEMS = 150
PILOT = "--pilot" in sys.argv
PILOT_N = 15

DIR_SPEC = {
    "boost": ("STRENGTHENS the actor's position in exactly ONE way (a resource added, "
              "a person's committed time increased, an approval landing, a friction removed)"),
    "nerf": ("WEAKENS the actor's position in exactly ONE way (a resource removed or cut, "
             "a person's availability lost, a new cost or veto appearing, a deadline moved "
             "EARLIER). No silver linings"),
}

PROMPT = (
    "You are building ONE two-turn training sequence teaching a model to re-derive a plan "
    "when a variable moves.\n\n"
    "PROBLEM: {problem}\nKEY FACETS: {facets}\nANGLE [{family}]: {angle}\n\n"
    "Return STRICT JSON only with these three fields:\n"
    '{{"plan":"<turn 1: a 4-6 sentence cold, analytical thread that COMMITS to the angle: '
    "audit what the actor actually holds (numbers only if the problem supplies them), name "
    "the ONE favorable variable, commit to a lawful plan spending only audited items "
    "(who/what/when, no invented actors or statistics), name the ONE most likely friction "
    "and its pre-arranged answer. Final line exactly: ESTIMATE: NN% (digits)>\",\n"
    '"update":"<ONE sentence, phrased as a dated update, that {dir_spec}. Exactly one '
    'change; concrete; targets something actually in the problem or plan>",\n'
    '"revision":"<turn 2: 3-4 sentences re-deriving under the update: (1) name precisely '
    "what the update changes for the plan, (2) the revised plan — reallocate what freed up "
    "or absorb what tightened, concretely, (3) how the estimate responds and WHY: move it "
    "proportionately in the direction the update implies, OR hold it ONLY if the binding "
    "constraint the estimate rests on was not the thing that moved — and in a hold, NAME "
    "that unmoved constraint. Never move opposite the update's direction. Final line "
    'exactly: ESTIMATE: NN% (digits)>"}}\n\n'
    "HARD RULES: modern voice matching the problem's own world; no historical/classical "
    "content unless the problem is set there; the revision must genuinely re-plan (not "
    "restate turn 1); proportionate numbers — one small shift never moves an estimate by "
    "more than ~25 points."
)


def pid(problem: str) -> str:
    return hashlib.md5(problem.encode()).hexdigest()[:12]


def load_problems():
    gate = [json.loads(l) for l in GATE.open()]
    admitted = [r for r in gate if r["judge"]["viability"] >= 4 and r["judge"]["foresight"] >= 3]
    admitted.sort(key=lambda r: (-r["judge"]["viability"], r["pid"]))
    pids = [r["pid"] for r in admitted[:N_PROBLEMS]]
    src = {}
    for p in (DF / "corpus_v5_train/passers.jsonl", DF / "corpus_v5_topup/passers.jsonl"):
        for l in p.open():
            r = json.loads(l)
            src[pid(r["problem"])] = r
    return pids, src


ESTLINE = re.compile(r"ESTIMATE:\s*\d{1,3}\s*%\s*$", re.M)


def valid(j):
    if not (j and all(isinstance(j.get(k), str) and j[k].strip() for k in ("plan", "update", "revision"))):
        return "missing fields"
    if not ESTLINE.search(j["plan"].strip()):
        return "plan missing tagged ESTIMATE line"
    if not ESTLINE.search(j["revision"].strip()):
        return "revision missing tagged ESTIMATE line"
    return None


async def gen(client, job):
    pd, direction, prompt = job
    async with SEM:
        for a in range(4):
            reason = "request failed"
            try:
                r = await client.post(OR_URL, headers={"Authorization": f"Bearer {KEY}"},
                                      json={"model": MODEL, "max_tokens": 10000, "temperature": 0.75,
                                            "messages": [{"role": "user", "content": prompt}]},
                                      timeout=180)
                r.raise_for_status()
                msg = (r.json()["choices"][0]["message"]["content"] or "").strip()
                m = re.search(r"\{.*\}", msg, re.S)
                j = json.loads(m.group()) if m else None
                reason = valid(j)
                if reason is None:
                    return pd, direction, j
            except Exception as e:
                reason = f"{type(e).__name__}"
            if a == 3:
                print(f"  [{pd}/{direction}] REJECTED: {reason}", flush=True)
            await asyncio.sleep(2 * (a + 1))
    return pd, direction, None


async def main():
    if not KEY:
        sys.exit("OPENROUTER_API_KEY not set")
    D11.mkdir(parents=True, exist_ok=True)
    pids, src = load_problems()
    if PILOT:
        pids = pids[:PILOT_N]
        print(f"PILOT MODE: {PILOT_N} problems ({2*PILOT_N} sequences)")
    done = set()
    if OUT.exists():
        for l in OUT.open():
            r = json.loads(l)
            done.add((r["pid"], r["direction"]))
        print(f"resume: {len(done)} sequences present")
    jobs = []
    for i, pd in enumerate(pids):
        row = src[pd]
        facets = "; ".join(row["facets"])
        for k, direction in enumerate(("boost", "nerf")):
            if (pd, direction) in done:
                continue
            ang = row["angles"][(i + k) % len(row["angles"])]
            jobs.append((pd, direction, PROMPT.format(
                problem=row["problem"], facets=facets, family=ang["family"],
                angle=ang["directive"], dir_spec=DIR_SPEC[direction])))
    print(f"{len(jobs)} sequences to generate")
    out_f = OUT.open("a")
    lock = asyncio.Lock()
    n_ok = n_fail = 0
    async with httpx.AsyncClient() as client:
        async def one(job):
            nonlocal n_ok, n_fail
            pd, direction, j = await gen(client, job)
            async with lock:
                if j:
                    out_f.write(json.dumps({"pid": pd, "direction": direction,
                                            "problem": src[pd]["problem"], **j}) + "\n")
                    out_f.flush(); n_ok += 1
                else:
                    n_fail += 1
                if (n_ok + n_fail) % 30 == 0:
                    print(f"  {n_ok} ok / {n_fail} fail", flush=True)
        await asyncio.gather(*[one(job) for job in jobs])
    out_f.close()
    total = sum(1 for _ in OUT.open())
    print(f"DONE: {n_ok} new, {n_fail} fail, {total} total on disk -> {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
