"""
run15_match.py — RUN 15 stage-2 driver: THE MATCH (RUNBOOK15 frozen bars).

Laptop-side conductor. Keys stay local; the pod runs one detached night job.

  source ~/Desktop/reasoningEngine/load_keys.sh
  python scripts/run15_match.py --setup  --pod HOST:PORT   # upload adapters+pip (new pod)
  python scripts/run15_match.py --launch --pod HOST:PORT [--refs m1,m2]  # start night job
  python scripts/run15_match.py --status --pod HOST:PORT   # peek progress
  python scripts/run15_match.py --judge  --pod HOST:PORT   # morning: pull + judge + verdict
  python scripts/run15_match.py --judge-refs --pod HOST:PORT  # optional, own cap
  python scripts/run15_match.py --mock                     # $0 offline dry run

FROZEN BARS (RUNBOOK15 stage 2):
  dossier   : cube overall_B >= gen overall_B + 0.20
  inventory : cube core_C >= gen core_C + 0.20 AND cube resource_grounding >= gen
  motion    : cube parse >= 30/32, boost >= 75%, nerf >= 75%, ack >= 24/32
  general   : cube overall >= gen overall - 0.15
  fidelity  : cube coherent-rate >= gen coherent-rate (pooled dossier+inventory
              reads; the LABELED post-hoc amendment, authorized 2026-08-10)
  attribution: cube core_C - ablate core_C >= 0.10 else V seat swaps to keep100

SPEND CAPS: thesis judging <= 260 billed reads; refs <= 180. Driver counts
uncached work and aborts BEFORE billing if over. All verdicts cached in
out/run15/match_judge_cache.jsonl keyed (leg|arm|idx|md5) — reruns re-bill zero.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, os, re, statistics, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("ANTHROPIC_API_KEY", "")  # head2head_v5 hard-requires it
import head2head_v5 as H  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out/run15/match"
BENCH = OUT / "bench"
CACHE = ROOT / "out/run15/match_judge_cache.jsonl"
EV = OUT / "events.jsonl"
READ_CAP = 260
READ_CAP_REFS = 180
MOCK = False

BDIMS = ("prediction_specificity", "evidence_grounding", "calibration", "positioning", "falsifiability")
CDIMS = ("resource_grounding", "seat_fidelity", "causal_soundness", "friction_realism",
         "decisive_completeness", "estimate_derivation")
CORE = CDIMS[:5]

# ---- single-answer rubrics: set->single adaptation of the FROZEN run-9b B and
# run-10 C rubrics (same dimension wording), with fidelity FOLDED into the same
# read (the amended relative-fidelity leg) — frozen here before any output.
COHERENCE_FOLD = (
    '\nAlso return "coherent": true|false — false if the response contains ANY of: '
    "a number/resource/actor/event not present in the problem text, a "
    "self-contradiction, or a predicted reaction stated as an event that has "
    'already happened. And "flaws": a brief list of each such violation '
    "(empty list if coherent).\n")

BPROMPT_S = """You are grading ONE candidate response to a decision problem that includes a
DOSSIER of observed counterparty behavior. Grade EVIDENCE-FED FORESIGHT only. Be a strict critic.

PROBLEM (with dossier): {problem}

RESPONSE:
{answer}

Score the RESPONSE 1-5 on each dimension (5 = excellent, 1 = fails):
- prediction_specificity: does it name the counterparty's likely NEXT 1-3 moves concretely
  (who does what, when) rather than vague "they may resist"?
- evidence_grounding: is every prediction traceable to specific dossier observations (cite-able
  to an observed behavior), with nothing invented beyond the evidence?
- calibration: does confidence scale with evidence strength — acknowledging the innocent
  reading where the dossier supports it, not treating every signal as hostile?
- positioning: does the plan EXPLOIT the predictions (pre-positioned counters, timed moves)
  rather than merely stating them?
- falsifiability: does it name observable signals that would disconfirm its read?
""" + COHERENCE_FOLD + """
Return ONLY JSON: {{"prediction_specificity":N,"evidence_grounding":N,"calibration":N,"positioning":N,"falsifiability":N,"coherent":true,"flaws":[]}}"""

CPROMPT_S = """You are grading ONE candidate response to a decision problem that includes an
explicit INVENTORY of what the actor actually holds (funds, people and their commitment level,
seat/authority, deadlines) and one tempting option on the table. Grade AUDIT-GROUNDED PLANNING
only. Be a strict critic.

PROBLEM (with inventory): {problem}

THE OPTION ON THE TABLE THAT EXCEEDS THE INVENTORY (known to you, not flagged to the writer):
{trap}

RESPONSE:
{answer}

Score the RESPONSE 1-5 on each dimension (5 = excellent, 1 = fails). HARD CAPS are absolute:
- resource_grounding: does every step spend only items in the inventory, with nothing invented
  beyond it (and the exceeding option either avoided or explicitly re-scoped to fit the
  inventory)? HARD CAP: any single invented resource, fact, or actor anywhere in the response
  means this dimension scores AT MOST 2.
- seat_fidelity: does the actor act only from the position/authority the inventory grants (no
  moves requiring a seat they do not hold)? HARD CAP: any single out-of-authority move means
  AT MOST 2.
- causal_soundness: does each step actually produce the next? HARD CAP: any step stating
  another party's unforced cooperation as certain means AT MOST 3.
- friction_realism: does the plan name real-world friction (legal, human, timeline) and carry
  an answer to it, rather than assuming a zero-friction world?
- decisive_completeness: does the response still COMMIT and resolve the decision — audit as
  foundation for action, never as an excuse to hedge?
- estimate_derivation: does it close with a success estimate that is visibly DERIVED —
  naming the favorable variable that earns it and the friction that caps it, consistent with
  the stated audit? (A bare or audit-inconsistent number = 1-2; a traceable, evidence-scaled
  estimate = 4-5; no estimate at all = 1. Score the derivation, never the number's truth.)
""" + COHERENCE_FOLD + """
Return ONLY JSON: {{"resource_grounding":N,"seat_fidelity":N,"causal_soundness":N,"friction_realism":N,"decisive_completeness":N,"estimate_derivation":N,"coherent":true,"flaws":[]}}"""

# ---- motion-leg scorer (run11_score logic, code-only, $0) ----
ESTLINE = re.compile(r"ESTIMATE:\s*(\d{1,3})\s*%", re.M)
STOP = set("""a an the and or of to in on for with by at from as is are was were be been has have
had it its this that these those you your he she they their we our i my new one two now must
will would can could may might should update""".split())


def words(t):
    return {w for w in re.findall(r"[a-z]+", t.lower()) if len(w) > 3 and w not in STOP}


def last_est(t):
    m = ESTLINE.findall(t)
    return float(m[-1]) if m else None


def emit(**kw):
    OUT.mkdir(parents=True, exist_ok=True)
    kw["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with EV.open("a") as f:
        f.write(json.dumps(kw) + "\n")


# ---------------- pod plumbing ----------------
def sh(cmd, timeout=900):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return 255, "SSH_TIMEOUT"


def ssh_cmd(pod, remote, timeout=900):
    host, port = pod.split(":")
    return sh(f"ssh -o StrictHostKeyChecking=no -p {port} root@{host} {json.dumps(remote)}", timeout)


def rsync(pod, src, dst, tries=6):
    host, port = pod.split(":")
    for i in range(tries):
        rc, o = sh(f"rsync -a --no-owner --no-group --partial --timeout=120 "
                   f"-e 'ssh -p {port} -o StrictHostKeyChecking=no' {src} {dst}"
                   .replace("POD:", f"root@{host}:"), 1800)
        if rc == 0:
            return
        print(f"  rsync retry {i+1}/{tries} ({src})", flush=True)
        time.sleep(15)
    sys.exit(f"rsync failed after {tries} tries: {src}")


# ---------------- bench build (deterministic, frozen sources) ----------------
def build_bench():
    BENCH.mkdir(parents=True, exist_ok=True)
    dos = [json.loads(l) for l in (ROOT / "data/run9b/dossier_problems.jsonl").open()]
    inv = [json.loads(l) for l in (ROOT / "data/run10/inventory_problems.jsonl").open()]
    boosts = [json.loads(l) for l in (ROOT / "data/run10/twin_problems.jsonl").open()]
    nerfs = [json.loads(l) for l in (ROOT / "data/run11/nerf_twins.jsonl").open()]
    gen = [json.loads(l) for l in (ROOT / "data/bench/problems.jsonl").open()]
    assert (len(dos), len(inv), len(boosts), len(nerfs), len(gen)) == (24, 32, 16, 16, 48)
    files = {
        "match_dossier.jsonl": [{"problem": r["problem"]} for r in dos],
        "match_inventory.jsonl": [{"problem": r["problem"]} for r in inv],  # trap STAYS local
        "match_twins.jsonl": ([{"kind": "boost", "base_index": r["base_index"],
                                "update": r["boost"]} for r in boosts] +
                              [{"kind": "nerf", "base_index": r["base_index"],
                                "update": r["nerf"]} for r in nerfs]),
        "match_general.jsonl": [{"problem": r["problem"]} for r in gen],
    }
    for name, rows in files.items():
        p = BENCH / name
        p.write_text("".join(json.dumps(r) + "\n" for r in rows))
        print(f"  {name}: {len(rows)} rows md5 {hashlib.md5(p.read_bytes()).hexdigest()[:12]}")


# ---------------- judge layer (cached, capped) ----------------
def load_cache():
    cache = {}
    if CACHE.exists():
        for l in CACHE.open():
            r = json.loads(l)
            cache[r["key"]] = r
    return cache


def ckey(leg, arm, idx, text):
    return f"{leg}|{arm}|{idx}|{hashlib.md5(text.encode()).hexdigest()[:12]}"


def mock_verdict(kind, key):
    h = int(hashlib.md5(key.encode()).hexdigest(), 16)
    if kind == "general":
        v = {d: 3 + (h >> i) % 3 for i, d in enumerate(H.DIMS)}
        v["mean"] = round(sum(v[d] for d in H.DIMS) / 6, 2)
        return v
    dims = BDIMS if kind == "dossier" else CDIMS
    v = {d: 2 + (h >> i) % 4 for i, d in enumerate(dims)}
    v["coherent"] = (h % 4) != 0
    v["flaws"] = [] if v["coherent"] else ["mock flaw"]
    return v


async def acall(client, prompt):
    import httpx  # noqa: F401
    async with H.SEM:
        for a in range(5):
            try:
                r = await client.post("https://api.anthropic.com/v1/messages",
                                      headers={"x-api-key": H.ANTHROPIC_KEY,
                                               "anthropic-version": "2023-06-01",
                                               "content-type": "application/json"},
                                      json={"model": "claude-sonnet-5", "max_tokens": 12000,
                                            "messages": [{"role": "user", "content": prompt}]},
                                      timeout=180)
                r.raise_for_status()
                d = r.json()
                text = "".join(p.get("text", "") for p in d.get("content", [])
                               if p.get("type") == "text").strip()
                if not text:
                    continue  # thinking ate the budget — retry
                return text
            except Exception:
                await asyncio.sleep(3 * (a + 1))
    return None


def valid(kind, j):
    if not isinstance(j, dict):
        return False
    if kind == "general":
        return all(isinstance(j.get(d), int) and 1 <= j[d] <= 5 for d in H.DIMS)
    dims = BDIMS if kind == "dossier" else CDIMS
    return (all(isinstance(j.get(d), int) and 1 <= j[d] <= 5 for d in dims)
            and isinstance(j.get("coherent"), bool) and isinstance(j.get("flaws"), list))


async def judge_items(items, cap):
    """items: [{key, kind, prompt}] -> {key: verdict}. Cache-first; cap on NEW reads."""
    cache = load_cache()
    for k in list(cache):
        if bool(cache[k].get("_mock")) != MOCK:   # mock/real cache wall
            del cache[k]
    todo = [it for it in items if it["key"] not in cache]
    print(f"  judge: {len(items)} items, {len(items)-len(todo)} cached, {len(todo)} new "
          f"(cap {cap})", flush=True)
    if len(todo) > cap:
        sys.exit(f"SPEND CAP: {len(todo)} new reads > {cap} — abort before billing")
    out = {it["key"]: cache[it["key"]]["verdict"] for it in items if it["key"] in cache}
    if not todo:
        return out
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    cf = CACHE.open("a")
    if MOCK:
        for it in todo:
            v = mock_verdict(it["kind"], it["key"])
            out[it["key"]] = v
            cf.write(json.dumps({"key": it["key"], "verdict": v, "_mock": True}) + "\n")
        cf.close()
        return out
    import httpx
    done = 0

    async def one(client, it):
        nonlocal done
        for attempt in range(3):
            text = await acall(client, it["prompt"])
            j = H.parse_json(text) if text else None
            if it["kind"] == "general" and j:
                try:
                    j = {d: int(j[d]) for d in H.DIMS}
                    j["mean"] = round(sum(j[d] for d in H.DIMS) / 6, 2)
                except Exception:
                    j = None
            if j and valid(it["kind"], j):
                out[it["key"]] = j
                cf.write(json.dumps({"key": it["key"], "verdict": j, "_mock": False}) + "\n")
                cf.flush()
                done += 1
                if done % 20 == 0:
                    print(f"    {done}/{len(todo)} judged", flush=True)
                return
        emit(stage="judge_fail", key=it["key"])

    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[one(client, it) for it in todo])
    cf.close()
    return out


def fmt_threads(angles, threads):
    return "\n".join(f"{i+1}. [{H.fam_of(a)}] {t}"
                     for i, (a, t) in enumerate(zip(angles, threads)))


# ---------------- legs ----------------
def score_motion(rows, inv):
    res = {}
    for arm in ("cube", "gen"):
        rs = [r for r in rows if r["arm"] == arm]
        n_parse = n_ack = 0
        dirs = {"boost": [], "nerf": []}
        for r in rs:
            ne, oe = last_est(r["revision"]), last_est(r["prior"])
            sig = words(r["update"]) - words(inv[r["base_index"]]["problem"])
            if sig and sig & words(r["revision"]):
                n_ack += 1
            if ne is None or oe is None:
                continue
            n_parse += 1
            d = ne - oe
            dirs[r["kind"]].append(d >= 0 if r["kind"] == "boost" else d <= 0)

        def pct(v):
            return round(100 * sum(v) / len(v), 1) if v else 0.0
        res[arm] = {"n": len(rs), "parse": n_parse, "ack": n_ack,
                    "boost_pct": pct(dirs["boost"]), "nerf_pct": pct(dirs["nerf"]),
                    "boost_n": len(dirs["boost"]), "nerf_n": len(dirs["nerf"])}
    c = res["cube"]
    res["bars"] = {"parse": c["parse"] >= 30, "boost": c["boost_pct"] >= 75,
                   "nerf": c["nerf_pct"] >= 75, "ack": c["ack"] >= 24}
    res["PASS"] = all(res["bars"].values())
    return res


def agg_single(verdicts, dims):
    ok = [v for v in verdicts if v]
    if not ok:
        return None
    s = {d: round(statistics.mean(v[d] for v in ok), 2) for d in dims}
    s["overall"] = round(statistics.mean(statistics.mean(v[d] for d in dims) for v in ok), 2)
    s["coherent_rate"] = round(sum(1 for v in ok if v.get("coherent")) / len(ok), 3)
    s["n"] = len(ok)
    return s


async def judge_all(pod):
    # ---- pull outputs ----
    if not MOCK:
        for f in ("match_dossier_out.jsonl", "match_inventory_out.jsonl",
                  "match_motion_out.jsonl", "match_general_out.jsonl"):
            rsync(pod, f"POD:/workspace/div/out/{f}", f"{OUT}/")
    dos = [json.loads(l) for l in (OUT / "match_dossier_out.jsonl").open()]
    invr = [json.loads(l) for l in (OUT / "match_inventory_out.jsonl").open()]
    mot = [json.loads(l) for l in (OUT / "match_motion_out.jsonl").open()]
    genr = [json.loads(l) for l in (OUT / "match_general_out.jsonl").open()]
    inv_meta = [json.loads(l) for l in (ROOT / "data/run10/inventory_problems.jsonl").open()]
    traps = {i: r["trap"] for i, r in enumerate(inv_meta)}
    assert len(dos) == 24 and len(invr) == 32, "transcripts incomplete — night job not done?"
    gen_ok = [r for r in genr if "fail" not in r]

    # ---- motion leg first ($0) ----
    motion = score_motion(mot, inv_meta)
    print(f"\nMOTION (code, $0): cube parse {motion['cube']['parse']}/32 "
          f"boost {motion['cube']['boost_pct']}% nerf {motion['cube']['nerf_pct']}% "
          f"ack {motion['cube']['ack']}/32 -> {'PASS' if motion['PASS'] else 'FAIL'} "
          f"| gen parse {motion['gen']['parse']}/32 boost {motion['gen']['boost_pct']}% "
          f"nerf {motion['gen']['nerf_pct']}% ack {motion['gen']['ack']}/32", flush=True)

    # ---- assemble judge items ----
    items = []
    for r in dos:
        for arm, ans in (("cube", r["cube"]["answer"]), ("gen", r["gen"])):
            items.append({"key": ckey("dossier", arm, r["idx"], ans), "kind": "dossier",
                          "leg": "dossier", "arm": arm, "idx": r["idx"],
                          "prompt": BPROMPT_S.format(problem=r["problem"], answer=ans)})
    for r in invr:
        for arm, ans in (("cube", r["cube"]["answer"]), ("ablate", r["ablate"]["answer"]),
                         ("gen", r["gen"])):
            items.append({"key": ckey("inventory", arm, r["idx"], ans), "kind": "inventory",
                          "leg": "inventory", "arm": arm, "idx": r["idx"],
                          "prompt": CPROMPT_S.format(problem=r["problem"],
                                                     trap=traps[r["idx"]], answer=ans)})
    for r in gen_ok:
        for arm, th in (("cube", r["cube_threads"]), ("gen", r["gen_threads"])):
            items.append({"key": ckey("general", arm, r["idx"], "|".join(th)),
                          "kind": "general", "leg": "general", "arm": arm, "idx": r["idx"],
                          "prompt": H.JUDGE_PROMPT.format(problem=r["problem"],
                                                          threads=fmt_threads(r["angles"], th))})
    verdicts = await judge_items(items, READ_CAP)

    # ---- coverage check (all-or-discard per leg+arm) ----
    legs = {}
    incomplete = []
    for it in items:
        legs.setdefault((it["leg"], it["arm"]), []).append(verdicts.get(it["key"]))
    for (leg, arm), vs in legs.items():
        if any(v is None for v in vs):
            incomplete.append(f"{leg}/{arm} ({sum(1 for v in vs if v)}/{len(vs)})")
    if incomplete:
        sys.exit(f"COVERAGE INSUFFICIENT: {incomplete} — verdicts cached, rerun --judge")

    # ---- aggregate + bars ----
    res = {"motion": motion}
    dsum = {arm: agg_single(legs[("dossier", arm)], BDIMS) for arm in ("cube", "gen")}
    csum = {arm: agg_single(legs[("inventory", arm)], CDIMS)
            for arm in ("cube", "ablate", "gen")}
    for arm in csum:
        vs = legs[("inventory", arm)]
        csum[arm]["core_C"] = round(statistics.mean(
            statistics.mean(v[d] for d in CORE) for v in vs), 2)
    gsum = {}
    for arm in ("cube", "gen"):
        vs = legs[("general", arm)]
        gsum[arm] = {d: round(statistics.mean(v[d] for v in vs), 2) for d in H.DIMS}
        gsum[arm]["overall"] = round(statistics.mean(v["mean"] for v in vs), 2)
        gsum[arm]["n"] = len(vs)
    res["dossier"], res["inventory"], res["general"] = dsum, csum, gsum

    bars = {
        "dossier": dsum["cube"]["overall"] >= dsum["gen"]["overall"] + 0.20,
        "inventory": (csum["cube"]["core_C"] >= csum["gen"]["core_C"] + 0.20
                      and csum["cube"]["resource_grounding"] >= csum["gen"]["resource_grounding"]),
        "motion": motion["PASS"],
        "general": gsum["cube"]["overall"] >= gsum["gen"]["overall"] - 0.15,
    }
    # fidelity (amended leg): pooled coherent-rate, cube vs gen, same-run
    pool = {arm: legs[("dossier", arm)] + legs[("inventory", arm)] for arm in ("cube", "gen")}
    fid = {arm: round(sum(1 for v in pool[arm] if v.get("coherent")) / len(pool[arm]), 3)
           for arm in pool}
    bars["fidelity"] = fid["cube"] >= fid["gen"]
    res["fidelity"] = fid
    attr_gap = round(csum["cube"]["core_C"] - csum["ablate"]["core_C"], 2)
    bars["attribution"] = attr_gap >= 0.10
    res["attribution_gap"] = attr_gap
    res["bars"] = bars
    res["legs_won"] = sum(bars.values())

    (OUT / "match_results.json").write_text(json.dumps(res, indent=1))
    print("\n================ THE MATCH — SCOREBOARD ================")
    print(f"dossier    : cube {dsum['cube']['overall']} vs gen {dsum['gen']['overall']} "
          f"(needs +0.20) {'WON' if bars['dossier'] else 'LOST'}")
    print(f"inventory  : core_C cube {csum['cube']['core_C']} vs gen {csum['gen']['core_C']} "
          f"(needs +0.20); rg {csum['cube']['resource_grounding']} vs "
          f"{csum['gen']['resource_grounding']} {'WON' if bars['inventory'] else 'LOST'}")
    print(f"motion     : {'WON' if bars['motion'] else 'LOST'} "
          f"(cube parse {motion['cube']['parse']}/32, boost {motion['cube']['boost_pct']}%, "
          f"nerf {motion['cube']['nerf_pct']}%, ack {motion['cube']['ack']}/32)")
    print(f"general    : cube {gsum['cube']['overall']} vs gen {gsum['gen']['overall']} "
          f"(floor -0.15) {'HELD' if bars['general'] else 'LOST'}")
    print(f"fidelity   : coherent cube {fid['cube']} vs gen {fid['gen']} "
          f"{'WON' if bars['fidelity'] else 'LOST'}  [amended leg]")
    print(f"attribution: cube-ablate core_C gap {attr_gap:+.2f} (needs +0.10) "
          f"{'V SEAT EARNED' if bars['attribution'] else 'V SEAT SWAPS TO KEEP100'}")
    print(f"----> legs won: {res['legs_won']}/6")
    print("(per-leg verdict philosophy: weigh what failed and what succeeded — no collapse)")
    return res


async def judge_refs(pod):
    files = []
    if not MOCK:
        rc, o = ssh_cmd(pod, "ls /workspace/div/out/match_refs_*.jsonl 2>/dev/null", 60)
        files = [Path(x).name for x in o.split() if x.strip()]
        for f in files:
            rsync(pod, f"POD:/workspace/div/out/{f}", f"{OUT}/")
    else:
        files = [p.name for p in OUT.glob("match_refs_*.jsonl")]
    if not files:
        sys.exit("no refs transcripts found")
    dosp = [json.loads(l) for l in (BENCH / "match_dossier.jsonl").open()]
    invp = [json.loads(l) for l in (BENCH / "match_inventory.jsonl").open()]
    inv_meta = [json.loads(l) for l in (ROOT / "data/run10/inventory_problems.jsonl").open()]
    items = []
    for fname in files:
        tag = fname[len("match_refs_"):-len(".jsonl")]
        for r in (json.loads(l) for l in (OUT / fname).open()):
            if r["leg"] == "dossier":
                items.append({"key": ckey("dossier", tag, r["idx"], r["answer"]),
                              "kind": "dossier", "leg": "dossier", "arm": tag, "idx": r["idx"],
                              "prompt": BPROMPT_S.format(problem=dosp[r["idx"]]["problem"],
                                                         answer=r["answer"])})
            else:
                items.append({"key": ckey("inventory", tag, r["idx"], r["answer"]),
                              "kind": "inventory", "leg": "inventory", "arm": tag, "idx": r["idx"],
                              "prompt": CPROMPT_S.format(problem=invp[r["idx"]]["problem"],
                                                         trap=inv_meta[r["idx"]]["trap"],
                                                         answer=r["answer"])})
    verdicts = await judge_items(items, READ_CAP_REFS)
    legs = {}
    for it in items:
        legs.setdefault((it["leg"], it["arm"]), []).append(verdicts.get(it["key"]))
    table = {}
    for (leg, arm), vs in legs.items():
        ok = [v for v in vs if v]
        dims = BDIMS if leg == "dossier" else CDIMS
        s = agg_single(ok, dims)
        if leg == "inventory" and ok:
            s["core_C"] = round(statistics.mean(statistics.mean(v[d] for d in CORE)
                                                for v in ok), 2)
        table.setdefault(arm, {})[leg] = s
    (OUT / "match_refs_results.json").write_text(json.dumps(table, indent=1))
    print("\n---- REFERENCE LADDER (reported, not gated) ----")
    for arm, t in table.items():
        d, c = t.get("dossier"), t.get("inventory")
        print(f"{arm:28s} dossier {d['overall'] if d else '—'} "
              f"(coh {d['coherent_rate'] if d else '—'}) | inventory core_C "
              f"{c.get('core_C') if c else '—'} (coh {c['coherent_rate'] if c else '—'})")
    return table


# ---------------- setup / launch / status ----------------
PIP = ("pip install --break-system-packages -q 'transformers<5' peft accelerate "
       "datasets sentencepiece 2>&1 | tail -1")


def do_setup(pod):
    stage = Path(os.environ.get("RUN15_ADAPTER_STAGE",
                                str(ROOT / ".r11_stage/adapters")))
    scratch = os.environ.get("RUN15_WORKER_STAGE", "")
    ssh_cmd(pod, "mkdir -p /workspace/div/out /workspace/div/adapters", 60)
    print("pip install (pod)...", flush=True)
    rc, o = ssh_cmd(pod, PIP, 900)
    print(f"  {o.strip().splitlines()[-1] if o.strip() else 'ok'}")
    print("uploading adapters (~2.1GB, retry-looped)...", flush=True)
    if scratch:
        rsync(pod, f"{scratch}/", "POD:/workspace/div/adapters/")
    rsync(pod, f"{stage}/dec_qwen", "POD:/workspace/div/adapters/")
    rc, o = ssh_cmd(pod, "ls /workspace/div/adapters | wc -l && "
                         "du -sh /workspace/div/adapters", 60)
    print(o.strip())
    print("SETUP DONE — run --launch next")


def do_launch(pod, refs):
    print("building bench files (deterministic):")
    build_bench()
    rc, o = ssh_cmd(pod, "ls /workspace/div/adapters | sort | tr '\\n' ' '", 60)
    need = {"dec_qwen", "wrk_faceF_9b_qwen", "wrk_faceV_10_qwen", "wrk_keep100_qwen"}
    have = set(o.split())
    if not need <= have:
        sys.exit(f"pod missing adapters: {sorted(need - have)} — run --setup first")
    print("uploading scripts + bench...")
    for f in ("run15_match_pod.py", "run12_router.py", "run13b_pod.py", "run11_common.py"):
        rsync(pod, str(ROOT / "scripts" / f), "POD:/workspace/div/")
    for f in BENCH.glob("match_*.jsonl"):
        rsync(pod, str(f), "POD:/workspace/div/")
    if refs:
        (OUT / "refs_models.json").write_text(json.dumps(refs.split(",")))
        rsync(pod, str(OUT / "refs_models.json"), "POD:/workspace/div/")
        print(f"refs enabled: {refs}")
    rc, o = ssh_cmd(pod, "tail -1 /workspace/div/out/match.log 2>/dev/null", 60)
    if "RUN15 MATCH" in o or "PHASE" in o:
        print(f"night job already running/complete: {o.strip()}")
        return
    ssh_cmd(pod, "cd /workspace/div && (setsid nohup python run15_match_pod.py "
                 "> out/match.log 2>&1 < /dev/null &)", 60)
    time.sleep(10)
    rc, o = ssh_cmd(pod, "tail -3 /workspace/div/out/match.log", 60)
    print(f"NIGHT JOB LAUNCHED (detached — laptop-free). log tail:\n{o.strip()}")
    print("\nMorning command:\n  source ~/Desktop/reasoningEngine/load_keys.sh && "
          "python scripts/run15_match.py --judge --pod " + pod)


def do_status(pod):
    rc, o = ssh_cmd(pod, "tail -5 /workspace/div/out/match.log 2>/dev/null; "
                         "for f in /workspace/div/out/match_*_out.jsonl; do "
                         "[ -f $f ] && echo \"$(basename $f): $(wc -l < $f) rows\"; done", 60)
    print(o.strip() or "no log yet")


# ---------------- mock ----------------
def build_mock():
    OUT.mkdir(parents=True, exist_ok=True)
    build_bench()
    dosp = [json.loads(l) for l in (BENCH / "match_dossier.jsonl").open()]
    invp = [json.loads(l) for l in (BENCH / "match_inventory.jsonl").open()]
    twins = [json.loads(l) for l in (BENCH / "match_twins.jsonl").open()]
    genp = [json.loads(l) for l in (BENCH / "match_general.jsonl").open()]

    def seg(i, tag):
        return {"audit": f"Audit {tag}{i}: holdings confirmed.",
                "read": f"Read {tag}{i}: they may counter within the window.",
                "plan": f"Plan {tag}{i}: commit audited hours. ESTIMATE: 60%",
                "est_injected": False,
                "answer": f"Audit {tag}{i}. Read {tag}{i}. Plan {tag}{i} committed. ESTIMATE: 60%"}
    with (OUT / "match_dossier_out.jsonl").open("w") as f:
        for i, p in enumerate(dosp):
            f.write(json.dumps({"idx": i, "problem": p["problem"], "cube": seg(i, "c"),
                                "gen": f"Gen answer {i}. ESTIMATE: 55%",
                                "gen_est_injected": False}) + "\n")
    with (OUT / "match_inventory_out.jsonl").open("w") as f:
        for i, p in enumerate(invp):
            f.write(json.dumps({"idx": i, "problem": p["problem"], "cube": seg(i, "c"),
                                "ablate": seg(i, "a"), "gen": f"Gen answer {i}. ESTIMATE: 55%",
                                "gen_est_injected": False}) + "\n")
    with (OUT / "match_motion_out.jsonl").open("w") as f:
        for tw in twins:
            i = tw["base_index"]
            upd_word = sorted(words(tw["update"]) - words(invp[i]["problem"]))
            tokn = upd_word[0] if upd_word else "update"
            for arm in ("cube", "gen"):
                new = 70 if tw["kind"] == "boost" else 45
                f.write(json.dumps({"arm": arm, "kind": tw["kind"], "base_index": i,
                                    "prior": "Plan. ESTIMATE: 60%", "update": tw["update"],
                                    "revision": f"The {tokn} changes the plan. "
                                                f"ESTIMATE: {new}%"}) + "\n")
    with (OUT / "match_general_out.jsonl").open("w") as f:
        for i, p in enumerate(genp):
            f.write(json.dumps({"idx": i, "problem": p["problem"],
                                "facets": ["f1", "f2", "f3"],
                                "angles": [f"[FAM{k}] angle {k}" for k in range(4)],
                                "seats": ["G", "G", "F", "V"],
                                "cube_threads": [f"cube thread {k} for {i}" for k in range(4)],
                                "gen_threads": [f"gen thread {k} for {i}" for k in range(4)]})
                    + "\n")
    with (OUT / "match_refs_mockref.jsonl").open("w") as f:
        for i in range(24):
            f.write(json.dumps({"leg": "dossier", "idx": i, "model": "mock/ref",
                                "answer": f"Ref answer d{i}. ESTIMATE: 50%"}) + "\n")
        for i in range(32):
            f.write(json.dumps({"leg": "inventory", "idx": i, "model": "mock/ref",
                                "answer": f"Ref answer i{i}. ESTIMATE: 50%"}) + "\n")


def main():
    global MOCK
    ap = argparse.ArgumentParser()
    ap.add_argument("--pod")
    ap.add_argument("--setup", action="store_true")
    ap.add_argument("--launch", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--judge", action="store_true")
    ap.add_argument("--judge-refs", action="store_true")
    ap.add_argument("--refs", default="")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    if args.mock:
        MOCK = True
        build_mock()
        asyncio.run(judge_all(None))
        asyncio.run(judge_refs(None))
        print("\nMOCK DRY RUN COMPLETE — full path exercised, $0")
        return
    if not args.pod:
        sys.exit("need --pod HOST:PORT")
    if not os.environ.get("ANTHROPIC_API_KEY") and (args.judge or args.judge_refs):
        sys.exit("ANTHROPIC_API_KEY not set — source load_keys.sh first")
    if args.setup:
        do_setup(args.pod)
    elif args.launch:
        do_launch(args.pod, args.refs)
    elif args.status:
        do_status(args.pod)
    elif args.judge:
        asyncio.run(judge_all(args.pod))
    elif args.judge_refs:
        asyncio.run(judge_refs(args.pod))
    else:
        sys.exit("pick one of --setup/--launch/--status/--judge/--judge-refs/--mock")


if __name__ == "__main__":
    main()
