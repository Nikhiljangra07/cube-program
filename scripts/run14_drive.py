"""
run14_drive.py — RUN 14 local orchestrator (RUNBOOK14 frozen). One command:

  source ~/Desktop/reasoningEngine/load_keys.sh && \
  python scripts/run14_drive.py --pod HOST:PORT

Phases (resumable via out/run14/state.json; judge cache out/run14/judge_cache.jsonl):
  relay     : pod generates segments + fusion attempt 1 for 160 train problems
  certify1  : session S judge-everything on attempt-1 speeches
  repair2/3 : feedback (judge flaws + advisory code flags) -> pod regen -> certify
  harvest   : first certified-coherent speech per pid -> diet (floor 100) -> upload
  train     : pod trains wrk_fusion_14_qwen (fixed recipe, md5-checked diet)
  evalgen   : pod generates eval segments + F14/A fusions on the frozen 24
  evalcert  : session T judge-everything on both arms
  verdict   : frozen bars -> results.json

Dry run: python scripts/run14_drive.py --mock
"""
from __future__ import annotations
import argparse, ast, hashlib, json, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run13_checker import check_speech, feedback as code_feedback  # noqa: E402
import run13b_judge as J  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out/run14"
J.CACHE = OUT / "judge_cache.jsonl"  # session S/T cache, isolated from 13B
TRAIN_PROBS = ROOT / "data/run14/train_problems.jsonl"
EVAL_PROBS = ROOT / "data/run13/staged_problems.jsonl"
EV = OUT / "events.jsonl"
STATE = OUT / "state.json"


def _extract_prompts():
    """Byte-extract SYS and FUSE from run13b_pod.py without importing torch —
    the training rows must carry the loop's prompts verbatim."""
    tree = ast.parse((ROOT / "scripts/run13b_pod.py").read_text())
    vals = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in ("SYS", "FUSE") \
                        and isinstance(node.value, ast.Constant):
                    vals[t.id] = node.value.value
    assert set(vals) == {"SYS", "FUSE"}, "prompt extraction failed"
    return vals["SYS"], vals["FUSE"]


SYS, FUSE = _extract_prompts()


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
    OUT.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s))
    emit(stage="phase", phase=phase, status="done")


def sh(cmd, timeout=900):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        # transient network stall — report failure, let poll loops retry
        return 255, "SSH_TIMEOUT"


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


def fuse_prompt(pr, run):
    return FUSE.format(problem=pr["problem"], update=pr["update"], audit=run["audit"],
                       read=run["read"], motion=run["motion"],
                       counterparty=pr["counterparty"])


def certify(rows_speeches, session_label):
    """rows_speeches: list of (pid, attempt, speech, pr, run). Judge-everything."""
    items = [{"arm": session_label, "pid": pid, "attempt": att,
              "problem": pr["problem"], "update": pr["update"], "audit": run["audit"],
              "read": run["read"], "motion": run["motion"], "speech": sp}
             for pid, att, sp, pr, run in rows_speeches]
    verdicts = J.certify_batch(items)
    for (pid, att, sp, pr, run), v in zip(rows_speeches, verdicts):
        emit(stage="judge", session=session_label, pid=pid, attempt=att,
             coherent=v["coherent"], flaws=v["flaws"], delivery=v["delivery"],
             cached=v.get("cached", False))
    return verdicts


def advisory_code(pr, run, speech):
    up = [pr["problem"], pr["update"], run["audit"], run["read"], run["plan"],
          run["motion"]]
    man = {"counterparty": pr["counterparty"], "dead_token": pr["dead_token"],
           "problem": pr["problem"], "update": pr["update"]}
    return check_speech(speech, up, man, run["motion"])


def build_feedback(judge_v, code_r):
    parts = []
    if judge_v and not judge_v["coherent"]:
        parts.append("A strict reviewer found these factual violations:\n" +
                     "\n".join(f"- {f}" for f in judge_v["flaws"]))
    if code_r["fidelity_flags"]:
        parts.append(code_feedback(code_r["fidelity_flags"]))
    parts.append("Rewrite the speech correcting ALL of the above. Same length and "
                 "discipline; end with the CURRENT PLAN's estimate, exactly: ESTIMATE: NN%")
    return "\n\n".join(parts)


# ---------------- mock helpers ----------------

def _mock_relay(problems):
    runs = []
    for pr in problems:
        dt, cp = pr["dead_token"], pr["counterparty"]
        filler = "The committed course holds on audited resources with discipline. " * 7
        seg = {"audit": "AUDIT: stated budget and hours held; deadline control favors us.",
               "read": f"READ: {cp} may escalate via a rival; watch for silence.",
               "plan": "PLAN: commit audited hours before the deadline. ESTIMATE: 60%",
               "motion": f"MOTION: with {dt} gone per the update, shift to direct talks. ESTIMATE: 55%"}
        clean = (f"With {dt} withdrawn, the position rests on audited resources. If {cp} "
                 f"escalates as anticipated, the plan is positioned early. {filler}ESTIMATE: 55%")
        a = clean if pr["pid"] % 3 == 0 else clean + " MOCKFLAW"
        runs.append({"pid": pr["pid"], "arch": pr["arch"], **seg, "fusion_A": a})
    (OUT / "transcript14.json").write_text(json.dumps({"base": "mock", "runs": runs}, indent=1))


def _mock_eval(eval_probs):
    runs = []
    for pr in eval_probs:
        dt, cp = pr["dead_token"], pr["counterparty"]
        filler = "The committed course holds on audited resources with discipline. " * 7
        seg = {"audit": "AUDIT: holdings confirmed.", "read": f"READ: {cp} may counter.",
               "plan": "PLAN: commit. ESTIMATE: 60%",
               "motion": f"MOTION: {dt} gone; revised. ESTIMATE: 55%"}
        clean = (f"With {dt} withdrawn, we proceed on what remains. If {cp} counters as "
                 f"read, we are early. {filler}ESTIMATE: 55%")
        runs.append({"pid": pr["pid"], **seg,
                     "fusion_F14": clean if pr["pid"] % 6 else clean + " MOCKFLAW",
                     "fusion_A": clean if pr["pid"] % 4 == 0 else clean + " MOCKFLAW"})
    (OUT / "eval_transcript14.json").write_text(json.dumps({"runs": runs}, indent=1))


# ---------------- phases ----------------

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
    probs = {json.loads(l)["pid"]: json.loads(l) for l in TRAIN_PROBS.open()}
    eval_probs = {json.loads(l)["pid"]: json.loads(l) for l in EVAL_PROBS.open()}

    # ---- relay ----
    if "relay" not in state()["done"]:
        if args.mock:
            OUT.mkdir(parents=True, exist_ok=True)
            _mock_relay(list(probs.values()))
        else:
            # idempotent relaunch: if a relay already ran (laptop slept, driver
            # restarted), never start a second one — resume polling or pull.
            rc, o = ssh_cmd(args.pod, "tail -1 /workspace/div/out/relay14.log 2>/dev/null",
                            60)
            already = "RUN14" in o or "done" in o
            if not already:
                ssh_cmd(args.pod, "cd /workspace/div && (setsid nohup python run14_pod.py "
                                  "--phase relay > out/relay14.log 2>&1 < /dev/null &)", 60)
            else:
                emit(stage="pod", action="relay_already_running_or_done")
            t0 = time.time()
            while True:
                time.sleep(60)
                rc, o = ssh_cmd(args.pod, "tail -3 /workspace/div/out/relay14.log", 60)
                if "RUN14 RELAY COMPLETE" in o:
                    break
                if "Traceback" in o:
                    sys.exit(f"RELAY FAILED:\n{o}")
                if time.time() - t0 > 12600:
                    sys.exit("RELAY TIMEOUT (3.5h)")
                emit(stage="pod_poll", mins=round((time.time() - t0) / 60, 1),
                     tail=o.strip()[-100:])
            rsync(args.pod, "POD:/workspace/div/out/transcript14.json", f"{OUT}/")
        mark("relay")
    runs = {r["pid"]: r for r in
            json.loads((OUT / "transcript14.json").read_text())["runs"]}

    # ---- certify attempt 1 + repair rounds ----
    speeches = {pid: {1: runs[pid]["fusion_A"]} for pid in runs}
    verdicts = {}  # pid -> {attempt: judge}
    if "corpus_certified" not in state()["done"]:
        batch = [(pid, 1, speeches[pid][1], probs[pid], runs[pid]) for pid in sorted(runs)]
        vs = certify(batch, "S1")
        for (pid, *_), v in zip(batch, vs):
            verdicts.setdefault(pid, {})[1] = v
        for rnd in (2, 3):
            dirty = [pid for pid in sorted(runs)
                     if not any(v["coherent"] for v in verdicts[pid].values())]
            if not dirty:
                break
            fb = {}
            for pid in dirty:
                last_att = max(speeches[pid])
                code_r = advisory_code(probs[pid], runs[pid], speeches[pid][last_att])
                fb[str(pid)] = build_feedback(verdicts[pid][last_att], code_r)
            (OUT / f"feedback14_r{rnd}.json").write_text(json.dumps(fb, indent=1))
            emit(stage="feedback", round=rnd, n=len(fb))
            if args.mock:
                att = {p: speeches[int(p)][max(speeches[int(p)])].replace(" MOCKFLAW", "")
                       if int(p) % 5 != 1 else speeches[int(p)][max(speeches[int(p)])]
                       for p in fb}
                (OUT / f"attempts14_r{rnd}.json").write_text(json.dumps(att, indent=1))
            else:
                rsync(args.pod, f"{OUT}/feedback14_r{rnd}.json", "POD:/workspace/div/")
                rc, o = ssh_cmd(args.pod, f"cd /workspace/div && python run14_pod.py "
                                          f"--phase repair --round {rnd} 2>&1 | tail -2",
                                timeout=5400)
                if f"REPAIR ROUND {rnd} COMPLETE" not in o:
                    sys.exit(f"REPAIR r{rnd} FAILED:\n{o}")
                rsync(args.pod, f"POD:/workspace/div/out/attempts14_r{rnd}.json", f"{OUT}/")
            att = json.loads((OUT / f"attempts14_r{rnd}.json").read_text())
            batch = [(int(p), rnd, s, probs[int(p)], runs[int(p)])
                     for p, s in sorted(att.items(), key=lambda x: int(x[0]))]
            vs = certify(batch, f"S{rnd}")
            for (pid, a, s, *_), v in zip(batch, vs):
                speeches[pid][a] = s
                verdicts[pid][a] = v
        (OUT / "corpus_verdicts.json").write_text(json.dumps(
            {str(p): {str(a): v for a, v in verdicts[p].items()} for p in verdicts},
            indent=1))
        (OUT / "corpus_speeches.json").write_text(json.dumps(
            {str(p): speeches[p] for p in speeches}, indent=1))
        mark("corpus_certified")
    else:
        verdicts = {int(p): {int(a): v for a, v in d.items()} for p, d in
                    json.loads((OUT / "corpus_verdicts.json").read_text()).items()}
        speeches = {int(p): {int(a): s for a, s in d.items()} for p, d in
                    json.loads((OUT / "corpus_speeches.json").read_text()).items()}

    # ---- harvest ----
    diet = []
    for pid in sorted(runs):
        for att in sorted(verdicts[pid]):
            if verdicts[pid][att]["coherent"]:
                diet.append({"messages": [
                    {"role": "system", "content": SYS},
                    {"role": "user", "content": fuse_prompt(probs[pid], runs[pid])},
                    {"role": "assistant", "content": speeches[pid][att]}]})
                break
    emit(stage="harvest", n=len(diet), of=len(runs))
    print(f"harvest: {len(diet)}/{len(runs)} certified pairs")
    if len(diet) < 100:
        sys.exit(f"HARVEST FLOOR BROKEN: {len(diet)} < 100 — STOP, report to Nikhil")
    dietp = OUT / "worker_train.jsonl"
    with dietp.open("w") as f:
        for r in diet:
            f.write(json.dumps(r) + "\n")
    diet_md5 = hashlib.md5(dietp.read_bytes()).hexdigest()
    print(f"diet md5 {diet_md5}")

    # ---- train ----
    if "train" not in state()["done"]:
        if args.mock:
            emit(stage="train", status="mock-skipped")
        else:
            host, port = args.pod.split(":")
            ssh_cmd(args.pod, "mkdir -p /workspace/div/faces/fusion14", 60)
            rsync(args.pod, str(dietp),
                  "POD:/workspace/div/faces/fusion14/")
            rc, o = ssh_cmd(args.pod, f"cd /workspace/div && bash run14_train.sh {diet_md5} "
                                      f"2>&1 | tail -4", timeout=3900)
            if "RUN14 TRAIN COMPLETE" not in o:
                sys.exit(f"TRAIN FAILED:\n{o}")
            emit(stage="train", status="done")
        mark("train")

    # ---- evalgen ----
    if "evalgen" not in state()["done"]:
        if args.mock:
            _mock_eval(list(eval_probs.values()))
        else:
            rc, o = ssh_cmd(args.pod, "cd /workspace/div && python run14_pod.py --phase "
                                      "evalgen 2>&1 | tail -2", timeout=2400)
            if "RUN14 EVALGEN COMPLETE" not in o:
                sys.exit(f"EVALGEN FAILED:\n{o}")
            rsync(args.pod, "POD:/workspace/div/out/eval_transcript14.json", f"{OUT}/")
        mark("evalgen")
    eruns = {r["pid"]: r for r in
             json.loads((OUT / "eval_transcript14.json").read_text())["runs"]}

    # ---- eval certify + verdict ----
    ev_verdicts = {}
    for arm in ("F14", "A"):
        batch = [(pid, 1, eruns[pid][f"fusion_{arm}"], eval_probs[pid], eruns[pid])
                 for pid in sorted(eruns)]
        vs = certify(batch, f"T_{arm}")
        ev_verdicts[arm] = {pid: v for (pid, *_), v in zip(batch, vs)}

    def cstats(arm):
        vs = ev_verdicts[arm]
        k = sum(1 for v in vs.values() if v["coherent"])
        d = round(sum(v["delivery"] for v in vs.values()) / len(vs), 2)
        return k, d

    f14_k, f14_d = cstats("F14")
    a_k, a_d = cstats("A")
    est_keep = sum(1 for pid in eruns if "ESTIMATE:" in eruns[pid]["fusion_F14"])
    bar1 = f14_k >= 18 and f14_k >= a_k + 8
    bar2 = (not bar1) and f14_k >= a_k + 5
    res = {"harvest": {"pairs": len(diet), "of": len(runs), "diet_md5": diet_md5},
           "eval": {"F14_clean": f14_k, "A_clean": a_k, "n": 24,
                    "F14_delivery": f14_d, "A_delivery": a_d,
                    "estimate_retention": est_keep},
           "bar1_dissolve": bar1,
           "bar2_partial_signal": bar2,
           "bar3_null": not (bar1 or bar2),
           "verdict": ("DISSOLVE — propose seam-gate rerun with F14, then run 15"
                       if bar1 else
                       "PARTIAL — training moved fidelity; fork returns to Nikhil"
                       if bar2 else
                       "NULL — wall stands vs prompting+size+repair+training; fork (c)")}
    (OUT / "results.json").write_text(json.dumps(res, indent=1))
    emit(stage="verdict", **res["eval"], bar1=bar1, bar2=bar2)
    print(json.dumps(res, indent=1))
    mark("verdict")
    print("\nRUN14 DRIVE COMPLETE")


if __name__ == "__main__":
    main()
