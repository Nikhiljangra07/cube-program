# DENSITY METHOD — Test Run 1 (the learnable-band gate)

> First controlled test of the corpus-density thesis: *data selected into the learnable band
> buys the same benchmark at meaningfully fewer training tokens.* Minimal by design — one
> GPU session, two new trains, one judging session. Target all-in cost: **under $10.**

## 1. Thesis under test

Same parameters, fewer tokens, same benchmark — IF the surviving tokens are the ones the
model has to *work* on. Formalized: keep training rows whose base-model completion NLL sits
in a mid band — hard enough to carry gradient, solvable enough to learn. Motivated by the
auditory-stream-segregation precedent (van Noorden/Bregman): perception has two measured
boundaries (coherence = too easy, automatic segregation = too obvious) with the active
"solving" zone between them. Our two boundaries are the NLL band edges.

This is the POST-TRAINING regime (LoRA SFT on a pretrained 3.4B base). No pretraining
claims are made or licensed by this run.

## 2. Arms (all on ibm-granite/granite-4.0-micro, identical recipe: `--r 64 --epochs 5`, α=64 default — matches the v5 SFT baseline "r64/5ep" per run1.log)

| Arm | Corpus | Train tokens (approx) | Status |
|---|---|---|---|
| `base` | none (untrained) | 0 | threads ON DISK (`data/bench/eval_bench_base_v5_threads.jsonl`) |
| `v5full` | v5 judge-gated, full | ~1.05M unique (dec ~230k + wrk ~821k, from run1.log num_tokens) | threads ON DISK (`eval_bench_sft_v5_threads.jsonl`) — **the baseline we must match** |
| `dense60` | v5 filtered to the NLL learnable band, ~60% token mass | ~630k | **NEW — the test arm** |
| `rand60` | v5 random rows at the SAME token mass (seed 42) | ~630k | **NEW — the control** |

Why `rand60` exists: without it, "dense60 ≈ v5full at 60% tokens" is uninterpretable —
maybe ANY 60% subset of an already judge-gated corpus is enough (redundancy, not density).
The control separates *fewer tokens* from *selected tokens*. This was the pattern in the
van Noorden stimuli too (Control 1 / Control 2 same-frequency arms).

## 3. What is reused vs new

Reused byte-identical (verified with cmp at copy time): `train_lora.py`, `dav_eval_v5.py`,
`head2head_v5.py` (judge prompt), v5 training data, 48-problem OOD bench, and the two
baseline thread files. Provenance: `~/Desktop/divergence-formula` round2_kit + corpus_run
(read-only — NEVER edit the source repo from here).

New instruments (this repo): `loss_band_gate.py` (base-model NLL scorer, matches trainer
masking/truncation), `build_arms.py` (band selection + matched-mass random control),
`rejudge_arms.py` (single-session Gemini judge over all 4 arms).

## 4. Order of operations

RUNBOOK.md has exact commands. Summary: pod → score (once) → pull scores → build arms
locally → push arms → 2×2 adapter trains → 2 bench thread generations (48 OOD problems,
same dav_eval harness that produced the baselines) → pull threads → kill pod →
single-session Gemini re-judge of all four arms locally.

## 5. Success criteria (decided BEFORE running — do not move these after seeing results)

- **Signal A (efficiency):** dense60 overall within **±0.15** of v5full overall
  (and distinctness within ±0.15). Same benchmark at ~60% of the tokens.
- **Signal B (selection):** dense60 overall **≥ 0.20 above** rand60.

| A | B | Reading |
|---|---|---|
| holds | holds | Density thesis first step CONFIRMED — the gate, not the token count, did it. Green-light iteration 1b (book distillation). |
| holds | fails | The v5 corpus is redundant at this size — any 60% works. Useful but weaker claim; density gate unproven. |
| fails | holds | The gate helps but tokens still bind at this scale — the leverage curve exists but is shallower than hoped. |
| fails | fails | Not visible at this scale/corpus. Thesis unsupported here; do NOT scale up on hope. |

Known noise floor: judge session wobble was measured at ±0.05, and 48-problem means move
~±0.1 between runs — hence the 0.15/0.20 thresholds and the single-session judge.

## 6. Budget ledger (fill in actuals)

| Item | Est | Actual |
|---|---|---|
| Pod: NLL scoring pass (~2.3k rows) | ~$0.15 (10 min) | |
| Pod: 4 adapter trains (2 arms × dec+wrk, ~60% of 13.5+27 min) | ~$0.60 | |
| Pod: 2 × 48-problem bench thread gen (+inline Haiku judge) | ~$1.50 | |
| Gemini re-judge, 4 × 48, one session | ~$2.50 | |
| **Total** | **~$5** | |

## 7. Safety rails

- No API keys in this repo, ever. Keys live in `~/Desktop/reasoningEngine/.env`; export
  without echoing (see RUNBOOK). `.gitignore` blocks `.env*`.
- Source repos (`divergence-formula`, `divergent-model-backups`) are READ-ONLY inputs.
- `data/` and `out/` are gitignored (derived artifacts; sources live in the origin repo).
- Success criteria in §5 are frozen as of 2026-07-20, before any training ran.
