# PILOT 8 — grounded-generation falsification pilot (pre-RUNBOOK8)

**Question:** before spending the remaining budget on full lane-corpus generation, test the
pipeline's central claim — that showing DeepSeek V4 Pro a high-density source passage
(Clausewitz-class for foresight, Cicero/Bagehot-class for viability) produces measurably
more lane-extreme threads than the same prompt WITHOUT the passage. If passages add
nothing, the "books as foundation" narrative is falsified and the pipeline is honest
frontier-model prompting — we would then say so, not dress it up. (WRAP / Allen-Zhu
license the transformation; this pilot tests whether OUR grounding is real.)

## Design

Lanes: **F (foresight)** and **V (viability)**. Distinctness is cut — it is a set-level
property the worker cannot move from inside one blind thread, and it has the least pool
headroom (8.17/10).

**Source books (on disk, read-only):**
- F: clausewitz-on-war, thucydides-peloponnesian-war, plutarch-lives
- V: cicero-on-duties, aristotle-nicomachean, bagehot-lombard-street

**Passage selection (generator-family selects its own food; judge family never sees it):**
~1,100-word chunks, 20 evenly-spaced per book (60/lane), DeepSeek scores lane density
1-10, top 8 per lane frozen with md5 → `data/pilot8/passages_{F,V}.json`.

**Problems:** seed-8 sample of 30 from the 964 pool (excluding prep_v5's last-20 holdout;
bench overlap already 0/48). First 15 → F, last 15 → V. Existing facets/angles reused;
4 threads per problem, one per angle, workers blind to each other (v5 pattern).

**Conditions (per lane × problem):**
| cond | prompt | passage |
|---|---|---|
| G grounded | lane-extreme worker | own-lane passage (rotate top-8 by problem index) |
| U ungrounded | SAME worker prompt | none — length-matched primary control |
| X cross | SAME worker prompt | wrong-lane passage, same index — specificity control |
| P pool | (no generation) | problem's original pos_threads — in-session baseline |

360 generated threads (15×4×3×2). All G/U/X prompts demand 4-6 sentences + a final
`TRACE:` line (structural device borrowed; stripped before judging so all conditions
present identically).

**Gate (Sonnet 5, one session, blind):** 120 calls — each (problem, condition) set of 4
threads scored 1-10 on OWN lane only, plus per-thread flags `leak` (source-era
particulars foreign to the problem's setting) and `hedge` (fails to commit). Judge never
sees passages or condition labels; call order shuffled. Retry-on-empty, no temperature
param, coverage 120/120 or the session is discarded.

## Frozen reads (all decided before generation)

1. **GROUNDING REAL:** mean own-lane score G ≥ U + 0.7. FAIL → passages falsified →
   grounding stage dropped from RUNBOOK8; program reports prompt-only generation honestly.
2. **PASSAGE-SPECIFIC:** G ≥ X + 0.5. FAIL (while read 1 passes) → "any classical text"
   effect — treated as falsification of the structure-transfer claim, same consequence.
3. **EXTREMITY:** ≥50% of G threads ≥8 own-lane AND G mean ≥ P mean + 1.5. FAIL alone →
   worker prompt insufficient → iterate prompt, re-pilot (~$1). *Annotated confound:
   G/U/X are 4-6 sentences vs P's 2-3 — G-vs-P is calibration only; G-vs-U is the clean
   length-matched read.*
4. **LEAK:** ≤10% of G threads leak-flagged. FAIL alone → tighten guard wording, re-pilot.
5. **DECISIVENESS PRESERVED:** ≤15% of G threads hedge-flagged (lane extremity must not
   buy hedging).

**Decision:** 1+2+3 pass → freeze full RUNBOOK8 and scale (~2,600 threads). 1 or 2 fail →
the honest fork (no book narrative). Only 3/4/5 fail → cheap prompt iteration.

## Isolation & budget

`data/pilot8/`, `out/pilot8/`, `scripts/pilot8_*.py`. No GPU. DeepSeek ≈ $0.40
(OpenRouter), Sonnet ≈ $1.30. **< $2 all-in.**

---

## RESULTS (2026-07-25 — coverage 120/120, single blind Sonnet session)

| lane | G grounded | U no-passage | X wrong-passage | P pool |
|---|---|---|---|---|
| F foresight | 8.00 | 7.83 | 7.98 | 6.40 |
| V viability | 7.72 | 7.70 | 7.58 | 6.60 |

| read | F | V |
|---|---|---|
| 1 GROUNDING REAL (G≥U+0.7) | **FAIL** (+0.17) | **FAIL** (+0.02) |
| 2 PASSAGE-SPECIFIC (G≥X+0.5) | **FAIL** (+0.02) | **FAIL** (+0.14) |
| 3 EXTREMITY (≥50% G≥8 AND G≥P+1.5) | PASS (78.3%, +1.60) | FAIL (66.7% ✓, +1.12 ✗) |
| 4 LEAK (≤10%) | PASS (8.3%) | PASS (0%) |
| 5 DECISIVENESS (≤15% hedge) | PASS (0%) | PASS (0%) |

**Frozen verdict (reads 1+2, both lanes): GROUNDING FALSIFIED.** Passages contribute
nothing measurable — G ≈ U ≈ X within noise. The wrong-lane passage performs identically
to the right one, so the passage is not even being read for content. The book-foundation
narrative is dead for thread generation at this model scale: DeepSeek V4 Pro already
contains the reasoning structures; the passage stage was frontier-model prompting wearing
a book jacket, exactly the self-deception the pilot's guardrail existed to catch. Per
the pre-registered decision rule, the grounding stage is DROPPED and any scaled corpus
is reported honestly as prompt-only synthetic generation.

**What the pilot found instead — the real lever is the worker prompt.** U (prompt-only,
no passage) scores 7.83 F / 7.70 V vs pool 6.40/6.60: the lane-extreme prompt ALONE
lifts foresight +1.43 and viability +1.10 over the v5 corpus, with zero hedging and
leak within bar. Foresight already clears the full extremity bar prompt-only; viability
misses only the mean-margin condition (+1.12 vs +1.5 needed) — a prompt-iteration
problem (demand harder mechanism/cost/constraint density), not a pipeline problem.

*Annotated confound (registered pre-run):* G/U/X threads are 4-6 sentences vs P's 2-3 —
the G-vs-P and U-vs-P lifts partially reflect length; the clean length-matched reads are
G-vs-U and G-vs-X, which are the ones that killed grounding.

Cost: ~$0.55 DeepSeek + ~$1.9 Sonnet ≈ **$2.5 all-in.** The falsification saved the
full-scale passage machinery (~$3 + a false paper claim) and redirected RUNBOOK8 to the
prompt-only path with one V-prompt iteration.
