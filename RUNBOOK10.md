# RUNBOOK 10 — the viability face (specialist two, aligned-target recipe)

**Question:** run 9b proved the recipe — founder definition as design center, corpus
admitted by the verdict instrument verbatim, dual evals frozen pre-output. Run 10
applies the identical recipe to the second face: viability. If it passes, the cube
has its second specialist and the dispatcher test (run 11) unlocks.

**Definition (Nikhil, 2026-07-29, adopted as the design center):** viability =
audit-first planning — "in planning we have to consider resources, manpower, and the
surrounding terrain involved — all of these — to see which variable is actually in
our favor to win that particular ordeal." Formalized: a plan is real only if it is
built from an audit of what the actor actually holds (resources, people,
position/seat, time), and every step spends only what the audit shows. A plan that
spends money, authority, or people the actor does not have is a paper plan, however
detailed it sounds.

**Definition extension (Nikhil, 2026-07-29 — the estimate leg):** "nothing is
absolute… we have to put a percentage criteria based on it — only then we can
measure something." A viable plan CLOSES with a success estimate explicitly derived
from the audit. The number itself is unverifiable on a fictional scenario and is
never scored; what is scored is the DERIVATION — the estimate must name which
favorable variable earns it and which friction caps it, and must move with the
evidence (an audit showing three frictions and no favorable variable cannot claim
80%). Nikhil's own trap-warning is the rubric: "if the model can create any sort of
mush out of those variables and just give a random number" — that mush is what
`estimate_derivation` (Eval C dim 6) exists to catch.

**Run-11 vision (recorded, not in scope for run 10):** the full loop Nikhil
described — foresight seat reads the concealed opponent → viability seat audits the
variables → the assembled chain outputs the final derived success percentage — is a
COMPOSITION of both specialists and is therefore the cube test's target output
shape, not a single-face capability. Run 11 inherits this as its deliverable.

This aligns with the frozen bench rubric verbatim (head2head_v5.py:59-60): "are the
four REALISTIC, LAWFUL, and actually executable in the real world (NOT fantasy, NOT
illegal, NOT convoluted obfuscation)?" — the definition operationalizes HOW
executability is checked. Unlike run 9b's foresight case, there is no definition gap
to bridge: audit-grounded execution IS what the bench scores.

**Anchor failure modes this face targets** (observed in run-9b anchor threads,
viability 2.94 = the base's weakest dim):
1. wrong seat — actor lacks the authority/position for the move (CISO selling
   advisory contracts to his own employer's merchants)
2. invented actors/facts — plan rests on entities not in the problem (the phantom
   competitor)
3. fake precision — confident numbers that are fabricated or incoherent (the 90%
   surgery statistic; 1200-cal plan "with a 1000-cal deficit")
4. broken causal chain — step A does not produce step B ("my refusal makes them
   halt recruitment")
5. zero-friction world — everything "by 5 PM tomorrow"; no legal review, taxes, or
   other humans

**PILOT8 V-history note (why retrying V is legitimate):** the two V strikes
(+1.46, +1.37 vs +1.5) were PROMPT-ONLY probes against the deprecated 1-10 mean-gap
pilot bar under judge-ceiling compression (~8.1 mean max). Run 10 is data-training
under the aligned recipe against the v5 1-5 instrument with the +0.20 bar — a
different intervention on a different instrument. The old `data/run9b/threads_V.jsonl`
detour (65/880, deep-chain-era prompt) is SUPERSEDED and will not be used.

**Program law (permanent):** no instrument defines the lane in its own words. The
admission gate IS `sonnet_judge`, byte-identical import. Sonnet NEVER generates
training data (generator≠judge family wall). Direct API only, no Batch API.

## Corpus

- Problems: run-7 V-carve, 220 problems / 880 worker rows, re-derived by the
  identical code path and identity-checked vs frozen manifest md5
  **0056aacbf580aadca2a06c92724de29a**. (Own-lane mean 6.91 vs pool 6.15; F&V
  overlap 17 problems / 8% — acceptable, both faces train the same worker seat.)
- Generator: **DeepSeek V4 Pro** via OpenRouter, temp 0.75, blind workers,
  resume-safe. Budget staged with kill-switches as always.
- Worker prompt (TASK_V4, to be frozen in run10_generate.py from THIS spec):
  1. AUDIT first — open by naming what the actor actually holds: the concrete
     resources (money/assets with real numbers only if the problem supplies them),
     the people actually available, the seat/authority they act from, and the time
     they have.
  2. Name the ONE variable from that audit that is actually in the actor's favor —
     the thing the plan is built on.
  3. COMMIT to the angle as a plan whose every step spends ONLY audited items —
     who does what, when, from which seat. No invented actors, no fabricated
     statistics, no moves outside the actor's authority.
  4. Name the ONE real-world friction most likely to stall the plan (legal step,
     another human's veto, timeline slip) and the pre-arranged answer to it.
  5. CLOSE with a success estimate (a percentage or tight range) explicitly derived
     from the audit — one clause of natural prose naming which favorable variable
     earns the number and which friction caps it. The number must move with the
     evidence; never a bare figure.
  4-6 sentences, cold and analytical (5 content beats need the extra room —
  9b's TASK_F2 packed 4 beats into 3-5; truncation risk stays covered by
  V5_WRK_MAXNEW=512). "Plan with what you hold, not what you wish."
  (Formatting guard: the estimate is one clause inside the final sentence, not a
  table or label — keeps Eval A leakage risk minimal, same class as 9b's
  falsification-signal line which cost nothing on A.)
- **Admission gate = bench judge verbatim** (`sonnet_judge` per problem on the 4
  generated threads): admit sets with **viability ≥ 4 AND foresight ≥ 3** (mirror of
  9b's gate with the legs swapped — the foresight leg blocks plans that audit well
  but ignore the counterparty entirely). Target ≥140 admitted; one regeneration
  round for failing problems; below 140 after retry → STOP, report.
- Diet: admitted gen rows + 1 original pos_thread per admitted problem (~20%),
  keep-0.6 band recomputed under Qwen, 1.25 epochs — the fixed recipe.

## Pod (short, ~20 min ≈ $1)

Reuse `dec_qwen` + `wrk_keep100_qwen` from run9_bundle (md5 708862dc…, no retrain).
Train **`wrk_faceV_10_qwen`** only. Gens: `faceV_10_qA` + `anchor_10_qA` (anchor
regenerated on-card — card-class control) + `faceV_10_qC` + `anchor_10_qC` (32
base each) + `faceV_10_qCtwin` (16 perturbed twins, face only — calibration
probe). V5_WRK_MAXNEW=512. Bundle `run10_bundle.tgz`.

## DUAL-EVAL DESIGN (the 9b architecture, facet-swapped)

**EVAL A — the frozen v5 bench (unchanged, byte-frozen).** 48 problems,
`sonnet_judge`, 6 dims. Comparability with all prior runs. Session K (+K2
only-if-pass).

**EVAL A FACE BAR (viability lane):** viability(face) ≥ viability(anchor) + 0.20
AND overall(face) ≥ overall(anchor) − 0.15.

**EVAL C — the INVENTORY bench (new instrument, frozen HERE, before any face
output exists).** Measures Nikhil's foundation directly: audit-grounded planning.
Where Eval B carried a dossier of opponent behavior, Eval C carries an inventory of
the actor's own means:

- **Format (Amendment 2, 2026-07-29 — Nikhil: "make it strict… only then we can
  trust the benchmark numbers"):** **32 base problems** (up from 24). Each = a
  concrete decision scenario in a modern real-world setting + an explicit
  INVENTORY of what the actor actually holds (funds, people and their actual
  commitment level, the actor's seat/authority, hard deadlines) + at least one
  TEMPTING move that exceeds the inventory (the trap — a high-upside option the
  actor cannot actually resource; mirror of B's innocent counter-signal). Generated
  by DeepSeek (family separation), OOD from all training problems, md5-frozen
  before any face thread exists.
- **Calibration probe (Amendment 2 — the objective "is the percentage right or
  wrong" check):** 16 of the 32 base problems additionally get a **PERTURBED
  TWIN**: the identical scenario with the inventory strengthened in exactly ONE
  named way (one friction removed OR one concrete resource added; nothing else
  changes). Twins are md5-frozen with the base set, used ONLY for the probe,
  never trained on, never judged by rubric. The FACE arm generates on all 16
  twins (anchor skipped — it emits no estimates by construction; documented).
  **Metric (judge-free, pure arithmetic on the model's own outputs):**
  - parseability: threads must contain a regex-extractable percentage or tight
    range (midpoint used). A twin-pair where either side has no parseable
    estimate counts as a FAIL — the habit must be consistent to be trusted.
  - direction-accuracy: pair passes iff estimate(boosted twin) ≥ estimate(base).
  A derived number MUST rise (or hold) when the inventory strengthens; a number
  that falls when the actor gets stronger is proven mush. No LLM opinion exists
  anywhere in this metric. (A reference-band alternative — problem-author
  supplies a "defensible range" — was considered and REJECTED: it inserts
  another LLM's opinion as ground truth; the monotonic probe is opinion-free.)
- **Task per arm:** same two-seat harness, same worker prompts as Eval A — no
  arm-specific prompting; the inventory arrives as part of the problem text.
- **Judge (Sonnet 5, new rubric, frozen in judge_run10.py):** 6 dims, 1-5, with
  **HARD CAPS (Amendment 2 strictness — single violations are disqualifying,
  not averaged away):**
  - resource_grounding: does every step spend only items in the inventory, with
    nothing invented beyond it (and the trap move either avoided or explicitly
    re-scoped to fit the inventory)? **CAP: any single invented resource, fact,
    or actor anywhere in the set → this dim scores at most 2.**
  - seat_fidelity: does the actor act only from the position/authority the
    inventory grants (no moves requiring a seat they do not hold)? **CAP: any
    single out-of-authority move → at most 2.**
  - causal_soundness: does each step actually produce the next — no step whose
    success depends on another party's unforced cooperation stated as certain?
    **CAP: any step stating another party's unforced cooperation as certain →
    at most 3.**
  - friction_realism: does the plan name real-world friction (legal, human,
    timeline) and carry an answer to it, rather than a zero-friction world?
  - decisive_completeness: does the thread still COMMIT and resolve the decision —
    audit as foundation for action, never as an excuse to hedge?
  - estimate_derivation: does the thread close with a success estimate that is
    visibly DERIVED — naming the favorable variable that earns it and the friction
    that caps it, consistent with the stated audit? (A bare or audit-inconsistent
    number = 1-2; a traceable, evidence-scaled estimate = 4-5. The number's
    "correctness" is never scored — only its chain of custody from the variables.)
  overall-C (reported) = mean of 6. **core-C (the bar metric) = mean of the 5
  non-estimate dims.** Coverage all-or-discard-whole-session, single session,
  direct API, no temperature param, max_tokens 12000, retry-on-empty.
- **C BAR (prototype-grade, single session L, documented as such) — now TWO
  legs, both required:**
  - **Leg 1 (comparative, judged, n=32):** core-C(face) ≥ core-C(anchor) + 0.20
    AND resource_grounding(face) ≥ anchor (the anti-trap leg — C must never
    reward confident plans that spend beyond the inventory).
  - **Leg 2 (absolute, objective — the trust-the-numbers leg, n=16 pairs):**
    parseable estimates on ≥ 14/16 pairs AND direction-accuracy ≥ 12/16 (75%).
    Binomial note: a random-number model hits 12/16 with p ≈ 0.038 — the leg
    genuinely discriminates derived numbers from mush. If Leg 1 passes but Leg 2
    fails, the verdict is PARTIAL: the planning face is real but the estimate
    habit is mush — reported as such, never averaged into a pass.
- **Why estimate_derivation is excluded from the bar (verification pass,
  2026-07-29):** the eval-time worker prompt (v5, arm-neutral) never asks for an
  estimate; only training installs the habit. The anchor therefore scores ~1 on
  this dim BY CONSTRUCTION, and a bar including it would be rigged in the face's
  favor — the same mechanism as 9b's falsifiability dim (face 3.88 vs anchor
  1.38, +2.50 on a dim the anchor was never asked to express). Retroactive
  check: 9b's B pass SURVIVES the same correction (core-4 gap +0.69 vs the
  +0.20 bar), so the 9b verdict stands — but run 10 applies the correction
  pre-freeze. estimate_derivation is scored and reported for both arms as
  capability-installation evidence only.

**Eval C FROZEN 2026-07-29: data/run10/inventory_problems.jsonl, 32/32, md5
ea0707a54dd17f2a0398293743ce8e3b; data/run10/twin_problems.jsonl, 16/16, md5
d3ec49d531cf7ca068a94683bb8346b4. Twin determinism verified 16/16 (each twin =
base + exactly one appended UPDATE line, byte-checked). Structure verified 32/32
(all sections present, ≥6 inventory items). Stage-1 actual cost $1.14 (incl. the
DeepSeek reasoning-token truncation diagnosis — root cause: V4 Pro spends
completion budget on reasoning; fix: max_tokens 2400→10000 here, 2600→8000 in
run10_generate.py, applied before stage 2 could hit the same landmine).**

## Verification-pass findings (2026-07-29, pre-spend, all resolved or documented)

1. **Rigged-bar fix (resolved):** estimate_derivation excluded from the C bar —
   see above. core-C is the bar metric.
2. **Estimate-clause risk on the frozen Eval A judge (covered by design):** every
   face thread will carry an invented percentage; if the v5 judge read that as
   fake-precision over-reach, viability would sink on A. Protection is built in:
   the **admission gate IS the v5 judge** — if estimate-bearing threads cannot
   clear viability ≥ 4 at the gate, generation stops before a dollar of training.
   The gate is the canary. (A derived "~60%, earned by X, capped by Y" is a
   judgment with shown work, not a fabricated fact-claim like the anchor's "90%
   surgery success rate" — but the gate proves it on the instrument, not on
   argument.)
3. **Trap-angle fairness (defensible as designed):** the decomposer may assign
   the trap move as one of the four angles, forcing a worker to commit to it.
   The rubric already prices this: re-scoping the trap to fit the inventory
   scores HIGH on resource_grounding — committing to the angle while refusing
   its unresourced form is exactly the skill. Both arms face identical dynamics.
4. **Generator-style confound (documented limitation, carried from 9b):**
   DeepSeek authors both the training corpus and the Eval C problems, so the
   face may hold a style-familiarity edge on C that the anchor lacks. Mitigants:
   both arms see identical problems; the C rubric dims are content-checks
   (inventory-traceability), not style; and Eval A remains the style-neutral
   leg — which is why the dual-eval exists. Same limitation was present in
   Eval B and is documented, not hidden.
5. **Foresight-leg feasibility at the gate (watch item):** TASK_V4 has no
   explicit counterparty-reaction step; the friction beat (step 4 — another
   human's veto, legal stall) is what carries the foresight ≥ 3 gate leg. If
   admission stalls below 140 with foresight as the binding failure, the fix is
   one line in step 4 ("frictions include the counterparty's most likely
   response"), rerun of failures — not a redesign.
6. **Namespace check (clean):** no `run10`/`faceV_10`/session-K/L collisions in
   any existing script; V-carve manifest confirms bench_overlap = 0 and
   prep_holdout = 20 excluded.

## Frozen reads

1. **EVAL A FACE BAR (sessions K + K2-only-if-pass):** as above.
2. **EVAL C BAR (session L, single, prototype-grade):** as above.
3. **VERDICT GRID:**
   - PASS A (both sessions) AND C → second specialist real under both definitions →
     run 11: cube/dispatcher test (wrk_faceF_9b_qwen + wrk_faceV_10_qwen +
     wrk_keep100_qwen; hot-swap re-verify on Qwen first).
   - PASS exactly one → split verdict, both numbers reported honestly, Nikhil
     decides (9b precedent: a split still yielded a declared specialist on the
     passing facet).
   - FAIL both with an aligned gate → viability headroom not buyable with SFT data
     at 4B — report, no 10b without a new causal hypothesis.

## Budget (staged, kill-switches at every gate)

DeepSeek generation ~$1.5-2.5 (OpenRouter) · Eval C problems + twins ~$0.9 ·
admission gate ~$3.5 (Anthropic) · pod ~$1 (RunPod) · Session K ~$2.5 · Session L
~$2.5 (32×2 arms judged; the 16-pair probe is judge-free arithmetic, $0) · K2
only-if-pass ~$2.5 → **~$11.5-15.5** total. Budget confirmed replenished by
Nikhil (2026-07-26: "we got the budget… GPU as well as the Anthropic").

## RESULTS (2026-07-29, Sessions K + L + probe)

**VERDICT: FAIL — all three legs.** First aligned-recipe fail in the program; the
definition-drift excuse does not apply (gate was the bench judge verbatim, corpus
scored viability 4.26 on the true instrument at admission).

- **Eval A (Session K, 48×2):** FAIL both legs. viability face 3.17 vs anchor 3.08
  (+0.09, positive sign but short of +0.20); overall floor BROKEN — face 3.53 vs
  floor 3.63 (anchor 3.78). The audit-first voice costs decisiveness (3.83 vs 4.44,
  −0.61) and concreteness (3.71 vs 4.17, −0.46) on the frozen bench: the long audit
  opening reads as committing late. K2 not run (cannot rescue).
- **Eval C (Session L, 32×2, hard-cap rubric):** FAIL both legs. core-C face 2.52
  vs anchor 2.57 — the face does not beat the anchor even on its own facet bench.
  Hard caps crushed BOTH arms (resource_grounding ≈2.0 both): at 4B, every set
  contains at least one invention/out-of-seat move, so the caps bind universally
  and erase differentiation. Only dim face leads: estimate_derivation 2.03 vs 1.59
  — the excluded-from-bar dim, i.e. the habit installed but nothing else improved.
- **Calibration probe (Leg 2, judge-free):** FAIL. Parseable 6/16 (needed 14) —
  the estimate habit fires on only ~35% of eval threads when the prompt doesn't ask
  for it. Direction 3/6 on parseable pairs — coin flip; wrong-direction deltas all
  small (57.5→56.7, 41.2→39.2), i.e. noise around underived numbers. Nikhil's
  "mush" scenario, measured and confirmed.

**Diagnosis (working, honest):** run-9b (foresight) vs run-10 (viability) is now a
controlled contrast — same base, same recipe, same aligned-gate method, opposite
outcomes. The pattern: **structural habits transfer to 4B by SFT** (anticipate →
position → falsifier: 9b passed Eval B +1.06), **fidelity constraints do not**
(don't invent, stay in seat, keep numbers coherent: run-10 failed all legs).
Viability is hallucination-adjacent — it demands sustained precision, not a
learnable response shape. Consistent with PILOT8's two prompt-only V strikes and
with the earlier granite foresight-ceiling finding (structure transfers, capacity
binds). Gate-vs-eval gap corroborates: DeepSeek's threads scored 4.26 at admission,
the trained 4B emits 3.17 — the 4B cannot reproduce its teacher's fidelity.

**Frozen-grid consequence:** "FAIL both with an aligned gate → report, no 10b
without a new causal hypothesis." The structure-vs-fidelity diagnosis IS a
candidate hypothesis for a different second face (distinctness is structural, and
its carve exists — own-lane mean 8.61), but that is a NEW decision for Nikhil, not
a continuation of run 10. wrk_faceV_10_qwen is NOT a specialist.

**Cost (run 10 actuals):** OpenRouter $4.43 (Eval C $1.14 + corpus $3.29; retry
round unused) · Anthropic ≈$6-7 (gate + K + L; K2 skipped) · pod ≈$1.2 · probe $0.

## PROBE 3 — elicited derivation (Nikhil's reframe, frozen 2026-07-30 pre-run)

**Hypothesis under test:** run-10's blind probe showed no SPONTANEOUS shift-tracking.
Nikhil's reframe: derivation may be a capability the face holds but was never
triggered — variables are not stagnant; put the shift in front of the model and ask
it to re-derive. If elicited derivation works, delta-derivation TRAINING (teach the
trigger as structure) is licensed as run 11; if even explicit elicitation fails,
the reframe is falsified for ~$1.

**Design (no OpenRouter, no training, judge-free scoring):**
- Inputs: the 16 frozen twin pairs + each arm's OWN base-problem threads from the
  run-10 bundle (up to 2 threads per pair, preferring threads with parseable
  estimates; old estimate recorded at selection).
- Revision prompt (elicitation is the point; NOT the frozen v5 eval): problem +
  the arm's own prior thread + "UPDATE: {boost}" + instruction to state what the
  update changes, revise the plan, and give a revised estimate in digits derived
  from the update. Greedy decoding (do_sample=False), max_new 384 — reproducible.
- Arms: faceV_10 (the subject) + keep100 anchor (reference only, no bar).
- Pod: any cheap card (A40), ~15 min. Outputs probe3_raw.jsonl.

**Frozen bars (face arm):**
1. ACKNOWLEDGMENT ≥ 12/16 pairs: at least one revision cites boost-signature
   content (same signature computation as probe2 — boost words minus base-problem
   words).
2. DIRECTION ≥ 75% of pairs with parseable old+new estimates: revised ≥ old
   (boost strictly strengthens by construction).
Read: both pass → capability present, trigger missing → run-11 delta-derivation
face licensed. Ack passes but direction fails → model narrates updates without
deriving → numbers decorative even when prompted; reframe dies. Ack fails →
elicitation itself beyond 4B-SFT reach here; reframe dies.

**PROBE 3 RESULTS (2026-07-30, A40 neutral_maroon_gibbon, 64/64 greedy revisions,
~$0.15):** **PASS on both frozen bars** — face ACK 12/16 (at bar), DIRECTION 11/14
parseable pairs (79% ≥ 75%). Parseability itself jumped: 14/16 pairs vs 6/16 in the
blind probe — when asked, the face emits digits.

**Post-hoc caveat (honest, from the anchor reference arm):** keep100 also scored
ACK 11/16 and DIRECTION 8/8 — by inflating nearly every revision to 82-100%
regardless of its old number (10→78, 15→82). The one-sided bar (boost always
strengthens) cannot distinguish derivation from indiscriminate "things improved"
uplift. The FACE shows discrimination the anchor lacks — 3 holds (40→40,
47.5→47.5, 50→50) and moderated moves vs the anchor's uniform ceiling — so the
pass is evidence of capability, not proof. **Run-11 eval requirement (binding):
bidirectional twins — half boosts, half NERFS (resource removed / friction added)
— so an always-up policy fails half the pairs. The delta-derivation face trains
and is judged on both directions.**

## Isolation & naming

`data/run10/`, `out/run10/`, adapter `wrk_faceV_10_qwen`, threads `*_10_q*`,
scripts `run10_*`, judge sessions K/K2/L, backup `density_run10/run10_bundle.tgz`.
No generalist work this run (phase-one discipline). No name collisions with any
prior artifact — verified against runs 7/8/9/9b namespaces.
