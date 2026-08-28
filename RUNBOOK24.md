# RUNBOOK 24 — CUBE (4B + harness) vs A 14B REASONING MODEL (2026-08-22)

**The question (the economics claim, on-domain):** does a 4B instruct model
with the frozen cube harness — NO reasoning training of any kind — match a
reasoning-trained model 3.5x its size on grounded decision fidelity, and at
what inference-compute ratio? Static benchmarks cannot answer this (PAL/ToRA
already own that field); the frozen third-party holdout can.

## Arms (run-23 harness, opponent swapped — one edit, logged)
- **C — cube-v2 generalized** (Qwen3-4B-Instruct-2507 + wrk_keep100 + frozen
  run-22 harness): answers AND verdicts immutable from run-22 cache (judged
  2026-08-18) — $0, one-directionally blind.
- **R14 — Qwen/Qwen3-14B, thinking mode (default), naked, one pass** (new):
  GEN_SINGLE verbatim, WRK_SYS, vendor thinking decoding (T=0.6, top_p=0.95,
  top_k=20), max_new 9000 + one 13000 retry on unclosed `</think>`,
  with_estimate law. Note: this is the hybrid Qwen3-14B (Apr 2025 release)
  with thinking on — no "-Thinking-2507" 14B exists; 30B-A3B does not fit an
  A40 in bf16. bf16 14B ≈ 28 GB — fits.
- **R (4B Thinking) and G (instruct naked)** dual-reported from caches.

Problems: run-22 holdout, md5 7620cd1646a7466388b1811219ed2219. Judge: Sonnet 5
frozen, STRICT_ONE + STRICT-D + blind QUAL byte-reused. Only R14 judged (48 reads).

## FROZEN READOUTS
1. **PRIMARY (RULER-T clean, cube vs R14): WIN / TIE / LOSS.** Cube has 5/16 banked.
2. **Stated prior (before spend): LOSS expected.** Run 13B measured 3.5x params
   ≈ half the errors; R14 is expected at 5–8 RULER-T-clean and may place
   answers on the strict band (≥3/16 STRICT-D). The information is the
   MARGIN and the compute ratio, not the sign.
3. **Efficiency rider (pre-declared, reported regardless):** inference-compute
   proxy = active parameters × generated tokens per answer. Cube ceiling =
   4.0B × 1,360 = 5.4e12; R14 = 14.8B × measured tokens. Report the ratio.
4. STRICT_ONE / STRICT-D / QUAL dual-reported; all 16 judged; no exclusions.

## Pre-committed claim wording
- **WIN/TIE:** "a 4B instruct model with the cube harness — no reasoning
  training — matched a 14B reasoning model on grounded decision fidelity at
  ~N× less inference compute" (N from the rider).
- **LOSS by ≤3:** "4B + harness sits between 4B and 14B reasoning-trained
  models on this criterion, at ~N× less compute."
- **LOSS by >3:** "reasoning training at 3.5× weights dominates the 4B
  harness on this criterion; the economics claim does not hold at this rung."
All carry the run-23 single-judge qualifier on the realistic band.

## Budget & discipline
Pod ~A40, no adapter upload, ~14B download + 16 thinking generations ≈ 45–60
min ≈ $0.35–0.50. Judge 48 reads ≈ $1.1 (SPEND CAP 55). Wallet at freeze:
Anthropic $3.66 · RunPod ≈ $19 · OpenRouter ≈ $2.9. **ONE run. No iteration
series. Then back to the bootcamp.**

*Frozen 2026-08-22 before any R14 token is generated.*
