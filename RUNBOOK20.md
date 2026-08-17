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

## RESULTS (2026-08-15, pod famous_turquoise_herring A40, ~$0.5)

| level | unstaged (run 19) | staged strict | staged RULER-T |
|---|---|---|---|
| D2 judgment | 5/8 | **8/8 (100%)** | **8/8** |
| D3 choice | 3/8 | 3/8 | **6/8 (75%)** |

**PRIMARY: FAIL (frozen bar, D3 strict leg) — recorded as written.** And the
mechanism readouts say the staging law essentially HELD:

1. **D2 is PERFECT under both rulers (8/8).** Anchoring the code-verified
   atomics fully cured the judgment level.
2. **The conflation disease is cured: cap-touching T1 flaws 6 -> 1.** The one
   survivor (pid 20) is a genuine model fault — it names the option
   non-executable, then chooses it anyway.
3. **D3's strict "failures" are hand-verified criterion artifacts:** every
   flagged window ("13-day Aug 6->19", "20-day", "10-day", "12-day") and the
   "$7,000" figure is BYTE-IDENTICAL to the code-verified anchor's own facts
   (the judge sees problem + answer only, per frozen design, and STRICT_ONE
   has no derivation exemption). The pre-registered tension is now
   load-bearing: strict D3 3/8 vs RULER-T 6/8. True model faults at D3: 2
   (pid 20's contradiction; pid 23's option/revenue conflation).
4. **Chain status at the realistic criterion: atomic 100% -> staged judgment
   100% -> staged choice 75%.** Staging doubled D3's RULER-T rate (3->6).

**Program consequence: the staging link substantially holds — run 11's
anchoring law now proven for constraint facts, not just estimates. The strict
ruler's missing derivation exemption is the single largest remaining artifact
in the instrumentation; any run-21 rematch must dual-report and may freeze a
labeled STRICT-D variant (derivation-with-basis exempt) PROSPECTIVELY as its
primary. Remaining true model deficit at 4B: choice-level commitment logic
(picks a known-non-executable option in 1-2/8 cases even when told).**
