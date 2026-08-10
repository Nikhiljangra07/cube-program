"""
run15_smoke.py — RUN 15 stage-1 driver (RUNBOOK15 frozen). One command:

  source ~/Desktop/reasoningEngine/load_keys.sh && \
  python scripts/run15_smoke.py --pod HOST:PORT

Phases (resumable; judge cache out/run15/judge_cache.jsonl; SPEND CAP 60 reads):
  relay     : pod generates segments + baseline fusion for the frozen 24
  motionfix : advisory code check on motions; flagged/estimate-less motions
              regenerate with feedback (<=2 rounds; coach production path —
              NO judge involved)
  assemble  : run15_coach template assembly (code)
  judge     : session U — 24 coach + 24 baseline reads, folded delivery
  bar       : coach_clean >= baseline_clean + 4 AND coach_clean >= 15/24

Dry run: python scripts/run15_smoke.py --mock
"""
from __future__ import annotations
import argparse, json, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run13_checker import check_speech, feedback as code_feedback  # noqa: E402
from run15_coach import assemble  # noqa: E402
import run13b_judge as J  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out/run15"
J.CACHE = OUT / "judge_cache.jsonl"
PROBS = ROOT / "data/run13/staged_problems.jsonl"
STATE = OUT / "state.json"
EV = OUT / "events.jsonl"
READ_CAP = 60


def emit(**kw):
    OUT.mkdir(parents=True, exist_ok=True)
    kw["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with EV.open("a") as f:
        f.write(json.dumps(kw) + "\n")


def state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"done": []}


def mark(p):
    s = state()
    s["done"].append(p)
    OUT.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s))


def sh(cmd, timeout=900):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return 255, "SSH_TIMEOUT"


def ssh_cmd(pod, remote, timeout=900):
    host, port = pod.split(":")
    return sh(f"ssh -o StrictHostKeyChecking=no -p {port} root@{host} {json.dumps(remote)}",
              timeout)


def rsync(pod, src, dst):
    host, port = pod.split(":")
    for i in range(4):
        rc, o = sh(f"rsync -a --no-owner --no-group --partial --timeout=90 "
                   f"-e 'ssh -p {port} -o StrictHostKeyChecking=no' {src} {dst}"
                   .replace("POD:", f"root@{host}:"), 600)
        if rc == 0:
            return
        time.sleep(10)
    sys.exit(f"rsync failed: {src}")


def advisory(pr, run, motion):
    up = [pr["problem"], pr["update"], run["audit"], run["read"], run["plan"], motion]
    man = {"counterparty": pr["counterparty"], "dead_token": pr["dead_token"],
           "problem": pr["problem"], "update": pr["update"]}
    return check_speech(motion, up, man, motion)


def _mock_transcript(probs):
    runs = []
    for pr in probs.values():
        dt, cp = pr["dead_token"], pr["counterparty"]
        filler = "The committed course holds on audited resources with discipline intact. " * 4
        motion = (f"MOTION: with {dt} gone per the update, hours shift to direct "
                  f"negotiation before the deadline. {filler}ESTIMATE: 55%")
        if pr["pid"] % 8 == 0:
            motion = motion.replace("ESTIMATE: 55%", "A $9,999 buffer helps. ESTIMATE: 55%")
        if pr["pid"] % 8 == 1:
            motion = motion + " MOCKFLAW"
        base = (f"With {dt} withdrawn we proceed. If {cp} counters as read, we are early. "
                f"{filler}ESTIMATE: 55%")
        if pr["pid"] % 3:
            base = base + " MOCKFLAW"
        runs.append({"pid": pr["pid"],
                     "audit": "AUDIT: holdings confirmed with stated budget.",
                     "read": f"READ: {cp} may counter within the window.",
                     "plan": "PLAN: commit audited hours. ESTIMATE: 60%",
                     "motion": motion, "fusion_base": base})
    (OUT / "smoke15_transcript.json").write_text(json.dumps({"runs": runs}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pod")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    if not args.mock and not args.pod:
        sys.exit("need --pod HOST:PORT (or --mock)")
    if args.mock:
        import os
        os.environ["RUN13B_MOCK_JUDGE"] = "1"
        J.MOCK = True
    probs = {json.loads(l)["pid"]: json.loads(l) for l in PROBS.open()}

    if "relay" not in state()["done"]:
        if args.mock:
            OUT.mkdir(parents=True, exist_ok=True)
            _mock_transcript(probs)
        else:
            rc, o = ssh_cmd(args.pod, "tail -1 /workspace/div/out/smoke15.log 2>/dev/null", 60)
            if "RUN15" not in o:
                ssh_cmd(args.pod, "cd /workspace/div && (setsid nohup python run15_pod.py "
                                  "--phase smoke > out/smoke15.log 2>&1 < /dev/null &)", 60)
            t0 = time.time()
            while True:
                time.sleep(30)
                rc, o = ssh_cmd(args.pod, "tail -2 /workspace/div/out/smoke15.log", 60)
                if "SMOKE RELAY COMPLETE" in o:
                    break
                if "Traceback" in o:
                    sys.exit(f"SMOKE RELAY FAILED:\n{o}")
                if time.time() - t0 > 2700:
                    sys.exit("SMOKE RELAY TIMEOUT (45 min)")
            rsync(args.pod, "POD:/workspace/div/out/smoke15_transcript.json", f"{OUT}/")
        mark("relay")
    runs = {r["pid"]: r for r in
            json.loads((OUT / "smoke15_transcript.json").read_text())["runs"]}

    # ---- motion screening + bounded retry (production path, judge-free) ----
    motions = {pid: runs[pid]["motion"] for pid in runs}
    for rnd in (1, 2):
        fb = {}
        for pid, m in motions.items():
            r = advisory(probs[pid], runs[pid], m)
            if r["fidelity_flags"] or "ESTIMATE:" not in m:
                parts = []
                if r["fidelity_flags"]:
                    parts.append(code_feedback(r["fidelity_flags"]))
                if "ESTIMATE:" not in m:
                    parts.append("Your previous attempt omitted the final line "
                                 "`ESTIMATE: NN%` — include it.")
                fb[str(pid)] = "\n\n".join(parts)
        emit(stage="motion_screen", round=rnd, flagged=len(fb))
        if not fb:
            break
        if args.mock:
            fixed = {p: motions[int(p)].replace("A $9,999 buffer helps. ", "")
                     for p in fb}
        else:
            (OUT / f"motionfix15_r{rnd}.json").write_text(json.dumps(fb, indent=1))
            rsync(args.pod, f"{OUT}/motionfix15_r{rnd}.json", "POD:/workspace/div/")
            rc, o = ssh_cmd(args.pod, f"cd /workspace/div && python run15_pod.py --phase "
                                      f"motionfix --round {rnd} 2>&1 | tail -2", 1800)
            if "COMPLETE" not in o:
                sys.exit(f"MOTIONFIX r{rnd} FAILED:\n{o}")
            rsync(args.pod, f"POD:/workspace/div/out/motionfix15_r{rnd}_out.json", f"{OUT}/")
            fixed = json.loads((OUT / f"motionfix15_r{rnd}_out.json").read_text())
        for p, m in fixed.items():
            motions[int(p)] = m

    # ---- assemble ----
    speeches = {}
    for pid in sorted(runs):
        s = assemble(motions[pid], probs[pid])
        if s is None:  # estimate still missing after retries — assembly refuses
            s = assemble(motions[pid] + " ESTIMATE: 50%", probs[pid])
            emit(stage="assemble", pid=pid, note="estimate fallback injected")
        speeches[pid] = s
    emit(stage="assemble", n=len(speeches))

    # ---- judge session U (cap enforced) ----
    items = []
    for pid in sorted(runs):
        r, pr = runs[pid], probs[pid]
        for arm, sp in (("COACH", speeches[pid]), ("BASE", r["fusion_base"])):
            items.append({"arm": arm, "pid": pid, "attempt": 1,
                          "problem": pr["problem"], "update": pr["update"],
                          "audit": r["audit"], "read": r["read"],
                          "motion": motions[pid], "speech": sp})
    if len(items) > READ_CAP:
        sys.exit(f"SPEND CAP: {len(items)} reads > {READ_CAP} — abort before billing")
    verdicts = J.certify_batch(items)
    for it, v in zip(items, verdicts):
        emit(stage="judge", arm=it["arm"], pid=it["pid"], coherent=v["coherent"],
             flaws=v["flaws"], delivery=v["delivery"], cached=v.get("cached", False))

    def stats(arm):
        vs = [v for it, v in zip(items, verdicts) if it["arm"] == arm]
        return (sum(1 for v in vs if v["coherent"]),
                round(sum(v["delivery"] for v in vs) / len(vs), 2))

    c_k, c_d = stats("COACH")
    b_k, b_d = stats("BASE")
    passed = c_k >= b_k + 4 and c_k >= 15
    res = {"coach_clean": c_k, "base_clean": b_k, "n": 24,
           "coach_delivery": c_d, "base_delivery": b_d,
           "bars": "coach >= base+4 AND coach >= 15",
           "STAGE1": "PASS — stage 2 (the match) unlocks, Nikhil's go required"
                     if passed else "FAIL — report, stop; no match on this harness"}
    (OUT / "smoke_results.json").write_text(json.dumps(res, indent=1))
    emit(stage="verdict", **{k: v for k, v in res.items() if k != "bars"})
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
