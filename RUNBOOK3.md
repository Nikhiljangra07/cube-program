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

**AMENDMENT (2026-07-22, pre-training, Nikhil's call):** keep-frac 0.6 -> **0.4**. Rationale:
a book is self-redundant (core concepts restated many times), so the easy token fraction is
larger than on the twice-distilled corpus where 0.4 sat at the tolerance edge — deeper cut
is better-motivated on raw prose. Accepted interpretation cost: if book arms fail, "blanks
fail on books" vs "0.4 too deep" needs one follow-up arm at 0.6 (~$3) to separate.

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
