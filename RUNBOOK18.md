# RUNBOOK 18 — the fatal-flaw gate (2026-08-15)

**Question:** does verification train small when the target is matched to the
weight class's wavelength? Run 16 proved detection trains small (0.99 recall)
but certification slid to all-flag — trained against the strict ruler, where
clean answers barely exist. The RULER-T reanalysis (RUNBOOK17B / DRAFT2 §17)
then measured ver_16 false-flagging **96%** of realistically-clean answers and
opened a 20–38% base clean-rate. Run 18 retrains the same recipe against the
matched criterion: flag only FATAL flaws (T1: contradiction, given-fact
distortion, constraint violation, temporal error, miscalculation,
misattribution — plus PRED asserted-as-fact and unclassifiable, per the
RULER-T-clean definition).

**Stakes:** a passing gate over the 20–38% clean base makes gated regeneration
arithmetically viable for the first time (~3–5 expected attempts to a
certified-clean answer) — the cube's recorded redemption path. A failing gate
(another all-flag slide) settles that 4B verification is capacity-bound even at
the matched wavelength.

## Design (frozen before any GPU spend)

- **Labels ($0, all from already-paid Sonnet reads), trust rules:**
  strict-complete reads get full two-class labels (208 STRICT_ONE relabels,
  match-source rows, 120 ladder reads from runs 17/17B); lenient-source reads
  (13B/14/15smoke originals) contribute FATAL only when their prose already
  shows a T1 marker, and are EXCLUDED otherwise (192 excluded — a lenient read
  cannot certify soundness). Classifier = ruler_t.py VERBATIM (the frozen
  RULER-T regexes that produced the §17 numbers).
- **Corpus:** 549 labeled pairs. Train 424 (151 SOUND / 273 FATAL; SOUND
  oversampled x3 -> 726 rows, md5 2aa949e3360e03aecaff2507d09f85c4). Eval 125
  (24 SOUND / 101 FATAL, md5 930fc306a7fbcbf1598d25e1a24b631c). Splits:
  verifier_real rows keep run-16's problem-level split verbatim; ladder pids
  < 28 train / >= 28 eval. New prompt (VER18, frozen in run18_corpus.py) asks
  for SOUND / FATAL with the fatal classes named and "proposing new specifics
  is NOT fatal" stated explicitly.
- **Training:** run16_train.sh unchanged (train_lora.py, r64, same recipe),
  adapter `ver_18_qwen`. Pod swift_amaranth_lizard (194.68.245.23:22017).
- **Eval ($0, pod-side):** run18_eval.py; unparseable outputs count as flags
  (conservative).

## FROZEN BARS

**PASS = recall_fatal >= 0.75 AND fp_on_sound <= 0.30** on the 125-row eval.
fp_on_sound is the exact quantity ver_16 failed at 96%. Single variant; any
18B iteration requires a new labeled amendment with its own frozen bar. Report
both numbers regardless of verdict.

## Budget

Pod ~$0.5-1 (upload corpus + scripts, train ~15-25 min, eval ~10 min). Judge
$0 (all labels cached). Wallets at freeze: Anthropic ≈ $3.7 · RunPod ≈ $28
(pod already deployed by Nikhil) · OpenRouter $3 (untouched).

*Frozen 2026-08-15 pre-spend: label trust rules, corpus md5s, prompt, recipe,
and both bars set before any pod dollar.*

## RESULTS (2026-08-15, pod swift_amaranth_lizard A40, ~$0.6)

**FAIL, both legs (single frozen variant, no rescue): recall_fatal 0.733
(74/101, bar 0.75 — missed by 2) · fp_on_sound 0.542 (13/24, bar 0.30).**
Unparseable 0/125 — the format trained perfectly; the discrimination did not.

**Honest reading, three parts:**
1. **The matched wavelength DID move the needle:** false-flags on sound answers
   fell 96% → 54%, and the gate genuinely certified 11 sound answers — the
   all-flag attractor is broken. The sound class was learnable in a way run 16
   never achieved (it had almost no real positives; this run had 151).
2. **But 4B certification fails at every wavelength tested.** Strict (run 16:
   0.25 clean recall) and matched (run 18: 0.46 sound recall as 1−FP) both land
   far from gate grade. And forcing discrimination exposed run 16's 0.99
   "detection" as partly trivial: asked to separate rather than flag-everything,
   fatal recall is 0.73, not 0.99.
3. **Caveat for the record:** the sound eval class is thin (24 rows; 13 FP), so
   fp_on_sound carries a wide interval — but no reasonable read of 13/24
   reaches the 0.30 bar. The verdict does not depend on granularity.

**Program consequence: verification-as-certification is now TWICE-failed at 4B
(strict and matched criteria) — the capacity-bound conclusion strengthens.
Gated regeneration remains blocked at this weight class.** Recorded 18B/19
candidates (not run, each needs its own frozen amendment): (a) grow the SOUND
label pool (151 train positives is the binding constraint — more ladder-style
strict reads at ~$0.9/40), (b) a 9–14B gate over the 4B generator (asymmetric
cube: small mind, bigger conscience), (c) claim-level decomposition (DRAFT2
fork 2, still the most promising unspent idea). Failed adapter not backed up
(run-16 precedent for failed instruments; reproducible from committed scripts +
md5-pinned corpus).
