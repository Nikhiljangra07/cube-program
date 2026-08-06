# RUNBOOK 13 — the fusion wall test (cheap, code-instrumented, four spokesmen)

**Question:** run 12 stage 1 measured the integration-fidelity law on n=3 with a
$0.05-per-read judge: at 4B, every free-prose step integrating multiple prior
texts commits ~1 fidelity error per ~3 attempts. This run re-measures the wall
PROPERLY (n=24, code-instrumented, judge-calibrated) and tests three candidate
dissolutions — few-shot elicitation, a bigger spokesman, and checker-guided
detect-and-repair — before any training money (fork b) or gate amendment
(fork a) is considered. Nikhil's directive (2026-08-06): "make this properly —
filters and eval precise, checked from every angle: verbosity, code, delivery."

**Relation to the parked run-12 fork:** this run changes NO frozen gate. If a
dissolution arm passes, the fix is a new stage-1 fusion mechanism — a fresh
baton iteration submitted to the SAME frozen seam gate ("proceed unless
incoherent"), which run 12 already allowed to iterate. If all arms fail, the
wall is confirmed at n=24 and fork (c) gains the strongest possible evidence.

## Instruments (all frozen before any output)

### 1. Staged problems (data/run13/staged_problems.jsonl, md5 frozen at build)
24 deterministic template-generated decision problems (seed 13), 3 archetypes
× 8. Every fact PLANTED and manifest-known: a unique counterparty surname, a
unique dead-token codename option (e.g. "the Meridian option"), planted money/
time/date figures, a 2-event observed timeline (foresight material), and an
UPDATE that (a) kills the codename option explicitly and (b) changes one
number. Staging is what makes the checker mechanical — these are instruments,
not benchmark problems; no bench contamination (namespace run13, never trained).

### 2. The fidelity checker (scripts/run13_checker.py — code, $0, no opinion)
Five checks per speech, mirroring the three observed sin classes of run 12 plus
the two speech disciplines:
- **invented_number** — every digit token in the speech must exist upstream
  (problem ∪ update ∪ audit ∪ read ∪ plan ∪ motion), comma-normalized.
  (Run-12 iter-2 sin: invented metric.)
- **prediction_as_fact** — a sentence naming the counterparty with a past-tense
  event verb NOT present in problem/update text must carry a conditional marker
  (if/may/should/likely/...). (Iter-1 sin: hypothetical → fact upgrade.)
- **dead_option_revived** — the killed codename may appear only in a sentence
  that also carries a negation/supersession marker. (Iter-3 sin: revived
  superseded option.)
- **estimate_drift** — the speech's tagged `ESTIMATE: NN%` must equal the
  motion segment's (nothing changed between motion and speech; any move is
  invention). Missing tag = flag.
- **verbosity** — 60–200 words (delivery-sized speech; reported as its own
  dimension per Nikhil's verbosity angle, NOT folded into fidelity).
**Fidelity-clean** = zero flags in the first four classes. Checker ships with a
self-test (synthetic cases, one per sin class + clean) that must pass 8/8
before the pod runs.

### 3. Judge calibration (Session Q — the checker itself is on trial)
Stratified sample ≈ 26 speeches (≈10 checker-flagged + ≈10 checker-clean from
arms A/B/C + 6 arm-D finals). Sonnet (claude-sonnet-5, no temperature,
max_tokens 12000, retry-on-empty, all-or-discard) reads each BLIND to the
checker verdict: coherent true/false + flaw list + delivery 1-5 (readable,
complete, decisive speech). **INSTRUMENT VALIDITY BAR (binding for ALL claims):
checker↔judge agreement ≥ 80% AND miss rate ≤ 2/10 (checker-clean speeches the
judge finds incoherent).** If the instrument bar fails, NO arm claims are made
— the run reports instrument failure and stops. Program law upheld: the
verdict instrument is quoted verbatim in any lane it defines.

## Arms (segments shared; only the spokesman varies)

Per problem, one greedy relay on the trained seats produces audit(V) → read(F)
→ plan(V) → motion(V, absorbs UPDATE, ends `ESTIMATE: NN%`). Then:
- **A — baseline:** free fusion on keep100 (fact-discipline prompt, run-12
  iter-2 class). Measures the wall's true rate at n=24.
- **B — few-shot:** identical prompt + 2 hand-written exemplar speeches
  (elicitation-before-training, the run-11 lesson).
- **C — bigger spokesman:** Qwen3-14B (no adapter, non-thinking chat mode),
  identical prompt to A. Tests whether the wall is a 4B wall.
- **D — detect-and-repair:** arm A's speech → checker → on fidelity flags,
  deterministic retry with the specific violation appended to the prompt
  (≤ 3 attempts total). Tests whether the wall dissolves into harness
  engineering (the motion-loop precedent).

## FROZEN BARS

1. **Instrument validity** (above) — gates everything.
2. **Wall estimate (arm A):** fidelity-clean rate at n=24 with 95% Wilson CI.
   Wall CONFIRMED if clean-rate ≤ 70% (consistent with run-12's 2-in-3);
   wall QUESTIONED (n=3 was unlucky) if ≥ 85%.
3. **Dissolution — B or C:** fidelity-clean ≥ 21/24 (87.5%) AND ≥ arm A + 4
   problems.
4. **Dissolution — D:** ≥ 22/24 problems reach fidelity-clean within ≤ 3
   attempts AND the judge finds ≥ 5/6 sampled D-finals coherent.
5. **Verbosity (reported, soft):** ≥ 20/24 speeches in 60–200 words per arm.
6. **Delivery (reported):** judge delivery mean per arm from Session Q; no
   pass/fail bar (descriptive), but a dissolution claim with delivery mean
   < 3.0 must say so in the same sentence.

**Verdict grid:** any of bars 3/4 passes (with bar 1 valid) → propose new
stage-1 baton iteration with the winning mechanism to the unchanged frozen
seam gate; run-12 stage 2 unblocks only if THAT passes. All dissolution arms
fail + bar 2 confirms → wall stands at n=24; fork (b) is the only remaining
door besides (c), priced honestly. Bar 1 fails → instrument failure, no claims,
report and stop.

## Budget (≤ $3 total)

Pod: 1× 48GB card (A40 or RTX 6000 Ada), ~1–1.5h ≈ $0.5–1.4 (14B load included).
Anthropic Session Q: ≈26 reads ≈ $1–2. OpenRouter: **$0** (no generation — the
staged problems are template code, the exemplars are hand-written by us).

## Isolation & naming

`data/run13/`, `out/run13/`, scripts `run13_*`, judge session Q. No training,
no new adapters, no bench problems touched. Pod uploads: run13_relay.py,
run13_checker.py, staged_problems.jsonl (md5-checked), adapters wrk_faceF_9b_qwen +
wrk_faceV_10_qwen + wrk_keep100_qwen (run-9/10 bundle copies, md5-known).

*Frozen 2026-08-06 pre-spend. Awaiting local verification pass + Nikhil's GPU.*

## RESULTS (2026-08-06, pod live_lime_stork RTX 6000 Ada, 28 min, ≈$0.45 + Session Q ≈$0.5)

**BAR 1 INSTRUMENT: FAILURE — by the frozen rule, NO ARM CLAIMS.**
Agreement 12/20 (60%, needed ≥80%); miss 8/10 (needed ≤2); false-alarm 0/10.
The checker's PRECISION is perfect (every flag it raised, the judge confirmed)
but its RECALL is poor: the judge found flaws in 8 of 10 checker-clean speeches.

**What the checker cannot see (the expanded sin taxonomy, from the 8 misses +
3 incoherent D-finals):**
1. **Concept revival** — the dead option revived by PARAPHRASE, never by token:
   "exclusivity beyond July 9" after exclusivity is barred; "the deposit
   scenario" after the deposit track died. Regex sees the codename; the model
   revives the concept.
2. **Self-contradiction** — states X is eliminated, then plans with X in the
   next sentence.
3. **Prediction leakage at the concept level** — READ-only figures/mechanisms
   ($1,500 contingency, the addendum, the 48-hour falsifier) used as live
   decision branches; the counterparty+verb heuristic only catches the
   sentence-level version.
All three are SEMANTIC, not lexical — the exact class regex cannot reach.

**Unofficial observations (no bar standing, recorded for design honesty):**
- Arm A checker-clean 16/24 (67%) — but of the 10 checker-cleans the judge
  sampled, 8 were incoherent → the judge-strict wall is far WORSE than run-12's
  1-in-3 (point estimate of true clean rate ≈ 13% on the sampled stratum).
- Arm B (few-shot): checker-clean 12/24, WORSE than baseline — 18 revival
  flags; the exemplars taught "mention the dead option" more than "negate it."
- Arm C (14B): checker-clean 21/24 — but ZERO C speeches entered the
  calibration sample (deterministic sorted selection filled the clean stratum
  with arm A), so C carries NO judge evidence either way.
- Arm D (detect-and-repair): 19/24 checker-clean within 3, and 3/6 D-finals
  judged incoherent — repair converges only on what the checker can see.
- Delivery means 4.0-4.5 across arms: the speeches READ excellently while
  being subtly unfaithful. Fluency is not fidelity — the wall is invisible to
  surface quality.

**The run's real finding:** code is a valid PRE-FILTER (100% precision, $0)
but cannot CERTIFY faithfulness; certification requires semantic reading. Any
future fusion instrument must be hybrid: code filter first (free, kills the
lexical third of errors), judge certification second. A run-13b would need:
stratified calibration quotas per arm (fix the sorted-selection bias), and
either a judge-in-the-loop repair arm or a semantic checker (NLI/entailment).

**Cost actuals:** pod ≈$0.45 (28 min) · Anthropic Session Q ≈$0.5 · OpenRouter
$0. Bundle run13_bundle.tgz md5 a669c8b9 pulled + verified; pod safe to
terminate. Transcript, checker results, calibration all local in out/run13/.
