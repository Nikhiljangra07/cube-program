"""
run13_stage.py — RUN 13 staged-problem generator (RUNBOOK13 frozen, seed 13).

24 deterministic decision problems, 3 archetypes x 8. Every fact PLANTED so the
fidelity checker is mechanical: unique counterparty surname (prediction-as-fact
check), unique dead-token codename (revival check), planted figures (provenance
check), an UPDATE that kills the codename and changes one number.

  python scripts/run13_stage.py     # writes data/run13/staged_problems.jsonl + md5
"""
from __future__ import annotations
import hashlib, json, random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/run13/staged_problems.jsonl"

SURNAMES = ["Calloway", "Reyes", "Okafor", "Lindqvist", "Bhandari", "Marchetti",
            "Osei", "Novak", "Ferreira", "Takahashi", "Adeyemi", "Kowalski",
            "Vance", "Herrera", "Abara", "Sorensen", "Rahimi", "Castellanos",
            "Duran", "Mbeki", "Petrova", "Kealoha", "Ostrowski", "Nakamura"]
CODENAMES = ["Meridian", "Halcyon", "Corsair", "Beacon", "Vantage", "Solstice",
             "Citadel", "Argent", "Lattice", "Quarry", "Cobalt", "Sable",
             "Ridgeline", "Foxglove", "Ironwood", "Bellwether", "Northstar",
             "Palisade", "Riverstone", "Granite", "Falcon", "Aurora", "Drift",
             "Keystone"]
COLLEAGUES = ["Priya", "Marcus", "Elena", "Tomas", "Ingrid", "Dev", "Rosa", "Kofi"]
MONTHS = ["March", "April", "May", "June", "July", "August", "September"]

# observed-timeline behaviors (verbs here are EXEMPT from the prediction check
# because they appear in the problem text — that is by design)
OBS = ["postponed the scheduled review call twice, citing internal conflicts",
       "declined to confirm the volume terms in writing",
       "forwarded a draft agreement referencing an unnamed second partner",
       "requested an extended exclusivity window without explaining why",
       "skipped the joint working session and sent a junior associate instead",
       "mentioned in passing that budget approvals now route through a new committee",
       "posted publicly about expanding into an adjacent market",
       "copied an unfamiliar advisor on the last two email threads"]

ARCH = {
    "vendor": {
        "intro": ("You are the {role} at a {org}. A critical platform launch depends on an "
                  "external vendor led by {surname}, and the contract window is closing."),
        "role": ["Digital Editor", "Head of Operations", "Product Lead"],
        "org": ["regional newspaper", "60-person logistics firm", "specialty retail chain"],
        "table": ("ON THE TABLE: an expedite package internally dubbed the {code} option — "
                  "{surname}'s firm would commit to delivery by {d_deliver} for an extra "
                  "${sweet}, payable on a handshake before formal sign-off."),
        "decide": ("DECISION NOW: redirect {colleague}'s remaining {hours} weekly hours to "
                   "manual testing of the incomplete integration, or keep {colleague} on "
                   "content and press {surname} for the original schedule?"),
        "kill": ("the {code} option is withdrawn entirely — {surname}'s firm can no longer "
                 "commit staff to any expedited schedule"),
    },
    "partner": {
        "intro": ("You are the {role} at a {org}, negotiating a multi-year agreement with a "
                  "counterpart named {surname}, and you suspect a rival bidder is in play."),
        "role": ["VP of Partnerships", "Commercial Director", "Head of Licensing"],
        "org": ["mid-size software company", "food distribution cooperative", "media studio"],
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
        "role": ["founder", "managing partner", "general manager"],
        "org": ["12-person design agency", "family-run food business", "boutique gym"],
        "table": ("ON THE TABLE: a pre-lease arrangement internally dubbed the {code} track — "
                  "{surname} holds the space until {d_deliver} for a non-refundable ${sweet} "
                  "deposit, with no terms in writing yet."),
        "decide": ("DECISION NOW: commit {colleague} and the ${budget} reserve to fitting out "
                   "the new space now, or hold cash and negotiate month-to-month while "
                   "{surname} shops the space?"),
        "kill": ("the {code} track is dead — {surname} informs you the owner has taken the "
                 "hold arrangement off the market"),
    },
}


def build(pid, arch_key, rng):
    a = ARCH[arch_key]
    surname = SURNAMES[pid]
    code = CODENAMES[pid]
    colleague = rng.choice(COLLEAGUES)
    budget = rng.choice([28, 34, 41, 47, 52, 63, 76, 88]) * 1000 + rng.choice([500, 0])
    cap = rng.choice([4, 5, 6]) * 1000
    sweet = rng.choice([9, 11, 13, 15, 17]) * 1000
    hours = rng.choice([12, 16, 18, 24])
    m = rng.randrange(len(MONTHS) - 2)
    d1 = f"{MONTHS[m]} {rng.randrange(3, 27)}"
    d2 = f"{MONTHS[m + 1]} {rng.randrange(3, 27)}"
    d_deliver = f"{MONTHS[m + 2]} {rng.randrange(3, 15)}"
    d_deadline = f"{MONTHS[m + 2]} {rng.randrange(16, 28)}"
    obs1, obs2 = rng.sample(OBS, 2)
    delta = rng.choice([3, 4, 6]) * 1000
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
    rng = random.Random(13)
    rows = [build(i, ("vendor", "partner", "expand")[i % 3], rng) for i in range(24)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    md5 = hashlib.md5(OUT.read_bytes()).hexdigest()
    # determinism check: rebuild and compare
    rng2 = random.Random(13)
    rows2 = [build(i, ("vendor", "partner", "expand")[i % 3], rng2) for i in range(24)]
    assert rows == rows2, "NON-DETERMINISTIC BUILD"
    # uniqueness checks
    assert len({r["counterparty"] for r in rows}) == 24
    assert len({r["dead_token"] for r in rows}) == 24
    print(f"24 staged problems -> {OUT}")
    print(f"md5 {md5}  (deterministic: rebuild byte-identical, surnames+codenames unique)")


if __name__ == "__main__":
    main()
