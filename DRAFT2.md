# The Cube Program: Composed LoRA Specialists, the Fidelity Wall, and the Weights/Harness Symmetry
## (A Pre-Registered Ten-Run Study at 4B — runs 7–16)

> **STATUS: UNOFFICIAL WORKING DRAFT — 2026-08-12.** Complete factual record of the
> cube program, runs 7–16, companion volume to DRAFT.md (runs 1–6 + probe study,
> the density/storage era). All numbers below are traceable to frozen runbooks
> (RUNBOOK7.md–RUNBOOK16.md), git history, and md5-pinned artifacts (Appendix A).
> Every success criterion was frozen before its run; the single post-hoc gate
> amendment in program history is labeled where it occurs (§13).
> Author: Nikhil Jangra. Drafting assistant: Claude (Anthropic).

---

## Abstract

We report a ten-run, pre-registered empirical study of a composed-specialist
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
toward all-flag across three corpus designs); and (4) lost the pre-registered match:
the composed cube with current specialists takes 2 of 6 legs against the naked
generalist, with the ablation showing the provisional viability specialist is a net
negative in its own seat. The unifying mechanism: under a strict grounding criterion,
only ~5% of 4B generations are fully clean, so specialist edges (real but ≤ +0.12)
drown beneath a shared invention noise floor that neither training, repair, nor
gating can lift at this scale. Reasoning structure trains; faithfulness does not —
faithfulness must be *constructed* in the harness, and at 4B the constructible
surface stops at the assembly layer. The wall is a generation-capacity property.

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

- **Base:** runs 7–8 ibm-granite/granite-4.0-micro (3.4B); runs 9–16
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
  post-hoc amendment in ten runs (§13). Frozen stop clauses are executed as written,
  including against the program's own hopes (§10, §16).
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

## 15. Program-level synthesis

**The two laws (positive, replicated, cheap to exploit):**
1. **Motion law (run 11, reconfirmed in the match at 93–100%):** directional
   re-derivation under a changed world is harness engineering — anchor the prior,
   present the update, ask. No training required.
2. **Coach law (run 15: 87.5% vs 21%):** multi-segment fusion fidelity is achieved
   by construction — template slots + verbatim carriage + digit-free connective
   tissue — not by generation. Together: **reasoning lives in the weights;
   faithfulness lives in the harness.**

**The wall (negative, measured from three sides):** free-prose grounding fidelity at
4B is ~21–42% clean (lenient) and ~5% clean (strict); ~1 integration error per ~3
attempts per free-prose step (run 12); not buyable by SFT in any of three forms
(the three-run law); repairable only to 19/24 with a frontier judge in the loop;
not certifiable by a trained 4B gate (16). A 14B halves the lenient wall (54%).

**On the thesis itself:** composition is not refuted in principle — the machine
works, routing is free, one specialist is certified at set-level, and the coach
closes the seam it was built for. What is refuted at 4B is composition *as a
winning strategy while fidelity is unsolved*: the noise floor is wider than any
specialist edge we can train. The cube lost to the wall, not to the generalist.

**What is dead:** carved faces (7); deep-chain corpora on any base (8–9); the
viability face as trained (10, executed by the match's ablation); delta diets (11);
fusion SFT including self-distillation (14); whole-discourse 4B certify-gates (16);
perfection seam gates as thesis instruments (12→15 amendment).

**What survives for any successor:** the frozen bench suite + staged problems; the
certified faceF; dec_qwen + router (94/104); the relay/coach machinery; 621
strict-labeled grounding pairs; a 0.99-recall hallucination detector (usable for
triage/monitoring, not gating); the laptop-free driver/pod ops pattern; and the
judge discipline that let ten runs contradict their own hopes without a single
unlabeled post-hoc change.

## 16. Instruments: validated, invalidated, lessons

**Validated:** single-session cached judging with all-or-discard coverage; the
staged-problem generator (deterministic, md5-frozen, unique entity names); the
ablation arm (sharpest causal instrument in the match); the two-ruler audit (§14);
spend caps that abort before billing (fired twice, run 16B); detached-pod overnight
ops (two full nights, zero incidents).

**Invalidated:** regex/code checkers as fidelity RECALL instruments (precision
perfect, recall 20% — semantic sins unreachable); delivery/fluency as any proxy for
fidelity (orthogonal, 13B); same-problem batching assumptions for relabeling (141/174
singletons); lenient-vs-strict criterion mixing in gold labels (65% flip rate).

**Ops lessons (costed):** TRL 1.9 fp32-logit loss OOMs a 48GB card at bs 8 on a
151k vocab (fix: bs2/accum4 + checkpointing); `transformers<5` breaks on
`qwen3_5`-class checkpoints (refs recovery required an upgrade after the thesis
phases completed); harmony-format channel markers are special tokens — decode with
specials or the final channel is unrecoverable; thinking-model reference arms need
explicit `enable_thinking=False` or they burn their budget on plain-prose thinking.

## 17. Threats to validity

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

## 18. Cost ledger (actuals, runs 7–16)

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
| **program total** | 10 runs, 2 laws, 1 certified face, 1 lost match, 1 closed wall | **~$83 + part-I $110 ≈ $193 all-era** |

Remaining wallets at close: Anthropic ≈ $6.5 · RunPod ≈ $31 · OpenRouter $3.

## 19. Open forks (recorded, not committed)

1. **Claim-level verification (the most promising unspent idea):** decompose
   answers into atomic claims and verify each against the problem — MiniCheck's
   actual granularity. Whole-discourse certification failed; sentence-level was
   never tested. Pairs naturally with **verify-and-PATCH** (surgically rewrite the
   flagged claim by template, coach-style) instead of regenerate-and-pray.
2. **The capacity pivot:** same architecture, 14B-class base (wall measured at 54%
   lenient-clean vs 21–42%); the efficiency recipe transfers.
3. **faceV rebuild** with aligned-gate + GPU-side or open-data corpora ($0 API) —
   only meaningful after (1) or (2) lifts the floor that drowned it.
4. **Reference-ladder judging** (~$3.5): three reasoning models' transcripts sit
   archived; answers whether the strict rubric flattens 9B/20B reasoners to the
   cube's ~2.6 (wall-is-universal) or not (wall-is-ours).
5. **The write-up→paper conversion** of both volumes.

---

## Appendix A — Artifact registry (runs 7–16)

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

## Appendix B — Frozen-criteria scoreboard (runs 7–16)

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
