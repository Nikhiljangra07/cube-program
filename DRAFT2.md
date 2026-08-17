# The Cube Program: Composed LoRA Specialists, the Fidelity Wall, and the Weights/Harness Symmetry
## (A Pre-Registered Fifteen-Run Study at 4B — runs 7–21)

> **STATUS: UNOFFICIAL WORKING DRAFT — 2026-08-15** (first issued 2026-08-12 for
> runs 7–16; §§15–17 added and §§18–21 added 2026-08-15). Complete factual
> record of the cube program, runs 7–21, companion volume to DRAFT.md (runs
> 1–6 + probe study, the density/storage era). All numbers below are traceable
> to frozen runbooks (RUNBOOK7.md–RUNBOOK21.md), git history, and md5-pinned
> artifacts (Appendix A). Every success criterion was frozen before its run;
> the labeled post-hoc events in program history — one gate amendment (§13),
> one criterion reanalysis that overturns no frozen verdict (§17), and one
> prospective ruler variant (STRICT-D, §21) — are labeled where they occur.
> Author: Nikhil Jangra. Drafting assistant: Claude (Anthropic).

---

## Abstract

We report a fifteen-run, pre-registered empirical study of a composed-specialist
architecture ("the cube") on a 4B-parameter base model: cheap LoRA lane-specialists +
a generalist + a deterministic dispatcher + a segment relay, evaluated head-to-head
against the same base model running naked. Across ~$120 of compute the program (1)
falsified carved and deep-chain specialist recipes and validated one aligned-gate
foresight specialist (+1.06 on its facet bench, the program's first face-bar pass);
(2) discovered two **harness laws** — directional re-derivation under a changed world
("the motion loop") is an engineering property of anchored prompting, not a trainable
skill (93–100% direction accuracy for *every* arm, including the untrained
generalist), and multi-segment fusion fidelity is a **coach function**, not a model
skill (template-slot assembly: 87.5% judge-clean vs 21% for free-prose fusion on the
same segments); (3) measured a **fidelity wall** from three independent directions —
training (specialist SFT, delta-format SFT, and self-distillation of the model's own
certified successes all fail to buy fidelity), harness repair (judge-in-loop feedback
plateaus at 19/24), and verification gating (a trained 4B verifier reaches 0.99 flaw
*detection* recall but only 0.25 clean *certification* recall, sliding monotonically
toward all-flag across three corpus designs); (4) lost the pre-registered match:
the composed cube with current specialists takes 2 of 6 legs against the naked
generalist, with the ablation showing the provisional viability specialist is a net
negative in its own seat; and (5) closed the wall's etiology in three final
experiments — a capacity ladder falsifying the state-load hypothesis (0/8
strict-clean at every load from 2 to 10 facts; invention is a gap-filling
*assertion policy*, anti-correlated with supplied information), a grounding-
discipline prompt that 4B models demonstrably cannot execute (marked their
specifics in 4–13 of 40 answers despite explicit instruction), and a weight-class
match in which the reasoning-trained sibling of the program base
(Qwen3-4B-Thinking-2507) *also* scores 0/40 strict-clean — the strict island is
empty for the entire weight class, and the harness was never the bottleneck.
A final $0 severity-stratified reanalysis (RULER-T: fatal flaws — contradiction,
distortion, constraint violation — separated from tolerable advisory decoration)
opens the island to 20–38%, gives the match an honest winner (the reasoning
sibling at 2× baseline), and confirms the trained verifier false-flags 96% of
realistically-clean answers. The unifying mechanism: under a strict grounding
criterion, only ~0–5% of 4B generations are fully clean, so specialist edges
(real but ≤ +0.12) drown beneath a shared invention noise floor that neither
training, repair, prompting, nor gating can lift at this scale. Reasoning
structure trains; faithfulness does not — faithfulness must be *constructed* in
the harness, and at 4B the constructible surface stops at the assembly layer.

The final act (runs 18–21) turns the diagnosis into an architecture. A
retrained fatal-flaw gate fails twice (certification is capacity-bound at 4B
even at the matched wavelength), but the **demand ladder** delivers the
program's steepest curve — hold the problem constant and shrink only the
*question*, and strict-clean rises monotonically from 0% (full plan) to 88%
strict / 100% realistic (atomic extraction-and-derivation): **invention
pressure = demanded specificity − supplied specificity**, and demand is the
lever. **Staging** (code-verified atomic answers injected as anchors into the
composite questions) then perfects the judgment level (8/8) and kills the
constraint-conflation disease (6 flaws → 1). The rematch assembles the full
chain — decompose → answer atomically → anchor upward → coach-assemble — and
the **cube-v2 beats the naked generalist 6–0 on certified-clean full answers**
(same weights, fresh problems, dual rulers; the generalist scores zero, as it
has in every run of the program). The absolute bar (10/16) is not yet met:
iterating the guards (21B, 21C) widens the win to **8–0 (50% vs 0%)** and
then asymptotes: each closed surface relocates the contradiction one level
deeper, ending at a precisely named residue — modal inconsistency, the true
4B reasoning limit. The strict wall is a weight-class property; beneath it,
a demand-matched harness turns the same weights from 0% to 50%
certified-clean — an existence proof that the architecture, not the model,
was the missing ingredient — and the remaining half is a judgment deficit
sized for the asymmetric-cube fork.

---

## 1. Motivation and thesis

Part I (DRAFT.md) ended with the storage null: LoRA continuation training at small
scale writes no retrievable knowledge, so knowledge-faces are dead and behavior-faces
are the only viable specialization currency. The **Rubik's-cube thesis** under test
here: several cheap behavioral LoRA specialists (foresight, viability), a generalist,
and a dispatcher, *composed* at inference time on one small base, can beat that same
base running naked — buying frontier-adjacent strategic reasoning at a fraction of
the training compute. The program's standing domain law (Nikhil, 2026-08-08):
strategic-reasoning problems only, until the first category is decisively acquired.

The end-state architecture (Nikhil's dispatcher doc, 2026-07-31): runner → coach →
runner topology; pre-assignment segment-level dispatch; a rigid rule-based governor
before any trained router; fusion at the coach. Runs 7–16 build and test this
end-to-end: specialists (7–10), the motion loop (11), the assembled prototype (12),
the fusion instrument and wall (13–13B), fusion training (14), the coach and the
match (15), and the verification gate (16).

## 2. Common methodology

- **Base:** runs 7–8 ibm-granite/granite-4.0-micro (3.4B); runs 9–21
  **Qwen/Qwen3-4B-Instruct-2507** after a controlled base-swap test (§5). Fixed
  recipe throughout (part-I efficiency result): r64 LoRA, keep-0.6 band masking,
  1.25 epochs, greedy decoding at eval.
- **Benches (all frozen, md5-pinned):** the 48-problem v5 general bench (6-dim
  set-level judge); the 24-problem dossier bench (evidence-fed foresight, 5-dim B
  rubric); the 32-problem inventory bench (audit-grounded planning, 6-dim C rubric
  with hard caps); 16 boost + 16 nerf twin updates (Eval D2, code-scored); the 24
  staged fusion problems (seed 13, unique surnames/codenames, deterministic rebuild,
  md5 b4c23eb3).
- **Judge discipline (inherited, hardened):** judge = Claude Sonnet 5, single
  session per comparison, no temperature parameter, max_tokens 12,000,
  retry-on-empty, all-or-discard coverage, verdicts cached keyed by content md5 —
  reruns re-bill nothing. The judge never writes training data (certification only).
  No Anthropic models as contestants; no DeepSeek contestants (authored bench
  problems).
- **Pre-registration:** every bar frozen in its RUNBOOK before spend. One labeled
  post-hoc gate amendment (§13), one labeled post-hoc reanalysis (§17), and
  one labeled prospective ruler variant (STRICT-D, §21) in fifteen runs. Frozen stop clauses are executed as written, including against the
  program's own hopes (§10, §14).
- **Ops pattern (matured over the arc):** local driver orchestrates; pods generate;
  API keys never touch a pod; long jobs run detached (`setsid nohup`) and
  laptop-free; resumable state + append-only JSONL; spend caps abort before billing.

## 3. Run 7 — Carved faces and the oracle mirage (2026-07-25)

**Question:** can specialists carved from the existing scored pool (top-quartile on
one lane, ≤ median on others) beat the generalist on their own lanes, and does oracle
routing clear the generalist?

**Results (Sessions F + F2, 48/48 both):** all three carved faces FAIL their lane
bars (foresight +0.16/+0.06 vs +0.20 needed; distinctness ~par; viability
+0.09/+0.04). Oracle(4) read +0.42/+0.40 — annotated as a construction artifact
(max of noisy arms); honest cross-session win-stability 41.7% vs 26.8% chance, hard
stable core **7/48 problems**. **Dispatcher deliberately NOT built** on a 7-problem
core. Riders: every cube member ≥ anchor overall on 17–32% of its row-mass
(efficiency replicates); peft hot-swap byte-clean, median 6.3 ms.

**Verdict:** carving is null — genuine specialization requires *generated* lane
corpora.

## 4. Run 8 — The deep-chain foresight face (granite; 2026-07-26)

Generated corpus (DeepSeek, 880 threads, opponent-move taxonomy, 3–4-step
consequence chains). **FAIL:** foresight 2.69 vs anchor 2.92 (−0.23; bar +0.20).
Diagnosis, paper-grade lesson #1: **the corpus admission gate must be the verdict
instrument verbatim** — the gate scored "chains 3–4 deep," the bench scores "a move
or two ahead WITHOUT over-reach"; the pipeline optimized a proxy and the bench
punished it.

## 5. Run 9 — The base-swap control (2026-07-26)

Byte-identical deep-chain diet on Qwen3-4B-Instruct-2507. The stronger base was
dragged FURTHER below its own anchor (−0.33 vs granite's −0.23) → **the diet, not
capacity, was binding**; the deep-chain corpus is bench-toxic on any base. The
positive read: Qwen anchor 3.73/3.12 vs granite 3.57/2.92 on identical data/recipe —
**Qwen qualifies as the program base** from here on.

## 6. Run 9b — The aligned-gate foresight face: first pass (2026-07-26)

Corpus regenerated with the gate = bench-judge rubric verbatim, plus a dossier bench
(24 problems with observed-counterparty evidence) to measure the facet directly.

**Results:** Eval A (general bench): foresight +0.12 (FAIL by 0.08, but a +0.45
swing from run 8 — the definition fix quantified); overall 3.75 vs 3.74 — the face
beats the anchor overall, a program first. **Eval B (dossier bench): PASS, +1.06**
(3.08 vs 2.02; every dimension up; falsifiability +2.50). **wrk_faceF_9b is the
program's first certified specialist.**

## 7. Run 10 — The viability face fails all legs (2026-07-29)

Same aligned-gate method, viability lane, inventory bench with hard-cap rubric.
**FAIL all three legs:** Eval A viability +0.09 with the overall floor broken
(−0.25; the audit-first voice costs decisiveness −0.61); Eval C core 2.52 vs 2.57 —
loses even on its own facet bench; calibration probe parseable 6/16, direction 3/6.
Hard caps crushed BOTH arms (resource_grounding ≈ 2.0 each): **at 4B every thread
set contains at least one invention, so grounding caps bind universally and erase
differentiation** — the first sighting of the wall.

**The controlled contrast (9b vs 10), the program's central discovery in weight
space:** same base, same recipe, same method, opposite outcomes. **Structural habits
transfer by SFT (anticipate → position → falsify: +1.06); fidelity constraints do
not (don't invent, stay in seat, keep numbers coherent: all legs failed).**
wrk_faceV_10 is retained *provisionally* for relay work only.

## 8. Run 11 — The delta diet and the motion-loop discovery (2026-07-30)

**Question:** can training buy directional re-derivation under updates (boosts and
nerfs)?

**Results (Eval D2, 32 bidirectional twins, code-scored):** the delta-trained
adapter FAILS its grid (ack 17/32) and the delta-vs-static read is −7 (needed +25) —
**the delta diet bought nothing**. The run's real finding: with an ANCHORED prior
(old estimate visible) + the revise instruction, **every arm — including the
untrained generalist — re-derives direction-correctly (keep100 nerf: 12% → 100%
between v1 and v2)**. The "sycophancy" of earlier probes was a missing-anchor
artifact.

**HARNESS LAW #1: the motion loop (notice the update → re-derive the estimate) is an
engineering property of the harness — track variables, present the update, show the
prior, ask — not a capability requiring training at 4B.** 93–100% direction accuracy
is available today with existing adapters.

## 9. Run 12 — The first cube prototype (2026-07-31)

Full relay on one card: dispatcher v1 (two deterministic tiers) + hot-swapped seats
(audit V → read F → plan V → motion V → fusion G).

**Stage 0 (router, marker-stripped): PASS 94/104 (bar 90%).** V's fingerprint =
enumerated money; F's = dated observed behavior; G = no timeline.
**Stage 1 (baton pass): mechanics PASS** — swap median 11.8 ms, hot-swap outputs
byte-identical to fresh loads, tagged estimates throughout. **Semantics FAIL the
frozen seam gate, three iterations:** (1) fusion upgraded the read's hypotheticals
into facts; (2) fact-discipline prompts cured the upgrade disease, new inventions
appeared; (3) rigid-coach assembly (motion + estimate carried by code, only a
digit-free bridge generated) — the flaws moved into the remaining free prose.

**The measured law:** at 4B, every FREE-PROSE step that must faithfully integrate
multiple prior texts commits ~1 fidelity error per ~3 attempts, regardless of prompt
engineering. Narrowing the free surface relocates the errors; it does not reduce the
rate. Stage 2 (the match) was NOT run — the frozen gate held, $8 unspent.

## 10. Runs 13 / 13B — Instrumenting the wall (2026-08-06/08)

**Run 13 (staged problems + code checker):** the checker's precision was perfect
(every flag confirmed) but recall failed the frozen instrument bar (agreement 60%,
miss 8/10) → **no arm claims**. The misses defined the semantic sin taxonomy —
concept revival by paraphrase, self-contradiction, prediction leakage at concept
level — the exact class regex cannot reach. Code demoted to advisory, permanently.

**Run 13B (hybrid instrument → judge-everything):** the code+spot-audit hybrid
failed its own audit (4/6) and the pre-planned fallback executed — full judge
coverage. **The wall, officially measured on the staged 24:** free-prose fusion
judge-clean = **6/24 (25%) at 4B** (95% CI 12–45%); a 14B spokesman on identical
segments = **13/24 (54%)** — capacity moves the wall but does not remove it.
**Judge-in-loop repair (D′): 19/24 after two feedback rounds — fails its bar by
one**; 5 problems never converge. Delivery scores 4.4–4.8 across ALL arms —
**fluency and fidelity are orthogonal**; the wall is invisible to any
delivery-flavored metric.

## 11. Run 14 — Self-distillation of the model's own successes (2026-08-09)

The strongest remaining training hypothesis: harvest the loop's own judge-certified
clean fusions (126/160 problems passed on disjoint problems, seed 14), train the
fusion seat on its own successes, eval on the frozen 24.

**Result: NULL.** F14 12/24 (50%) vs same-day baseline 10/24 (42%) — +2 problems,
inside noise. Format retention 24/24 (the style trained; the discipline did not).

**THE THREE-RUN LAW (10, 11, 14): fidelity is not buyable by SFT at 4B — not from a
frontier teacher (10), not from delta-format data (11), not from self-distillation
of the model's own certified successes (14).**

## 12. Run 15, stages 0–1 — The coach (2026-08-10)

If fidelity cannot enter the weights, construct it. **Template-slot assembly:**
final speech = [fixed digit-free update-settlement sentence quoting the dead option]
+ [motion body verbatim minus estimate] + [fixed contingency bridge] + [estimate
line carried by code]. Invented numbers, revived options, and predictions-as-fact
are *unrepresentable in the added text by construction*; residual risk lives only
inside the motion segment (screened by the advisory checker, ≤2 retries, judge-free).

**Stage 0 ($0):** zero flags added across all 184 stored run-14 relays.
**Stage 1 (fresh segments, frozen 24, judge-everything):**

| arm | judge-clean | delivery |
|---|---|---|
| COACH (assembled) | **21/24 (87.5%)** | 4.83 |
| BASELINE (free fusion, same segments) | 5/24 (21%) | 4.04 |

Both frozen bars cleared decisively; delivery IMPROVED under templating.
**HARNESS LAW #2: fusion fidelity is a coach function, not a model skill.** The
21–42% free-prose wall is bypassed by construction at 87.5%. Together with §8:
**reasoning lives in the weights; faithfulness lives in the harness.**

## 13. Run 15, stage 2 — THE MATCH (2026-08-10/11)

**⚠ THE PROGRAM'S ONLY POST-HOC GATE AMENDMENT (labeled, authorized by Nikhil
2026-08-10):** run 12's seam gate demanded PERFECT fusion transcripts; runs 13/13B/14
then measured that no arm — including the naked generalist — meets that standard.
The gate was measuring the wall, not the thesis. Fidelity became a RELATIVE leg
(cube ≥ generalist, judged same-run). Every other bar was frozen pre-data as always.

**Design:** CUBE (full pipeline + coach) vs GENERALIST (same weights, naked; the
single-pass prompt carries the same information and asks) vs ABLATE (keep100 in the
V seat). Four legs + folded fidelity + attribution; single-answer B/C rubrics
adapted set→single with coherence folded into the same judge read; ~240 reads,
spend-capped; the entire generation ran as one detached overnight pod job,
laptop-free, zero incidents.

**Results (scoreboard, 2/6 legs):**

| leg | bar | result | verdict |
|---|---|---|---|
| dossier (24, B-single) | cube ≥ gen + 0.20 | 2.67 vs 2.59 (+0.08) | LOST |
| inventory (32, C-single) | cube ≥ gen + 0.20 ∧ rg ≥ gen | 2.51 vs 2.73 (−0.22); rg 2.00 vs 2.09 | LOST |
| motion (32 twins, code) | parse≥30, boost≥75%, nerf≥75%, ack≥24 | 29/32 · 93.3% · 100% · 22/32 | LOST (by 1 & 2; directions excellent) |
| general (48, set-level) | cube ≥ gen − 0.15 | 3.70 vs 3.71 | **HELD** |
| fidelity (amended) | cube coherent-rate ≥ gen | 0.054 vs 0.054 | **WON (tie)** |
| attribution | cube − ablate ≥ +0.10 on core-C | **−0.10** | **FAILED — V seat swaps to keep100** |

**Readings:** (1) the ablation is the sharpest instrument in the match — plain
keep100 in the V seat BEAT faceV_10; the provisional specialist is a net negative in
its own chair, consistent with its run-10 bars. (2) Both arms hallucinate at the
identical rate and both are crushed to ~2.5–2.7 by the strict rubric: **specialist
edges (faceF's +0.08 is real) drown beneath a shared invention noise floor.** (3)
The general leg confirms routing costs nothing on neutral ground. (4) Absolute
single-answer B/C scores are not comparable to part-set-level history; all
comparisons are same-run relative, by design. Reference-ladder transcripts
(Qwen3-4B-Thinking-2507, Qwen3.5-9B, gpt-oss-20b, same single-answer prompt) were
generated overnight and are archived unjudged (a ~$3.5 decision deferred).

**Honest verdict: the composed cube with current specialists does NOT beat the
naked generalist on specialist single-answer legs at 4B.** What survived: the
machine (mechanics, routing, motion direction handling, the coach), and faceF's
under-bar edge. What failed: faceV (seat executed per the frozen spec), and the
+0.20 bars against the noise floor.

## 14. Run 16 — The grounding verifier (2026-08-11/12)

The match localized the binding constraint at fidelity, and industry precedent
(MiniCheck-class verifiers) says verification — unlike generation — trains small.
**Question: does it?**

**Stage 0 ($0):** mined every Sonnet-labeled (answer → coherent/flaws) pair the
program had already paid for — runs 13B (77/77), 14 (379/379), 15-smoke (48/48),
match (144/144), every join md5-verified, zero unjoined → **621 unique real pairs**;
+ seeded synthetic corruptions (invented number/actor, prediction-as-fact,
dead-option revival, self-contradiction), each verified absent from the problem
text before emission. Problem-level splits; synthetic never enters eval.

**Three variants, frozen bars recall_flawed ≥ 0.75 ∧ recall_clean ≥ 0.70:**

| variant | change | recall_flawed | recall_clean |
|---|---|---|---|
| v1 | as mined | 0.907 | 0.382 |
| 16B | single-ruler relabel of all 208 clean labels ($1.9): **135/208 flip to FLAGGED** — 65% of historical "clean" certifications were lenient-ruler artifacts; labeled split amendment for a measurable clean-eval (20 rows) | 0.967 | 0.40 |
| 16C | legal-mention counter-class (208 GROUNDED rows carrying the same dead tokens/counterparties as the corruptions, legal phrasing; classes balanced 522:585) | 0.992 | 0.25 |

**The frozen stop clause fired. RECORDED VERDICT: detection trains small at 4B
(0.99 flaw recall from ~500 mined labels, vs 0.20 for the best rule-based checker);
CERTIFICATION does not — the model slides monotonically toward all-flag.**

**The three-sided wall, closed:** under the strict criterion only ~5% of 4B
generations are clean at all (match: 5.4% both arms; relabel: 35% of even
lenient-certified texts survive). "Clean" is a tiny island in the output
distribution, so (a) a student verifier sees almost no natural positives, and (b)
even a perfect gate with ≤2 regenerations rarely lands a clean draw (the 13B repair
ceiling of 19/24 was measured under the LENIENT ruler and does not transfer).
Training (§11), repair (§10), and gating (§14) all fail against the same object:
**the invention disease at 4B is a generation-capacity property, not a gateable
one, at this strictness.**

## 15. Run 17 — The capacity ladder (2026-08-13)

**Question (Nikhil's hypothesis):** is the wall a STATE-LOAD property? If invention
is what happens when the facts to track exceed working capacity, clean-rate should
climb steeply as problems shrink, and an operating envelope should exist inside
which the 4B is honest.

**Design (frozen pre-spend, ~$1.4):** 40 deterministic problems (seed 17,
md5 95a293bba2d2583d10edb0f45fed1605), five state-load levels × 8 problems with
NESTED fact types (L1 = 2 facts … L5 = 10 facts; load is the only variable;
archetype mix, prompt, and greedy decoding constant), keep100 single-pass, gold =
STRICT_ONE byte-reused (the same criterion as the match and run 16). Entity pools
fresh and disjoint from every pool the verifier ever saw in a training label.
ver_16 rendered verdicts on all 40 as a $0 rider.

**Result: FLAT ZERO — 0/8 strict-clean at EVERY level. No envelope exists; the
load hypothesis is falsified.** Sanity guard: L3 (match-like load) 0.0 vs the
match's 0.054 — the ladder reproduces the match floor, no style confound.

**The flaw autopsy is the run's real finding.** Classifying all 176 flaws as
ADDITIONS (specifics absent from the problem) vs DISTORTIONS (given facts
mis-stated): L1 = 59 additions / 0 distortions (and the MOST flaws of any level);
L3 = 18/8; L5 = 30/2. Three decisive readings: (1) **tracking is not the
disease** — distortions are rare at every load; the model keeps what it is given.
(2) **Invention is gap-filling, anti-correlated with supplied information at the
sparse end** — the 2-fact problems produced 2.3× the inventions of the 6-fact
problems, and stock decorations ("$45,000", "14-day window", "48-hour window")
recur across unrelated problems: a generation *policy*, not a memory failure.
(3) **The reframe: invention pressure = demanded specificity − supplied
specificity.** The prompt demands a concrete plan; concreteness requires
specifics no problem supplies; the model asserts them as facts rather than
proposing them as choices. Under the strict ruler, a fully-grounded concrete
plan is therefore structurally near-impossible at ANY capacity — the wall is a
task-demand × criterion interaction plus an assertion policy, not working
memory. Verifier rider: 40/40 recall on flawed; FP unmeasurable (zero clean
gold existed).

## 16. The stagnant-judge audit and run 17B — marking, and the weight-class match (2026-08-15)

**The $0 audit (Nikhil's moving-data thesis).** Hypothesis: the pipeline now
*derives* (the motion loop), so a static grounding criterion might be
false-flagging legitimately derived values — "the layer is stagnant, but our
questions are moving." All 176 cached run-17 flaws were read against their
problems' planted tokens. Two-level verdict: **the gold judge is NOT stagnant** —
it performed date arithmetic itself (flagging a claimed "10-day buffer between
July 8 and July 23" as actually 15 days) and 0/176 flaws were correct
derivations mis-flagged. The model's rare derivation attempts were themselves
wrong (unit errors, arithmetic errors) or built on invented premises. The
verifier level of the thesis stayed open — unmeasurable without clean answers
(resolved in §17).

**Run 17B (frozen pre-spend, ~$3.3 = pod ~$1.5 RTX Pro 6000 Blackwell + judge
~$1.8):** three arms on the run-17 ladder, same STRICT_ONE gold, full
observability (every flaw dumped beside its problem's planted tokens).
- **B — baseline:** run 17's cached answers and verdicts ($0).
- **M — keep100 + GROUND:** a grounding discipline appended to the prompt —
  every specific must be (a) QUOTED from the problem, (b) DERIVED with its basis
  shown inline, or (c) PROPOSED and explicitly marked as a chosen parameter.
  The direct test of the §15 assertion-policy reframe.
- **R — Qwen3-4B-Thinking-2507 + GROUND:** the reasoning-trained sibling of the
  program base, same system + user prompt, vendor-recommended decoding (its
  model card warns greedy decoding loops), per-item seeds. Identical base
  lineage isolates "reasoning training" vs "our harness" at fixed capacity.

Ops event (labeled amendment, run-15 refs-fix precedent): 24/40 rival answers
hit max_new 4096 mid-thinking and never emitted `</think>` — raw deliberation
stored as the answer. run17b_fix.py regenerated exactly those rows at 9k/13k
budgets (same seed law): zero residual leaks; verifier verdicts re-rendered.
The judged match is fair.

**Strict scoreboard: 0/40 clean in ALL THREE ARMS** (total flaws: B 176, M 170,
R 124 — the rival ~30% fewer, monotone across levels, at ~25× the tokens per
answer). The marking bar (≥ 4/40) FAILED, and the compliance analysis names the
mechanism precisely: **the models did not execute the discipline** — M marked
proposals in 4/40 answers and showed a derivation basis in 2/40; R managed
13/40 and 5/40, and even dressed inventions as derivations ("15-day window
(August 10–25)" with no August 10 anywhere in the problem). The assertion-policy
wall is real but **not prompt-fixable at 4B**: the discipline does not fit the
weight class. And the match settles the exoneration question: **the strict
island is empty for the entire 4B weight class, reasoning training included —
the harness was never the bottleneck.** Verifier: 79/80 new answers flagged
(99% recall on flawed); FP still undefined under the strict ruler — strict-clean
4B answers may simply not exist to be falsely flagged.

## 17. The RULER-T reanalysis — matching the criterion to the weight class (2026-08-15, $0)

**⚠ THE PROGRAM'S SECOND LABELED POST-HOC EVENT (Nikhil's directive, 2026-08-15).
A stratified REANALYSIS of cached verdicts — the strict results above stand
unchanged and remain the comparability spine.** Rationale: the strict ruler
kills answers for behavior every competent human advisor performs (proposing an
opening number, naming a check-in date). The guardrail: stratify severity, never
lower the bar until the model passes.

**Method:** all 470 cached judge flaws across the three arms classified from the
judge's own prose — **T1 FATAL** (96: self-contradiction, given-fact distortion,
stated-constraint violation, temporal error, miscalculation, misattribution),
**PRED** (35: a likely reaction asserted as settled fact), **ADD, tolerated**
(325: invented-but-consistent specifics — the decoration class), and 14
unclassifiable flaws conservatively treated as fatal. Regex classifier plus
spot-read verification; no new judge spend.

| arm | strict | RULER-T (no fatal, no PRED) | T-loose (PRED tolerated) |
|---|---|---|---|
| B baseline | 0/40 | 8/40 (20%) | 14/40 (35%) |
| M ours + GROUND | 0/40 | 5/40 (13%) | 8/40 (20%) |
| R Thinking + GROUND | 0/40 | **15/40 (38%)** | 19/40 (48%) |

**Four findings.** (1) **The island opens at the matched wavelength**:
realistically-clean 4B strategic answers exist at 20–38%; what remains below
them is a real *fatal-flaw* rate, now cleanly separated from decoration.
(2) **The match has an honest winner — the reasoning sibling, at 2× baseline.**
Reasoning training buys realistic cleanliness, not merely fewer flaws
(spot-check: its clean answers budget within given numbers and predict
conditionally with falsifiable signals). (3) **GROUND actively hurt** (5/40 vs
the baseline's 8/40): in-prompt fidelity discipline adds instruction load
without compliance and is dead at 4B. (4) **The stagnant-verifier thesis is
CONFIRMED at the layer it was aimed at: ver_16 false-flags 96% of RULER-T-clean
answers (27/28; 98% on T-loose)** — the trained layer is tuned to the strict
wavelength (near-all-flag) and is useless as a gate for realistic quality. This
is the program's first measured verifier FP rate.

**The arithmetic consequence, recorded as run-18's candidate design:** a
fatal-flaw-only detector (detection DID train small — run 16's 0.99 recall)
retrained on RULER-T labels (derivable from existing caches at $0), sitting
over a 20–38% base clean-rate, makes gated regeneration viable for the first
time: ~3–5 expected attempts to a certified-clean answer.

## 18. Run 18 — The fatal-flaw gate (2026-08-15)

**Question:** does verification train small when the target matches the
weight class's wavelength? Corpus mined for $0 from existing judge caches
under frozen trust rules (strict-complete reads give both classes; lenient
reads may only convict, never certify — 192 rows excluded): 549 labels, 151
genuine SOUND training positives (the class run 16 starved on).

**Result: FAIL both frozen legs — recall_fatal 0.733 (bar 0.75, missed by
two answers), fp_on_sound 0.542 (bar 0.30).** The matched wavelength halved
false-flags (96% → 54%) and produced the program's first genuine
certifications (11 sound answers) — the all-flag attractor is broken — but
**verification-as-certification is now twice-failed at 4B (strict and
matched), and forcing discrimination exposed run 16's 0.99 "detection" as
partly trivial (0.73 when it must separate rather than flag everything).**
Certification is capacity-bound; gated regeneration stays blocked at 4B.

## 19. Run 19 — The demand ladder (2026-08-15)

**Nikhil's hypothesis:** the questions are too big for the model — PhD exams
handed to a graduation-level mind. Run 17 varied SUPPLY with demand fixed
(flat zero, sparse problems *worse*); run 19 flips the axis: the 8 six-fact
L3 problems byte-reused, **demand varied** across five levels — D1 atomic
extraction + derivation-with-basis, D2 single judgment, D3 bounded choice,
D4 plan-lite with a [TBD] escape hatch, D5 the full plan (the cached run-17
arm, 0/8).

**THE DEMAND CURVE (strict / RULER-T, n=8/level): D1 7/8 · 8/8 — D2 5/8 —
D3 3/8 — D4 0/8 — D5 0/8 · 1/8.** Monotone as registered; the first
strict-clean answers in program history at any level. The frozen primary
(D1 ∧ D2 ≥ 6/8) failed by one answer on D2 — and D1's single strict miss is
the pre-registered criterion tension confirmed by hand ($17,000 − $5,000 =
$12,000 and a correct day-count, flagged as "not present verbatim").
**Autopsy:** the disease changes species as demand falls — the invention
flood (D4–D5) gives way to pure constraint-conflation (D2–D3: the model
mis-applies the sign-off cap *inside composite reasoning* that it computes
correctly *atomically*). The [TBD] hatch went unused (2/8). Compounding
arithmetic: atomic decomposition is viable (~100% realistic per piece);
composite levels need staging.

## 20. Run 20 — The staged decomposer (2026-08-15)

**The last unmeasured link:** does injecting the code-verified atomic answers
into the composite prompts transplant the knowledge? The model's cached D1
answers passed code verification 8/8 (its atomic arithmetic was perfect);
a fixed VERIFIED-FACTS anchor (code carries text — the coach law applied to
knowledge) was appended to the run-19 D2/D3 prompts verbatim.

**Results: staged D2 8/8 — PERFECT under both rulers (was 5/8). Staged D3
3/8 strict / 6/8 RULER-T (was 3/8). Cap-conflation flaws 6 → 1.** The frozen
bar failed on D3's strict leg — and hand-verification showed every flagged D3
"invention" (the 13-, 20-, 10-, and 12-day windows, the $7,000 difference)
was **byte-identical to the anchor's own code-verified facts**: the strict
ruler, lacking a derivation exemption, flagged the harness's certified truths.
Genuine model faults: two, both the same shape — the model names an option
non-executable and then commits to it (the last true 4B deficit: choice-level
commitment logic). **Run 11's anchoring law extends from estimates to
constraint facts; the staging link holds.**

## 21. Run 21 — THE REMATCH, with 21B/21C iterations (2026-08-15)

**The assembled chain vs the naked generalist — same weights
(Qwen3-4B-Instruct-2507 + wrk_keep100), 16 fresh six-fact problems (seed 21),
so the only experimental variable is the architecture.** Arm C: five
demand-matched calls per problem (code-checked atomic → anchored judgment →
anchored conditional-prediction → anchored choice → anchored estimate),
coach-assembled with zero re-narration. Arm G: the full problem in one pass
(GEN_SINGLE, the standing baseline operationalization). **⚠ STRICT-D — the
program's labeled prospective ruler variant, first use:** STRICT_ONE plus a
derivation-with-basis exemption (asserted single-clause construction),
motivated by two runs of hand-verified artifacts, applied to both arms
symmetrically; strict and RULER-T dual-reported throughout.

| arm | strict | STRICT-D | RULER-T |
|---|---|---|---|
| CUBE-v2 (staged) | 3/16 | **6/16** | 6/16 |
| GENERALIST (naked) | 0/16 | 0/16 | 1/16 |

**THE CUBE BEATS THE GENERALIST 6–0 — the first fidelity win in program
history** (run 15's match was a 2-of-6-legs rubric loss; this is the
head-to-head on the fidelity criterion itself). Pipeline integrity perfect
(16/16 atomic code-checks, zero estimate injections, assembly added no
flagged content). The frozen absolute leg (≥ 10/16) failed: the ten failures
decompose into choice-commitment contradiction (~5–6; one answer chose an
option it had itself called "impossible" and estimated 0%) and
prediction-piece decorations (~4).

**21B (labeled amendment):** a code CONSTRAINT GUARD on the choice (the
harness knows which branch the anchor disqualifies; bar it, retry once) plus
a digit screen on the prediction. **Result: STRICT-D flat at 6/16; RULER-T
6 → 8.** The guard worked where aimed (commit-to-barred-choice: zero) — but
the contradiction *relocated* into the prediction piece (run 12's law at
piece scale: closing one free surface moves the error to the next), and the
screen missed its target through an implementation bug (a 1–3-digit
exemption that exempted exactly the "48 hours" class it was built to catch;
five of the ten failures are single-flaw answers in that class).

**21C (labeled amendment, run same day):** the fixed screen (unit-tested;
two matching bugs caught pre-spend) + the barred-branch clause on the
prediction prompt. **Result: 8/16 STRICT-D — the relative win widens to 8–0,
the absolute bar (10/16) still FAILS.** The screen eliminated its target
class completely (zero 48/24-hour flaws remain); the +2 fell short of the
10–13 projection because closing the decoration surface exposed the next
stratum: **modal inconsistency** — the model treats the barred option as a
live hypothetical in the same answer that declares it infeasible. **The
series was closed at three iterations (6 → 6 → 8; the run-16 three-variant
precedent): each guard eliminates its class and the contradiction relocates
one level deeper. The residue is the true 4B reasoning limit — a judgment
failure, the exact class the asymmetric-cube fork targets. What stands:
cube-v2 at 50% certified-clean vs 0% naked, same weights.**

## 22. Program-level synthesis

**The four laws (positive, replicated, cheap to exploit):**
1. **Motion law (run 11, reconfirmed in the match at 93–100%):** directional
   re-derivation under a changed world is harness engineering — anchor the prior,
   present the update, ask. No training required.
2. **Coach law (run 15: 87.5% vs 21%):** multi-segment fusion fidelity is achieved
   by construction — template slots + verbatim carriage + digit-free connective
   tissue — not by generation.
3. **Demand law (run 19: 0% → 88% strict / 100% realistic, monotone):**
   clean-rate is a function of QUESTION size, not problem size — never hand the
   model a question larger than one move; the decomposer's true job is
   demand-splitting.
4. **Staging law (run 20: judgment 5/8 → 8/8, conflation 6 → 1; 21B guard:
   commit-to-barred-choice 0):** knowledge the model holds atomically but
   fumbles compositely is transplanted by injecting its code-verified atomic
   answers as anchors — the motion law generalized from estimates to constraint
   facts. Corollary (21B): errors RELOCATE to the nearest open free surface;
   guards must cover every generation step, not one.
Together: **reasoning lives in the weights; faithfulness lives in the harness —
and the assembled harness now beats the same weights running naked, 6–0 on
certified-clean answers (run 21).**

**The wall (negative, measured from FIVE sides, etiology closed):** free-prose
grounding fidelity at 4B is ~21–42% clean (lenient), ~5% clean (strict, match
load), and 0% clean (strict, ladder — both models, all loads); ~1 integration
error per ~3 attempts per free-prose step (run 12); not buyable by SFT in any of
three forms (the three-run law); repairable only to 19/24 with a frontier judge
in the loop; not certifiable by a trained 4B gate (§14); **not a state-load
property (§15 — flat zero from 2 to 10 facts); not prompt-fixable (§16 — the
grounding discipline goes unexecuted); and not specific to our weights (§16 —
the reasoning-trained sibling also scores 0/40 strict).** A 14B halves the
lenient wall (54%). The final decomposition (§17): the strict wall = a real
fatal-flaw rate (contradiction/distortion/constraint violation) PLUS an
assertion policy that decorates every plan with unmarked invented specifics;
under a severity-matched criterion the first component leaves 20–38% of answers
clean, and reasoning training doubles that rate.

**On the thesis itself:** composition is not refuted in principle — the machine
works, routing is free, one specialist is certified at set-level, and the coach
closes the seam it was built for. What is refuted at 4B is composition *as a
winning strategy while fidelity is unsolved*: the noise floor is wider than any
specialist edge we can train. The cube lost to the wall, not to the generalist.
The RULER-T reading sharpens this: at the matched criterion the naked base is
realistically clean 20% of the time, and the binding contest for any successor
is the fatal-flaw rate, not the decoration rate. **Runs 19–21 then resolve the
contest in the harness's favor: cube-v2 at 38% certified-clean (dual-ruler) vs
0% naked — the thesis's first outright win — with the absolute bar (62.5%)
still open pending 21C and a replication wave. The claim that stands: at fixed
weights, architecture converts 0% into 38%; nothing else in fifteen runs
converted it into anything.**

**What is dead:** carved faces (7); deep-chain corpora on any base (8–9); the
viability face as trained (10, executed by the match's ablation); delta diets (11);
fusion SFT including self-distillation (14); whole-discourse 4B certify-gates (16);
perfection seam gates as thesis instruments (12→15 amendment); **the state-load
hypothesis (17); in-prompt grounding discipline at 4B (17B); the strict ruler as
a stand-alone quality criterion for this weight class (17B + RULER-T — retained
as the comparability spine, demoted as the deployment target); 4B
verification-as-certification at ANY wavelength (16 + 18 — twice-failed);
single-surface guards (21B — errors relocate).**

**What survives for any successor:** the frozen bench suite + staged problems +
the 40-problem capacity ladder (md5-pinned); the certified faceF; dec_qwen +
router (94/104); the relay/coach machinery; 621 strict-labeled grounding pairs
plus 120 severity-stratified ladder verdicts and the RULER-T taxonomy; a
0.99-recall hallucination detector (usable for triage/monitoring, not gating —
measured 96% FP against realistic-clean); the measured reasoning-training gap
(2× realistic-clean at ~25× tokens); the laptop-free driver/pod ops pattern;
**the full cube-v2 pipeline (run21_pod.py + 21C variant, unit-tested) with its
16-problem rematch bench (seed 21, md5-pinned) and the 6–0 result**; and the
judge discipline that let fifteen runs contradict their own hopes with every
post-hoc event labeled.

## 23. Instruments: validated, invalidated, lessons

**Validated:** single-session cached judging with all-or-discard coverage; the
staged-problem generator (deterministic, md5-frozen, unique entity names); the
ablation arm (sharpest causal instrument in the match); the two-ruler audit (§14);
spend caps that abort before billing (fired twice, run 16B); detached-pod overnight
ops (two full nights, zero incidents); **the $0 cached-verdict reanalysis pattern
(the stagnant-judge audit and RULER-T both ran entirely on already-paid reads);
the flaw-autopsy dump (every flaw beside its problem's planted tokens) as the
program's cheapest diagnostic; free third arms from cached baselines (17B's arm
B cost nothing).**

**Invalidated:** regex/code checkers as fidelity RECALL instruments (precision
perfect, recall 20% — semantic sins unreachable); delivery/fluency as any proxy for
fidelity (orthogonal, 13B); same-problem batching assumptions for relabeling (141/174
singletons); lenient-vs-strict criterion mixing in gold labels (65% flip rate);
**in-prompt fidelity discipline as an instrument or a fix (GROUND: 4–13/40
compliance, negative net effect); word-count-only sanity on thinking-model
outputs (24/40 leaked deliberations initially passed as "answers").**

**Ops lessons (costed):** TRL 1.9 fp32-logit loss OOMs a 48GB card at bs 8 on a
151k vocab (fix: bs2/accum4 + checkpointing); `transformers<5` breaks on
`qwen3_5`-class checkpoints (refs recovery required an upgrade after the thesis
phases completed); harmony-format channel markers are special tokens — decode with
specials or the final channel is unrecoverable; thinking-model reference arms need
explicit `enable_thinking=False` or they burn their budget on plain-prose thinking;
**always-thinking models need generation budgets larger than their deliberation
length or `</think>` never arrives and the stored answer is raw monologue —
detect by word-count outliers, repair by regenerating at 2–3× budget (24/40
leaked at 4096 → 0 residual at 9k/13k); vendor decoding specs are part of match
fairness (running a thinking model greedy against its own card sandbags it).**

## 24. Threats to validity

1. **LLM-as-judge throughout**; single judge family (Sonnet 5); the strict
   coherence criterion is itself judge-operationalized. Mitigations: single-session
   relative comparisons, cached verdicts, per-leg pre-registered bars, spot-read
   audits of false positives. Not mitigated: judge self-consistency on borderline
   "clean" was never measured (recorded as a known gap).
2. **Small clean-side Ns** after the strict relabel (20 eval cleans) — the 16C
   clean-recall read (0.25) is coarse; the *direction* of the slide (0.40→0.25) and
   the stop verdict do not depend on granularity.
3. **One base family at 4B** (Qwen3-4B-Instruct-2507); the 14B wall point is a
   single measurement; the reference ladder is generated but unjudged.
4. **Single-answer B/C rubrics** were adapted set→single for the match (frozen
   pre-output, but new instruments with no history).
5. **The generalist's match prompt** packs all three segment demands into one pass —
   a fair-information design choice, but other operationalizations exist.
6. **The RULER-T taxonomy is post-hoc and machine-classified**: a regex over the
   judge's own flaw prose (spot-read verified; 14 unclassifiable flaws treated
   conservatively as fatal), designed after the strict verdicts were seen. It is
   anchored in run 17's pre-frozen addition/distortion split and overturns no
   frozen verdict, but its clean-rates are a reanalysis, not a pre-registered
   result — any successor should freeze a severity-tiered rubric *before* its
   next run and have the judge classify directly.
7. **The 17B rival arm ran with sampling** (vendor decoding, fixed per-item
   seeds) while our arms ran greedy — required for a fair match per the model
   card, but it means the rival's numbers carry sampling variance the other arms
   do not.

## 25. Cost ledger (actuals, runs 7–21)

| run | what | cost |
|---|---|---|
| 7 | carved faces + oracle | ~$6 |
| 8 | deep-chain face (granite) | ~$8 |
| 9 | base-swap control | ~$4 |
| 9b | aligned foresight face — first pass | ~$5.5 |
| 10 | viability face + probe | ~$8 |
| 11 | delta diet + motion discovery | ~$17 |
| 12 | cube prototype (stage 2 unspent) | ~$1 |
| 13 + 13B | wall instrumentation | ~$2.6 |
| 14 | self-distillation null | ~$10.5 |
| 15 | coach + THE MATCH (incl. pod nights) | ~$15 |
| 16 | verifier (3 variants + relabel) | ~$5.3 |
| 17 | capacity ladder | ~$1.4 |
| 17B | marking + weight-class match (incl. rival repair) | ~$3.3 |
| audits | stagnant-judge audit + RULER-T reanalysis | $0 (cached verdicts) |
| 18 | fatal-flaw gate ($0 corpus from caches) | ~$0.6 |
| 19 | demand ladder | ~$1 |
| 20 | staged decomposer | ~$0.5 |
| 21 + 21B | THE REMATCH + guard iteration | ~$2.6 |
| 21C | fixed-screen iteration | ~$0.9 |
| **program total** | 15 runs, 4 laws, 1 certified face, 1 lost match, 1 closed wall, 1 opened island, 1 won rematch | **~$93 + part-I $110 ≈ $203 all-era** |

Remaining wallets at close: Anthropic ≈ $4.7 · RunPod ≈ $20 · OpenRouter $3.

## 26. Open forks (recorded, not committed)

1. **Replication wave (~$1.8):** one more 16-problem seed of the rematch —
   turns the 6–0 existence proof into a citable rate.
2. **The asymmetric cube:** 4B answers every piece; a 9–14B makes ONLY the
   choice call (the one remaining true deficit — commitment logic). Every
   capacity measurement in the program says judgment scales faster than
   generation.
3. **Claim-level verification:** decompose answers into atomic claims and verify
   each against the problem — MiniCheck's actual granularity. Whole-discourse
   certification failed; sentence-level was never tested. Pairs naturally with
   **verify-and-PATCH** (surgically rewrite the flagged claim by template,
   coach-style) instead of regenerate-and-pray.
4. **The capacity/reasoning pivot:** same architecture on a 14B-class base (wall
   measured at 54% lenient-clean vs 21–42%), OR on a thinking-class 4B base —
   §17 measured reasoning training alone doubling realistic-clean (38% vs 20%)
   at ~25× tokens; a thinking base + the coach + a T1 gate is an unexplored
   stack. The efficiency recipe transfers.
5. **faceV rebuild** with aligned-gate + GPU-side or open-data corpora ($0 API) —
   only meaningful after the floor-lifting forks above.
6. **Reference-ladder judging** (~$3.5): three reasoning models' match-bench
   transcripts sit archived unjudged. Partially pre-answered by 17B (the
   thinking twin flattens to 0/40 on the ladder under strict), but the 9B/20B
   rungs would calibrate how far above the weight class the strict wall extends.
7. **The write-up→paper conversion** of both volumes (the natural framing:
   fifteen pre-registered runs from 'the wall is unbeatable' to 'the harness
   beats the weights 6–0' — demand-matching as the missing variable).

---

## Appendix A — Artifact registry (runs 7–21)

| bundle / artifact | contents | note |
|---|---|---|
| density_run9b/run9b_bundle.tgz | wrk_faceF_9b_qwen (CERTIFIED) + threads | md5 37b5e811 |
| density_run10/run10_bundle.tgz | wrk_faceV_10_qwen (provisional; seat revoked §13) | verified |
| density_run11/run11_bundle.tgz | wrk_faceVD_11_qwen (not a specialist) + evalD | md5 67eeb5ea |
| density_run14/run14_bundle.tgz | wrk_fusion_14_qwen (null) + diet | md5 0354bf61 |
| density_run16/ver_16_qwen | verifier v1 (detector-grade) | safetensors md5 4066a0e7 |
| out/run15/match/ | full match + refs transcripts, judged verdicts, logs | local |
| data/run16/ | 621 strict-labeled grounding pairs, v1–v3 corpora | md5s in RUNBOOK16 |
| adapters (staged) | dec_qwen + 3 workers, 2.1GB upload set | .r11_stage + scratchpad |
| data/run17/ladder_problems.jsonl | 40-problem capacity ladder, 5 levels × 8 | md5 95a293bba2d2583d10edb0f45fed1605 |
| out/run17/ | ladder transcripts + verifier verdicts + judge cache (40 strict reads) | local |
| out/run17b/ | 3-arm match transcripts (incl. repaired rival + .pre_fix), verifier verdicts, judge cache (80 strict reads), match_results.json | local |
| data/run18/ + out/run18/ | 549-pair fatal-flaw corpus (md5s in RUNBOOK18) + eval verdict | local |
| data/run19/ + out/run19/ | demand ladder (md5 ebb30bd7) + curve verdicts | local |
| data/run20/ + out/run20/ | staged prompts (md5 b97d0ec3) + verdicts | local |
| data/run21/ + out/run21/ | rematch bench (seed 21, md5 aea3d98b) + 21/21B transcripts, dual-ruler cache | local |
| divergent-model-backups/density_run17_21/ | era 17–21 bundle | md5 6378979b |
| scripts/ruler_t.py | frozen RULER-T taxonomy (the §17 classifier, verbatim) | committed |

## Appendix B — Frozen-criteria scoreboard (runs 7–21)

| run | headline bar | outcome |
|---|---|---|
| 7 | ≥2 carved faces pass lanes | FAIL (0/3) — generated corpora required |
| 8 | deep-chain face ≥ anchor+0.20 | FAIL (−0.23) — gate ≠ instrument lesson |
| 9 | same diet, stronger base | FAIL harder (−0.33) — diet toxic; Qwen adopted |
| 9b | Eval B ≥ anchor+0.20 | **PASS (+1.06)** — first certified face |
| 10 | viability: A + C + probe | FAIL all — structure transfers, fidelity doesn't |
| 11 | delta ≥ static+25 on nerfs | FAIL (−7) — **motion law found instead** |
| 12 | seam gate: 3/3 coherent | FAIL ×3 — ~1 error / 3 free-prose attempts |
| 13 | checker agreement ≥80% | FAIL (60%) — semantic sin taxonomy |
| 13B | wall + repair bars | wall 25%/54%; repair 19/24 (fail by one) |
| 14 | F14 ≥ A + 6/24 | NULL (+2) — **three-run law complete** |
| 15 s1 | coach ≥ base+4 ∧ ≥15/24 | **PASS (21 vs 5)** — coach law |
| 15 s2 | the match, 6 legs | **2/6** — V seat revoked; noise floor named |
| 16 | verifier 0.75/0.70 | FAIL ×3 (0.99 detection / 0.25 certification) — wall closed |
| 17 | envelope: clean ≥50% at some load | FAIL — flat zero 2→10 facts; assertion-policy reframe |
| 17B | marking ≥4/40 strict-clean | FAIL (0/40 all arms) — discipline unexecutable; rival also 0/40 strict |
| 17B-T | (labeled reanalysis, no frozen bar) | island 20–38%; rival 2× baseline; verifier FP 96% — thesis confirmed |
| 18 | gate 0.75 recall ∧ 0.30 FP | FAIL (0.733 / 0.542) — certification twice-failed at 4B |
| 19 | D1 ∧ D2 ≥ 6/8 strict | FAIL by one (D2 5/8) — **demand curve 0→88% monotone; demand law** |
| 20 | staged D2 ∧ D3 ≥ 6/8 strict | FAIL (D3 leg = criterion artifact, hand-verified) — **D2 8/8 perfect; staging law** |
| 21 | STRICT-D: cube ≥ 10/16 ∧ ≥ gen+4 | FAIL leg 1; **relative leg 6–0 — first fidelity win** |
| 21B | bars carried | FAIL flat 6/16 (RULER-T 6→8); guard worked, screen bug named |
| 21C | bars carried | FAIL 8/16 (8–0 relative) — screen class eliminated; modal-inconsistency residue; series closed |
