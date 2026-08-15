# RUNBOOK 17B — the marking test + the rival (2026-08-15)

**Two questions, one run, full observability:**

1. **The marking test (17B proper).** Run 17 located the wall in ASSERTION
   POLICY: the model fabricates needed specifics AS FACTS instead of marking
   them. The strict ruler explicitly allows conditional/proposed content. If a
   GROUNDING DISCIPLINE prompt (every specific = quoted / derived-with-basis /
   proposed-and-marked) moves strict-clean off zero, the wall is
   prompt-fixable, not capacity.
2. **The weight-class match (Nikhil's proposal).** Same 40 problems, same
   judge, same weight class: our harnessed 4B vs an open-source REASONING
   sibling — **Qwen3-4B-Thinking-2507** (identical Qwen3-4B lineage, thinking
   variant). This isolates "reasoning training" vs "our harness + marking
   prompt" at identical base capacity. Run 17's cached keep100 answers are the
   FREE third arm (baseline, already judged: 0/40 clean).
3. **The verifier rider (stagnant-layer thesis).** The $0 flaw audit
   (2026-08-15, cached run-17 verdicts) settled the gold half: Sonnet is NOT
   stagnant — it computed date gaps itself (pid 24: flagged "10-day buffer"
   as actually 15 days) and 0/176 flaws were correct derivations mis-flagged.
   The 4B verifier half is unmeasurable until gold-clean answers exist. This
   run should produce some — then ver_16_qwen's false-flag rate on them
   finally measures the stagnant-verifier thesis.

## Design (frozen before any GPU or judge spend)

- **Problems:** the run-17 ladder verbatim, all 40 (5 levels x 8),
  md5 95a293bba2d2583d10edb0f45fed1605. No new problems.
- **Arm M (marked):** keep100 generalist, GEN_SINGLE + GROUND block (frozen in
  run17b_pod.py): every specific must be (a) QUOTED, (b) DERIVED with basis
  shown inline, or (c) PROPOSED and explicitly marked. Greedy, max_new 600.
- **Arm R (rival):** Qwen/Qwen3-4B-Thinking-2507, SAME system + user prompt
  (including GROUND — fairness), vendor-recommended decoding (temp 0.6,
  top_p 0.95, top_k 20 — the model card warns greedy causes repetition
  loops; per-item seed 1700+pid for reproducibility). Thinking stripped via
  special-token decode + last `</think>` split (gpt-oss lesson). max_new 4096.
- **Arm B (baseline):** run 17's cached keep100 answers + cached verdicts. $0.
- **Verifier pass:** ver_16_qwen renders GROUNDED/FLAGGED on all 80 new
  answers, run-16 prompt verbatim, pod-side, $0.
- **Gold:** STRICT_ONE byte-reused (same ruler as runs 15/16/17). 80 new
  reads, cached, SPEND CAP 90.

## FROZEN READOUTS

1. **PRIMARY — marking bar:** arm M strict-clean **>= 4/40 (10%)** → the wall
   is relocated to assertion policy (harness-fixable). Below 4/40 → marking
   alone does not open the island; record honestly.
2. **THE MATCH:** per-arm, per-level clean-rate + total flaw count. Reported
   both directions; no seat/stakes attached — observability run.
3. **VERIFIER RIDER:** pooled gold-clean answers across arms M+R; if >= 5
   exist, ver_16 false-flag rate on them. **FP > 30% → stagnant-verifier
   thesis CONFIRMED** (it flags legitimately-moving answers); FP <= 30% on
   >= 5 cleans → the v1 verifier survives its first fair test.
4. **Autopsy dump:** every flaw on arms M and R printed with planted tokens
   (same $0 classification method as the run-17 audit).

## Budget & isolation

Pod: keep100 + ver_16_qwen upload (~1.05GB) + rival download from HF (~8GB).
Gen 40 marked (~10 min) + 40 rival (thinking, the slow arm) + 80 verifier
passes. RTX 6000-class recommended for the thinking arm's long generations
(~40-60 min total, <= ~$1); A40 works at roughly double wall-clock. Judge: 80
reads ~= $1.8 (cap 90). Total ~= **$2.5-3**. Wallets at freeze: Anthropic
~= $5.5 · RunPod ~= $30 · OpenRouter $3 (untouched).
`out/run17b/`, scripts `run17b_*`. No training this run.

*Frozen 2026-08-15 pre-spend. Prompts, arms, decoding, bars, and caps set
before any pod or judge dollar. Decoding note recorded at freeze: arm M keeps
the program's greedy law; arm R uses its vendor's published operating spec —
running a thinking model greedy against its own card would sandbag the rival
and invalidate the match.*
