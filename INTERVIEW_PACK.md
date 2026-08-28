# THE CUBE PROGRAM — Interview & Resume Pack
*(canonical version, 2026-08-28; every number traceable to DRAFT.md / DRAFT2.md,
frozen runbooks, and md5-pinned artifacts)*

---

## 1. Resume block (paste-ready)

**Project title:** The Cube Program — pre-registered small-LLM reasoning research (solo)

- Designed and executed a **24-run pre-registered research program** (~$209
  total compute, 40 days, solo) testing whether composed LoRA specialists +
  a verification harness can beat same-weight baselines on grounded
  strategic reasoning at 4B scale — every success bar frozen in writing
  before spend; every failure published alongside the wins.
- Built a five-stage pipeline (machine-verified fact extraction →
  code-computed comparisons → anchored judgment/prediction/choice →
  template assembly) that took the same 4B weights from **0/16 to 6/16
  certified-clean answers (paired p≈0.008)** vs a one-pass control, and
  **beat the reasoning-trained sibling of its own base model 5–2** on a
  third-party-authored holdout at comparable token budget (primary-judge
  criterion; strict-band conclusions replicated across two judge families
  at 97.9% agreement).
- Invited an **external adversarial audit** of my own methodology, then
  built the locked holdout it demanded — harness frozen by git commit
  *before* the problems existed, zero post-contact edits — and reported
  the headline strict-band claim failing to transfer (generator-local) at
  equal volume with the wins.
- Mapped the **capability ceiling of the 4B weight class** across five
  falsified mechanisms (specialist SFT, verifier gating, prompting,
  reasoning-trained weights, harness-at-ceiling), naming the residual
  failure mode (cross-stage judgment coherence) and pricing the scaling
  path to the next weight class.

*(Shorter one-liner if space is tight:)* Ran a 24-run pre-registered study
(~$207, solo) showing a verification harness beats both a naked same-weight
baseline (6–0, p≈0.008) and a reasoning-trained sibling model (5–2,
third-party holdout) on grounded-reasoning fidelity at 4B — externally
audited, all failures published.

---

## 2. The 30-second version (say this first)

"I spent a month running a pre-registered research program on a question I
cared about: can architecture substitute for scale in small language models?
I built a pipeline where code verifies every fact a 4B model extracts,
computes the arithmetic itself, and anchors each reasoning step — and it
beat the same weights running naked six-to-nothing on certified-clean
answers, and beat the reasoning-trained version of the same model 5–2 on
problems a third party wrote. The part I'm proudest of isn't the win — it's
that I invited an external audit, built the holdout it demanded with the
harness frozen before the problems existed, and published the claim that
*didn't* survive right next to the ones that did."

## 3. The 2-minute version (the arc)

1. **The bet.** Cheap LoRA specialists + a generalist + a harness on one 4B
   base, composed at inference — the "Rubik's cube" — against the same base
   naked. If it works small, the methodology scales.
2. **The wall.** Fourteen runs of honest failure with a shape: *reasoning
   structure trains; faithfulness doesn't.* At a strict grounding criterion,
   ~0–5% of 4B generations are clean. I falsified the fix from five
   directions — specialist SFT, self-distillation, a trained verifier
   (0.99 detection, 0.25 certification — it can find flaws but can't certify
   cleanliness), prompting discipline (models simply don't execute it), and
   reasoning-trained weights (also 0/40 strict).
3. **The turn.** Two measured laws changed the design: clean-rate is a
   function of *question size*, not problem size (demand ladder: 0% → 88%
   monotone as the question shrinks), and facts the model fumbles in
   composition can be transplanted by injecting its own code-verified
   atomic answers back as anchors (staging: 5/8 → 8/8).
4. **The win.** The assembled pipeline — cube-v2 — beat the same weights
   naked **6–0** on certified-clean full answers (paired p≈0.008), widening
   to 8–0 with iterated guards (exploratory).
5. **The stress test.** I handed the methodology to GPT with instructions to
   attack it. It named template circularity as the deepest threat. So I
   generalized the harness to free text, froze it by commit, had GPT author
   16 natural-prose problems, and ran with zero post-contact edits. **The
   strict-band win did not transfer — and I published that.** What survived:
   the machinery generalized (10.4 verified facts/problem, zero dropped), a
   5× realistic-band fidelity edge, and both pre-registered blind
   constraint-fidelity predictions.
6. **The final match.** Same holdout, against Qwen3-4B-Thinking — the
   reasoning-trained sibling — with my pipeline's verdicts cached before
   the comparison existed. **Cube 5, Thinking 2, naked 1** on the realistic
   criterion, at comparable token budgets. Caveat I volunteer: the Thinking
   model is the only arm that ever placed answers on the *strict* band
   (3/16) — the two mechanisms are complementary, not substitutes.
7. **The 14B probe (run 24).** Same holdout, the same cube (LoRA-adapted
   4B + harness) against a naked Qwen3-14B in thinking mode. Observed 5 vs 4
   RULER-T-clean (paired: 4 cube-only, 3 R14-only, McNemar p=1.0) — a
   non-result at n=16, and the 14B led the blind quality rubric on three of
   four dimensions. I pre-committed a "matched" wording, a second hostile
   audit killed it, and I retracted it the same day. What it *does* show:
   the strict-grounding island is still empty one weight class up (1/16).
8. **The last check.** A second judge family re-read all 48 holdout
   verdicts: 97.9% agreement on flaw detection (the walls are two-judge
   robust), but the severity *ordering* is single-judge until a
   judge-native severity read disambiguates my regex classifier from real
   disagreement. That qualifier is in my resume wording on purpose.

---

## 4. Claims discipline — what I say, qualify, and never say

**Say freely (two-judge robust / pre-registered / replicated):**
- The strict grounding island is empty for the entire 4B weight class —
  measured across both models, all prompts, all loads (0/40, 0/32), 97.9%
  cross-judge agreement.
- Same weights, 0/16 → 6/16 certified-clean via harness alone on the
  template bench (paired p≈0.008).
- The harness generalizes mechanically to free text (frozen-clause test:
  10.4 verified facts/problem, 0 dropped, on third-party prose).
- Both blind constraint-fidelity predictions (vs naked, vs Thinking)
  registered before their runs, and both held.
- The four laws (motion, coach, demand, staging) — each on its own
  pre-registered instrument.

**Say with the qualifier attached:**
- "Beat the reasoning-trained sibling 5–2" → *primary-judge criterion,
  n=16; strict-band conclusions are two-judge robust, the ordering is
  pending a judge-native severity read.*
- "5× fidelity edge over naked" → same qualifier, existence-grade
  (Wilson CI on 5/16 ≈ 14–56%).
- "8–0 / 50% certified-clean" → *exploratory, adapted on the same problem
  set; the locked figure is 6/16.*
- Everything is a **fidelity** result (grounding), not overall reasoning
  quality — the blind quality rubric exists for the latter and the cube
  leads it on constraint fidelity and action quality, trails on
  calibration.

**Never say:**
- "Matched a 14B reasoning model" or "3× less compute" (run 24: p=1.0,
  proxy unmeasured — retracted, see AUDIT_GPT_2026-08-28). "No reasoning
  training" (the worker is a LoRA on reasoning threads).
- "Beats reasoning models" unqualified. "50% clean" as a general property
  (generator-local). "25× cheaper than reasoning" (measured comparable on
  the holdout: 1,525 vs ≤1,360 tokens/answer). "Production-ready." Any
  SOTA claim. Any claim about problems wider than strategic decision
  reasoning.

---

## 5. Hard questions I expect — and the answers

**"n=16? That's tiny."**
Correct, and priced in: I quote Wilson intervals with every rate and call
the results existence-grade. The one inferential claim I make, the 6–0, is
paired within-problem (p≈0.008). The replication wave is a recorded fork —
the constraint was a ~$200 total budget, and I chose breadth of falsification
over depth of replication deliberately.

**"LLM-as-judge — isn't that circular?"**
Three defenses, then the honest limit. The judge never writes training
data; every prompt is frozen and every verdict cached; and my pipeline's
holdout answers were judged *before* the opponent comparison existed. The
honest limit: I ran the two-judge study myself — detection is robust
(97.9%), severity ordering is single-judge pending a judge-native read, and
that's published in the same repo.

**"Your holdout killed your headline. Why is that on your resume?"**
Because that's what the pre-registration was *for*. The strict claim was
generator-local; I found that out for $2.50 with a frozen harness instead
of in production, and the realistic-band edge plus both registered
predictions survived. A result that can't die isn't a result.

**"Couldn't the cube's edge just be five calls vs one?"**
Yes — that's an open confound, recorded by the external audit as finding 4,
and the matched-compute ablation (best-of-5 baseline, corrupted-anchor arm)
is the next priced run. Today's claim is bundle-level and I say so.

**"Why 4B at all?"**
Cost-bounded science: the whole program cost ~$207 because 4B iterates in
minutes on an A40. The deliverable is a *map* — five falsified mechanisms,
one named residue (cross-stage judgment coherence), and a measured scaling
prior (25% → 54% clean at 3.5× params) that tells the next dollar exactly
where to go: a 14B judgment seat, everything else stays 4B, fits one A40.

**"What did you actually build?"** (engineering screen)
Model-agnostic verification harness (fact extraction with verbatim +
coverage checks, code-computed comparisons/date arithmetic, anchored stage
prompts, template assembly with digit screens and modal guards); a frozen
LLM-judging stack (cached verdicts, spend caps that abort before billing,
all-or-discard coverage); pod ops (detached GPU jobs, resumable JSONL
state, md5-verified transfers); and the pre-registration tooling itself —
runbooks, frozen bars, zero-edit locks enforced by git ordering.

**"Biggest mistake in the program?"**
Definition drift — my corpus gate scored "foresight" as depth while the
bench judge scored it as calibration, and I burned two runs before naming
it. The law that came out (no instrument defines a lane in its own words —
quote the verdict instrument verbatim) is now how I build all instruments.
Runner-up: my severity taxonomy was a regex tuned on one judge's phrasing;
the two-judge study caught it doing exactly what the threat register
predicted.

**"What would you do with real funding?"**
In order: judge-native severity read (~$1, restores or honestly kills the
ordering claims); matched-compute ablation (~$3); the 14B asymmetric
judgment seat (~$5, the direct test of the residue); difficulty-matched
second holdout; then the 30B-A3B MoE class — judgment-class capacity at
4B-class inference cost — which is the thesis endpoint.

---

## 6. Numbers cheat-sheet (quote exactly)

| Figure | Value | Source |
|---|---|---|
| Program size | 24 runs, 2 phases, 40 days (Jul 20 – Aug 28, 2026), solo | DRAFT.md + DRAFT2.md |
| Total spend | ~$209 (~$99 cube era) | DRAFT2 §28 |
| The locked rematch | cube 6/16 vs naked 0/16 STRICT-D, paired p≈0.008 | RUNBOOK21 |
| Iterated (exploratory) | 8/16 vs 0/16 | RUNBOOK21 (21C) |
| Holdout (strict) | 0/16 vs 0/16 — did not transfer | RUNBOOK22 |
| Holdout (realistic) | cube 5/16 vs naked 1/16 | RUNBOOK22 |
| vs reasoning model | cube 5 vs Thinking 2 (naked 1); Thinking alone on strict band (3/16 STRICT-D) | RUNBOOK23 |
| Token budgets | Thinking 1,525/answer measured vs cube ≤1,360 ceiling | RUNBOOK23 |
| Blind constraint fidelity | cube 2.31 vs Thinking 2.19 vs naked 2.06 (both predictions registered + held) | RUNBOOK22/23 |
| vs 14B reasoning (run 24) | cube 5 vs Qwen3-14B-thinking 4 RULER-T; paired 4/3, McNemar p=1.0; STRICT-D 0 vs 1; 14B leads QUAL 3/4 dims — observed counts only | RUNBOOK24 |
| Judge agreement | 97.9% strict (two-judge robust); 70.8% severity (single-judge qualifier) | MINISTUDY_JUDGE |
| Extraction on free prose | 10.4 verified facts/problem, 0.0 dropped | RUNBOOK22 |
| Demand ladder | 0% → 88% strict, monotone in question size | RUNBOOK19 |
| Coach law | 87.5% vs 21% judge-clean | RUNBOOK15 |
| Verifier split | 0.99 detection / 0.25 certification recall | RUNBOOK16 |
| Size prior | 25% → 54% clean at 3.5× params (4B→14B) | RUNBOOK13B |

## 7. Evidence index (if they want receipts)

- **DRAFT.md + DRAFT2.md** — the two-volume record (runs 1–6, 7–23), every
  bar and outcome, threats to validity, cost ledger.
- **AUDIT_GPT_2026-08-18.md, AUDIT_GPT_2026-08-28.md** — two external hostile
  audits (8 + 10 findings) with dispositions; the second retracted run 24's
  pre-committed wording.
- **RUNBOOK7–23 + MINISTUDY_JUDGE.md** — frozen pre-spend protocols with
  results appended, never edited in place.
- **Holdout problems** md5 `7620cd1646a7466388b1811219ed2219` — frozen on
  receipt; harness commit `4093a26` predates it in git history (the
  zero-edit proof).
- All adapters, transcripts, and judge caches md5-pinned in DRAFT2
  Appendix A.

*Prepared 2026-08-20, revised 2026-08-28 after audit #2. If a number here ever disagrees with DRAFT2, DRAFT2
wins — update this pack, never the record.*
