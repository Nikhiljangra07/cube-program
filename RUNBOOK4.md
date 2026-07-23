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
3. Diversity/collapse: (a) no actor first-name OR surname in >4% of scenes,
   (b) mean pairwise 4-gram Jaccard on 200 random scene pairs < 0.05,
   (c) all 16 domains within 2x of each other in count,
   (d) no deadline/dollar token in >15% of scenes (gen-1: "Friday" 44%, "$340K" 9%),
   (e) no 5-gram in >5% of scenes (gen-1: brief-phrase echoes up to 19%),
   (f) zero "Option A/B/1/2" labels; zero second-person projections (bench is third-person).
4. Fidelity spot-check: 10 random scenes read manually against their source pages.

### Gen-1 post-mortem (2026-07-23, full corpus discarded before GPU — the gates worked)
Deep scan of the 812-scene gen-1 corpus found, beyond the known Maya-collapse (67%):
surname collapse ("Chen" 69%, "Voss" 22%), Option-A/B template in 77%, renderer parroting
the brief's own phrases (up to 19% of scenes), stock deadlines/dollars ("Friday" 44%,
"72 hours" 17%), war metaphors leaking into 11% of non-military scenes, and 6% mechanical
JSON parse drops. Register check against bench problems confirmed third-person is CORRECT
(bench briefs are third-person case statements) — first-person "fix" rejected. All fixes
applied at the prompt+gate level; gen-2 rendered fresh. Cost of discard: ~$3.

### Gen-2 QC verdict (2026-07-23, Nikhil's call: ACCEPT & GO GPU)
Final corpus: 843/855 scenes, ~469k est tokens. Gates: coverage PASS, bloat PASS (median
285w, max 419), 4-gram jaccard PASS (0.0004), domains PASS (1.30), 5-gram echo PASS (4.3%),
phrase-family PASS (all <=14%), templates PASS (0 Option-labels, 0 second-person),
fidelity spot-check PASS (3 deep reads — principle mapping verified incl. non-obvious
treasury->hidden-compensation transfer). ACCEPTED RESIDUALS (asterisks, furniture-level):
(a) recurring secondary surname "Okonkwo" ~9% of scenes, (b) "Tuesday" deadlines ~17%,
(c) protagonist-pool names recruited as secondary characters (~16% mention-rate for worst).
Lesson recorded: BAN-LISTS DON'T DIVERSIFY — the model promotes its next default
(Maya->Priya-as-secondary, Voss->Okonkwo, Friday->Tuesday); INJECTION diversifies
(assigned protagonists hit ~1.6% by construction). Future lanes: inject secondary
names/companies/weekdays too. Render cost total (gen-1 + gen-2 + retries): ~$11 OpenRouter.

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

---

## RESULTS (2026-07-23, single-session Sonnet 5 judge, all 3 thread sets same-card RTX 6000 Ada)

| arm | overall | foresight | dist>=4% | viability | n |
|---|---|---|---|---|---|
| keep100 anchor (no book) | **3.61** | 3.02 | 72.9 | 2.73 | 48 |
| book_C06 (raw book, keep-0.6+mastery) | 3.60 | 2.96 | 64.6 | 2.65 | 48 |
| laneF (TRANSFORMED book, keep-0.6+mastery) | 3.47 | 2.85 | 75.0 | 2.46 | 48 |

**Against the frozen criteria:**
- **SIGNAL E: FAILS** — laneF foresight 2.85 vs needed >= 3.27. Foresight did not rise;
  it reads 0.17 BELOW the in-session anchor. The dimension the lane was built to move
  did not move.
- **Narrowing-tax guard: HOLDS by 0.01** (3.47 vs floor 3.46) — technically no tax, but
  viability 2.46 is the arm's worst dimension, the same narrowing signature as run 3's
  mastery arms.
- **Transformation vs raw: WITHIN NOISE** (-0.13 overall, -0.11 foresight vs book_C06).
  The cleanest one-variable ablation the program has run: same book, same masking, same
  schedule — transformed scenes bought NOTHING over raw pages.
- **Book value: still none** (3.47 < 3.61). Two runs, five arms, two data forms: Clausewitz
  does not move this bench at 3.4B.

**THE PROGRAM-LEVEL READ (runs 1-4):** all three data-side levers have now returned
honest nulls on the "higher score" half of the density thesis at 3.4B — selection
(run 1), schedule (runs 2-3), substance/transformation (run 4). The v3 conclusion
("foresight is capacity-bound — model ceiling, not corpus") has survived its strongest
attack. What SURVIVES and replicates is the efficiency half: par benchmark at ~36-40%
of tokens and ~70% of compute (runs 2-3, both substrates). Mastery telemetry footnote:
transformed scenes took MORE work to master (4.53 mean visits vs 3.52 raw) — denser to
chew, but the extra chewing bought no benchmark. Next forks (Nikhil's call): (a) bigger
base (7-9B / H-Small class) where capacity may unlock the levers, (b) different lane
(foresight may be uniquely capacity-bound), (c) bank the efficiency result and write the
program up. Costs: run 4 ~= $17 all-in (renders $11 + pod $1.90 + judge $4).
Adapters: divergent-model-backups/density_run4/run4_bundle.tgz (md5 5d2a7ff9, verified).
