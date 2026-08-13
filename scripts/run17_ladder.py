"""
run17_ladder.py — RUN 17 capacity-ladder problem generator (RUNBOOK17, seed 17).

40 deterministic strategic decision problems: 5 STATE-LOAD levels x 8 problems.
State load = the number of planted facts the answer must track. Fact types are
NESTED across levels (each level adds fact types to the previous level's set),
so load is the ONLY variable; archetype mix, prompt, and decoding are constant.

  L1 = 2 facts   (deadline, budget)
  L2 = 4 facts   (+ colleague-hours, observation-1)
  L3 = 6 facts   (+ offer-on-the-table, approval-cap)   <- match-bench-like load
  L4 = 8 facts   (+ observation-2, second-colleague)
  L5 = 10 facts  (+ held-inventory, regulatory-constraint)

Every fact carries a plantable token (number, name, date) so the strict
coherence read is mechanical. Entity pools are DISJOINT from run13 staged
surnames/codenames, run14 pools, and run16 synthetic ACTORS — the verifier
under test has never seen these names in any training label.

  python scripts/run17_ladder.py   # writes data/run17/ladder_problems.jsonl + md5
"""
from __future__ import annotations
import hashlib, json, random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/run17/ladder_problems.jsonl"

SURNAMES = ["Aldercroft", "Bellamira", "Cotswald", "Draventi", "Elphinstone",
            "Farrowgate", "Gildenhall", "Hollowbrook", "Ivencourt", "Jasperlyn",
            "Kentwilde", "Lorimont", "Maravelle", "Nethercott", "Ollivander",
            "Pemsworth", "Quillfeather", "Ravensmere", "Silverthorn", "Tarrowmoor",
            "Umberfield", "Vantrellis", "Wyndermere", "Xanthippe", "Yarrowdale",
            "Zephyrine", "Ashgrove-Nile", "Briarholm", "Cindervale", "Dunmorrow",
            "Everleth", "Foxwharton", "Greyvale", "Huxtermill", "Ironsgate",
            "Juniperre", "Kestwick", "Larkmoor", "Mistrelane", "Northquill"]
CODENAMES = ["Tessellate", "Windrose", "Copperline", "Marrowgate", "Skylark",
             "Thornfield", "Vellum", "Wintermark", "Yieldstone", "Zenithal",
             "Ambercrest", "Bracken", "Cloudbreak", "Duskwater", "Embertide",
             "Frostpane", "Gablewood", "Harborlight", "Inkwell", "Jettison",
             "Kilnview", "Lodestone", "Mothwing", "Nightjar", "Oakenshield",
             "Pinnacle", "Quartzite", "Rainshadow", "Saltmarsh", "Tidebreak",
             "Underwood", "Vesselgate", "Wheelhouse", "Yellowfin", "Zincline",
             "Archline", "Bellcurve", "Crestfall", "Dovewind", "Eastmarch"]
COLLEAGUES = ["Anouk", "Bram", "Csilla", "Darius", "Esme", "Farid", "Greta", "Hollis",
              "Imani", "Jasper", "Katya", "Lior", "Milena", "Nadir", "Odette", "Pavel"]
MONTHS = ["March", "April", "May", "June", "July", "August", "September"]
OBS = ["postponed the scheduled review call twice, citing internal conflicts",
       "declined to confirm the volume terms in writing",
       "forwarded a draft agreement referencing an unnamed second partner",
       "requested an extended exclusivity window without explaining why",
       "skipped the joint working session and sent a junior associate instead",
       "mentioned that budget approvals now route through a new committee",
       "posted publicly about expanding into an adjacent market",
       "copied an unfamiliar advisor on the last two email threads"]
INVENTORY = ["a paid-up equipment lease running through {d2}",
             "a transferable permit valid until {d2}",
             "a storage unit under contract through {d2}",
             "a retainer with an outside counsel capped at 10 hours"]
CONSTRAINT = ["any public announcement before {d2} requires board notice",
              "the {org} bylaws bar multi-year commitments without a partner vote",
              "an open compliance review freezes new hires until {d2}",
              "insurance terms void if work begins before a site inspection"]

ARCH = {
    "vendor": {"intro": ("You are the {role} at a {org}. A critical platform launch depends "
                         "on an external vendor led by {surname}, and the contract window is "
                         "closing."),
               "role": ["Digital Editor", "Head of Operations", "Product Lead"],
               "org": ["regional newspaper", "60-person logistics firm", "specialty retail chain"],
               "decide": ("DECISION NOW: press {surname} for the original schedule, or "
                          "restructure the launch around what you hold?")},
    "partner": {"intro": ("You are the {role} at a {org}, negotiating a multi-year agreement "
                          "with a counterpart named {surname}, and you suspect a rival bidder "
                          "is in play."),
                "role": ["VP of Partnerships", "Commercial Director", "Head of Licensing"],
                "org": ["mid-size software company", "food distribution cooperative", "media studio"],
                "decide": ("DECISION NOW: impose a hard final-offer deadline, or improve terms "
                           "to close before the suspected rival does?")},
    "expand": {"intro": ("You are the {role} of a {org} weighing a one-site expansion. The "
                         "landlord's agent, {surname}, controls the only suitable space in "
                         "the district."),
               "role": ["founder", "managing partner", "general manager"],
               "org": ["12-person design agency", "family-run food business", "boutique gym"],
               "decide": ("DECISION NOW: commit to the space now, or hold cash and negotiate "
                          "month-to-month while {surname} shops it?")},
    "crisis": {"intro": ("You are the {role} at a {org}. A key client managed by {surname} "
                         "has signaled they may not renew, and the renewal date is close."),
               "role": ["Account Director", "Client Services Lead", "Managing Consultant"],
               "org": ["marketing consultancy", "IT services firm", "training company"],
               "decide": ("DECISION NOW: escalate directly to {surname} with a retention "
                          "offer, or quietly line up replacement revenue first?")},
}

LEVEL_FACTS = {1: 2, 2: 4, 3: 6, 4: 8, 5: 10}


def build(pid, level, arch_key, rng):
    a = ARCH[arch_key]
    surname = SURNAMES[pid]
    code = CODENAMES[pid]
    c1, c2 = rng.sample(COLLEAGUES, 2)
    budget = rng.choice([28, 34, 41, 47, 52, 63, 76, 88]) * 1000 + rng.choice([500, 0])
    cap = rng.choice([4, 5, 6]) * 1000
    sweet = rng.choice([9, 11, 13, 15, 17]) * 1000
    hours = rng.choice([12, 16, 18, 24])
    hours2 = rng.choice([6, 8, 10])
    m = rng.randrange(len(MONTHS) - 2)
    d1 = f"{MONTHS[m]} {rng.randrange(3, 27)}"
    d2 = f"{MONTHS[m + 2]} {rng.randrange(16, 28)}"
    d_deliver = f"{MONTHS[m + 2]} {rng.randrange(3, 15)}"
    obs1, obs2 = rng.sample(OBS, 2)
    org = rng.choice(a["org"])
    inv = rng.choice(INVENTORY).format(d2=d2)
    con = rng.choice(CONSTRAINT).format(d2=d2, org=org)
    # nested fact list, fixed priority order (the load knob)
    facts = [
        f"Hard deadline: {d2}; after it the opportunity lapses.",
        f"${budget:,} in uncommitted budget.",
        f"{c1}, your strongest operator, has {hours} hours per week free for this and no more.",
        f"Observed {d1}: {surname} {obs1}.",
        (f"ON THE TABLE: an option internally dubbed the {code} track — {surname} holds "
         f"the terms open until {d_deliver} for ${sweet:,}, nothing in writing yet."),
        f"Any single expense above ${cap:,} requires sign-off you cannot get before {d2}.",
        f"Also observed: {surname} {obs2}.",
        f"{c2} can contribute {hours2} hours per week, but only after {d1}.",
        f"You hold {inv}.",
        f"Constraint: {con}",
    ]
    k = LEVEL_FACTS[level]
    fact_block = " ".join(f"({i+1}) {f}" for i, f in enumerate(facts[:k]))
    fmt = dict(role=rng.choice(a["role"]), org=org, surname=surname)
    problem = (f"{a['intro'].format(**fmt)} WHAT YOU HOLD: {fact_block} "
               f"{a['decide'].format(**fmt)}")
    return {"pid": pid, "level": level, "n_facts": k, "arch": arch_key,
            "problem": problem, "counterparty": surname,
            "code_token": f"the {code}" if k >= 5 else None}


def main():
    # disjointness guards vs every pool the verifier saw in training labels
    import importlib.util
    r13 = set("Calloway Reyes Okafor Lindqvist Bhandari Marchetti Osei Novak Ferreira "
              "Takahashi Adeyemi Kowalski Vance Herrera Abara Sorensen Rahimi Castellanos "
              "Duran Mbeki Petrova Kealoha Ostrowski Nakamura".split())
    r16 = set("Halvorsen Okafor Brandt Ceballos Whitfield Marchetti Duval Petrov "
              "Lindqvist Abernathy".split())
    r14 = set("Ashworth Baptiste Cormier Delacroix Eversole Fairbanks Galloway Hargrove "
              "Iwamoto Jokinen Kessler Lachance Mansour Nordvik Obradovic Pemberton "
              "Quintero Rosales Sandoval Thackeray Umarov Villanueva Wetherby Yamasaki "
              "Zielinski Ansaldo Beaumont Castellan Dragomir Eskola Fontaine Grimaldi "
              "Havelock Ilyenko Jarvis Kirchner Lindgren Motravec Norwood Oyelaran".split())
    assert not (set(SURNAMES) & (r13 | r16 | r14)), "surname pool collision"

    rng = random.Random(17)
    archs = list(ARCH)
    rows = []
    pid = 0
    for level in (1, 2, 3, 4, 5):
        for j in range(8):
            rows.append(build(pid, level, archs[j % 4], rng))
            pid += 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    # determinism + uniqueness
    rng2 = random.Random(17)
    rows2 = []
    pid = 0
    for level in (1, 2, 3, 4, 5):
        for j in range(8):
            rows2.append(build(pid, level, archs[j % 4], rng2))
            pid += 1
    assert rows == rows2, "NON-DETERMINISTIC"
    assert len({r["counterparty"] for r in rows}) == 40
    md5 = hashlib.md5(OUT.read_bytes()).hexdigest()
    words = [len(r["problem"].split()) for r in rows]
    print(f"40 ladder problems (5 levels x 8) -> {OUT}")
    for lv in (1, 2, 3, 4, 5):
        w = [len(r["problem"].split()) for r in rows if r["level"] == lv]
        print(f"  L{lv}: {LEVEL_FACTS[lv]} facts, {min(w)}-{max(w)} words")
    print(f"md5 {md5}  (deterministic, 40 unique fresh surnames, pools disjoint)")


if __name__ == "__main__":
    main()
