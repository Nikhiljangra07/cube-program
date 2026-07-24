# RUNBOOK 6 — Exposure Sweep ("our repetition number")

**Question (Nikhil's Test 3):** every run so far used 5 epochs because papers said so. What is
OUR number? Sweep repetition count on FIXED data and find the sweet spot — and check whether
the curve is flat (data saturated), rising (we under-trained everything), or peak-then-fall
(memorization burn).

**Pod:** B — `remarkable_tan_ocelot` (RTX PRO 6000 Blackwell 96GB, ssh -p 11874). ALL RUN-6
threads generate on this card; judged in their own single session (Session-S). Never mixed
with RUN-5 files (pod A).

## Design (FROZEN before launch, 2026-07-23)

- **Data: byte-identical `masked/wrk_laneF.jsonl` from run 4** (1143 rows = 843 foresight-lane
  scenes keep-0.6 + 300 anchor keep-1.0). md5 recorded below. NOTHING re-derived, re-scored,
  or re-masked — the sweep varies exactly one knob.
- **Trainer: `train_masked.py` (fixed schedule) for ALL five points — NOT train_mastery.**
  Mastery self-stops when every page is mastered (~655 steps on this data), so mastery arms
  above 1× would collapse into the same adapter. Fixed schedule is the only way to actually
  administer higher exposure. Consequence: the 1× point here is a NEW fixed-schedule adapter,
  not run-4's mastery laneF (different scheduler, different pod) — laneF is NOT re-judged in
  this session and no cross-session comparison to run-4 numbers is allowed.
- **Arms** (bs=8 → 143 steps/epoch; "exposures" ≈ epochs = times each page is seen):

  | adapter | epochs | steps | exposures/page |
  |---|---|---|---|
  | `wrk_swp_x025` | 1.25 | ~179 | 1.25 |
  | `wrk_swp_x05`  | 2.5  | ~358 | 2.5 |
  | `wrk_swp_x1`   | 5    | ~715 | 5 (the paper-default we always used) |
  | `wrk_swp_x2`   | 10   | ~1430 | 10 |
  | `wrk_swp_x4`   | 20   | ~2860 | 20 |

  (Nikhil's "100/300/600 repetitions" translated to LoRA scale: pretrain-style hundreds of
  exposures on 1143 rows would be pure memorization; 1.25–20 exposures brackets the whole
  plausible zone at this scale, with 4× headroom above our default.)
- All other hyperparams identical across arms: r64/α64/lr2e-4/bs8/seed42.
- **Judge Session-S:** 6 thread sets — 5 sweep arms + `anchor_keep100` regenerated ON THIS
  CARD (in-session anchor law). Sonnet 5, max_tokens 12000, coverage ≥44/48 per arm before
  any signal is read. Decomposer = `dec_keep1.0` everywhere (never varied).

## Frozen reads

Let ov(x) = overall score of arm x; anchor = keep100 in-session.

1. **CURVE SHAPE** (primary):
   - FLAT: max−min across the 5 points ≤ 0.15 → exposure is not a lever on this data.
   - RISING: ov(x4) ≥ ov(x05) + 0.20 with no interior point above x4 by >0.10 → we have been
     under-training; our number is HIGHER than 5 epochs.
   - PEAK-THEN-FALL: some interior point ≥ both endpoints + 0.15 → that point is our number;
     memorization burn exists beyond it.
   - FALLING: ov(x025) or ov(x05) ≥ ov(x4) + 0.15 and ≥ ov(x1) → we have been OVER-training;
     cheaper than 5 epochs is better.
2. **OUR NUMBER:** the smallest x with ov(x) ≥ (best ov − 0.10). This is the exposure count we
   adopt going forward (cheapest point within noise of the peak).
3. **SATURATION HALF-CONDITION** (program law, first half): if ov(x2) and ov(x4) are within
   ±0.15 of ov(x1), the exposure lever is EXHAUSTED at this scale. (Second half — every
   ingredient load-bearing — is Test 4, still deferred.)
4. **MEMORIZATION CHECK:** ov(x4) < ov(x1) − 0.20 → over-exposure actively degrades
   (photograph-burn confirmed at 20 exposures).
5. **Narrowing-tax guard** carried over: any sweep arm < anchor − 0.30 overall is flagged
   (training on the lane data at that exposure damages general capability).

Honest-null clause: if the curve is FLAT, that is a real answer — "our number" is then the
cheapest point (x025), and repetition joins selection/schedule/substance as a nulled lever
at 3.4B.

## Isolation rules (Nikhil's mandate)

- Adapters live only under `adapters/wrk_swp_*` on pod B; backed up as `run6_bundle.tgz`.
- Thread files: `out/eval_swp_*_v5_threads.jsonl` + `out/eval_anchor_keep100_v5_threads.jsonl`
  (pod-B card). Judged by `rejudge_arms.py` SESSION 6 block only.
- No adapter is merged, averaged, or reused as init for another arm. Each trains from base.

## Data fingerprint

- masked/wrk_laneF.jsonl md5: `eee0921044d96fea956617243fa4ce8c` (1143 rows; verified on pod
  at RUN6 START 07:20:55 — byte-identical to run-4 training input)
- bench_data/eval_problems.jsonl: 48 rows verified on pod (run-4's 20-row bug precluded)

## Cost estimate

Trains 5,485 steps total split into two parallel tracks (~3.6h wall) + 6 gen sets 2-parallel
(~2.5h) ≈ 6.2h pod B ≈ $12.5. Session-S judge ≈ $8.

---

## RESULTS (2026-07-24, Session-S valid full-coverage read, 48/48 all six arms)

| arm | exposures | overall | foresight | dist>=4% |
|---|---|---|---|---|
| swp_x025 | 1.25 | **3.62** | 3.06 | 64.6 |
| swp_x05 | 2.5 | 3.60 | 2.98 | 77.1 |
| swp_x1 | 5 | 3.56 | 3.00 | 68.8 |
| swp_x2 | 10 | 3.67 | 3.06 | 75.0 |
| swp_x4 | 20 | 3.48 | 2.96 | 64.6 |
| keep100 anchor | — | 3.66 | 2.98 | 77.1 |

Frozen reads:
1. **CURVE SHAPE: MIXED/AMBIGUOUS → flat-ish** (max−min 0.19, just past the 0.15 FLAT band,
   no rising trend). An earlier session (invalidated: x1 n=42<44) independently showed the
   same shape (x2 nominal peak, x4 near-last) — cross-session agreement on shape.
2. **OUR NUMBER: 1.25 exposures/page** (x025, 3.62; cheapest within 0.10 of best x2=3.67).
   The 5-epoch paper default buys nothing over 1.25 epochs on this data. This EXTENDS the
   efficiency result: par benchmark at ~36-40% tokens AND ~25% of the epochs.
3. **SATURATION HALF-CONDITION: MET** — x2/x4 within ±0.15 of x1. Exposure lever exhausted
   at 3.4B/LoRA on this corpus.
4. **MEMORIZATION CHECK: no formal burn** (x4 3.48 > x1−0.20), but x4 ranked last in both
   sessions — soft over-exposure signal, within noise.
5. No narrowing-tax flags (all arms ≥ anchor−0.30).

**Exposure-probe extension (exploratory, frozen probe instrument, answers generated pod-B
card, keep100 reference from pod-A card):** Δrecall vs keep100 at 1.25×/5×/10×/20× =
+0.04/−0.08/−0.17/+0.04 — NO storage at ANY exposure. Repetition does not create
retrievable knowledge; the storage failure is structural, not under-exposure.
