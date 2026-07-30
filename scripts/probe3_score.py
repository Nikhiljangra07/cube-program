"""
probe3_score.py — PROBE 3 verdict (RUNBOOK10 frozen bars, code-only, $0).

Bars (face arm): ACK >= 12/16 pairs (>=1 revision cites boost signature);
DIRECTION >= 75% of pairs with parseable old+new estimates (new >= old).
Anchor arm reported as reference, no bar.
"""
from __future__ import annotations
import json, re, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTD = ROOT / "out/run10"
D10 = ROOT / "data/run10"
PCT = re.compile(r"(\d{1,3})(?:\s*(?:-|–|to)\s*(\d{1,3}))?\s*%")
STOP = set("""a an the and or of to in on for with by at from as is are was were be been has have
had it its this that these those you your he she they their we our i my new one two now must
will would can could may might should after before over under all any each which who whom
when where while during still also only just more most less least very much many if then than
into out up down off no not nor so such own same s t d ll re ve day days week weeks month
months year years am pm update""".split())


def words(text):
    return {w for w in re.findall(r"[a-z]+", text.lower()) if len(w) > 3 and w not in STOP}


def last_pct(t):
    found = PCT.findall(t)
    if not found:
        return None
    a, b = found[-1]
    return (int(a) + int(b)) / 2 if b else float(a)


def main():
    inv = [json.loads(l) for l in (D10 / "inventory_problems.jsonl").open()]
    raw = [json.loads(l) for l in (OUTD / "probe3_raw.jsonl").open()]
    for arm in ("faceV_10", "keep100"):
        rows = [r for r in raw if r["arm"] == arm]
        pairs = {}
        for r in rows:
            pairs.setdefault(r["pair"], []).append(r)
        ack_pairs = 0
        dirs = []
        print(f"\n=== ARM {arm} ({len(rows)} revisions, {len(pairs)} pairs) ===")
        for pid in sorted(pairs):
            grp = pairs[pid]
            base_problem = inv[pid]["problem"]
            sig = words(grp[0]["boost"]) - words(base_problem)
            ack = any(len(sig & words(r["revision"])) >= 1 for r in grp) if sig else False
            if ack:
                ack_pairs += 1
            pair_dirs = []
            for r in grp:
                new = last_pct(r["revision"])
                if r["old_est"] is not None and new is not None:
                    pair_dirs.append(new >= r["old_est"])
            d = None
            if pair_dirs:
                d = all(pair_dirs) if len(pair_dirs) == 1 else (sum(pair_dirs) >= len(pair_dirs) / 2)
                dirs.append(d)
            ests = [(r['old_est'], last_pct(r['revision'])) for r in grp]
            print(f"  pair {pid:2d}: ack={'Y' if ack else 'n'} dir={'OK' if d else ('WRONG' if d is not None else '-')} "
                  f"est {ests}")
        n_dir_ok = sum(dirs)
        print(f"[{arm}] ACK {ack_pairs}/16 | DIRECTION {n_dir_ok}/{len(dirs)} pairs "
              f"({100*n_dir_ok/len(dirs):.0f}% of parseable)" if dirs else f"[{arm}] ACK {ack_pairs}/16 | no parseable pairs")
        if arm == "faceV_10":
            ack_ok = ack_pairs >= 12
            dir_ok = dirs and (n_dir_ok / len(dirs)) >= 0.75
            print(f"[PROBE3 VERDICT] ack {'OK' if ack_ok else 'FAIL'}; direction "
                  f"{'OK' if dir_ok else 'FAIL'} -> {'PASS — capability present, trigger missing; run-11 delta face licensed' if ack_ok and dir_ok else 'FAIL — reframe falsified at this scale'}")


if __name__ == "__main__":
    main()
