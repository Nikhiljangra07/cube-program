# RUNBOOK 3 — the BOOK run: page-restricted mastery on Clausewitz (On War, Graham PD)

Question: does the page-by-page restricted method (band blanks + mastery) extract more
benchmark from RAW BOOK TEXT than plain reading, at matched compute? First run on a
substrate with real bulk redundancy (346k train tokens, 855 pages + 94 held-out pages).

## Design (settled 2026-07-22, before any training)

**Substrate:** `data/book/book_pages_train.jsonl` — 855 pages x ~300 words, each row =
prev-page tail (120w context, user turn) -> page (assistant turn). Built by
build_book_pages.py from lora-corpus-source Clausewitz (outside all corpus lineage).

**Fixed decomposer:** ALL arms reuse run-2's `dec_keep1.0` adapter (from
divergent-model-backups/density_run2). Book pages don't fit decomposer format; freezing it
removes dec-format noise — arms differ ONLY in the worker adapter.

**Format anchor:** every arm's worker training includes the SAME 300-row slice of the run-2
`wrk_keep1.0` dataset (full labels, seed-42 sample) so the bench answer format survives.
The book teaches substance; the anchor holds format. Identical across arms = cancels out.

**Arms (worker adapter only, identical recipe, matched optimizer steps):**
| arm | book labels | schedule |
|---|---|---|
| A book_plain | ALL page tokens graded | uniform (train_masked, keep-frac 1.0 build) |
| B book_blank | band **keep-0.4** of page tokens (per-token NLL, 3:1 easy-bias, band RE-MEASURED on book) | uniform |
| C book_mastery | same labels as B | mastery loop, 85% exit, capped at A/B's steps |

**AMENDMENT 1 (2026-07-22, pre-training, Nikhil):** keep-frac 0.6 -> 0.4 (books are
self-redundant; deeper cut better-motivated on raw prose).
**AMENDMENT 2 (2026-07-22, pre-training, Nikhil):** run BOTH fractions in parallel on a
bigger card (RTX PRO 6000, 96GB) — arms B/C at 0.4 AND B'/C' at 0.6. This converts the
gamble into the fraction-response curve on books: C-0.4 vs C-0.6 decides whether keep-0.3/
0.35 is licensed next. Five worker trains total; pair trains 2-at-a-time (~45GB each,
sequential fallback on OOM).
**Card-class control:** PRO 6000 is a different arch than the Ada that generated all prior
threads — so the session-3 ANCHOR threads (keep100, mastery60) are REGENERATED on the PRO
pod from archived adapters. Every thread set judged in session 3 then shares one card.
Judge session 3 = 7 arms: bookA, bookB04, bookC04, bookB06, bookC06, keep100*, mastery60*.
Budget update: pod ~3h @ $1.99 ≈ $6 | judge 7x48 ≈ $10 | all-in ≈ $16-17.

**Steps:** A and B train 5 epochs over (855 book + 300 anchor) rows; C capped at same steps.

## Procedure (pod: RTX 6000 Ada, pins per RUNBOOK.md step 0)
1. Upload scripts + data/book/*.jsonl + anchor slice + bench problems.
2. `loss_band_gate.py --per-token` on book_pages_train (conditional NLL given page context).
3. `build_masked_dataset.py` keep-frac 1.0 and 0.6 (band) on book rows; concat anchor slice
   (full labels) to each arm's file.
4. Train A, B (train_masked) and C (train_mastery, --max-steps = A's steps).
5. Free metric: heldout_nll.py on book_pages_heldout (94 pages) per arm — pipeline check ONLY
   (metric is biased toward unmasked arms — proven in run 2; never a verdict).
6. gen_threads.py per arm (--dec = dec_keep1.0 restored from archive, --wrk = arm adapter).
7. Judge session 3, ONE session: bookA, bookB, bookC + anchors mastery60 + keep100 (threads
   on disk). Coverage guard >=44/48 per arm.

## Success criteria (FROZEN before training)
- **Format survival:** every arm answers >=44/48. An arm below that fails regardless of mean
  (the anchor slice exists precisely to prevent this).
- **Signal D (the run's headline):** bookC (mastery-blanks) overall >= bookA (plain reading)
  + 0.20 -> the restricted-page method extracts more than reading. bookB vs bookA isolates
  the blanks' share; bookC vs bookB isolates mastery's share.
- **Book value check:** if NO book arm beats the in-session keep100 anchor by > 0.0, the book
  added nothing measurable to this bench — report as such (possible: bench is modern-decision
  flavored; Clausewitz may transfer weakly. That is a finding about substrate-bench match,
  not about the method).
- **CHECKPOINT 1 WATCH (foresight ceiling):** claimed ONLY if some book arm's foresight
  >= in-session keep100 foresight + 0.25 AND >= 3.25 absolute. Anything less is "watch
  continues," not a claim. (History: flat ~2.9-3.0 across 8 rounds; mastery60 hit 3.19.)
- **Null:** all book arms within noise of each other AND of anchors -> raw-book occlusion
  doesn't move this bench at this scale; the transformation gate (fluent re-render) becomes
  the only remaining path for books. Report honestly.

## Budget
Scoring ~15 min | 3 worker trains ~60 min | 3 bench gens ~75 min | pod total ~3h ≈ $2.60
Judge session 3 (5 arms x 48) ≈ $7. All-in ≈ $10.

---

## RESULTS (2026-07-22, single-session Sonnet 5 judge, all 7 thread sets generated on the
## RTX PRO 6000 — card-class control honoured; verdicts computed by rejudge_arms.py)

| arm | overall | foresight | dist>=4% | n |
|---|---|---|---|---|
| book_A (plain reading) | 3.60 | 3.00 | 62.5 | 48 |
| book_B04 (blanks 0.4) | 3.52 | 2.90 | 64.6 | 48 |
| book_B06 (blanks 0.6) | 3.59 | 3.02 | 66.7 | 48 |
| book_C04 (mastery 0.4) | 3.46 | 2.94 | 66.7 | 48 |
| book_C06 (mastery 0.6) | 3.50 | 2.92 | 75.0 | 48 |
| keep100 anchor (regen) | **3.69** | 3.15 | 77.1 | 48 |
| mastery60 anchor (regen) | 3.50 | 2.93 | 56.5 | 46 |

**Against the frozen criteria:**
- **Format survival: PASS** — every arm >= 46/48. The 300-row anchor slice did its job on all
  five book arms (zero format fails on 48-problem gens for the book arms).
- **Signal D: FAILS** — book_C06 3.50 vs book_A 3.60 (delta -0.10; needed +0.20). Neither
  blanks (B ~= A) nor mastery (C slightly under B) extracted more than plain reading.
- **Fraction curve: 0.4 PAR with 0.6** (C04 3.46 vs C06 3.50, delta -0.04) — deep cuts do no
  harm on raw books, replicating run 2's Signal C on a new substrate. keep-0.3/0.35 is
  technically licensed but POINTLESS here until any book arm shows value at all.
- **Book value: NONE** — best book arm (A, 3.60) < in-session keep100 anchor (3.69). The
  PRE-REGISTERED null fired: Clausewitz continuation-training added nothing measurable to a
  modern-decision bench. Finding about substrate-bench match, not the occlusion method.
- **CHECKPOINT 1: watch continues** — best book foresight 3.02 (needed >= 3.40 in-session
  AND >= 3.25). No arm moved the ceiling.
- **Anchor-regen wrinkle (unplanned observation):** mastery60 regenerated on the PRO 6000
  reads -0.19 vs keep100 in-session (3.50 vs 3.69), where run 2's Ada-generated threads read
  PAR (3.65 vs 3.66), and its foresight 2.93 vs run-2's 3.19. Same adapters, same judge
  family, different card + session. Either (a) greedy-decode card drift is larger than
  assumed, or (b) run-2's mastery-par carried more session luck than the +-0.05 wobble
  estimate. Run 2's stacked headline (par at ~36% tokens / 70% compute) should be quoted
  with this asterisk until a third regen settles it.

**Reading:** raw-book occlusion at this scale does not move this bench — the transformation
gate (fluent dense re-render, method 4-strong) is now the only remaining path for book
substrates, exactly as the frozen null clause anticipated. The durable positive across
runs 2-3: grading 40-60% of completion tokens is FREE (never hurts) on both curated corpus
and raw book. Costs: pod ~$5.60 + judge ~$10 = ~$16 all-in.
