"""
run11_regen_junk.py — RUN 11: targeted regeneration round (one round, pre-authorized).

Removes the audit-junked (pid, direction) rows from sequences.jsonl (archived to
sequences_junked.jsonl) so run11_generate.py's resume logic regenerates exactly
those slots fresh. Run AFTER a run11_gate.py pass has written out/run11/junk_keys.json.

  python scripts/run11_regen_junk.py
  python scripts/run11_generate.py        # fills the removed slots
  python scripts/run11_gate.py            # cache makes this cheap: only regens audited
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D11 = ROOT / "data/run11"
SEQ = D11 / "sequences.jsonl"
JUNK = ROOT / "out/run11/junk_keys.json"

junk = {(j["pid"], j["direction"]) for j in json.loads(JUNK.read_text())}
rows = [json.loads(l) for l in SEQ.open()]
keep = [r for r in rows if (r["pid"], r["direction"]) not in junk]
drop = [r for r in rows if (r["pid"], r["direction"]) in junk]
with (D11 / "sequences_junked.jsonl").open("a") as f:
    for r in drop:
        f.write(json.dumps(r) + "\n")
with SEQ.open("w") as f:
    for r in keep:
        f.write(json.dumps(r) + "\n")
print(f"removed {len(drop)} junked sequences (archived); {len(keep)} remain — "
      f"run run11_generate.py to refill")
