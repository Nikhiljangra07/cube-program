"""
probe2_derivation.py — RUN 10 post-hoc: derivation-sensitivity at the EVENT level
(Nikhil's reframe, 2026-07-30). Judge-free, $0, existing outputs only.

Question: when the one boosted variable shifts (base -> twin), does the face's
REASONING react — does the twin thread-set reference the boost content and re-plan
around it — even where the raw number was noisy?

Method per pair (16 deterministic twins):
  boost-signature = content words of the boost sentence MINUS words already present
  in the base problem text (so only genuinely new material counts).
  uptake = fraction of the 4 twin threads containing >=1 signature word.
  control = same signature checked against the 4 BASE threads (must be ~0; the base
  model never saw the boost — any hits are coincidence-noise floor).
Conditional read: among pairs with real uptake (>= 2/4 threads), how often does the
estimate direction go the right way? (Was the number-noise hiding a live derivation?)
"""
from __future__ import annotations
import json, re, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTD = ROOT / "out/run10"
D10 = ROOT / "data/run10"

STOP = set("""a an the and or of to in on for with by at from as is are was were be been has have
had it its this that these those you your he she they their we our i my new one two now must
will would can could may might should after before over under all any each which who whom
when where while during still also only just more most less least very much many if then than
into out up down off no not nor so such own same s t d ll re ve day days week weeks month
months year years am pm""".split())

PCT = re.compile(r"(\d{1,3})(?:\s*(?:-|–|to)\s*(\d{1,3}))?\s*%")


def words(text):
    return {w for w in re.findall(r"[a-z]+", text.lower()) if len(w) > 3 and w not in STOP}


def estimates(threads):
    vals = []
    for t in threads:
        found = PCT.findall(t)
        if found:
            a, b = found[-1]
            vals.append((int(a) + int(b)) / 2 if b else int(a))
    return vals


def main():
    inv = [json.loads(l) for l in (D10 / "inventory_problems.jsonl").open()]
    twin_meta = [json.loads(l) for l in (D10 / "twin_problems.jsonl").open()]
    base_rows = {r["problem"]: r for r in (json.loads(l) for l in (OUTD / "eval_faceV_10_qC_v5_threads.jsonl").open())}
    twin_rows = {r["problem"]: r for r in (json.loads(l) for l in (OUTD / "eval_faceV_10_qCtwin_v5_threads.jsonl").open())}

    results = []
    for m in twin_meta:
        base_problem = inv[m["base_index"]]["problem"]
        b, t = base_rows.get(base_problem), twin_rows.get(m["problem"])
        if not (b and t):
            continue
        sig = words(m["boost"]) - words(base_problem)
        if not sig:
            results.append({"i": m["base_index"], "sig": 0})
            continue
        def hits(threads):
            return [len(sig & words(th)) for th in threads]
        t_hits = hits(t["threads"])
        b_hits = hits(b["threads"])  # noise floor: boost words appearing without the boost
        uptake = sum(1 for h in t_hits if h >= 1)
        floor = sum(1 for h in b_hits if h >= 1)
        be, te = estimates(b["threads"]), estimates(t["threads"])
        dir_ok = None
        if len(be) >= 2 and len(te) >= 2:
            dir_ok = statistics.mean(te) >= statistics.mean(be)
        results.append({"i": m["base_index"], "sig": len(sig), "uptake": uptake,
                        "floor": floor, "dir_ok": dir_ok,
                        "sig_words": sorted(sig)[:6]})

    print("pair | sig-words | twin uptake /4 | base noise-floor /4 | number-direction")
    real = []
    for r in results:
        if r["sig"] == 0:
            print(f"  {r['i']:2d} | (boost fully overlapped base text — skipped)")
            continue
        d = {True: "OK", False: "WRONG", None: "unparseable"}[r["dir_ok"]]
        print(f"  {r['i']:2d} | {r['sig']:2d} | {r['uptake']}/4 | {r['floor']}/4 | {d}   {r['sig_words']}")
        real.append(r)
    n = len(real)
    strong = [r for r in real if r["uptake"] >= 2 and r["floor"] <= 1]
    print(f"\nEVENT-LEVEL UPTAKE: {len(strong)}/{n} pairs show real uptake (>=2/4 twin threads cite boost, noise-floor <=1)")
    print(f"mean twin uptake {statistics.mean(r['uptake'] for r in real):.2f}/4 vs base noise floor {statistics.mean(r['floor'] for r in real):.2f}/4")
    cond = [r for r in strong if r["dir_ok"] is not None]
    if cond:
        ok = sum(1 for r in cond if r["dir_ok"])
        print(f"CONDITIONAL DIRECTION (uptake pairs with numbers): {ok}/{len(cond)} correct")
    print("\nReads: uptake HIGH + direction improves -> derivation alive at event level, "
          "number noisy (Nikhil's reframe supported: train derivation-as-structure).")
    print("uptake HIGH + direction still random -> events tracked, numbers decorative.")
    print("uptake LOW -> derivation absent at every level; reframe unsupported at 4B-SFT.")


if __name__ == "__main__":
    main()
