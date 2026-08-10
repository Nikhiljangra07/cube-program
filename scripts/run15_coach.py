"""
run15_coach.py — RUN 15 harness-fusion coach (RUNBOOK15 frozen).

Template-slot rigid assembly: the final speech is COMPOSED by code from the
motion segment plus fixed, digit-free template sentences. The three measured
sin classes are unrepresentable in the added text by construction; residual
risk lives only inside the motion segment (screened upstream by the advisory
checker + bounded retry).

  python scripts/run15_coach.py     # stage-0 offline test over run-14 transcripts
"""
from __future__ import annotations
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EST = re.compile(r"ESTIMATE:\s*\d{1,3}\s*%")

OPENER = ("As of the update, {dead_token} is no longer available and the "
          "working numbers are revised accordingly.")
BRIDGE = ("If {counterparty} responds as the read anticipates, the plan is "
          "already positioned for it; if not, nothing in the commitment "
          "depends on that prediction.")


def assemble(motion: str, manifest: dict) -> str | None:
    """Compose the final speech. Returns None if motion lacks a tagged estimate
    (caller must retry motion upstream)."""
    m = EST.search(motion)
    if not m:
        return None
    est_line = m.group(0)
    body = re.sub(r"\s*ESTIMATE:\s*\d{1,3}\s*%\s*", " ", motion).strip()
    body = re.sub(r"\s+", " ", body)
    if not body.endswith((".", "!", "?")):
        body += "."
    return " ".join([
        OPENER.format(dead_token=manifest["dead_token"]),
        body,
        BRIDGE.format(counterparty=manifest["counterparty"]),
        est_line,
    ])


# ---------------- stage-0 offline test (RUNBOOK15 frozen bar) ----------------

def _stage0():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from run13_checker import check_speech

    sources = []
    t14 = ROOT / "out/run14/transcript14.json"
    e14 = ROOT / "out/run14/eval_transcript14.json"
    man14 = {json.loads(l)["pid"]: json.loads(l)
             for l in (ROOT / "data/run14/train_problems.jsonl").open()}
    man13 = {json.loads(l)["pid"]: json.loads(l)
             for l in (ROOT / "data/run13/staged_problems.jsonl").open()}
    for path, man in ((t14, man14), (e14, man13)):
        if path.exists():
            for r in json.loads(path.read_text())["runs"]:
                sources.append((r, man[r["pid"]]))
    assert sources, "no run-14 transcripts found — stage 0 needs them"

    n = len(sources)
    ok_fid = ok_est = ok_verb = 0
    added_flags = {}
    for run, pr in sources:
        speech = assemble(run["motion"], pr)
        if speech is None:
            continue
        ok_est += 1
        up = [pr["problem"], pr["update"], run["audit"], run["read"],
              run.get("plan", ""), run["motion"]]
        man = {"counterparty": pr["counterparty"], "dead_token": pr["dead_token"],
               "problem": pr["problem"], "update": pr["update"]}
        r_full = check_speech(speech, up, man, run["motion"])
        r_motion = check_speech(run["motion"], up, man, run["motion"])
        motion_kinds = {k for k, _ in r_motion["fidelity_flags"]}
        # bar: flags in the ASSEMBLED speech must not exceed the motion's own —
        # i.e., the added template text introduces ZERO new flags
        new = [f for f in r_full["fidelity_flags"] if f[0] not in motion_kinds]
        if not new:
            ok_fid += 1
        else:
            for k, d in new:
                added_flags[(k, str(d)[:40])] = added_flags.get((k, str(d)[:40]), 0) + 1
        if r_full["verbosity_flag"] is None:
            ok_verb += 1
    print(f"stage-0 over {n} stored relays:")
    print(f"  tagged estimate present:      {ok_est}/{n}")
    print(f"  zero flags added by assembly: {ok_fid}/{ok_est} (bar: 100%)")
    print(f"  verbosity 60-200:             {ok_verb}/{ok_est} (bar: >=95%)")
    if added_flags:
        print("  added-flag detail:", added_flags)
    passed = ok_fid == ok_est and ok_verb >= 0.95 * ok_est
    print("STAGE 0:", "PASS" if passed else "FAIL — iterate templates ($0)")
    return passed


if __name__ == "__main__":
    _stage0()
