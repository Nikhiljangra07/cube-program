# Data-Side Levers in Small-Model LoRA Post-Training: A Pre-Registered Six-Run Study
## (Corpus Density, Mastery Scheduling, and the Storage Question at 3.4B)

> **STATUS: UNOFFICIAL WORKING DRAFT — 2026-07-24.** Complete factual record of the
> density-method program, runs 1–6 + probe study, written to preserve everything while
> fresh. Convert to formal paper after run 4b decides the ending. All numbers below are
> traceable to frozen runbooks (RUNBOOK.md–RUNBOOK6.md, PROBES.md), git history
> (237ef4a → 5475fa4), and md5-pinned artifact bundles (Appendix A).
> Author: Nikhil Jangra. Drafting assistant: Claude (Anthropic).

---

## Abstract

We report a six-run, pre-registered empirical study of data-side levers in the LoRA
post-training regime of a small language model (granite-4.0-micro, 3.4B). Across ~$110 of
compute we tested four levers against a fixed 48-problem judged benchmark: example
**selection** into a learnable NLL band (run 1), token-level **loss occlusion** and a
**mastery scheduler** (run 2, replicated on raw-book substrate in run 3), semantic
**transformation** of book text into skill-pure decision scenes (run 4), and **exposure
count** (run 6); plus a fresh-corpus **headroom** test (run 5) and a purpose-built
**recall-vs-manipulation probe study** to separate stored-but-inert knowledge from usable
knowledge. Every success criterion was frozen before its run.

Two results survive everything. **(1) Efficiency:** benchmark parity is preserved when
only ~36–40% of corpus tokens carry gradient and training runs for ~1.25 epochs instead
of the 5-epoch default — a ~10× reduction of the naive token×epoch budget, replicated on
curated-conversation and raw-book substrates. **(2) A storage null with a mechanism:**
no book-training variant — raw pages, band-masked pages, mastery-scheduled, semantically
transformed, at exposures from 1.25 to 20 per page — wrote *retrievable* knowledge into
the model, despite perfect training-side mastery (85% token accuracy on every page).
Recall probes never moved (Δ ≤ +0.17 on a 0–2 scale vs a no-book control; bar +0.30).
The divergence between climbing token accuracy (saturates ~4.5 visits) and flat benchmark
(saturates ~1.25 visits) makes the gap between *page-completion skill* and *knowledge
acquisition* directly visible with cheap instruments. Selection, schedule, substance, and
exposure nulls are thereby unified under a single mechanism: at this scale and modality,
LoRA continuation training does not create extractable knowledge — so no arrangement of
the data could have mattered. The two surviving unlock candidates are presentation
diversity (Allen-Zhu-style multi-paraphrase rendering; untested as of this draft) and
model capacity.

---

## 1. Motivation and thesis

The program grew out of the divergent-model work (v3/v5, granite-4.0-micro): a 32-round
evidence base showing corpus quality rebalances breaking score ceilings that corpus *size*
could not, and a foresight dimension that stayed flat (~2.9–3.0) across every corpus
intervention — provisionally attributed to model capacity.

The **corpus-density thesis** under test: essence-dense training data buys (a) the same
benchmark at meaningfully fewer tokens [the cheap half], and eventually (b) a higher
benchmark than raw data at any size [the contested half]. Framing corrections adopted at
program start: this is *data-leverage curves in the post-training regime* — not per-token
essence packing, not a Chinchilla extension; the mechanism is gradient-per-token; the
"right zone" is the mid band of base-model per-token NLL, by analogy to the two measured
boundaries of auditory stream segregation (van Noorden 1975; Bregman 1990: coherence
boundary = too easy, segregation boundary = noise).

## 2. Related work (anchors; full map in PAPERS.md)

- **Selection/band:** Marion et al. 2023 (mid-perplexity pruning wins at pretraining
  scale); RHO-Loss (Mindermann 2022: learnable ∧ worth-learning ∧ not-yet-learnt);
  Rho-1 (Lin 2024: token-level selective loss, 3% of tokens); Ankner 2024 (band placement
  is corpus-dependent — a warning we later confirmed); Sorscher 2022 (regime-dependent
  pruning).
- **Quality gates:** LIMA; AlpaGasus; Deita; DataComp-LM (fixed-recipe/vary-corpus
  design we mirror); FineWeb-Edu; phi series.
- **Transformation:** WRAP (Maini 2024: rephrasing ≈ 3× speedup); Nemotron-CC;
  SwallowMath; BeyondWeb (style diversity of rewrites beats rewriter size); **Allen-Zhu &
  Li, Physics of LMs 3.1/3.3: facts require MANY DIVERSE paraphrases to become
  *extractable* rather than merely memorized; ~2 bits/param at ~1000 exposures** — the
  single most load-bearing prior for interpreting our storage null.
- **Repetition:** Muennighoff 2023 (≤4 epochs of repeated data ≈ fresh); Goyal 2024
  (quality × reuse interaction).
- **Cognitive precedents:** Wilson 2019 (85% rule — our mastery exit criterion), Bjork
  desirable difficulties, testing effect, generation effect, Vygotsky ZPD.
- **Known eval hazards:** judge length bias (Zhao 2024), style-vs-capability confusion
  (Berkeley "False Promise"), model collapse (Shumailov 2024) + antidote
  (Gerstgrasser 2024: accumulate, never replace; depth-1 grounded rewriting is safe zone).

Positioning: the mid-band and selective-loss results are pretraining-scale; their SFT/LoRA
small-model behavior was not established. This program contributes that datapoint — mostly
as disciplined nulls plus one strong efficiency replication.

## 3. Common methodology (all runs)

- **Base:** ibm-granite/granite-4.0-micro (3.4B, MoE-hybrid). Two-seat harness:
  decomposer + worker LoRA adapters (r64/α64/lr 2e-4/bs 8/seq 1024, --gc). From run 3
  onward the decomposer is FROZEN at run-2's `dec_keep1.0` for all arms — arms differ only
  in the worker.
- **Benchmark:** 48 out-of-distribution decision problems, 6 dimensions (admits-
  multiplicity, distinctness, concreteness, decisiveness, foresight, viability), graded by
  a judge LLM. **Judge discipline (hard-won):** single judge = Claude Sonnet 5; no
  temperature parameter (rejected by the API); max_tokens 12,000 (thinking eats budget);
  retry-on-empty; coverage guard ≥44/48 per arm — a session below coverage is discarded
  wholesale and rerun, never patched. **All comparisons are within a single judge session**
  (measured cross-session wobble ±0.05, cross-family skew ~0.9).
- **Card-class control:** all thread sets entering one judge session are generated on one
  GPU card, with in-session regeneration of anchor arms. (Adopted after run 3's anchor
  wrinkle, §6.)
- **Pre-registration:** every run's success criteria frozen in its RUNBOOK before any
  training; results read against the frozen grid only; post-hoc diagnoses labeled as such.
- **Provenance:** training data md5-pinned in runbooks; source repos read-only; adapters
  backed up per-run to md5-verified bundles (Appendix A); no adapter ever merged, reused
  as init, or shared across runs.
- **Noise floor:** 48-problem means move ~±0.1 between runs; thresholds set at 0.15–0.30
  accordingly.

## 4. Run 1 — Selection: the learnable-band gate (2026-07-21, ~$5)

**Design.** v5 corpus (~1.05M unique training tokens, already 6-dim judge-gated) vs
`dense60` (NLL mid-band rows, 60% token mass, 3:1 easy-side drop) vs `rand60` (random
rows, matched mass, seed 42). Frozen: Signal A (efficiency) dense60 within ±0.15 of
v5full; Signal B (selection) dense60 ≥ rand60 + 0.20.

**Results** (single-session Sonnet 5, n=47/48/48/48):

| arm | overall | distinctness | dist≥4% | foresight |
|---|---|---|---|---|
| base | 3.28 | 2.43 | 17.0% | 3.02 |
| v5full (1.05M tk) | 3.56 | 3.73 | 75.0% | 2.88 |
| dense60 (0.63M tk) | 3.53 | 3.58 | 62.5% | 2.94 |
| rand60 (0.63M tk) | 3.58 | 3.62 | 64.6% | 3.00 |

**Signal A HOLDS** (Δ0.03): 60% of tokens bought the full corpus's benchmark.
**Signal B FAILS** (Δ−0.05, in noise): the NLL band added nothing over random on this
corpus. Frozen-grid reading: v5 corpus redundant at this size; selection gate unproven —
do not scale it on hope. Post-hoc (labeled): double-gating — the judge gate had already
removed the junk tail (consistent with Ankner corpus-dependence).

## 5. Run 2 — Occlusion + the mastery loop (2026-07-22, ~$19)

**Design.** Rho-1-style loss-side masking on dense60: keep-fraction sweep {1.0 control,
0.6, 0.4, 0.25} of tokens graded (band policy; nothing hidden from the model — full
disclosure, concentrated solving). Plus Nikhil's **mastery regime**: repeat each page
until 85% token accuracy, then advance; compute-capped at the fixed arm's steps.

**Results** (two single-session judgments):
- Session 1: keep100 3.60, keep60 3.64 (run-1 arms replicated in-session).
- Session 2: dense60 3.57 | keep100 3.66 | keep60 3.66 | keep40 3.54 | mastery60 3.65.

**Signal C HOLDS twice:** grading only the mid-band 60% of tokens = par (Δ0.00–0.04);
keep40 holds at tolerance edge (−0.12) ≈ **~24% of original corpus tokens carrying
gradient at par benchmark** (stacked with run 1's 60% row mass → ~36% of v5full tokens).
**Mastery:** par overall (3.65) at **70% compute** (stopped 484/685 steps; all 1,093
pages mastered; mean 3.52 visits — the scheduler self-discovered Muennighoff's ~4-epoch
zone), with best-ever dist≥4% (85.1%) and best-ever foresight (3.19) — individually in
noise, jointly suggestive.
**Instrument finding:** held-out full-token NLL ranked arms OPPOSITE to the blind judge —
demoted to pipeline-check only. (Foreshadowing: this bias returns decisively in run 5.)

## 6. Run 3 — Raw book, page-restricted mastery (Clausewitz; 2026-07-22, ~$16)

**Design.** First bulk-redundancy substrate: On War → 855 train pages (300 words, 120-word
context tail) + 94 held-out; five worker arms at matched steps — plain reading vs band
blanks vs mastery-blanks, at keep-0.4 AND keep-0.6 (dual-fraction amendment, pre-training);
300-row format-anchor slice in every arm. Frozen: Signal D = mastery-blanks ≥ plain
reading + 0.20; book-value check vs in-session keep100 anchor; foresight checkpoint
(≥ anchor+0.25 AND ≥3.25).

**Results** (single session, 7 arms, all threads same-card RTX PRO 6000):

| arm | overall | foresight | n |
|---|---|---|---|
| book_A plain | 3.60 | 3.00 | 48 |
| book_B04 / B06 blanks | 3.52 / 3.59 | 2.90 / 3.02 | 48 |
| book_C04 / C06 mastery | 3.46 / 3.50 | 2.94 / 2.92 | 48 |
| keep100 anchor (regen) | **3.69** | 3.15 | 48 |
| mastery60 anchor (regen) | 3.50 | 2.93 | 46 |

**Signal D FAILS** (−0.10; needed +0.20): neither blanks nor mastery extract more than
plain reading. **Fraction curve PAR** (0.4 ≈ 0.6) — deep cuts free on raw books too
(Signal C replicated on a second substrate). **Book value: NONE** — best book arm 3.60 <
anchor 3.69; pre-registered null fired. **Anchor-regen wrinkle:** mastery60 regenerated on
a different card class read −0.19 vs its run-2 par — source of the card-class control rule;
run-2's mastery headline carries an asterisk pending a third regen.

## 7. Run 4 — The transformation gate (foresight lane; 2026-07-23, ~$17)

**Design.** The substance lever, strong form: re-render each Clausewitz page into a
skill-pure, surface-diverse third-person decision scene (situation → projection with ≥2
time horizons/option, ≥1 second-order effect, a "what breaks this projection," directional
close). Three model families, no self-grading: renderer **Kimi K2.6** (beat Kimi K3 5:1,
position-swapped, two judge families, n=19), gate Gemini 2.5 Flash (6 kill-rules + length
guard), judge Sonnet 5. 16 surface domains + 64-name injection pool rotated by page index.

**Corpus QC (the expensive lesson).** Gen-1 (812 scenes) was discarded whole before any
GPU: protagonist collapse (Maya 67%), surname collapse (Chen 69%), Option-A/B template
(77%), brief-phrase parroting (≤19%), stock deadlines ("Friday" 44%). Gen-2 fixes were
prompt- and gate-level; a phrase-family loose-match check was added after exact n-gram
counters under-measured collapse (75 exact vs 450 family hits = 45% of corpus).
**Program law learned: BAN-LISTS DON'T DIVERSIFY, INJECTION DOES** — a banned default is
replaced by the model's next default (Maya→Priya-as-secondary, Voss→Okonkwo,
Friday→Tuesday); *assigned* names hit ~1.6% by construction. Final corpus: 843 scenes,
~469k tokens, all 9 QC gates passed, residuals documented (Okonkwo ~9%, Tuesday ~17%).

**Arms.** laneF (transformed scenes, keep-0.6 + mastery + anchor) vs book_C06 (SAME book,
SAME masking, SAME schedule, raw pages — the cleanest one-variable ablation of the
program) vs keep100 anchor; all threads one card, one session.

**Results:**

| arm | overall | foresight | dist≥4% | n |
|---|---|---|---|---|
| keep100 anchor | **3.61** | 3.02 | 72.9 | 48 |
| book_C06 (raw) | 3.60 | 2.96 | 64.6 | 48 |
| laneF (transformed) | 3.47 | 2.85 | 75.0 | 48 |

**Signal E FAILS** (foresight 2.85; needed ≥3.27). **Transformation vs raw: WITHIN NOISE**
(−0.13 overall). Book value: still none. Mastery telemetry footnote: transformed scenes
took MORE chewing (4.53 vs 3.52 mean visits) — and the extra chewing bought nothing.
Program-level after run 4: selection, schedule, substance all nulled at 3.4B; the v3
capacity hypothesis survives its strongest attack.

**Caveat recorded at the time:** the gate rendered ONE scene per principle — the original
multi-angle spec (3–4 scenes per principle) was under-implemented. Run 4's null is
therefore "single-angle transformation fails"; multi-angle (run 4b) remained untested —
a caveat that becomes central after the probe study (§9).

## 8. Run 5 — Headroom: fresh-corpus absorption (Federalist Papers; 2026-07-24, ~$7)

**Question (Nikhil's Test 1).** Are the nulls because the model is *full*, or because our
data hit diminishing returns? Disk research identified the burned lineage (Reverend
Insanity, Jin Ping Mei, Machiavelli, Thucydides, Plutarch, Mahabharata, Clausewitz) and
selected the **Federalist Papers** (195k words → 651 pages; never trained; size-twin of
Clausewitz) for the exact run-3 C06 recipe: 586 train + 65 held-out pages, per-token band
scoring, keep-0.6, +300 anchor rows, mastery at matched steps (555).

**Results (frozen reads):**
1. **Learns-the-book telemetry: HOLDS.** 886/886 rows mastered at step 504/555, mean 4.48
   visits (raw Clausewitz: 3.52). ~7 minutes wall on an RTX PRO 6000 Blackwell.
2. **Held-out NLL: INSTRUMENT INVALIDATED by its own control.** fedH read +1.93 nats worse
   than base on unseen Federalist pages (4.47 vs 2.53) — apparently catastrophic. The
   pre-planned control ran run-3's raw-book adapter on *Clausewitz* held-out with the same
   instrument: identical inflation (+2.14; 5.13 vs 2.99). Full-token NLL is structurally
   biased against mastery/masked-trained adapters (run 2's demotion, now terminal). The
   criterion carries no signal in either direction.
3. **No-forgetting guard: FAILS by 0.03** — fedH 3.43 vs in-session keep100 3.61 (floor
   3.46), n=48/48 (first session discarded at n=12 coverage). NOT catastrophic (≫3.31).
   The −0.18 tax equals the book-tax every book arm has paid (run 3: −0.09..−0.19; laneF
   −0.14) — third book, same signature.

**Verdict (frozen grid, interference branch, softened by context):** the model still
absorbs a fresh book mechanically at the usual small rent; it is not "full." The headroom
question dissolves into the storage question (§9).

## 9. The probe study — recall vs manipulation (Test 2; 2026-07-24, ~$8)

**Design (frozen before any inference; PROBES.md).** 24 Clausewitz principles stratified
across the book's page range; per principle a **recall probe** (direct doctrine question —
answering = stating the principle; no scene surfaces; no principle 5-grams embedded) and a
**manipulation probe** (novel non-military two-path scenario solvable only via the
principle's mechanism; principle never stated; wrong path superficially attractive; hidden
grading key). Code gates: JSON schema, length bounds, 5-gram leakage check, scene-name ban
list, Path-1/Path-2 structure. The gates fired 3× during generation and forced redrafts;
all 24 pairs passed human readback. Grading: Sonnet 5, blind to arm labels, 0–2 rubric.
Frozen bars: storage = Δrecall ≥ +0.30 vs the no-book keep100 control; usability =
Δmanip ≥ +0.30. Negative control: fedH (never saw Clausewitz) must sit within ±0.20.

**Results (24/24 coverage every arm; full regrade replicated every read within ±0.1):**

| arm | Δrecall vs keep100 | Δmanip | read |
|---|---|---|---|
| base | −0.08..−0.17 | −0.21 | v5 SFT helps both slightly |
| book_C06 (raw book) | +0.04..+0.13 | −0.17..−0.13 | **no storage, no usability** |
| laneF (transformed) | +0.08..+0.17 | +0.04..+0.13 | **no storage, no usability** |
| fedH (negative ctrl) | −0.04..+0.08 | −0.04..0.00 | control behaves — instrument valid |

**Verdict: NOT STORED.** This is explicitly *not* the photograph failure mode the study
was designed to catch (recall-high/manip-flat): **recall itself never moves.** A model at
85% token accuracy on every page of the book cannot answer direct questions about the
book's content. Combined with §8: the failure is at the storage step, not arrangement,
not usability, not fullness.

## 10. Run 6 — The exposure sweep ("our number"; 2026-07-24, ~$14)

**Question (Nikhil's Test 3).** Every run inherited 5 epochs from papers. Find OUR number,
and check the curve shape (flat = saturated; rising = under-trained; peak-then-fall =
memorization burn).

**Design.** Data byte-identical to run-4's training file (masked/wrk_laneF.jsonl, 1143
rows, md5 eee09210…, verified on-pod). Five fixed-schedule arms — **fixed, not mastery,
by necessity: the mastery scheduler self-stops at ~655 steps once all pages are mastered,
which would silently collapse the 10× and 20× arms into the 5× point** (documented
pre-launch). Exposures {1.25, 2.5, 5, 10, 20} = steps {179, 358, 715, 1430, 2860}; all
other hyperparameters identical; every arm trains from base. (Nikhil's "100/300/600
repetitions" translated to LoRA scale — pretrain-style hundreds of exposures on 1,143 rows
would be pure memorization; 1.25–20 brackets the plausible zone with 4× headroom above
default.) Judge Session-S: 6 arms, one card, one session; first session discarded whole
(x1 at n=42 < 44) and fully rerun; the two sessions independently agreed on curve shape.

**Results (valid session, 48/48 all arms):**

| exposures/page | 1.25 | 2.5 | 5 (old default) | 10 | 20 | anchor |
|---|---|---|---|---|---|---|
| overall | **3.62** | 3.60 | 3.56 | 3.67 | 3.48 | 3.66 |
| foresight | 3.06 | 2.98 | 3.00 | 3.06 | 2.96 | 2.98 |

**Frozen reads:** (1) curve shape MIXED/AMBIGUOUS → flat-ish (spread 0.19, no rising
trend); (2) **OUR NUMBER = 1.25 exposures/page** (cheapest arm within 0.10 of best);
(3) **saturation half-condition MET** (x2, x4 within ±0.15 of x1) — the exposure lever is
formally exhausted at this scale; (4) no formal memorization burn (x4 misses the −0.20
bar) but x4 ranked last in both sessions — soft over-exposure signal; (5) no narrowing-tax
flags. **Exposure-probe extension (exploratory, frozen instrument):** Δrecall at
1.25×/5×/10×/20× = +0.04/−0.08/−0.17/+0.04 — **no storage at ANY exposure. Repetition
does not create retrievable knowledge.**

## 11. Program-level synthesis

**The unified mechanism.** Four data-side levers returned pre-registered nulls at 3.4B —
selection (run 1), schedule (runs 2–3), substance (run 4), exposure (run 6) — and the
probe study explains all four with one sentence: *LoRA continuation training on book text
at this scale writes no extractable knowledge, at any exposure, raw or transformed.* The
levers were all attempts to improve what gets stored; nothing gets stored. The model
perfects page-completion (telemetry) while acquiring nothing retrievable (probes), and
pays a small uniform bench tax for the privilege (−0.09..−0.19, three books).

**The mastery-vs-storage gap, made visible.** Token accuracy keeps improving until ~4.5
visits per page; benchmark quality saturates at ~1.25 visits; retrievable knowledge never
appears. Training-side progress metrics and knowledge acquisition are not merely loosely
coupled at this scale — they are measuring different processes. The mastery loop is
hereby **demoted with honor**: it is a genuine compute-efficiency device (self-stopping,
visit-concentrating; run 2: par at 70% compute) and NOT a learning-quality device (run 3
Signal D; run 6 sweep).

**What survives, strengthened.** The efficiency half of the density thesis, now
triple-replicated and extended: **par benchmark with ~36–40% of corpus tokens carrying
gradient (runs 1–3, two substrates) × ~1.25 epochs instead of 5 (run 6) ≈ par at roughly
one-tenth of the naive token×epoch budget.**

**What is dead.** Example-level NLL-band selection on judge-gated corpora; the exposure
lever below ~4B; naive "rearrange the data and it will absorb" headroom hopes;
single-angle semantic transformation as a quality lever; full-token held-out NLL as a
verdict instrument on masked/mastery arms.

**What remains open — the two unlock candidates.**
1. **Presentation diversity (run 4b).** Every corpus tested presents each principle
   exactly once. Allen-Zhu 3.1: facts become extractable only under many diverse
   paraphrases. Run 4b (3–4 scenes per principle, ~$25 all-in) is the last untested
   data-side lever, and the probe instrument gives it a direct storage verdict
   independent of the bench. Its motivation SHIFTED post-probes: diversity-for-storage,
   not diversity-for-usability.
2. **Capacity/modality (H-Small fork).** If 4b nulls on storage, the conclusion "LoRA
   continuation at 3.4B cannot write extractable knowledge" stands airtight, and the face
   factory moves to a ~9B-active-class base — with the efficiency recipe (whose transfer
   is already replicated across substrates) as the cost-containment layer.

**Implication for the Rubik's-cube architecture** (multi-adapter lane specialists + a
dispatcher on one small base): the gating milestone is unchanged and unmet — zero
validated faces (an adapter that beats the generalist on its own lane). The program
converted "faces mysteriously fail" into "faces fail because storage fails," with a named
$25 experiment that decides which base the cube lives on. Secondary blocker on the cube's
critical path: peft 0.19.1 multi-adapter hot-switching garbles granite-4.0-micro
(documented in dav_eval_v5.py; current workaround = separate model instance per seat).

## 12. Instruments: validated, invalidated, and lessons

**Validated:**
- The 6-dimension, 48-problem single-session judge protocol with coverage guard (≥44/48,
  discard-and-rerun) — caught two invalid sessions this program would otherwise have read.
- The probe instrument (24 recall/manip pairs, leakage gates, blind grading, negative
  control) — control behaved; full regrade replicated all reads.
- Card-class control with in-session anchor regeneration.
- Mastery telemetry (visits/page, steps-to-mastery) as a free training-side diagnostic.

**Invalidated:**
- Full-token held-out NLL on masked/mastery-trained adapters (run 2 demotion → run 5
  terminal: the control arm shows identical inflation; bias +≈2 nats).
- Exact n-gram counters as sole diversity QC (45% phrase-family collapse hid behind 9%
  exact-match; loose family matching required).

**Ops lessons (costed):**
- transformers 5.14.1 breaks granite-4.0-micro `generate()` (linear-attention cache
  assertion); training and forward-NLL unaffected. Pin `transformers<5` on pods.
- peft treats an adapter path without safetensors as a HF repo id → 401 (the run-5b race:
  gens launched while adapters were mid-upload).
- rsync `-z` corrupts on resume of partial large files ("deflate on token"); transfer
  .tgz uncompressed with `--partial`.
- RTX PRO 6000 Blackwell ≈ 70 LoRA steps/min solo on this recipe (~15× an Ada-calibrated
  estimate); two concurrent trains fit in 96GB.
- Judge budget: Sonnet 5 thinking requires max_tokens 12,000; expect occasional
  full-session reruns for coverage — budget 2× per session.

## 13. Threats to validity (to address before formalizing)

1. **LLM-as-judge** throughout; single judge family; no human evaluation. Mitigations in
   place: blind grading, single-session comparisons, pre-registered thresholds above the
   measured noise floor, replication of key reads. Not mitigated: rubric-model
   co-adaptation risk.
2. **n=48 bench, n=24 probes** — powered for ~0.15–0.30 effects only; sub-noise effects
   are undetectable by design.
3. **One base model, one scale** (3.4B granite MoE-hybrid); one adapter method (LoRA
   r64). "At this scale/modality" qualifiers are load-bearing; nothing here licenses
   claims about full fine-tuning or larger bases.
4. **Substrate breadth:** two books (strategy/political theory) + one curated
   conversation corpus; bench is modern-decision flavored (substrate-bench transfer was
   itself a measured null in run 3).
5. **The 1.25-exposure result** is one sweep on one (transformed) substrate; before
   adopting program-wide, replicate on a raw substrate.
6. Run-2's mastery-par headline carries the run-3 anchor-regen asterisk (card drift vs
   session luck; third regen pending).

## 14. Cost ledger (actuals)

| run | what | cost |
|---|---|---|
| 1 | selection gate | ~$5 |
| 2 | occlusion + mastery | ~$19 |
| 3 | book dual-fraction | ~$16 |
| 4 | transformation gate (incl. $11 renders, 1 discarded gen) | ~$17 |
| 5+6+probes | headroom + sweep + probe study (2 pods, 4 judge sessions, 3 grading passes) | ~$47 |
| **program total** | 6 runs, 4 pre-registered nulls, 1 replicated positive, 1 mechanism | **~$104–110** |

## 15. Next experiments (pre-registered intentions)

1. **Run 4b — multi-angle render:** 3–4 scenes per principle, injection-based diversity
   (names, companies, weekdays, domains), same K2.6/Flash/Sonnet three-family pipeline,
   keep-0.6 + mastery at matched steps. **Primary read is the PROBE verdict** (storage bar
   Δrecall ≥ +0.30), bench secondary. ~$25 all-in. Decides 3.4B-vs-H-Small for the cube.
2. **Exposure-sweep replication on raw substrate** (Clausewitz pages, x025 vs x1) before
   adopting 1.25 program-wide. ~$4.
3. **Third mastery60 regen** to settle the run-3 anchor wrinkle. ~$3.
4. **Test 4 (ingredient ablation):** still correctly deferred — only meaningful on a
   recipe with signal.

---

## Appendix A — Artifact registry

| bundle | contents | md5 |
|---|---|---|
| density_run1/ (1.6G) | dense60/rand60 adapters, run-1 outputs | verified at archive time |
| density_run2/density_run2_adapters.tgz (4.1G) | keep-sweep + mastery60 + dec/wrk_keep1.0 | verified |
| density_run3/run3_bundle.tgz (2.0G) | 5 book arms incl. wrk_bookC06 | verified |
| density_run4/run4_bundle.tgz (420M) | wrk_laneF, masked data, logs | 5d2a7ff9… |
| density_run5/run5_bundle.tgz (419M) | wrk_fedH, fed data, NLL logs, probe answers | 3b6a78f1… |
| density_run6/run6_bundle.tgz (2.0G) | 5 sweep adapters, threads, probe answers | 68fc2c22… |

Data fingerprints: run-4/6 training file eee09210…; run-5 fed pages 905e8b9b…; probe set
201d7174… (24 pairs, frozen). Git: density-method 237ef4a → 5475fa4 (29+ commits).
Corpora source: lora-corpus-source (private, read-only). Benchmark + v5 baselines:
divergence-formula (read-only).

## Appendix B — Frozen-criteria scoreboard

| run | headline signal | frozen bar | outcome |
|---|---|---|---|
| 1 | A: efficiency | ±0.15 of v5full | **HOLDS** (Δ0.03) |
| 1 | B: selection | ≥ rand60+0.20 | FAILS (−0.05) |
| 2 | C: occlusion | ±0.15 of control at ≤0.5 keep | **HOLDS ×2** (0.00–0.04) |
| 3 | D: mastery>reading | ≥ +0.20 | FAILS (−0.10) |
| 3 | book value | > in-session anchor | NONE |
| 4 | E: foresight lane | ≥ anchor+0.25 ∧ ≥3.25 | FAILS (2.85 vs 3.27) |
| 4 | transformation vs raw | ≥ +0.20 | within noise (−0.13) |
| 5 | 1a telemetry | all pages mastered in budget | **HOLDS** (886/886) |
| 5 | 1b NLL | ≤ base−0.15 | instrument invalidated by control |
| 5 | no-forgetting | ≥ anchor−0.15 | fails by 0.03 (book-tax −0.18) |
| probes | storage | Δrecall ≥ +0.30 | **NOT STORED** (max +0.17, all arms) |
| probes | usability | Δmanip ≥ +0.30 | not usable (max +0.13) |
| 6 | our number | cheapest within 0.10 of best | **1.25 exposures** |
| 6 | saturation half | x2,x4 within ±0.15 of x1 | **MET** |
| 6 | memorization burn | x4 < x1−0.20 | not formal (soft signal) |
