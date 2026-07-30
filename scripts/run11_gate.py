"""
run11_gate.py — RUN 11 stage 2: code gate + Sonnet sample-audit + delta diet build
(RUNBOOK11 frozen; gate check 5 = proportionality |delta| <= 30, added pre-run as a
stricter reading of the corpus prompt's hard rule).

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/run11_gate.py

Writes out/run11/gate_report.json, data/run11/faceVD_11/worker_train.jsonl + manifest.
"""
from __future__ import annotations
import asyncio, hashlib, json, os, random, re, statistics, sys
from pathlib import Path

import httpx

from run11_common import WRK_SYS, REVISE_USER

ROOT = Path(__file__).resolve().parent.parent
D11 = ROOT / "data/run11"
D10 = ROOT / "data/run10"
OUTD = ROOT / "out/run11"
KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SEM = asyncio.Semaphore(6)
EST = re.compile(r"ESTIMATE:\s*(\d{1,3})\s*%\s*$", re.M)
HOLDJUST = re.compile(r"unchanged|still |remains|binding|hinges|unaffected|does not (?:change|move)|not the (?:constraint|bottleneck)|same constraint", re.I)
STOP = set("the and for with that this from will would could a an of to in on by at is are was were it its as be has have had".split())
AUDIT_N = 30
JUNK_MAX = 0.20

AUDIT_PROMPT = """You are auditing ONE training sequence that teaches a model to re-derive a plan when
a variable moves. Judge whether it is SOUND teaching material. Be strict.

PROBLEM: {problem}
TURN-1 PLAN: {plan}
UPDATE: {update}
REVISION: {revision}

A sequence is JUNK if any: the update is not a single clean change; the revision
ignores or contradicts the update; the revision invents resources/actors not in the
problem or update; the estimate move is disproportionate or unexplained; a hold is
unjustified; the prose is incoherent.

Return ONLY JSON: {{"sound": true/false, "issue": "<=12 words or empty"}}"""


def est(t):
    m = EST.findall(t)
    return int(m[-1]) if m else None


def words(t):
    return {w for w in re.findall(r"[a-z]+", t.lower()) if len(w) > 3 and w not in STOP}


def code_gate(r):
    e1, e2 = est(r["plan"]), est(r["revision"])
    if e1 is None or e2 is None:
        return "missing tagged ESTIMATE"
    d = e2 - e1
    if r["direction"] == "boost" and d < 0:
        return "boost moved down"
    if r["direction"] == "nerf" and d > 0:
        return "nerf moved up"
    if d == 0 and not HOLDJUST.search(r["revision"]):
        return "hold without named constraint"
    if abs(d) > 30:
        return f"disproportionate move ({d:+d})"
    sig = words(r["update"]) - words(r["problem"])
    if sig and not (sig & words(r["revision"])):
        return "update not cited in revision"
    if len(words(r["revision"]) - words(r["plan"])) < 8:
        return "revision does not re-plan"
    return None


async def audit_one(client, r):
    async with SEM:
        for a in range(4):
            try:
                resp = await client.post("https://api.anthropic.com/v1/messages",
                                         headers={"x-api-key": KEY, "anthropic-version": "2023-06-01",
                                                  "content-type": "application/json"},
                                         json={"model": "claude-sonnet-5", "max_tokens": 12000,
                                               "messages": [{"role": "user", "content": AUDIT_PROMPT.format(
                                                   problem=r["problem"], plan=r["plan"],
                                                   update=r["update"], revision=r["revision"])}]},
                                         timeout=180)
                resp.raise_for_status()
                text = "".join(p.get("text", "") for p in resp.json().get("content", [])
                               if p.get("type") == "text")
                m = re.search(r"\{[^{}]*\}", text)
                if m:
                    j = json.loads(m.group())
                    if isinstance(j.get("sound"), bool):
                        return j
            except Exception:
                await asyncio.sleep(3 * (a + 1))
    return None


async def main():
    if not KEY:
        sys.exit("ANTHROPIC_API_KEY not set")
    OUTD.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(l) for l in (D11 / "sequences.jsonl").open()]
    admitted, rejected = [], {}
    for r in rows:
        why = code_gate(r)
        if why is None:
            admitted.append(r)
        else:
            rejected[why] = rejected.get(why, 0) + 1
    n_b = sum(1 for r in admitted if r["direction"] == "boost")
    n_n = len(admitted) - n_b
    print(f"code gate: {len(admitted)}/{len(rows)} admitted (boost {n_b}, nerf {n_n})")
    print(f"rejections: {json.dumps(rejected)}")
    if len(admitted) < 220:
        sys.exit(f"ADMISSION SHORTFALL: {len(admitted)} < 220 — STOP, report to Nikhil")

    # AMENDMENT (2026-07-30, after pilots 1-3): audit ALL admitted sequences and DROP
    # junk from the diet (per-sequence filter), instead of sample-and-stop. Global
    # sanity line: junk > 35% overall -> stop anyway. Diet floor: 180 sound sequences.
    async with httpx.AsyncClient() as client:
        audits = await asyncio.gather(*[audit_one(client, r) for r in admitted])
    pairs = [(r, a) for r, a in zip(admitted, audits) if a is not None]
    if len(pairs) < len(admitted) - 10:
        sys.exit(f"AUDIT COVERAGE FAIL: {len(pairs)}/{len(admitted)} scored — rerun")
    sound = [r for r, a in pairs if a["sound"]]
    junk = [(r, a) for r, a in pairs if not a["sound"]]
    print(f"Sonnet audit-all (session M): {len(pairs)} scored, junk {len(junk)} "
          f"({100*len(junk)/len(pairs):.0f}%) dropped; {len(sound)} sound")
    (OUTD / "gate_report.json").write_text(json.dumps(
        {"total": len(rows), "code_admitted": len(admitted), "boost": n_b, "nerf": n_n,
         "rejections": rejected, "audited": len(pairs), "junk_dropped": len(junk),
         "sound": len(sound), "junk_issues": [a["issue"] for _, a in junk][:20]}, indent=1))
    if len(junk) / len(pairs) > 0.35:
        sys.exit(f"AUDIT FAIL: junk {100*len(junk)/len(pairs):.0f}% > 35% — STOP before training")
    if len(sound) < 180:
        sys.exit(f"DIET FLOOR FAIL: {len(sound)} sound < 180 — STOP, report to Nikhil")
    admitted = sound
    n_b = sum(1 for r in admitted if r["direction"] == "boost")
    n_n = len(admitted) - n_b

    # ---- diet build: delta revision rows + static faceV_10 diet ----
    face_dir = D11 / "faceVD_11"
    face_dir.mkdir(exist_ok=True)
    n_delta = 0
    with (face_dir / "worker_train.jsonl").open("w") as f:
        for l in (D10 / "faceV_10/worker_train.jsonl").open():
            f.write(l)
        for r in admitted:
            f.write(json.dumps({"messages": [
                {"role": "system", "content": WRK_SYS},
                {"role": "user", "content": REVISE_USER.format(
                    problem=r["problem"], prior=r["plan"].strip(), update=r["update"].strip())},
                {"role": "assistant", "content": r["revision"].strip()}]}) + "\n")
            n_delta += 1
    md5 = hashlib.md5((face_dir / "worker_train.jsonl").read_bytes()).hexdigest()
    manifest = {"static_rows": 945, "delta_rows": n_delta, "total_rows": 945 + n_delta,
                "boost": n_b, "nerf": n_n, "worker_md5": md5}
    (face_dir / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    asyncio.run(main())
