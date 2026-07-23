# RUNBOOK 4 — the TRANSFORMATION GATE run: foresight-lane Clausewitz (face #1 of the cube)

Question: does TRANSFORMED data (book re-rendered into skill-pure, surface-diverse
foresight-scenes) move the one dimension that raw-book training could not (run 3 null:
best book arm 3.60 < keep100 anchor 3.69; foresight flat 2.9-3.0 across 9 reads)?
This is the first test of the "higher score" half of the density thesis — and it
manufactures the first specialist adapter for the Rubik's-cube routing architecture.

## Design (settled 2026-07-23, before any training)

**Substrate:** `data/lane_foresight/lane_pages_train.jsonl` — up to 855 scenes, one per
Clausewitz train page. Renderer: **Kimi K2.6** via OpenRouter (beat K3 5:1
position-consistent across two judge families, n=19 pages, out/renderer_verification.json).
Gate: Gemini 2.5 Flash, 5 kill-rules (fidelity, concreteness, foresight density, collapse,
close) + 420-word length guard. Judge: Sonnet 5 — three families, no self-grading.

**Scene contract:** situation w/ named actor + concrete stakes (user turn) → projection
(assistant turn): >=2 time horizons per option, >=1 second-order effect, one "what breaks
this projection," directional close with flip condition. Lane-EMPHASIZED, not exclusive
(run-3 narrowing-tax lesson): multiplicity + decisiveness floors present in every scene.
16 surface domains rotate by page_idx (Physics-of-LMs multi-presentation rule).

**Arms (worker adapter only; decomposer = run-2 dec_keep1.0 for ALL arms, unchanged):**
| arm | data | labels | schedule |
|---|---|---|---|
| laneF | lane scenes + anchor_300 | band keep-0.6 (re-scored on lane data) | mastery, 85% exit, capped at matched steps |
| keep100 anchor | (run-2 adapter, regen threads on-card) | — | — |
| book_C06 anchor | (run-3 adapter, regen threads on-card) | — | — |

laneF uses the PROVEN settings end-to-end (keep-0.6 + mastery + anchor_300); the ONLY new
variable vs run-3's book_C06 is the data transformation. book_C06 is therefore the direct
ablation: same book, same masking, same schedule — raw pages vs transformed scenes.

**Card-class control:** all three thread sets generated on the SAME pod/card in one
session (run-3 lesson: mastery60 anchor read PAR on Ada, -0.19 on PRO 6000 regen).

## Pre-training QC gates (data must pass BEFORE any GPU spend)
1. Coverage: >=800/855 scenes on disk (drop rate <=6.5%); rejected.jsonl reviewed.
2. Bloat: median projection 220-360 words; NO scene >420 (guard enforced at render).
3. Diversity/collapse: (a) no actor first-name appearing in >4% of scenes,
   (b) mean pairwise 4-gram Jaccard on 200 random scene pairs < 0.05,
   (c) all 16 domains within 2x of each other in count.
4. Fidelity spot-check: 10 random scenes read manually against their source pages.

## Success criteria (FROZEN before training)
- **Format survival:** laneF >= 44/48 answered.
- **SIGNAL E (headline): laneF foresight >= in-session keep100 foresight + 0.25 AND
  >= 3.25 absolute** — the unchanged checkpoint-1 bar. This is the claim the run exists
  to test.
- **Narrowing-tax guard: laneF overall >= in-session keep100 overall - 0.15.** If
  foresight rises but overall craters below this, the lane bought its dimension by
  selling the others — report as "purity's price," not success.
- **Transformation's share: laneF vs book_C06 (same book, same machinery, raw vs
  transformed).** laneF - book_C06 >= +0.20 overall OR >= +0.30 foresight isolates the
  transformation as the active ingredient.
- **Null:** laneF within noise of book_C06 on foresight AND overall -> transformation
  adds nothing at this scale on this bench; capacity-bound hypothesis (v3) survives its
  strongest challenge yet. Report honestly; the cube loses its face factory and the
  program pivots (different lane, or bigger base).

## Budget
Render ~$2.50 (OpenRouter K2.6) + gate ~$0.30 (Gemini Flash) | pod (score + 1 train +
3 gens, RTX 6000 Ada class) ~2h ≈ $2 | judge session 4 (3 arms x 48) ≈ $4-5.
All-in ≈ $9-10.
