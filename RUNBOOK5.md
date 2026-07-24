# RUNBOOK 5 — Headroom Test (fresh-book absorption)

**Question (Nikhil's Test 1):** did runs 1–4 null out because the MODEL is full, or because
the DATA we fed it hit diminishing returns? Take a corpus that was never in this model's
training lineage, push it through the exact run-3 raw-book recipe, and ask: does the model
still learn genuinely new material cleanly, without forgetting and without catastrophic
failures? If yes → room exists → the run-4 null was a data-arrangement problem and
rearrangement (multi-angle, run 4b) is licensed. If no → capacity story confirmed.

**Pod:** A — `dominant_rose_mollusk` (RTX PRO 6000 Blackwell 96GB, ssh -p 30347). ALL RUN-5
threads generate on this card; judged in their own single session (Session-H). Never mixed
with RUN-6 files (pod B).

## Corpus selection (research done 2026-07-23, frozen)

BURNED for this 3.4B lineage (v5 sources + prior runs): Reverend Insanity, Jin Ping Mei,
Machiavelli's Prince, Thucydides, Plutarch, Mahabharata, Clausewitz.

**Chosen: `federalist-papers.txt` (~196k words → ~650 pages).** Reasons: (1) never trained
in any lineage adapter, (2) nearly identical size to Clausewitz (~196k) so mastery telemetry
and step counts compare apples-to-apples against run-3 book_C06 and run-4 laneF, (3)
institutional strategy dense in consequence-projection — same family as the bench without
being the bench. Runner-up: Bagehot's Lombard Street (better bench-domain match, half the
size — kept in reserve for a replication).

## Design (FROZEN before launch)

- Pipeline = run-3 C06 recipe, UNCHANGED: `build_fed_pages.py` (300-word pages, 120-word
  context tail, heldout every 10th page) → `loss_band_gate --per-token` → keep-0.6 band mask
  → + anchor_300 keep-1.0 → concat → `train_mastery.py` at matched steps
  STEPS = (ROWS+7)/8*5.
- Adapter: `wrk_fedH`. Decomposer: `dec_keep1.0` (never varied).
- **Judge Session-H:** 2 thread sets — `fedH` + `anchor_keep100` regenerated ON THIS CARD.
  Sonnet 5, max_tokens 12000, coverage ≥44/48 before reading.
- Secondary learning evidence: `heldout_nll.py` on the ~65 never-trained Federalist pages,
  base vs fedH. (NLL is demoted for cross-arm benchmark comparisons per run 2, but
  same-arm-vs-base on untrained pages of the SAME book is valid pure learning evidence.)

## Frozen reads

1. **LEARNS-THE-BOOK** (two pieces, both required):
   a. Mastery telemetry: all pages mastered within the step budget (mean visits recorded;
      Clausewitz raw was 3.52).
   b. Fed heldout NLL: fedH ≤ base − 0.15 nats mean (the model genuinely absorbs unseen
      pages of the new book, not just the trained ones).
2. **NO-FORGETTING GUARD:** fedH bench overall ≥ keep100 − 0.15 (in-session). Training on a
   fresh book must not damage general capability.
3. **VERDICT GRID:**
   - 1a+1b hold AND guard holds → **ROOM EXISTS.** The model still absorbs new corpora
     cleanly at 3.4B. Runs 1–4 nulls were about our data/arrangement → rearrangement
     (multi-angle run 4b) is the licensed next move.
   - 1a or 1b fails → the model can no longer even store new material at this scale →
     **capacity story confirmed at the storage level** (stronger than v3's claim).
   - Guard fails (fedH < keep100 − 0.15) → new learning EVICTS old capability →
     **interference ceiling** — capacity confirmed at the interference level.
   - Bonus (not required, treat as anomaly + re-verify): fedH > keep100 + 0.15 would be the
     first-ever positive book value on the bench.
4. Honest-null clause: "ROOM EXISTS" does NOT claim the bench improved — Federalist is not
  expected to move a modern-decision bench. The claim is strictly learn-without-damage.

## Isolation rules (Nikhil's mandate)

- New data dir `data/book_fed/` — run-3 `data/book/` (Clausewitz) untouched.
- New script `build_fed_pages.py` — run-3 `build_book_pages.py` frozen.
- Adapter `wrk_fedH` only on pod A; backed up as `run5_bundle.tgz`. No merges, no reuse
  as init, judged only in Session-H.

## Cost estimate

~885 rows → ~555 steps mastery train (~1h) + 2 gens parallel (~50 min) + NLL pass (~10 min)
≈ 2h pod A ≈ $4. Session-H judge ≈ $3.
