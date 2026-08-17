# RUNBOOK 19 — the demand ladder (2026-08-15)

**Question (Nikhil's hypothesis):** the questions are too big for the model —
we are handing PhD problems to a graduation-level mind. Run 17 varied SUPPLY
(2–10 facts) with demand fixed and found flat zero — which the frozen equation
explains: **invention pressure = demanded specificity − supplied specificity.**
Lowering supply RAISED the pressure. Run 19 flips the axis: supply FIXED,
**DEMAND varied** — the untested side of the equation, which predicts clean-rate
rises steeply as the question shrinks. Everywhere the 4B ever passed a fidelity
bar, the question was already small (motion loop 93–100%; coach 87.5%).

**Stakes:** if small questions come back clean, the decomposer's job is
redefined as demand-splitting (PhD problem → N graduation questions → coach
assembles; fusion is already a solved harness function, 87.5%), and the
compounding arithmetic (clean^N) gets its base number. If even atomic questions
fail, the disease is deeper than demand.

## Design (frozen before any GPU or judge spend)

- **Problems:** the 8 six-fact L3 problems byte-reused from run 17
  (pids 16–23; supply constant, match-like).
- **Demand levels (templates frozen in run19_demand.py, parameters parsed from
  the fixed problem templates, parse asserted on all 8):**
  - **D1 atomic** — extraction + one derivation-with-basis (cap check, day count)
  - **D2 judgment** — name the binding constraint, quote the fact; no plan
  - **D3 choice** — pick one option, exactly two fact-grounded reasons; no plan
  - **D4 plan-lite** — three steps, ONLY stated specifics, [TBD] for absent
    ones, ESTIMATE line (run-13b retry law)
  - **D5 full** — GEN_SINGLE verbatim = the cached run-17 L3 arm (0/8, $0)
- **Ladder file:** 32 rows (8 × D1–D4), md5 ebb30bd7766ed620313e0911034e32f0;
  D5 never regenerated. **Arm:** keep100, greedy, max_new 256 (D1–D3) / 512 (D4).
- **Gold:** STRICT_ONE byte-reused, judged against the FULL problem text.
  32 reads, cached, SPEND CAP 40. Secondary: RULER-T (ruler_t.py verbatim).

## FROZEN READOUTS

1. **PRIMARY: D1 strict-clean >= 6/8 AND D2 strict-clean >= 6/8 → the
   demand-matching thesis is VALIDATED.** Registered prediction: monotone rise
   D5 → D1 on both rulers.
2. **SECONDARY:** RULER-T clean per level; D4 [TBD] compliance count (does the
   simpler escape hatch get used where the 17B three-class discipline did
   not?); full autopsy with RULER-T class per flaw.
3. **Known criterion tension (recorded at freeze):** D1 demands a derived
   number; STRICT_ONE has no explicit derivation exemption. If D1 fails strict
   solely on judge-flagged CORRECT derivations, the autopsy will show it and
   the RULER-T read carries the secondary verdict — recorded, not overridden.

## Budget & isolation

Pod supposed_gray_bandicoot (69.30.85.29:22164): keep100 upload (46MB) +
32 gens ≈ 10 min ≈ $0.2. Judge 32 reads ≈ $0.75 (cap 40). Total ≈ **$1**.
Wallets at freeze: Anthropic ≈ $3.7 · RunPod ≈ $21 · OpenRouter $3 (untouched).
`data/run19/`, `out/run19/`, scripts `run19_*`. No training this run.

*Frozen 2026-08-15 pre-spend: demand templates, arm, decoding, bars, caps, and
the criterion-tension note set before any pod or judge dollar.*
