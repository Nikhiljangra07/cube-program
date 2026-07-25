# RUNBOOK 8 — Face Factory III: generated foresight face (prompt-only, post-PILOT8)

**Question:** can a GENERATED lane-extreme corpus do what run 7's carving could not —
produce a real foresight specialist that beats the incumbent generalist on its own lane
without cratering overall? This is the existence proof for the cube: one real face.

**Provenance (all frozen upstream):** run 7 killed carved faces; PILOT8 falsified
book-grounding (G≈U≈X) and proved the lane-extreme worker prompt alone lifts foresight
+1.43 over pool with 78%≥8, clearing the pilot extremity bar. PILOT8 addendum dropped
the viability face (two strikes against judge ceiling compression). Run 8 is therefore
**foresight-only, prompt-only, honestly reported as synthetic generation by DeepSeek
V4 Pro** — no book narrative.

## Corpus (Stage 1 — no GPU)

- **Problems:** the run-7 face-F carve, 220 problems (md5-frozen in carve_manifest).
  Preserves the run-7 cube partition: F-carve ∩ faceG complement = 0, so the reused
  `wrk_faceG` stays a disjoint-diet cube member.
- **Generation:** F-prompt v1 verbatim from PILOT8 (`pilot8_generate.py` TASK["F"],
  no passage), DeepSeek V4 Pro, temp 0.75, 4 threads/problem (one per original angle,
  workers blind to each other), TRACE stripped. 880 threads ≈ $1.4 OpenRouter.
- **Gate (Sonnet 5, blind, single session):** per-problem set scored with the PILOT8
  gate instrument (foresight lane def, leak/hedge flags), shuffled, coverage 220/220 or
  discard. **Admission (frozen):** set mean ≥ 7.5 AND no leak-flagged thread.
  Target ≥ 150 admitted problems (600 rows). If < 150: top up from D∪V-carve problems
  ranked by F-contrast (still disjoint from faceG's diet — partition preserved);
  top-up generation+gating repeats the same instrument. ≈ $3.5 Sonnet.
- **Diet:** admitted generated rows (~600-880) + ONE original pos_thread per admitted
  problem (~150-220 rows, ≈20% anti-narrowing slice, rows the run-7 faceF already
  trained on — no new leak surface). Worker file byte-compatible with prep_v5 format
  (build via the build_faces.py templates). Bench overlap re-verified 0/48 (inherited
  from carve, re-checked at build).

## Training (Stage 2 — pod, ~$1.5)

One adapter: `wrk_faceF_gen`, from base, r64/α64/lr2e-4/bs8/seq1024/--gc,
**keep-0.6 band mask, fixed 1.25 epochs** (the program recipe; no mastery-loop
scheduler). Decomposer `dec_keep1.0` unchanged. No merges, no shared init.

## Judge Sessions G + G2 (two independent sessions, one card each)

3 arms × 48 bench problems: `faceF_gen`, `faceG` (run-7 adapter, threads REGENERATED
on-card), `anchor keep100` (regenerated on-card). Sonnet 5, max_tokens 12000, no
temperature param, coverage ≥44/48 per arm, discard-whole-and-rerun rule. Session G2
is the mandatory stability replicate (run-7 lesson: single-session wins are noise
until replicated).

## Frozen reads

1. **FACE BAR (the run's verdict, must hold in BOTH sessions):**
   foresight(faceF_gen) ≥ foresight(anchor) + 0.20 AND overall(faceF_gen) ≥
   overall(anchor) − 0.15.
2. **CUBE MEMBER READ:** overall(faceF_gen) and overall(faceG) ≥ anchor − 0.15 both
   sessions (economics replication #6).
3. **ORACLE + STABILITY (reported, not licensing):** oracle over {faceF_gen, faceG}
   vs anchor; cross-session win-stability. With a 2-member cube no dispatcher is
   built this run regardless — these reads only inform run 9 design.
4. **VERDICT GRID:**
   - Read 1 passes both sessions → **first real face exists**; generated-corpus path
     validated; run 9 may fund V/D faces (with %-based extremity bars) + dispatcher.
   - Read 1 fails → generated lane corpora at this intensity do not specialize 3.4B
     under SFT either → the specialization ceiling is the model or the recipe, not
     the data — H-Small capacity fork becomes the live question.
   - Read 2 fails while 1 passes → purity's price is real; report, do not ship.

## Isolation & naming

`data/run8/` (corpus + gate), `out/run8/` (threads, judge), adapter `wrk_faceF_gen`,
scripts `scripts/run8_*.py|sh`, backup `run8_bundle.tgz`. Never mixed with runs 1-7.

## Budget (remaining: ~$26 Anthropic, ~$9 OpenRouter, ~$77 RunPod)

Generation ~$1.4 OR · gate ~$3.5 · pod ~$1.5 · sessions G+G2 ~$10 → **~$17 all-in**,
≥$9 Anthropic margin. Stage gates: gate fails → stop before pod; train fails → stop
before judge; every stage reports before the next spends.
