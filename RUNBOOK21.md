# RUNBOOK 21 — THE REMATCH: cube-v2 vs the naked generalist (2026-08-15)

**The question the whole arc has been building to:** runs 19–20 measured every
link of the demand-matched architecture (atomic 100% · staged judgment 100% ·
staged choice 75% RULER-T · coach assembly 87.5%). Run 15's match was lost 2/6
with the OLD architecture (specialist seats + free composition). The rematch
fields **cube-v2** — decompose to demand-matched questions, code-verify
atomics, anchor upward, assemble by coach — against the same naked generalist
weights on 16 fresh full problems. **If the cube wins, the thesis closes at
4B: a small model + harness produces certified-clean strategic answers the
same small model alone cannot.**

## Design (frozen before any GPU or judge spend)

- **Problems:** 16 fresh six-fact problems, seed 21, run-17 ladder machinery
  byte-reused (template-parametric -> anchors computable). Generated pre-pod,
  md5 aea3d98b4b15ffbe3e32c62d02c13a3a.
- **Arm C (cube-v2), five demand-matched keep100 calls + code:** atomic (D1,
  code-checked; greedy so failures counted, anchor always carries code truth)
  -> judgment (D2+anchor) -> prediction (bounded conditional+signal question,
  frozen in run21_pod.py) -> choice (D3+anchor) -> one-line estimate (anchored
  on the made choice, run-13b retry law). **Final = verbatim pieces + fixed
  digit-free BRIDGE (run-15 coach constant) + estimate line. No model
  re-narration anywhere.**
- **Arm G:** GEN_SINGLE verbatim single pass + with_estimate — the run-15/17
  baseline operationalization, unchanged.
- **Rulers (dual, both judged on every answer, judge sees problem + final
  answer only):**
  - STRICT_ONE byte-reused — the comparability spine, unchanged forever.
  - **STRICT-D — ⚠ LABELED PROSPECTIVE INSTRUMENT, first use this run,**
    frozen in run21_score.py by asserted single-clause .replace(): a number
    explicitly derived from given figures WITH BASIS SHOWN and correct
    arithmetic is grounded. Motivated by two runs of hand-verified artifacts
    (runs 19–20: every disputed flag was a correct derivation or the anchor's
    own code-verified fact). Applied to BOTH arms symmetrically.
  - RULER-T computed from STRICT_ONE flaw prose (ruler_t.py verbatim).
- **Judge:** 32 answers x 2 rulers = 64 reads, cached, SPEND CAP 70.

## FROZEN READOUTS

1. **PRIMARY (STRICT-D): CUBE clean >= 10/16 (62.5%) AND CUBE >= GEN + 4.**
   Both legs required. PASS = the cube wins the rematch and the prototype
   thesis closes at 4B.
2. **SECONDARY:** full dual-ruler table both arms; RULER-T; pipeline
   integrity (d1 code-check rate, estimate injections); STRICT-D autopsy
   with RULER-T classes.
3. Strict-ruler numbers are reported alongside for continuity with runs
   15–20; they carry no bar this run.

## Budget

Pod (famous_turquoise_herring, still deployed; adapter + deps already
loaded): ~96 short gens + 16 baselines ~ 25-35 min ~ $0.3. Judge 64 reads
~ $1.5 (cap 70). Total ~ **$1.8**. Wallets at freeze: Anthropic ≈ $2.6 ·
RunPod ≈ $20 · OpenRouter $3 (untouched).

*Frozen 2026-08-15 pre-spend: problems md5, pipeline prompts, assembly
template, both rulers, bars, and caps set before any pod or judge dollar.*

## RESULTS (2026-08-15, pod famous_turquoise_herring A40, ~$1.8 total)

| arm | strict | STRICT-D | RULER-T |
|---|---|---|---|
| **CUBE-v2 (staged)** | 3/16 | **6/16 (38%)** | 6/16 |
| GENERALIST (naked) | 0/16 | 0/16 | 1/16 |

**PRIMARY: FAIL — leg 1 (absolute >= 10/16) missed; leg 2 (relative >= GEN+4)
passed 6–0.** Recorded as written.

**What the scoreboard actually says:**
1. **THE CUBE BEATS THE GENERALIST FOR THE FIRST TIME IN PROGRAM HISTORY —
   6-0 on certified-clean full answers.** The naked 4B produced ZERO clean
   full-demand answers on fresh problems (consistent with every prior run);
   the same weights inside the staged harness produced six. The run-15 match
   was 2/6 legs on rubric points; this is the first head-to-head on the
   fidelity criterion itself, and it is not close.
2. **Pipeline integrity was perfect:** 16/16 atomics passed code-check, zero
   estimate injections, assembly added no flagged content (coach law holds on
   a fresh problem set).
3. **The 10 failures decompose into exactly the two predicted residues:**
   (a) **choice-commitment contradiction, ~5-6/16** — the model names the
   option non-executable (correctly, from the anchor) and then RECOMMENDS it
   anyway (pid 12 chose an option it called 'impossible' and estimated 0%);
   run 20 measured this deficit at 1-2/8, and at full pipeline length it
   binds. (b) **prediction-piece decorations, ~4/16** — the conditional-
   reaction piece invents '48 hours' / 'term sheet' / 'competitor' texture.
4. **STRICT-D behaved as designed:** symmetric on both arms, lifted the cube
   3->6 by exempting only correct shown-basis derivations (hand-pattern
   consistent with runs 19-20), left the generalist at 0 (its flaws are real
   inventions, not derivations).

**Recorded 21B candidate (needs its own frozen amendment, ~$1):** two
harness-side fixes aimed at the measured residues — (a) CONSTRAINT GUARD on
the choice: code already knows which branch the anchor disqualifies; check
the choice text, and if it commits to the barred branch, regenerate once with
the branch explicitly excluded (constraint propagation, not new modeling);
(b) tightened prediction prompt (name the reaction + signal in the problem's
OWN vocabulary only). Wallet note at close: Anthropic ≈ $1.1 — a 21B judge
pass (~$0.75, C-arm only) fits; anything larger needs a top-up.
