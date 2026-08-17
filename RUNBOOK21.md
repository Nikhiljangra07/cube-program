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

## 21B AMENDMENT (labeled, frozen 2026-08-15 pre-spend): the constraint guard + digit screen

Two harness fixes aimed at the two measured residues; nothing else changes.
Arm G is NOT regenerated — its run-21 answers and cached verdicts stand.

1. **CONSTRAINT GUARD (choice step).** By construction in every problem the
   option track's price exceeds the sign-off cap, so committing it before the
   deadline is non-executable — code KNOWS this. The anchor gains a VERIFIED
   CONSEQUENCE clause: the {code} track is barred; select the alternative
   path. If the generated choice still commits to the barred track (regex on
   commit-verbs + code token), ONE retry with a harder reminder; retries
   counted. Division-of-labor rationale: code propagates constraints, the
   model reasons within them — same law as the coach carrying the estimate.
2. **DIGIT SCREEN (prediction step).** Any digit-bearing token in the
   prediction that does not appear in the problem text -> ONE regeneration
   with "use NO numbers at all"; residuals counted (run-15 advisory-screen
   precedent).

**Bars carried over VERBATIM from run 21 (STRICT-D: CUBE >= 10/16 AND
>= GEN + 4).** Judge: only the 16 new C answers x 2 rulers = 32 reads
(~$0.75, cap 40); G verdicts are cache hits. Pod: same warm pod, pennies.
Wallet at freeze: Anthropic $6.29 (corrected from console).

## 21B RESULTS (2026-08-15, same pod, ~$0.8)

| arm | strict | STRICT-D | RULER-T |
|---|---|---|---|
| CUBE + guard/screen | 2/16 | 6/16 | **8/16** |
| GENERALIST (cached) | 0/16 | 0/16 | 1/16 |

**PRIMARY: FAIL — STRICT-D flat at 6/16 (needle: strict 3->2 noise, RULER-T
6->8 up).** Honest decomposition of what each fix did:

1. **The constraint guard WORKED at the layer it addressed:** retries 2,
   residual commit-to-barred-choice 0. Direct "chose the impossible option"
   failures are gone. But the contradiction RELOCATED to the prediction piece
   (predicts the counterparty "will sign the [barred] track anyway"; pid 15's
   prediction narrates the barred $13,000 payment happening) and into choice
   reasons referencing the rejected option's dates (pid 04). Run-12's law
   again, at piece scale: narrowing one free surface relocates the error to
   the next free surface.
2. **The digit screen MISSED ITS TARGET — implementation bug (Claude's):**
   the foreign-digit detector exempted all 1-3-digit numbers (meant for
   percents/day-counts), which is EXACTLY the class the target flaws live in
   ("48 hours", "24 hours") — so the screen churned on harmless anchor echoes
   (15 retries) while never catching the real offenders. **5 of the 10
   STRICT-D failures are single-flaw answers whose ONLY flaw is a 48/24-hour
   decoration** — the recoverable class if the screen worked as designed.

**Recorded 21C candidate (one fix, one extension, ~$0.8):** (a) FIX the
screen — exempt only trailing ESTIMATE percents and the code-computed
day-count; flag ALL other foreign numbers including 1-2 digit ones; (b)
extend the barred-branch clause to the PREDICTION prompt ("do not narrate the
[code] track occurring"). Targets the 5 single-decoration failures + 2-3
relocated contradictions -> projected 10-13/16. Wallet after 21B: ~$5.5.

## 21C AMENDMENT (labeled, frozen 2026-08-15, built pre-pod — NOT YET RUN)

Two changes vs 21B, both fully specified by the 21B autopsy; bars carried
over VERBATIM (STRICT-D CUBE >= 10/16 AND >= GEN+4):
1. **Screen fix:** foreign-number detector exempts ONLY (a) a trailing
   ESTIMATE percent and (b) the code-computed day-count for that problem.
   ALL other numbers absent from the problem text — including 1-2 digit ones
   ("48 hours", "24 hours") — trigger one no-numbers regeneration. Screen now
   also covers the CHOICE piece (same rule), not just the prediction.
2. **Prediction-side bar:** the VERIFIED CONSEQUENCE clause is appended to
   the prediction prompt too, with "do not narrate the {code} track being
   signed, paid, or executed" — closing the relocation channel the guard
   opened.
Cost when run: ~16 gens (pod pennies) + 32 reads (~$0.8, cap 40).
