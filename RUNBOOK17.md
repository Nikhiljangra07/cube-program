# RUNBOOK 17 — the capacity ladder (Nikhil's hypothesis, 2026-08-13)

**Question:** is the fidelity wall a STATE-LOAD property? If invention is what
happens when the number of facts the model must track exceeds its working
capacity, then clean-rate should climb steeply as problems shrink — and there
exists an operating envelope inside which the 4B is honest. Corollary
(verifier rehabilitation): at low load, clean answers are common, so the
run-16 verifier finally gets a fair test — does its flagging TRACK the true
flaw rate down, or does it flag everything regardless?

**Why the hypothesis is live (evidence in hand):** match problems carry 6-7
tracked facts and both arms cratered to ~5% strict-clean; a 14B (double
capacity) halved the lenient wall (54% vs 21-42%); delivery stayed 4.4-4.8
while fidelity collapsed — an over-subscription signature, not a comprehension
one.

**Architectural stake:** if an envelope exists, the decomposer's job is
redefined — shrink every segment's state load below the ceiling. The cube
thesis gets a new, testable form that works WITH the capacity limit.

## Design (frozen before any GPU or judge spend)

- **Ladder:** 40 deterministic problems (seed 17), 5 state-load levels x 8:
  L1=2 facts, L2=4, L3=6 (match-like), L4=8, L5=10. Fact types NESTED across
  levels (fixed priority order) — load is the only variable; archetype mix
  (vendor/partner/expand/crisis) identical per level; decoding identical
  (greedy, max_new 500); prompt = the match's GEN_SINGLE verbatim.
  md5 95a293bba2d2583d10edb0f45fed1605. Entity pools FRESH and disjoint from
  run13/run14/run16 pools (asserted in the generator) — the verifier has never
  seen these names in any training label.
- **Arm:** keep100 generalist single-pass (the match measured cube ≈ generalist
  on the fidelity floor; one arm carries the curve; cube phase optional later).
- **Verifier under test:** ver_16_qwen v1 (archived, safetensors md5 4066a0e7)
  — the best clean-recall variant (0.382). Run-16 prompt verbatim, pod-side, $0.
- **Gold:** strict single-ruler coherence read, STRICT_ONE byte-reused from
  run16b_relabel.py — the same criterion as the match and run 16. 40 reads,
  cached, SPEND CAP 50.

## FROZEN READOUTS

1. **Capacity curve:** gold clean-rate per level. **ENVELOPE-70 / ENVELOPE-50**
   = highest level with clean-rate >= 70% / >= 50% (8/level -> one problem =
   12.5 pts; reported with raw counts).
2. **Verifier tracking:** per level, flag-rate, false-flag rate on gold-clean,
   recall on gold-flawed. **GATE-VIABILITY BAR: at every level where gold
   clean-rate >= 50%, false-flag rate on clean answers <= 30% -> the verifier
   is declared gate-viable WITHIN the envelope** (detector status is already
   settled by run 16 and is not re-litigated).
3. **Sanity guard:** L3 approximates match load; if L3 clean-rate >> the
   match's 0.054, the load hypothesis is confounded by style/format and the
   run says so honestly.

## Budget & isolation

Pod: upload keep100 + ver_16_qwen (~1.05GB) + scripts; generate 40 + verify 40
(~25-35 min, ~$0.5). Judge: 40 reads ≈ $0.9 (cap 50). Total ≈ **$1.5-2**.
Wallets at start: Anthropic ≈ $6.5 · RunPod ≈ $31 · OpenRouter $3 (untouched).
`data/run17/`, `out/run17/`, scripts `run17_*`. No training this run.

*Frozen 2026-08-13 pre-spend. Generator, prompts, bars, and caps set before
any pod or judge dollar.*
