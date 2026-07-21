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

**Run-day deviation (2026-07-21):** trains run with `--gc` (gradient checkpointing) added —
bs8/seq1024/r64 all-linear OOMs on the RTX 6000 Ada's 48GB without it (the v5 baseline
evidently trained on a larger card). GC recomputes activations instead of storing them:
identical gradients, identical optimization — recipe comparability to v5full is unaffected;
only wall-clock is ~30% slower.

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

## 7. RESULTS (2026-07-21, Sonnet 5 single-session judge, n=47/48/48/48)

| arm | overall | distinct | dist>=4% | decisive | concrete | foresight | viability |
|---|---|---|---|---|---|---|---|
| base | 3.28 | 2.43 | 17.0% | 3.30 | 3.30 | 3.02 | 3.62 |
| v5full (~1.05M tk) | 3.56 | 3.73 | 75.0% | 4.44 | 3.52 | 2.88 | 2.52 |
| dense60 (~0.63M tk) | 3.53 | 3.58 | 62.5% | 4.29 | 3.60 | 2.94 | 2.50 |
| rand60 (~0.63M tk) | 3.58 | 3.62 | 64.6% | 4.31 | 3.67 | 3.00 | 2.58 |

**Signal A (efficiency): HOLDS** — dense60 3.53 vs v5full 3.56 (Δ0.03 « 0.15). 60% of the
tokens bought the full corpus's benchmark, across every dimension.
**Signal B (selection): FAILS** — dense60 3.53 vs rand60 3.58 (Δ −0.05, inside the ±0.1
noise floor). The NLL band added nothing over random at matched token mass.

**Frozen-grid reading (§5, A-holds/B-fails):** the v5 corpus is REDUNDANT at this size —
any 60% subset reproduces it. Token count was not the binding constraint; the selection
gate is unproven. Do not scale the selection gate on hope.

**Post-hoc diagnosis (labeled as such):** the corpus was already judge-gated — the 6-dim
judge had already removed the junk tail, so the NLL band had little variance left to
exploit (double-gating). This is the least favorable arena for a selection effect
(consistent with Ankner 2024: band value is corpus-dependent; and with WORKING_PAPER §15:
the quality gate is where the leverage lives). A selection effect smaller than the
48-problem noise floor (~±0.1) would also be invisible at this scale.

**Judge-run cost note:** three verdict passes were needed (Sonnet 5 rejects `temperature`;
thinking tokens ate max_tokens at 600 and partially at 4000; final pass at 12000 with
retry-on-empty reached full coverage). Only the full-coverage pass counts.

## 7b. Safety rails

- No API keys in this repo, ever. Keys live in `~/Desktop/reasoningEngine/.env`; export
  without echoing (see RUNBOOK). `.gitignore` blocks `.env*`.
- Source repos (`divergence-formula`, `divergent-model-backups`) are READ-ONLY inputs.
- `data/` and `out/` are gitignored (derived artifacts; sources live in the origin repo).
- Success criteria in §5 are frozen as of 2026-07-20, before any training ran.
