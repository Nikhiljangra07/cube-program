"""
run21_problems.py — RUN 21 rematch problem set (RUNBOOK21, $0).

16 fresh six-fact (L3-load) strategic problems, seed 21, generated with the
run-17 ladder machinery byte-reused (same templates, same fact priority order,
fresh RNG draw). Template-parametric by construction, so the harness can parse
every planted parameter (the cube-v2 anchor requirement).

  python scripts/run21_problems.py   # writes data/run21/rematch_problems.jsonl
"""
from __future__ import annotations
import hashlib, json, random, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run17_ladder import ARCH, build  # byte-reuse  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/run21/rematch_problems.jsonl"


def gen():
    rng = random.Random(21)
    archs = list(ARCH)
    return [build(pid, 3, archs[pid % 4], rng) for pid in range(16)]


def main():
    rows = gen()
    assert rows == gen(), "NON-DETERMINISTIC"
    assert len({r["counterparty"] for r in rows}) == 16
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"16 rematch problems (six-fact, seed 21) -> {OUT}")
    print("md5", hashlib.md5(OUT.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
