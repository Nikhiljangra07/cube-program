"""
run14_corpus.py — RUN 14 training-problem generator (RUNBOOK14 frozen, seed 14).

160 staged decision problems for the self-distillation corpus. Pools are FULLY
DISJOINT from the eval set's (run13_stage.py, seed 13) — verified at build:
no surname or codename overlap with data/run13/staged_problems.jsonl.
Same manifest contract (counterparty, dead_token) so the loop and the judge
prompts work unchanged. Four archetypes (vendor/partner/expand + crisis).

  python scripts/run14_corpus.py    # writes data/run14/train_problems.jsonl + md5
"""
from __future__ import annotations
import hashlib, json, random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/run14/train_problems.jsonl"
EVAL = ROOT / "data/run13/staged_problems.jsonl"

SURNAMES = ["Ashworth", "Baptiste", "Cormier", "Delacroix", "Eversole", "Fairbanks",
            "Galloway", "Hargrove", "Iwamoto", "Jokinen", "Kessler", "Lachance",
            "Mansour", "Nordvik", "Obradovic", "Pemberton", "Quintero", "Rosales",
            "Sandoval", "Thackeray", "Umarov", "Villanueva", "Wetherby", "Yamasaki",
            "Zielinski", "Ansaldo", "Beaumont", "Castellan", "Dragomir", "Eskola",
            "Fontaine", "Grimaldi", "Havelock", "Ilyenko", "Jarvis", "Kirchner",
            "Lindgren", "Motravec", "Norwood", "Oyelaran"]
CODENAMES = ["Amberline", "Basalt", "Cinder", "Dovetail", "Emberfall", "Flintlock",
             "Gossamer", "Hawthorn", "Ironbark", "Juniper", "Kingfisher", "Larkspur",
             "Mistral", "Nightjar", "Oakmont", "Pinnacle", "Quarterline", "Redwood",
             "Silverpine", "Tidewater", "Umberly", "Valeview", "Wintermark", "Yellowbird",
             "Zephyrline", "Ashgrove", "Brindle", "Coppervein", "Duskwater", "Elmstead",
             "Fernline", "Goldcrest", "Harborlight", "Inkwell", "Jadeway", "Kestrelmoor",
             "Lanternhill", "Marrowgate", "Nettlebrook", "Oxbowline"]
COLLEAGUES = ["Sana", "Viktor", "Amara", "Jonas", "Leila", "Owen", "Yuki", "Bram",
              "Noor", "Felix", "Zara", "Iker"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October"]
OBS = ["postponed the scheduled review call twice, citing internal conflicts",
       "declined to confirm the volume terms in writing",
       "forwarded a draft agreement referencing an unnamed second partner",
       "requested an extended exclusivity window without explaining why",
       "skipped the joint working session and sent a junior associate instead",
       "mentioned in passing that budget approvals now route through a new committee",
       "posted publicly about expanding into an adjacent market",
       "copied an unfamiliar advisor on the last two email threads",
       "asked twice who else you had spoken with about the terms",
       "began responding only through their assistant",
       "invited a third party to observe the last negotiation call",
       "announced an internal reorganization affecting your main contact"]

ARCH = {
    "vendor": {
        "intro": ("You are the {role} at a {org}. A critical platform launch depends on an "
                  "external vendor led by {surname}, and the contract window is closing."),
        "role": ["Delivery Manager", "Head of Platform", "Launch Director"],
        "org": ["regional insurer", "45-person e-learning firm", "specialty publisher"],
        "table": ("ON THE TABLE: an expedite package internally dubbed the {code} option — "
                  "{surname}'s firm would commit to delivery by {d_deliver} for an extra "
                  "${sweet}, payable on a handshake before formal sign-off."),
        "decide": ("DECISION NOW: redirect {colleague}'s remaining {hours} weekly hours to "
                   "manual testing of the incomplete integration, or keep {colleague} on "
                   "core work and press {surname} for the original schedule?"),
        "kill": ("the {code} option is withdrawn entirely — {surname}'s firm can no longer "
                 "commit staff to any expedited schedule"),
    },
    "partner": {
        "intro": ("You are the {role} at a {org}, negotiating a multi-year agreement with a "
                  "counterpart named {surname}, and you suspect a rival bidder is in play."),
        "role": ["Alliances Lead", "Business Development Director", "Head of Distribution"],
        "org": ["regional brewery group", "industrial sensor maker", "animation studio"],
        "table": ("ON THE TABLE: a concession bundle internally dubbed the {code} package — "
                  "granting {surname} exclusivity through {d_deliver} in exchange for a "
                  "${sweet} upfront commitment, unsigned but verbally floated."),
        "decide": ("DECISION NOW: impose a hard final-offer deadline of {d_deadline} with "
                   "reduced concessions, or preemptively improve terms to close before the "
                   "suspected rival does?"),
        "kill": ("the {code} package is off the table entirely — legal has barred any "
                 "exclusivity clause after a regulator inquiry"),
    },
    "expand": {
        "intro": ("You are the {role} of a {org} weighing a one-site expansion. The landlord's "
                  "agent, {surname}, controls the only suitable space in the district."),
        "role": ["founder", "co-owner", "operations chief"],
        "org": ["ceramics studio", "family bakery chain", "climbing gym"],
        "table": ("ON THE TABLE: a pre-lease arrangement internally dubbed the {code} track — "
                  "{surname} holds the space until {d_deliver} for a non-refundable ${sweet} "
                  "deposit, with no terms in writing yet."),
        "decide": ("DECISION NOW: commit {colleague} and the ${budget} reserve to fitting out "
                   "the new space now, or hold cash and negotiate month-to-month while "
                   "{surname} shops the space?"),
        "kill": ("the {code} track is dead — {surname} informs you the owner has taken the "
                 "hold arrangement off the market"),
    },
    "crisis": {
        "intro": ("You are the {role} at a {org}. A key account managed through {surname} is "
                  "wobbling after a service failure, and renewal season is weeks away."),
        "role": ["Account Director", "Customer Success Lead", "Managing Consultant"],
        "org": ["IT services partnership", "regional logistics broker", "training consultancy"],
        "table": ("ON THE TABLE: a make-good bundle internally dubbed the {code} offer — "
                  "a ${sweet} service credit plus priority staffing through {d_deliver}, "
                  "drafted but not yet approved by anyone above you."),
        "decide": ("DECISION NOW: spend {colleague}'s {hours} weekly hours on a full remediation "
                   "audit before renewal talks, or go straight to {surname} with terms and "
                   "handle findings as they surface?"),
        "kill": ("the {code} offer is scrapped — finance has frozen all service credits "
                 "pending a quarter-end review"),
    },
}


def build(pid, arch_key, rng):
    a = ARCH[arch_key]
    surname = SURNAMES[pid % len(SURNAMES)] if pid < len(SURNAMES) else \
        SURNAMES[pid % len(SURNAMES)]
    code = CODENAMES[pid % len(CODENAMES)]
    colleague = rng.choice(COLLEAGUES)
    budget = rng.choice([23, 29, 36, 42, 48, 55, 61, 72, 84, 91]) * 1000 + rng.choice([500, 0])
    cap = rng.choice([3, 4, 5, 6, 7]) * 1000
    sweet = rng.choice([8, 10, 12, 14, 16, 18]) * 1000
    hours = rng.choice([10, 14, 16, 20, 22])
    m = rng.randrange(len(MONTHS) - 2)
    d1 = f"{MONTHS[m]} {rng.randrange(3, 27)}"
    d2 = f"{MONTHS[m + 1]} {rng.randrange(3, 27)}"
    d_deliver = f"{MONTHS[m + 2]} {rng.randrange(3, 15)}"
    d_deadline = f"{MONTHS[m + 2]} {rng.randrange(16, 28)}"
    obs1, obs2 = rng.sample(OBS, 2)
    delta = rng.choice([2, 3, 5, 7]) * 1000
    fmt = dict(role=rng.choice(a["role"]), org=rng.choice(a["org"]), surname=surname,
               code=code, colleague=colleague, budget=f"{budget:,}", cap=f"{cap:,}",
               sweet=f"{sweet:,}", hours=hours, d_deliver=d_deliver, d_deadline=d_deadline)
    problem = (
        f"{a['intro'].format(**fmt)} WHAT YOU HOLD: (1) ${budget:,} in uncommitted budget; "
        f"any single expense above ${cap:,} requires sign-off you cannot get before "
        f"{d_deadline}. (2) {colleague}, your strongest operator, has {hours} hours per week "
        f"free for this and no more. (3) Hard deadline: {d_deadline}; after it the "
        f"opportunity lapses. OBSERVED: (a) {d1}: {surname} {obs1}. (b) {d2}: {surname} "
        f"{obs2}. {a['table'].format(**fmt)} {a['decide'].format(**fmt)}")
    update = (f"UPDATE ({d_deadline.split()[0]} {rng.randrange(1, 12)}): "
              f"{a['kill'].format(**fmt)}; separately, the available budget figure is "
              f"revised to ${budget - delta:,} after a booking error surfaced.")
    return {"pid": pid, "arch": arch_key, "problem": problem, "update": update,
            "counterparty": surname, "dead_token": f"the {code}",
            "colleague": colleague}


def main():
    rng = random.Random(14)
    kinds = ("vendor", "partner", "expand", "crisis")
    rows = [build(i, kinds[i % 4], rng) for i in range(160)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    md5 = hashlib.md5(OUT.read_bytes()).hexdigest()
    # determinism
    rng2 = random.Random(14)
    assert rows == [build(i, kinds[i % 4], rng2) for i in range(160)], "NON-DETERMINISTIC"
    # DISJOINTNESS vs eval set (frozen bar precondition)
    ev = [json.loads(l) for l in EVAL.open()]
    ev_sur = {e["counterparty"] for e in ev}
    ev_code = {e["dead_token"] for e in ev}
    tr_sur = {r["counterparty"] for r in rows}
    tr_code = {r["dead_token"] for r in rows}
    assert not (ev_sur & tr_sur), f"SURNAME OVERLAP: {ev_sur & tr_sur}"
    assert not (ev_code & tr_code), f"CODENAME OVERLAP: {ev_code & tr_code}"
    print(f"160 training problems -> {OUT}")
    print(f"md5 {md5}")
    print(f"disjointness vs eval: surnames OK ({len(tr_sur)} vs {len(ev_sur)}), "
          f"codenames OK ({len(tr_code)} vs {len(ev_code)})")


if __name__ == "__main__":
    main()
