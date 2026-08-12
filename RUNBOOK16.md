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

## Budget & isolation

Stage 0 $0 (done) · stage 1 pod ~$2-3, API $0 · stage 2 pod ~$1 + ~30 judge
reads. RunPod ≈ $36, Anthropic ≈ $8.5-9.5, OpenRouter $0 (untouched, stays $3).
`out/run16/`, `data/run16/`, scripts `run16_*`, adapter `ver_16_qwen`.

*Stage 0 complete and bars frozen 2026-08-11, before any training spend.*
