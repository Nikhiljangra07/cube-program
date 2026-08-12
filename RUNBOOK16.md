# RUNBOOK 16 — the grounding verifier (the fidelity harness's missing organ)

**Question:** does verification train small at 4B — can a LoRA verifier catch
the invention disease (the measured wall that capped every arm of the run-15
match at ~2.5-2.7) well enough to gate the relay?

**Why this run, not specialist data:** the three-run law (10/11/14) says
generation-fidelity is not buyable by SFT at 4B; the match showed both arms
hallucinate identically and specialist edges drown under that noise floor.
MiniCheck (industry) says verification — unlike generation — DOES train small.
The weights/harness symmetry law says faithfulness lives in the harness; the
coach (run 15) guards its added text, and this verifier is the guard for the
free-prose segments. Cost fits the wallet: $0 data (mined from our own judge
caches), ~$3 GPU, ~zero API.

## Stage 0 — corpus assembly ($0, local) — COMPLETE 2026-08-11

`run16_corpus.py`: joined EVERY Sonnet-labeled (answer -> coherent/flaws) pair
the program has paid for, label-to-text verified by md5 against the cache key.
Sources & joins: run13b 77/77 · run14 harvest 331 + eval 48 (= cache 379/379)
· run15 smoke 48/48 · run15 match 144/144 coherence reads. Zero unjoined.

**Real pool: 621 unique (208 clean / 413 flawed), 2 label-conflicts dropped.**
Split by PROBLEM identity (no leakage; staged problems split identically across
sources): staged pids 20-23, run14 pids 140-159, match dossier idx 16-23,
match inventory idx 21-31 -> **eval = 109 real pairs (34 clean / 75 flawed),
synthetic NEVER enters eval.**

Train: 512 real + 522 seeded synthetic corruptions (seed 16, verified against
problem text before emission; classes: invented_number, invented_actor,
prediction_as_fact, dead_option_revival [manifest rows], self_contradiction)
+ clean rows oversampled x3 (else the 860:174 skew teaches "always flag").
Task format frozen: GROUNDED | "FLAGGED: <one-sentence reason>" (the reason is
the regen feedback for stage 2's repair loop).
md5s: train dfe880fc2863 · eval f2bbf2a4ea56 · real ab19283f6cfa.

## Stage 1 — train + measure (~$2-3 pod, $0 API) — FROZEN BARS

`run16_train.sh`: plain full-token SFT (NO band masking — the verdict string
IS the label), r64/alpha128, 2 epochs, Qwen3-4B base. `run16_eval.py` scores
the 109 held-out real pairs, code-only.

**BARS (both required): recall_flawed >= 0.75 AND recall_clean >= 0.70.**
Reference points: run-13 code checker semantic recall 0.20; all-flag baseline
recall_clean 0. Reported: per-source breakdown, malformed-output count.
FAIL -> report and stop; no stage 2 on an unproven verifier.

## Stage 2 — verifier-in-loop floor lift (own go, ~$1-2) — FROZEN BARS

Verifier gates the cube's ASSEMBLED answer (training distribution match);
FLAGGED -> regenerate the plan segment with the verifier's reason appended as
feedback, reassemble, recheck (<=2 rounds; judge-free production path). Rerun
the 32-problem inventory leg cube arm; judge those 32 (~$0.75; baselines
already cached from the match).
**BARS: coherent-rate(cube+verifier) >= 0.20 AND core_C >= match-cube + 0.20.**
Expectation calibration: judge-in-loop repair ceiling was 19/24 (run 13B); a
local verifier will be below that ceiling.

## STAGE 1 RESULTS (2026-08-11, pod creative_olive_fowl RTX 6000 Ada, ~$1)

Train: 796s, loss 0.327, token-acc 0.975 (after OOM fix b024f0e: bs2/accum4/gc
— TRL 1.9 fp32 logits on 151k vocab). Eval on the 109 held-out real pairs:
**recall_flawed 0.907 (68/75, bar 0.75) — verification DOES train small at 4B
(code-checker reference: 0.20). recall_clean 0.382 (13/34, bar 0.70) — FAIL.**
Malformed 0. **STAGE 1 FAIL per frozen bars; stage 2 blocked.**

**Diagnosis (per-source FP autopsy):** 16/21 clean false-positives are run14
harvest cleans. The gold is TWO-RULER: runs 13B/14/15smoke cleans were
certified under the lenient Session-Q criterion (3 sin classes); the match
cleans under the strict folded criterion (any unsupported specific). The
verifier learned ~the strict ruler; spot-reads show its "false" flags on
lenient-certified cleans are often true strict-criterion sins (e.g. prediction
treated as actionable fact). The instrument may exceed its report card.

## 16B — INSTRUMENT REBUILD (labeled, frozen 2026-08-12 pre-read)

Single-ruler relabel. Criterion law: **strict ⊇ lenient** (every Session-Q sin
class is also a strict-criterion sin), therefore ALL flawed labels (488)
survive unchanged; ONLY clean labels are ambiguous and get relabeled under the
strict criterion (the same coherence fold the match used and stage 2 will
use — one ruler end to end):
- eval cleans (34): INDIVIDUAL Sonnet reads — eval gold stays pristine.
  Cleans that fail become FLAGGED gold with the returned reason. NOTE: the
  surviving clean-eval n will be small (~10-20); recall_clean granularity
  coarsens; reported with counts, bars unchanged.
- train cleans (174): batched reads, ≤3 answers of the SAME problem per call
  (training labels tolerate batching; eval never batched). Fails become
  FLAGGED train rows with reasons; passes stay GROUNDED, oversampling
  recomputed to balance.
- synthetics unchanged (strict-criterion by construction).
**BARS UNCHANGED: recall_flawed >= 0.75 AND recall_clean >= 0.70.**
Judge discipline: claude-sonnet-5, max_tokens 12000, no temperature, cached
(out/run16/relabel_cache.jsonl), spend caps: eval 40 reads / train 80 calls.
Est. cost ≈ $1.9 Anthropic + ~$0.5 pod retrain.
(Batching amendment at execution: train cleans spread over 141 problems —
same-problem batching degenerates to singletons — so train batches are ≤3
MIXED problem+answer cases per call, judged independently. Eval unchanged.)

**RELABEL RESULT (2026-08-12, 92 calls ≈ $1.9): of 208 lenient-clean rows,
only 73 survive the strict ruler; 135 flip to FLAGGED.** The two-ruler
diagnosis is confirmed at scale — 65% of the old clean gold was lenient-ruler
artifact, so v1's recall_clean 0.382 was measured against majority-wrong gold.

**LABELED SPLIT AMENDMENT (pre-v2-training):** strict relabel left only 7
clean EVAL rows — unmeasurable against a 0.70 bar. 12 clean-bearing problems
moved train->eval (deterministic md5 order, whole problems, before any v2
training — v16B trains fresh from base, so nothing it trains on enters eval).
**v2 corpus: train 956 rows (53 strict cleans x7 oversample + 426 real flawed
+ 159 synthetic; md5 fffd7d59c573efcfc7aec8506b81bc2c) · eval 142 rows
(20 clean / 122 flawed; md5 95dc5c91f6d4e19945d7920def378521). Bars unchanged;
recall_clean now measured on 20 rows (>= 14/20).**

## 16B RESULTS (2026-08-12, pod happy_emerald_gibbon A40, ~$0.4)

Single-ruler gold, bars unchanged: **recall_flawed 0.967 (118/122) — up from
0.907. recall_clean 0.40 (8/20) — FAIL AGAIN, and this time against clean
gold.** Malformed 0.

**Autopsy: all 12 clean false-positives are ONE mistake** — the verifier flags
LEGAL mentions of eliminated options ("mention only to note it is gone", which
the fusion discipline REQUIRES) and LEGAL conditional read references ("if
they respond as anticipated") as revival/leak sins. Shortcut learning traced
to the synthetic corpus: revival corruptions made the dead token's PRESENCE
the discriminative feature; the corpus contained zero counter-examples
teaching presence-vs-liveness. A data bug, not (yet) a capacity verdict.

## 16C — COUNTER-CLASS REBUILD (frozen 2026-08-12, $0 data + ~$0.4 pod)

Add LEGAL-MENTION synthetic GROUNDED rows (208): the SAME dead tokens and the
SAME counterparties as the corruptions carry, in their legal forms (gone-and-
unused; conditional positioning) — the only difference between a flagged and a
grounded twin is the liveness phrasing itself. Classes balanced 522:585 via
x2 reps (oversample formula now includes the counter-class). Eval gold
UNTOUCHED (md5 95dc5c91… identical). **BARS UNCHANGED.** If 16C also fails
recall_clean, the verdict is recorded as a 4B capacity limit on the
mention-vs-liveness discrimination and the run stops.
train_v3 md5 402b1e9ae83e890fc83f04cdd24e5871.

## Budget & isolation

Stage 0 $0 (done) · stage 1 pod ~$2-3, API $0 · stage 2 pod ~$1 + ~30 judge
reads. RunPod ≈ $36, Anthropic ≈ $8.5-9.5, OpenRouter $0 (untouched, stays $3).
`out/run16/`, `data/run16/`, scripts `run16_*`, adapter `ver_16_qwen`.

*Stage 0 complete and bars frozen 2026-08-11, before any training spend.*
