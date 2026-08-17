# RUNBOOK 20 — the staged decomposer (2026-08-15)

**Question:** run 19's atomic/composite dissociation — the model computes the
cap violation correctly at D1 (7/8 strict, 8/8 RULER-T, 8/8 code-check) but
misapplies it inside D2 judgments (5/8) and D3 choices (3/8). Run 11's law
says what free reasoning fumbles, anchored prompting fixes. **Does injecting
the code-verified atomic answers into the composite prompts lift D2/D3 to
D1's clean rate?** This is the last unmeasured link of the cube-v2 chain
(decompose -> atomic ✅ -> STAGE ⚠ -> coach ✅).

## Design (frozen before any GPU or judge spend)

- **Chain:** run-19 D1 answers (cached, model-produced) -> CODE verification
  against deterministic truth (params parsed from templates + datetime
  calendar arithmetic; result: 8/8 pass) -> fixed ANCHOR template (coach law:
  code carries text) appended to the run-19 D2 and D3 prompts VERBATIM.
  Anchor states: (i) option price exceeds cap by $X, sign-off unobtainable
  before deadline, therefore committing before deadline not executable;
  (ii) N days between option-open and deadline.
- **Generation:** 16 answers (8 problems x staged-D2, staged-D3), keep100,
  greedy, max_new 256. Staged file md5 b97d0ec347e56a0d27f419fc0eaa488b.
- **Baseline:** run-19 unstaged D2 (5/8) and D3 (3/8), cached verdicts, $0.
- **Gold:** STRICT_ONE byte-reused (judge sees problem + answer only, as in
  every prior run). 16 reads, cached, SPEND CAP 24. Secondary: RULER-T.

## FROZEN READOUTS

1. **PRIMARY: staged D2 >= 6/8 AND staged D3 >= 6/8 strict-clean -> the
   staging link holds and the cube-v2 chain is COMPLETE** (all five links
   measured green); below -> record honestly.
2. **SECONDARY:** lift vs unstaged baseline; RULER-T; count of T1 flaws still
   touching the sign-off cap (run-19 unstaged: 6) — staging should drive this
   toward zero; full autopsy with RULER-T classes.

## Budget

Pod: 16 gens ~5 min (~$0.1; keep100 + helper scripts already on the run-19
pod if alive, else re-upload ~46MB). Judge 16 reads ~$0.4 (cap 24). Total
~**$0.5**. Wallets at freeze: Anthropic ≈ $3 · RunPod ≈ $21 · OpenRouter $3.

*Frozen 2026-08-15 pre-spend: anchor template, arms, bars, caps set before any
pod or judge dollar.*
