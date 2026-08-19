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

## Crash-fix log
- First launch died at import: `peft` missing (skipped in install since no
  adapter is used this run, but run15_match_pod imports it unconditionally).
  Environment-only fix: `pip install peft`, relaunch. Zero code edits.

## RESULTS (2026-08-19 — pod prominent_amethyst_quokka A40; judge 48 reads ~$1.1)

| arm | strict | STRICT-D | RULER-T | cf / pq / aq / cal |
|---|---|---|---|---|
| C cube (instruct+harness) | 0/16 | 0/16 | **5/16** | **2.31** / 2.31 / **2.44** / 1.69 |
| R Thinking naked | **1/16** | **3/16** | 2/16 | 2.19 / 2.19 / 2.19 / **1.88** |
| G instruct naked | 0/16 | 0/16 | 1/16 | 2.06 / 2.38 / 2.25 / 2.06 |

**PRIMARY: WIN** — RULER-T cube 5 vs Thinking 2 (vs instruct-naked 1).
**Registered prediction HELD** — constraint_fidelity 2.31 vs 2.19.
**Efficiency rider (honest):** Thinking averaged 1,525 generated
tokens/answer (min 675, max 7,458, 0 leaks) vs cube's 1,360 stage-budget
ceiling — COMPARABLE budgets, not the 17B-era 25x. The "fraction of the
cost" phrasing is NOT licensed; "at a comparable token budget" is.

### Honest reading
1. **The claim is licensed with one caveat attached.** At the realistic
   criterion, a base instruct model + the cube harness beat a
   reasoning-trained model of the same weight class (5 vs 2) on
   independently authored held-out problems, with the pre-registered
   constraint-fidelity edge held — cube verdicts cached before this
   comparison existed (one-directionally blind).
2. **The caveat (dual-report, strict band):** Thinking is the ONLY 4B-class
   arm ever to produce strict-clean answers on the holdout — 1/16 strict,
   3/16 STRICT-D, vs 0 for cube and 0 for naked instruct. Reasoning
   training buys occasional strict-band coherence the harness does not;
   the harness buys consistent realistic-band fidelity the reasoning
   training does not. Complementary strengths, not domination.
3. Thinking's failure autopsy shows the SAME disease as naked instruct
   (invented dates, actors, mechanisms; arithmetic self-contradictions) —
   deliberation reduces but does not change the species. Calibration:
   Thinking 1.88 > cube 1.69 (cube's estimate stage remains its weakest
   piece, consistent with run 22).
4. Combined 22+23 scoreboard on the holdout (RULER-T): cube 5 · Thinking 2
   · instruct naked 1. The harness is worth more than reasoning training
   at this weight class on this criterion; both are far from the strict
   island. Natural next probe (unrun): cube harness ON the Thinking seat.

*Verdict recorded 2026-08-19. Wallets after: Anthropic ≈ $0.6 · RunPod ≈
$19 · OpenRouter $3.*
