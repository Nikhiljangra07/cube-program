# RUNBOOK 23 — CUBE vs REASONING MODEL, SAME WEIGHT CLASS (2026-08-19)

**The question:** does the cube methodology on a BASE instruct model beat a
REASONING-TRAINED model of the same weight class on fidelity, on the
independently authored holdout? This is the resume claim Nikhil wants to
make ("base model + my methodology vs reasoning training") — it has never
been tested; run 17B's evidence (Thinking = best 4B at RULER-T on the
ladder, 15/40 vs baseline 8/40) says it is genuinely at risk. Frozen bars
below decide it either way.

## Arms
- **C — cube-v2 generalized** (Qwen3-4B-Instruct-2507 + wrk_keep100 +
  frozen run-22 harness): answers AND verdicts fully cached from run 22
  (judged 2026-08-18, before this comparison existed) — **$0, immutable,
  one-directionally blind.** RULER-T 5/16 banked.
- **R — Qwen3-4B-Thinking-2507, naked, one pass** (new): GEN_SINGLE prompt
  verbatim (same user prompt as arm G), WRK_SYS system, vendor decoding
  (T=0.6, top_p=0.95, top_k=20), max_new 9000 with ONE 13000 retry on
  unclosed `</think>` (the 17B leak fix); with_estimate law replicated
  (one nudge retry, then inject 50% + flag). No adapter, no harness.
- **G — instruct naked** (cached from run 22): dual-reported context row.

Problems: the run-22 frozen holdout, md5 7620cd1646a7466388b1811219ed2219.
Judge: Sonnet 5 frozen; STRICT_ONE + STRICT-D + blind QUAL byte-reused.
Only R is judged (48 reads); C/G verdicts must come from the run-22 cache —
re-judging them is forbidden.

## FROZEN READOUTS
1. **PRIMARY (RULER-T clean count on the holdout): cube vs Thinking.**
   WIN if C > R · TIE if C = R · LOSS if C < R. No absolute bar.
2. **Registered prediction:** cube >= Thinking on blind constraint_fidelity.
3. **Efficiency rider (reported regardless of outcome):** R's measured
   generated tokens/answer (thinking included) vs cube's stage-budget
   ceiling of 1,360 tokens/answer (sum of arm-C max_new caps:
   400+160+256+192+256+96).
4. STRICT_ONE + STRICT-D dual-reported (expected 0-0 per run 22).
   All 16 R answers judged; no exclusions; leaked answers judged as-is.

## Pre-committed claim wording
- **WIN:** "a base instruct model plus the cube harness beat a
  reasoning-trained model of the same weight class on fidelity, on
  independently authored held-out problems, at <=1360 vs ~N thousand
  generated tokens per answer."
- **TIE:** "matched a reasoning-trained model's fidelity at a fraction of
  the inference tokens."
- **LOSS:** reported plainly; the resume claim is dropped; 17B's
  reasoning-training result extends to the holdout.

## Budget
Pod ~A40, no adapter upload, ~20-30 min ≈ $0.3. Judge: 16 answers x 3
reads = 48 ≈ $1.1 (SPEND CAP 55). Wallet at freeze: Anthropic ≈ $1.70 ·
RunPod ≈ $19.5 · OpenRouter $3.

*Frozen 2026-08-19 before any R-arm token is generated.*
