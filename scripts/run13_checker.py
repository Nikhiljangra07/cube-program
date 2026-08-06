"""
run13_checker.py — RUN 13 fidelity checker (RUNBOOK13 frozen). Pure code, no LLM.

Five checks per speech, mirroring run-12's three observed sin classes plus the
two speech disciplines:
  invented_number    — every digit token in the speech exists upstream
  prediction_as_fact — counterparty + past-tense event verb not in problem/update
                       and no conditional marker in the sentence
  dead_option_revived— killed codename appears without a negation/supersession
                       marker in the same sentence
  estimate_drift     — speech ESTIMATE != motion ESTIMATE (or missing)
  verbosity          — outside 60-200 words (reported separately, NOT fidelity)

fidelity_flags = first four classes only. Dependency-free (ships to pod).

  python scripts/run13_checker.py   # self-test: 8 synthetic cases, must pass 8/8
"""
from __future__ import annotations
import re

NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
EST = re.compile(r"ESTIMATE:\s*(\d{1,3})\s*%")
SENT = re.compile(r"[^.!?]*[.!?]")
WORD = re.compile(r"[A-Za-z']+")

# past-tense event verbs a speech could use to state a predicted counterparty
# action as an accomplished fact (run-12 iter-1 sin class)
EVENT_VERBS = ("accepted", "agreed", "signed", "declined", "countered", "confirmed",
               "refused", "approved", "rejected", "responded", "replied", "committed",
               "conceded", "withdrew", "escalated", "matched", "capitulated", "folded",
               "walked away", "backed down", "came back", "returned with", "offered",
               "granted", "delivered", "paid")
CONDITIONAL = re.compile(r"\b(?:if|may|might|could|should|would|will likely|likely|"
                         r"unlikely|unless|expect\w*|predict\w*|anticipat\w*|risk\w*|"
                         r"probab\w*|assuming|contingent|were to|in case|whether|"
                         r"read|forecast\w*|scenario|hypothetical\w*|potential\w*)\b", re.I)
NEGATION = re.compile(r"\b(?:withdrawn|withdraw|dead|no longer|off the table|off the "
                      r"market|superseded|lost|gone|dropped|cancel\w*|barred|revoked|"
                      r"eliminated|unavailable|collapsed|was|had been|previously|"
                      r"former\w*|defunct|abandon\w*|without)\b", re.I)


def norm_nums(text: str) -> set:
    return {m.replace(",", "") for m in NUM.findall(text)}


def check_speech(speech: str, upstream: list, manifest: dict, motion: str) -> dict:
    """upstream = every text the speech may draw from (problem, update, segments).
    Returns {"fidelity_flags": [...], "verbosity_flag": str|None, "words": int}."""
    flags = []
    up_text = " ".join(upstream)

    # 1 — invented_number
    up_nums = norm_nums(up_text)
    for n in sorted(norm_nums(speech) - up_nums):
        flags.append(("invented_number", n))

    # 2 — prediction_as_fact
    cp = manifest["counterparty"].lower()
    known = (manifest["problem"] + " " + manifest["update"]).lower()
    for s in SENT.findall(speech) or [speech]:
        sl = s.lower()
        if cp not in sl:
            continue
        for v in EVENT_VERBS:
            if v in sl and v not in known and not CONDITIONAL.search(s):
                flags.append(("prediction_as_fact", v))

    # 3 — dead_option_revived
    dt = manifest["dead_token"].lower()
    for s in SENT.findall(speech) or [speech]:
        if dt in s.lower() and not NEGATION.search(s):
            flags.append(("dead_option_revived", manifest["dead_token"]))

    # 4 — estimate_drift
    ms, ss = EST.search(motion), EST.search(speech)
    if not ss:
        flags.append(("estimate_drift", "missing tagged ESTIMATE"))
    elif ms and ss.group(1) != ms.group(1):
        flags.append(("estimate_drift", f"{ms.group(1)}% -> {ss.group(1)}%"))

    # 5 — verbosity (separate dimension)
    words = len(WORD.findall(speech))
    vflag = None if 60 <= words <= 200 else f"{words} words (band 60-200)"
    return {"fidelity_flags": flags, "verbosity_flag": vflag, "words": words}


def feedback(flags) -> str:
    """Deterministic repair feedback for arm D retries."""
    lines = []
    for kind, detail in flags:
        if kind == "invented_number":
            lines.append(f"- You used the number {detail}, which appears nowhere in the "
                         f"problem or prior segments. Remove or replace it with a real one.")
        elif kind == "prediction_as_fact":
            lines.append(f"- You stated a predicted action ('{detail}') as if it already "
                         f"happened. It has NOT happened — restate it conditionally.")
        elif kind == "dead_option_revived":
            lines.append(f"- You referenced {detail}, which the UPDATE eliminated. Either "
                         f"drop it or state explicitly that it is no longer available.")
        elif kind == "estimate_drift":
            lines.append(f"- Your ESTIMATE line is wrong ({detail}). End with the CURRENT "
                         f"PLAN's estimate, unchanged, as `ESTIMATE: NN%`.")
    return "Your previous attempt had factual violations:\n" + "\n".join(lines)


# ---------------- self-test (RUNBOOK13: must pass 8/8 before pod) ----------------
def _selftest():
    man = {"counterparty": "Calloway", "dead_token": "the Meridian",
           "problem": "You hold $47,500. Deadline June 30. Calloway postponed the call. "
                      "ON THE TABLE: the Meridian option for $15,000.",
           "update": "UPDATE: the Meridian option is withdrawn; budget revised to $43,500."}
    up = [man["problem"], man["update"],
          "AUDIT: $47,500 held, revised to $43,500; 12 hours weekly.",
          "READ: Calloway may counter with a shorter window.",
          "PLAN: spend $4,000 on testing. ESTIMATE: 60%",
          "MOTION: with the Meridian option withdrawn, shift to manual QA. ESTIMATE: 55%"]
    motion = up[-1]
    ok = "With the Meridian option withdrawn, the plan shifts to manual QA using the 12 " \
         "weekly hours and the revised $43,500. If Calloway counters with a shorter " \
         "window, the deadline still holds. " + ("The team holds course. " * 12) + \
         "ESTIMATE: 55%"
    cases = [
        ("clean", ok, []),
        ("invented number", ok.replace("$43,500", "$52,750"), ["invented_number"]),
        ("prediction as fact", ok.replace("If Calloway counters",
                                          "Calloway countered"), ["prediction_as_fact"]),
        ("dead option revived", ok.replace("With the Meridian option withdrawn, the plan "
                                           "shifts", "The plan leans on the Meridian "
                                           "option and shifts"), ["dead_option_revived"]),
        # a drifted estimate is ALSO an invented number — both flags are correct
        ("estimate drift", ok.replace("ESTIMATE: 55%", "ESTIMATE: 70%"),
         ["estimate_drift", "invented_number"]),
        ("missing estimate", ok.replace("ESTIMATE: 55%", ""), ["estimate_drift"]),
        ("verbosity short", "Hold course. ESTIMATE: 55%", "VERBOSITY"),
        ("negated mention ok", ok.replace("the plan shifts",
                                          "the plan drops the Meridian entirely and shifts"),
         []),
    ]
    passed = 0
    for name, speech, want in cases:
        r = check_speech(speech, up, man, motion)
        got = sorted({k for k, _ in r["fidelity_flags"]})
        if want == "VERBOSITY":
            good = r["verbosity_flag"] is not None
        else:
            good = got == sorted(set(want))
        # verbosity must NOT fire on in-band cases
        if want != "VERBOSITY" and name != "verbosity short" and r["verbosity_flag"]:
            good = False
        print(f"  [{'PASS' if good else 'FAIL'}] {name}: flags={got} "
              f"verbosity={r['verbosity_flag']}")
        passed += good
    print(f"self-test: {passed}/8")
    if passed < 8:
        raise SystemExit("CHECKER SELF-TEST FAILED — do not proceed to pod")


if __name__ == "__main__":
    _selftest()
