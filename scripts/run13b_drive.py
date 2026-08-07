"""
run13b_drive.py — RUN 13B local orchestrator (RUNBOOK13B frozen). One command:

  source ~/Desktop/reasoningEngine/load_keys.sh && \
  python scripts/run13b_drive.py --pod HOST:PORT

Phases (resumable via out/run13b/state.json; judge verdicts cached, never
re-billed):
  relay    : launch pod relay detached, poll for completion, pull transcript
  round1   : code-filter A/C/D'a1 -> judge-certify code-cleans (session R)
             + precision spot-audit (quota 3 A + 3 C code-flagged)
  round2/3 : D' feedback (code + judge flaws) -> pod regenerates dirty pids ->
             pull -> filter+certify
  verdict  : frozen bars, results.json, observability events merged

Dry run (no pod, no API): python scripts/run13b_drive.py --mock
"""
from __future__ import annotations
import argparse, json, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run13_checker import check_speech, feedback as code_feedback, WORD  # noqa: E402
import run13b_judge as J  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out/run13b"
PROBS = ROOT / "data/run13/staged_problems.jsonl"
EV = OUT / "events.jsonl"
STATE = OUT / "state.json"
ARMS = ("A", "C", "Dp")


def emit(**kw):
    OUT.mkdir(parents=True, exist_ok=True)
    kw["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with EV.open("a") as f:
        f.write(json.dumps(kw) + "\n")


def state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"done": []}


def mark(phase):
    s = state()
    s["done"].append(phase)
    STATE.write_text(json.dumps(s))
    emit(stage="phase", phase=phase, status="done")


def sh(cmd, timeout=900):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def ssh_cmd(pod, remote, timeout=900):
    host, port = pod.split(":")
    return sh(f"ssh -o StrictHostKeyChecking=no -p {port} root@{host} {json.dumps(remote)}",
              timeout)


def rsync(pod, src, dst, timeout=600):
    host, port = pod.split(":")
    for i in range(3):
        rc, out = sh(f"rsync -a --no-owner --no-group --partial --timeout=90 "
                     f"-e 'ssh -p {port} -o StrictHostKeyChecking=no' {src} {dst}"
                     .replace("POD:", f"root@{host}:"), timeout)
        if rc == 0:
            return
        emit(stage="rsync_retry", attempt=i + 1, err=out[-200:])
        time.sleep(5)
    sys.exit(f"rsync failed 3x: {src} -> {dst}")


# ---------------- phases ----------------

def phase_relay(pod, mock):
    if "relay" in state()["done"]:
        return
    if mock:
        _mock_transcript()
    else:
        ssh_cmd(pod, "cd /workspace/div && (setsid nohup python run13b_pod.py --phase relay "
                     "> out/relay13b.log 2>&1 < /dev/null &)", 60)
        emit(stage="pod", action="relay_launched")
        t0 = time.time()
        while True:
            time.sleep(45)
            rc, out = ssh_cmd(pod, "grep -c 'RUN13B RELAY COMPLETE' /workspace/div/out/relay13b.log 2>/dev/null; "
                                   "tail -2 /workspace/div/out/relay13b.log", 60)
            if "RUN13B RELAY COMPLETE" in out:
                break
            if "Traceback" in out or "Error" in out and "CUDA" in out:
                sys.exit(f"POD RELAY FAILED:\n{out}")
            if time.time() - t0 > 4200:
                sys.exit("POD RELAY TIMEOUT (70 min)")
            emit(stage="pod", action="poll", tail=out.strip()[-120:],
                 mins=round((time.time() - t0) / 60, 1))
        rsync(pod, "POD:/workspace/div/out/transcript13b.json", f"{OUT}/")
        rsync(pod, "POD:/workspace/div/out/pod_events.jsonl", f"{OUT}/")
    mark("relay")


def load_data():
    t = json.loads((OUT / "transcript13b.json").read_text())
    man = {json.loads(l)["pid"]: json.loads(l) for l in PROBS.open()}
    return t, man


def item_of(arm, pid, attempt, run, pr, speech):
    return {"arm": arm, "pid": pid, "attempt": attempt, "problem": pr["problem"],
            "update": pr["update"], "audit": run["audit"], "read": run["read"],
            "motion": run["motion"], "speech": speech}


def hybrid_pass(items, label):
    """Code-filter every item; judge-certify code-cleans. Returns rows."""
    rows = []
    judge_q = []
    for it in items:
        pr_texts = [it["problem"], it["update"], it["audit"], it["read"],
                    it["motion"]]
        man = {"counterparty": MAN[it["pid"]]["counterparty"],
               "dead_token": MAN[it["pid"]]["dead_token"],
               "problem": it["problem"], "update": it["update"]}
        # plan text included in upstream (numbers there are legitimate provenance)
        up = pr_texts + [RUNS[it["pid"]].get("plan", "")]
        r = check_speech(it["speech"], up, man, it["motion"])
        row = {"arm": it["arm"], "pid": it["pid"], "attempt": it["attempt"],
               "code_flags": r["fidelity_flags"], "verbosity": r["verbosity_flag"],
               "words": r["words"], "judge": None}
        emit(stage="filter", arm=it["arm"], pid=it["pid"], attempt=it["attempt"],
             flags=[k for k, _ in r["fidelity_flags"]], words=r["words"])
        rows.append((row, it))
        if not r["fidelity_flags"]:
            judge_q.append((row, it))
    if judge_q:
        verdicts = J.certify_batch([it for _, it in judge_q])
        for (row, it), v in zip(judge_q, verdicts):
            row["judge"] = v
            emit(stage="judge", arm=it["arm"], pid=it["pid"], attempt=it["attempt"],
                 coherent=v["coherent"], flaws=v["flaws"], delivery=v["delivery"],
                 cached=v.get("cached", False))
    emit(stage="pass_done", label=label, n=len(rows),
         judged=len(judge_q))
    return [row for row, _ in rows]


def is_clean(row):
    return not row["code_flags"] and row["judge"] is not None and row["judge"]["coherent"]


def phase_round1():
    if "round1" in state()["done"]:
        return json.loads((OUT / "round1.json").read_text())
    items = []
    for pid, run in sorted(RUNS.items()):
        pr = MAN[pid]
        items.append(item_of("A", pid, 1, run, pr, run["fusion_A"]))
        items.append(item_of("C", pid, 1, run, pr, run["fusion_C"]))
    rows = hybrid_pass(items, "round1")
    # precision spot-audit: quota 3 A + 3 C code-flagged, judge-read anyway
    audit_rows = []
    for arm in ("A", "C"):
        flagged = [r for r in rows if r["arm"] == arm and r["code_flags"]][:3]
        audit_rows += flagged
    if audit_rows:
        verdicts = J.certify_batch([
            item_of(r["arm"], r["pid"], r["attempt"], RUNS[r["pid"]], MAN[r["pid"]],
                    RUNS[r["pid"]][f"fusion_{r['arm']}"]) for r in audit_rows])
        confirmed = sum(1 for v in verdicts if not v["coherent"])
        emit(stage="spot_audit", n=len(audit_rows), confirmed=confirmed)
    else:
        confirmed = -1  # nothing flagged anywhere (would itself be news)
    out = {"rows": rows, "audit_n": len(audit_rows), "audit_confirmed": confirmed}
    (OUT / "round1.json").write_text(json.dumps(out, indent=1))
    mark("round1")
    return out


def build_feedback(row):
    parts = []
    if row["code_flags"]:
        parts.append(code_feedback(row["code_flags"]))
    if row["judge"] and not row["judge"]["coherent"]:
        parts.append("A strict reviewer found these factual violations:\n" +
                     "\n".join(f"- {f}" for f in row["judge"]["flaws"]))
    parts.append("Rewrite the speech correcting ALL of the above. Same length and "
                 "discipline; end with the CURRENT PLAN's estimate, exactly: ESTIMATE: NN%")
    return "\n\n".join(parts)


def phase_repair(pod, mock, rnd, prev_rows):
    key = f"round{rnd}"
    if key in state()["done"]:
        return json.loads((OUT / f"{key}.json").read_text())["rows"]
    dirty = [r for r in prev_rows if not is_clean(r)]
    if not dirty:
        (OUT / f"{key}.json").write_text(json.dumps({"rows": []}, indent=1))
        mark(key)
        return []
    fb = {str(r["pid"]): build_feedback(r) for r in dirty}
    (OUT / f"feedback_r{rnd}.json").write_text(json.dumps(fb, indent=1))
    emit(stage="feedback", round=rnd, n=len(fb),
         mean_chars=round(sum(len(v) for v in fb.values()) / len(fb)))
    if mock:
        att = {p: RUNS[int(p)]["fusion_A"].replace("MOCKFLAW", "") for p in fb}
        (OUT / f"attempts_r{rnd}.json").write_text(json.dumps(att, indent=1))
    else:
        rsync(pod, f"{OUT}/feedback_r{rnd}.json", "POD:/workspace/div/")
        rc, out = ssh_cmd(pod, f"cd /workspace/div && python run13b_pod.py --phase repair "
                               f"--round {rnd} 2>&1 | tail -3", timeout=1500)
        if f"REPAIR ROUND {rnd} COMPLETE" not in out:
            sys.exit(f"REPAIR ROUND {rnd} FAILED:\n{out}")
        rsync(pod, f"POD:/workspace/div/out/attempts_r{rnd}.json", f"{OUT}/")
        rsync(pod, "POD:/workspace/div/out/pod_events.jsonl", f"{OUT}/")
    att = json.loads((OUT / f"attempts_r{rnd}.json").read_text())
    items = [item_of("Dp", int(p), rnd, RUNS[int(p)], MAN[int(p)], s)
             for p, s in sorted(att.items(), key=lambda x: int(x[0]))]
    rows = hybrid_pass(items, key)
    (OUT / f"{key}.json").write_text(json.dumps({"rows": rows}, indent=1))
    mark(key)
    return rows


def wilson(k, n, z=1.96):
    import math
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def phase_verdict(r1, r2rows, r3rows):
    rows_a = [r for r in r1["rows"] if r["arm"] == "A"]
    rows_c = [r for r in r1["rows"] if r["arm"] == "C"]
    # D' trajectory: attempt1 = A rows; later rounds override per pid
    final = {r["pid"]: dict(r, arm="Dp", attempt=1) for r in rows_a}
    for rows in (r2rows, r3rows):
        for r in rows:
            final[r["pid"]] = r
    dp = sorted(final.values(), key=lambda r: r["pid"])

    def clean_n(rows):
        return sum(1 for r in rows if is_clean(r))

    a_k, c_k, d_k = clean_n(rows_a), clean_n(rows_c), clean_n(dp)
    lo, hi = wilson(a_k, 24)
    # shortcut stands iff at most ONE audited flag was unconfirmed (>=5/6 at full
    # quota; scales down when fewer speeches were code-flagged). -1 = none flagged.
    audit_ok = (r1["audit_confirmed"] < 0
                or r1["audit_confirmed"] >= r1["audit_n"] - 1)

    def deliveries(rows):
        ds = [r["judge"]["delivery"] for r in rows if r["judge"]]
        return round(sum(ds) / len(ds), 2) if ds else None

    def lex_sem(rows):
        lex = sum(len(r["code_flags"]) for r in rows)
        sem = sum(len(r["judge"]["flaws"]) for r in rows
                  if r["judge"] and not r["judge"]["coherent"])
        return lex, sem

    res = {
        "bar1_spot_audit": {"n": r1["audit_n"], "confirmed": r1["audit_confirmed"],
                            "shortcut_stands": audit_ok},
        "bar2_wall_A": {"clean": a_k, "n": 24, "rate": round(a_k / 24, 3),
                        "ci95": [round(lo, 3), round(hi, 3)]},
        "bar3_C": {"clean": c_k, "pass": c_k >= 18 and c_k >= a_k + 8},
        "bar4_Dp": {"clean_within_3": d_k, "pass": d_k >= 20,
                    "attempts_hist": {str(a): sum(1 for r in dp if r["attempt"] == a)
                                      for a in (1, 2, 3)}},
        "bar5_verbosity": {arm: sum(1 for r in rows if r["verbosity"] is None)
                           for arm, rows in (("A", rows_a), ("C", rows_c), ("Dp", dp))},
        "bar6_delivery": {"A": deliveries(rows_a), "C": deliveries(rows_c),
                          "Dp": deliveries(dp)},
        "lex_sem_flaws": {"A": lex_sem(rows_a), "C": lex_sem(rows_c), "Dp": lex_sem(dp)},
    }
    (OUT / "results.json").write_text(json.dumps(res, indent=1))
    emit(stage="verdict", **{k: v for k, v in res.items() if k.startswith("bar")})
    print(json.dumps(res, indent=1))
    if not audit_ok:
        print("\nWARNING: spot-audit failed (<5/6) — code-flag shortcut revoked; "
              "rerun with judge-everything before trusting bar 2-4 numbers.")
    mark("verdict")


def _mock_transcript():
    """Dry-run dataset: planted code flaws + MOCKFLAW semantic flaws."""
    man = {json.loads(l)["pid"]: json.loads(l) for l in PROBS.open()}
    runs = []
    for pid, pr in sorted(man.items()):
        dt, cp = pr["dead_token"], pr["counterparty"]
        filler = "The committed course holds on audited resources with deadline discipline central. " * 6
        seg = {"audit": "AUDIT: holds stated budget and hours; deadline control favors the actor.",
               "read": f"READ: {cp} may escalate via a rival; watch for sudden silence.",
               "plan": "PLAN: commit audited hours before the deadline. ESTIMATE: 60%",
               "motion": f"MOTION: with {dt} gone per the update, shift hours to direct talks. ESTIMATE: 55%"}
        clean = (f"With {dt} withdrawn, the position rests on audited resources. If {cp} "
                 f"escalates as the read anticipates, the plan is positioned early. {filler}"
                 f"ESTIMATE: 55%")
        a = clean
        if pid % 4 == 0:
            a = clean.replace("ESTIMATE: 55%", "A $9,999 buffer remains. ESTIMATE: 55%")
        elif pid % 4 == 1:
            a = clean + " MOCKFLAW"       # semantic-only flaw (judge catches, code blind)
        c = clean if pid % 6 else clean + " MOCKFLAW"
        runs.append({"pid": pid, "arch": pr["arch"], **seg, "fusion_A": a, "fusion_C": c})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "transcript13b.json").write_text(json.dumps({"base": "mock", "big": "mock",
                                                        "runs": runs}, indent=1))
    (OUT / "pod_events.jsonl").write_text("")


def main():
    global RUNS, MAN
    ap = argparse.ArgumentParser()
    ap.add_argument("--pod", help="HOST:PORT of the pod (ssh root)")
    ap.add_argument("--mock", action="store_true", help="offline dry run")
    args = ap.parse_args()
    if not args.mock and not args.pod:
        sys.exit("need --pod HOST:PORT (or --mock)")
    if args.mock:
        import os
        os.environ["RUN13B_MOCK_JUDGE"] = "1"
        J.MOCK = True
    phase_relay(args.pod, args.mock)
    t, MAN_ = load_data()
    RUNS = {r["pid"]: r for r in t["runs"]}
    MAN = MAN_
    r1 = phase_round1()
    a_rows = [dict(r, arm="Dp") for r in r1["rows"] if r["arm"] == "A"]
    r2 = phase_repair(args.pod, args.mock, 2, a_rows)
    carry = {r["pid"]: r for r in a_rows}
    for r in r2:
        carry[r["pid"]] = r
    r3 = phase_repair(args.pod, args.mock, 3, list(carry.values()))
    phase_verdict(r1, r2, r3)
    print("\nRUN13B DRIVE COMPLETE — build the report: python scripts/run13b_report.py")


if __name__ == "__main__":
    main()
