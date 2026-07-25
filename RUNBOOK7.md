# RUNBOOK 7 — Face Factory II: carved behavioral specialists + the oracle ceiling

**Question (the Rubik's-cube qualification test):** can three behavior-specialist adapters
(foresight / distinction / viability), carved from the existing scored v5 pool and trained
at the program's efficiency settings, each beat the generalist on their own lane — and does
per-problem ORACLE routing over {3 faces + generalist} beat the generalist at all? Only if
both hold does building a dispatcher mean anything. The goal is NOT beating frontier
models; it is "touch the generalist's mark at a fraction of the training compute, with
routing headroom above it."

**Why this can work where run 4 failed:** run 4 tried a KNOWLEDGE face (book-derived) and
died on the storage null (probes: nothing retrievable). This run builds BEHAVIOR faces
from response-style data — the modality where SFT provably moves dimensions at 3.4B
(v5: distinctness 2.43 → 3.73 vs base). No book knowledge required.

## Data & curation (Stage 0 — before any GPU)

- Pool: 964 problems (corpus_v5_train 480 + corpus_v5_topup 484, zero overlap), each with
  4 pos_threads and original 6-dim gate scores.
- Original gate scores are truncated (multiplicity all-5; foresight 3/4 only) → carving on
  them would produce near-clones. **Curation = blind 1-10 re-score** (rescore_pool.py,
  Sonnet 5, one pass, set-level, three lanes only: foresight / distinctness / viability)
  → `data/faces/rescored.jsonl`.
- **Carve procedure (frozen; numeric cuts filled from the rescored distributions and
  recorded here before training):** face-K subset = top-quartile on lane K AND ≤ median on
  the other two lanes; minimum 200 problems per face (loosen the other-lane condition
  stepwise, documented, if under 200); pairwise subset overlap measured and published —
  target ≤ 25%. Every carve decision happens BEFORE any training.
- Training rows: all 4 threads of each selected problem, worker format (same prep as v5).

## Arms

| adapter | data | labels | schedule |
|---|---|---|---|
| `wrk_faceF` (foresight) | face-F subset | keep-0.6 band | fixed, 1.25 epochs (our number, run 6) |
| `wrk_faceD` (distinction) | face-D subset | keep-0.6 band | fixed, 1.25 epochs |
| `wrk_faceV` (viability) | face-V subset | keep-0.6 band | fixed, 1.25 epochs |
| `wrk_faceG` (cube generalist) | 317-problem COMPLEMENT (pool − face union; zero row-sharing with faces) | keep-1.0 | fixed, 1.25 epochs |
| `wrk_keep1.0` anchor | (existing run-2 adapter — NOT retrained, NOT a cube member) | keep-1.0 | — |

**Design amendment (2026-07-25, pre-training, Nikhil):** the cube gets its OWN generalist
`wrk_faceG`, trained on the complement so the four cube diets PARTITION the pool — no row
clash between members. The incumbent `wrk_keep1.0` remains the measuring stick only: the
test becomes "four small disjoint-diet adapters (routed) vs one big-diet incumbent."
Complement lane profile is naturally balanced (fore 6.31 / dist 8.24 / via 6.20 ≈ pool),
md5 6915284… . Session-F grows to 5 arms; oracle is computed over the 4 CUBE members
(faceF/D/V/G), read against the keep100 anchor.

Decomposer: `dec_keep1.0` everywhere, unchanged. All new adapters train from base — no
merges, no shared init, per the isolation mandate.

## Judge Session-F (one card, one session)

4 arms × 48 problems: faceF, faceD, faceV + keep100 regenerated on-card. Sonnet 5,
max_tokens 12000, coverage ≥44/48 per arm (discard-and-rerun rule).

## Frozen reads

1. **FACE BAR (per face):** own-lane dimension ≥ keep100's + 0.20 AND overall ≥ keep100
   − 0.15. A face that buys its lane by cratering overall is "purity's price," not a pass.
2. **ORACLE CEILING (the cube's go/no-go, computed from the same session, free):** for
   each of the 48 problems take max(per-problem overall) across the 4 arms; oracle mean
   vs keep100 mean:
   - oracle ≥ keep100 + 0.20 → real routing headroom exists → dispatcher build licensed.
   - oracle < keep100 + 0.10 → even PERFECT routing buys nothing at this scale →
     **cube dead at 3.4B with carved faces** — no dispatcher gets built, regardless of
     how many faces passed read 1.
3. **VERDICT GRID:**
   - ≥2 faces pass + oracle headroom → build dispatcher (Stage 2), run routed-system test.
   - Faces pass but no oracle headroom → faces are real but redundant on this bench —
     report; cube needs harder/more-varied problems or bigger base.
   - No face passes → carved behavioral faces null at 3.4B → lane corpora must be
     GENERATED, not carved (ties into run-4b fork decisions).
4. **Stage 2 (only if licensed): routed-system bar** — dispatcher-routed answers ≥
   keep100 − 0.10 overall (touch the mark) with routing ≠ constant (must actually switch;
   a dispatcher that always picks one arm is a null result even at par).

## Mechanics rider (same pod, ~$1)

peft multi-adapter hot-swap test on granite: reproduce the 0.19.1 garbling, test newer
peft, measure swap latency. Independent of face quality; retires the cube's known
engineering landmine.

## Isolation & naming

`data/faces/` for curation artifacts; adapters `wrk_face{F,D,V}`; threads
`out/run7/eval_face*_v5_threads.jsonl`; judged by `judge_run7.py` (Session-F block);
backup `run7_bundle.tgz`. Never mixed with runs 1-6 files.

## Budget

Re-score ~$8 · pod (3 trains ~200 steps each + 4 gens + mechanics test, Blackwell) ~$3 ·
Session-F ×2 coverage margin ~$12 → **~$23 all-in; zero OpenRouter.**

---

## Stage 0 RESULTS — curation (2026-07-25, frozen before any GPU)

Re-score: 964/964 problems, 0 failures, blind Sonnet 5, 1-10 scale (~$8). Distributions
un-truncated: foresight sd 0.72 (4-8), distinctness sd 0.71 (4-9), viability sd 0.66 (5-8).

Carve: strict quartile carve FAILED the 200-minimum for D (56) and V (81); stepwise slack
reached size only at slack (1,1) where the other-lane constraint is vacuous. Adopted
documented endpoint: contrast score z(own) - mean z(others), top 220 per lane.

| face | problems | worker rows | own lane (pool) | other lanes | md5 |
|---|---|---|---|---|---|
| F foresight | 220 | 880 | 7.05 (6.44) | dist 7.85, via 5.91 | 11910a55… |
| D distinctness | 220 | 880 | 8.61 (8.17) | fore 6.21, via 5.55 | e9feb55f… |
| V viability | 220 | 880 | 6.91 (6.15) | fore 6.23, dist 7.84 | 0056aacb… |

Overlaps: F&V 8%, D&F 5%, D&V 3% (bar was <=25%). Leak guards: 20 prep_v5 holdout
problems excluded (generalist parity); bench overlap verified 0/48.

---

## RESULTS (2026-07-25, Session-F + Session-F2 stability replicate, 48/48 all arms both)

| arm | overall s1/s2 | own lane s1/s2 (anchor) | face bar |
|---|---|---|---|
| faceF foresight | 3.66 / 3.71 | 3.04 / 2.94 (2.88 / 2.88) | FAIL (needed +0.20; got +0.16/+0.06) |
| faceD distinctness | 3.72 / 3.62 | 3.65 / 3.71 (3.67 / 3.75) | FAIL (~par on own lane) |
| faceV viability | 3.61 / 3.61 | 2.67 / 2.77 (2.58 / 2.73) | FAIL (+0.09/+0.04) |
| faceG generalist | 3.66 / 3.56 | — | fallback seat, ≈ anchor |
| keep100 anchor | 3.56 / 3.59 | — | — |

Frozen verdict (fired in BOTH sessions): **<2 faces pass → carved behavioral faces are
NULL as lane-specialists at 3.4B; genuine specialization requires GENERATED lane corpora.**

Findings beyond the grid (replicated in both sessions):
1. **Every cube member ≥ anchor overall** (3.56-3.72 vs 3.56/3.59) — four adapters, each
   on 17-32% of the incumbent's row-mass at 1.25 epochs, all match-or-beat it. The
   efficiency result replicates from a new angle (disjoint small diets).
2. **Oracle ceiling +0.42/+0.40** — but the pre-registered oracle read is hereby annotated:
   max-of-4-noisy-arms inflates by construction. Cross-session WIN-STABILITY is the honest
   metric: 41.7% same-winner agreement vs 26.8% chance (real, p≈0.01, modest); hard core
   (same winner both sessions AND ≥0.5 over anchor in both) = **7/48 problems**.
3. **Mechanics rider: peft hot-swap CLEAN on granite** under load_adapter/set_adapter
   (peft 0.19.1, exact output match vs fresh single loads; median swap 6.32 ms). The
   0.19.1 landmine did not reproduce in this two-adapter pattern; dispatcher-layer
   engineering is unblocked (out/run7/swap_verdict.json).

**Stage-2 decision: dispatcher NOT built.** Routing signal exists above noise but the
exploitable stable core (~15% of problems) bounds realistic dispatcher gain to roughly
+0.05-0.15 over the best single arm — an order below the oracle mirage, and the best
single arm is itself session-unstable (faceD s1, faceF s2). Building a router to harvest
7 stable problems would be the slop this runbook exists to prevent.

Costs: rescore ~$8 · pod ~1h ≈ $2 · Session-F ×2 ≈ $16 · probes/none → ~$26 all-in.
Bundle: density_run7/run7_bundle.tgz md5 b1dcf8a4… (4 adapters, threads, swap verdict).
