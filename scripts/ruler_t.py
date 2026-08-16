"""
ruler_t.py — the RULER-T severity taxonomy (frozen 2026-08-15).

These regexes are the EXACT classifier used for the RULER-T reanalysis recorded
in RUNBOOK17B / DRAFT2 §17 (470 flaws: T1 96, PRED 35, ADD 325, OTHER 14).
Codified verbatim so run 18 labels and any future reanalysis are byte-consistent
with the published numbers. Priority order: T1 > PRED > ADD > OTHER.

  T1   fatal   : self-contradiction, given-fact distortion, stated-constraint
                 violation, temporal error, miscalculation, misattribution
  PRED         : likely reaction / prediction asserted as settled fact
  ADD  tolerated: invented-but-consistent specifics (decoration)
  OTHER        : unclassifiable — treated as fatal (conservative)

RULER-T-clean answer = no T1, no PRED, no OTHER (only ADD flaws, or none).
"""
from __future__ import annotations
import re

CONTRA = re.compile(
    r"contradict|self-contradic|despite|conflat|misattribut|mis-?stat|miscalculat|"
    r"actual gap|exceeds the|violat|already (observed|happened|an observed|a past)|"
    r"treats an already|temporal|redundantly|undermined|inconsistenc|does not follow|"
    r"not matching the stated", re.I)
PRED = re.compile(
    r"as settled|as a definite|rather than (a )?conditional|as near-certain|"
    r"near-fact|as (a )?fact|predicted (event|reaction)|as certain|as an? already|"
    r"prediction", re.I)
ADD = re.compile(
    r"invent|introduc|not (present|in|stated|mentioned|grounded|derivable)|"
    r"fabricat|new actor", re.I)


def classify(flaw: str) -> str:
    if CONTRA.search(flaw):
        return "T1"
    if PRED.search(flaw):
        return "PRED"
    if ADD.search(flaw):
        return "ADD"
    return "OTHER"


def fatal(flaws) -> bool:
    """True if the answer fails RULER-T (any T1 / PRED / OTHER flaw)."""
    return any(classify(f if isinstance(f, str) else str(f)) != "ADD" for f in flaws)
