# RUNBOOK 17B — the marking test + the rival (2026-08-15)

**Two questions, one run, full observability:**

1. **The marking test (17B proper).** Run 17 located the wall in ASSERTION
   POLICY: the model fabricates needed specifics AS FACTS instead of marking
   them. The strict ruler explicitly allows conditional/proposed content. If a
   GROUNDING DISCIPLINE prompt (every specific = quoted / derived-with-basis /
   proposed-and-marked) moves strict-clean off zero, the wall is
   prompt-fixable, not capacity.
2. **The weight-class match (Nikhil's proposal).** Same 40 problems, same
   judge, same weight class: our harnessed 4B vs an open-source REASONING
   sibling — **Qwen3-4B-Thinking-2507** (identical Qwen3-4B lineage, thinking
   variant). This isolates "reasoning training" vs "our harness + marking
   prompt" at identical base capacity. Run 17's cached keep100 answers are the
   FREE third arm (baseline, already judged: 0/40 clean).
3. **The verifier rider (stagnant-layer thesis).** The $0 flaw audit
   (2026-08-15, cached run-17 verdicts) settled the gold half: Sonnet is NOT
   stagnant — it computed date gaps itself (pid 24: flagged "10-day buffer"
   as actually 15 days) and 0/176 flaws were correct derivations mis-flagged.
   The 4B verifier half is unmeasurable until gold-clean answers exist. This
   run should produce some — then ver_16_qwen's false-flag rate on them
   finally measures the stagnant-verifier thesis.

## Design (frozen before any GPU or judge spend)

- **Problems:** the run-17 ladder verbatim, all 40 (5 levels x 8),
  md5 95a293bba2d2583d10edb0f45fed1605. No new problems.
- **Arm M (marked):** keep100 generalist, GEN_SINGLE + GROUND block (frozen in
  run17b_pod.py): every specific must be (a) QUOTED, (b) DERIVED with basis
  shown inline, or (c) PROPOSED and explicitly marked. Greedy, max_new 600.
- **Arm R (rival):** Qwen/Qwen3-4B-Thinking-2507, SAME system + user prompt
  (including GROUND — fairness), vendor-recommended decoding (temp 0.6,
  top_p 0.95, top_k 20 — the model card warns greedy causes repetition
  loops; per-item seed 1700+pid for reproducibility). Thinking stripped via
  special-token decode + last `</think>` split (gpt-oss lesson). max_new 4096.
- **Arm B (baseline):** run 17's cached keep100 answers + cached verdicts. $0.
- **Verifier pass:** ver_16_qwen renders GROUNDED/FLAGGED on all 80 new
  answers, run-16 prompt verbatim, pod-side, $0.
- **Gold:** STRICT_ONE byte-reused (same ruler as runs 15/16/17). 80 new
  reads, cached, SPEND CAP 90.

## FROZEN READOUTS

1. **PRIMARY — marking bar:** arm M strict-clean **>= 4/40 (10%)** → the wall
   is relocated to assertion policy (harness-fixable). Below 4/40 → marking
   alone does not open the island; record honestly.
2. **THE MATCH:** per-arm, per-level clean-rate + total flaw count. Reported
   both directions; no seat/stakes attached — observability run.
3. **VERIFIER RIDER:** pooled gold-clean answers across arms M+R; if >= 5
   exist, ver_16 false-flag rate on them. **FP > 30% → stagnant-verifier
   thesis CONFIRMED** (it flags legitimately-moving answers); FP <= 30% on
   >= 5 cleans → the v1 verifier survives its first fair test.
4. **Autopsy dump:** every flaw on arms M and R printed with planted tokens
   (same $0 classification method as the run-17 audit).

## Budget & isolation

Pod: keep100 + ver_16_qwen upload (~1.05GB) + rival download from HF (~8GB).
Gen 40 marked (~10 min) + 40 rival (thinking, the slow arm) + 80 verifier
passes. RTX 6000-class recommended for the thinking arm's long generations
(~40-60 min total, <= ~$1); A40 works at roughly double wall-clock. Judge: 80
reads ~= $1.8 (cap 90). Total ~= **$2.5-3**. Wallets at freeze: Anthropic
~= $5.5 · RunPod ~= $30 · OpenRouter $3 (untouched).
`out/run17b/`, scripts `run17b_*`. No training this run.

*Frozen 2026-08-15 pre-spend. Prompts, arms, decoding, bars, and caps set
before any pod or judge dollar. Decoding note recorded at freeze: arm M keeps
the program's greedy law; arm R uses its vendor's published operating spec —
running a thinking model greedy against its own card would sandbag the rival
and invalidate the match.*

## RESULTS (2026-08-15, pod confused_moccasin_orca RTX Pro 6000 Blackwell, ~$1.5 pod + ~$1.8 judge)

**Rival-arm repair (amendment, run-15 refs-fix precedent):** 24/40 rival
answers hit max_new 4096 mid-thinking and never closed `</think>` — the stored
"answer" was raw deliberation. run17b_fix.py regenerated them (max_new 9000,
retry 13000, same seed law), 0 residual leaks, verifier re-rendered. Judged
transcripts are all clean finals.

**Scoreboard (STRICT_ONE, 120 judged answers):**

| arm | model | clean | flaws | L1..L5 flaws |
|---|---|---|---|---|
| B | keep100 baseline (run 17, cached) | 0/40 | 176 | 59/34/26/25/32 |
| M | keep100 + GROUND discipline | 0/40 | 170 | 46/45/27/23/29 |
| R | Qwen3-4B-Thinking-2507 + GROUND | 0/40 | 124 | 33/28/22/22/19 |

- **PRIMARY: FAIL.** Arm M 0/40 (bar was >= 4/40). But the mechanism is
  decisive: compliance analysis shows the models DID NOT EXECUTE the
  discipline — M used proposal-marking in 4/40 answers, showed a derivation
  basis in 2/40; R: 13/40 and 5/40. R even dressed inventions AS derivations
  ("15-day window (August 10–25)" — August 10 appears nowhere). The
  assertion-policy wall is real, but it is NOT prompt-fixable at 4B: the
  models cannot hold the grounding discipline while planning. Same shape as
  run 16's lesson (detection trains small; certification doesn't): the
  DISCIPLINE does not fit in the weight class.
- **THE MATCH: the wall is weight-class-wide.** The reasoning-trained sibling,
  on vendor decoding, with the same grounding prompt, also scores 0/40
  strict-clean. Reasoning training buys ~30% fewer flaws (124 vs 170-176,
  monotone across levels) — better, never clean. Our harness is not the
  bottleneck; the 4B class is. (Also: thinking cost ~25x the tokens per
  answer for that 30%.)
- **VERIFIER RIDER: unmeasurable AGAIN — now for a deeper reason.** Zero
  gold-clean answers exist anywhere in the 4B weight class (120/120 flawed
  across three arms). Verifier recall on flawed: 99% (M 39/40 + R 40/40
  flagged). Its false-positive rate remains undefined — not because the run
  was unlucky, but because strict-clean 4B answers may effectively not exist
  to be falsely flagged. The stagnant-verifier thesis stays open and may be
  untestable inside this weight class.
- **Observability delivered:** full autopsy dump (every flaw beside its
  problem's planted tokens) in out/run17b/ and the scorer output. Flaw texture
  identical across arms: unmarked invented specifics (dates, dollar figures,
  windows, actors) — the rival's are fewer but the same species.

**Program consequence:** three walls now triangulate the same point — the
strict-fidelity island at 4B is empty-to-negligible for training (runs 7-15),
gating (run 16), prompting (17B), and even for a reasoning-trained sibling
(the match). The wall is a property of the weight class under this criterion,
not of our data, harness, or adapters. Next forks: raise the weight class,
relax the criterion to lenient+marked, or move verification to claim-level
external checking (DRAFT2 fork e).

## RULER-T REANALYSIS (2026-08-15, $0, labeled post-hoc reanalysis — strict verdicts above stand unchanged)

**Nikhil's directive: match the ruler to the weight class.** Guardrail applied:
stratify, don't lower — flaws classified by severity from the cached judge
prose (taxonomy anchored in RUNBOOK17's frozen addition/distortion split):
- **T1 FATAL** (96 flaws): self-contradiction, given-fact distortion, stated-
  constraint violation, temporal error, miscalculation, misattribution.
- **PRED** (35): likely-reaction asserted as settled fact.
- **ADD tolerated** (325): invented-but-consistent specifics — the class every
  human advisor produces ("open at $45,000"). 14 OTHER flaws treated as fatal
  (conservative). Regex classifier + spot-read verification.

**Scoreboard under the matched ruler (RULER-T = no fatal, no PRED, no OTHER):**

| arm | strict | RULER-T | T-loose (PRED tolerated) |
|---|---|---|---|
| B baseline | 0/40 | 8/40 (20%) | 14/40 (35%) |
| M ours + GROUND | 0/40 | 5/40 (13%) | 8/40 (20%) |
| R Thinking + GROUND | 0/40 | **15/40 (38%)** | 19/40 (48%) |

1. **The island opens at the matched wavelength.** 4B models CAN produce
   realistically-clean strategic answers 20-38% of the time. The strict-empty
   island was a criterion artifact plus a real fatal-flaw rate — now separable.
2. **The match has a winner under RULER-T: the reasoning rival, ~2x baseline**
   (38% vs 20%). Reasoning training buys realistic cleanliness, not just fewer
   decorations. Honest and useful: at matched criterion the rival IS better.
3. **GROUND hurt our model** (5/40 vs baseline 8/40) — the marking prompt adds
   instruction load without compliance. Drop it from our arm going forward.
4. **STAGNANT-VERIFIER THESIS CONFIRMED (Nikhil, 2026-08-15): ver_16 false-
   flags 96% of RULER-T-clean answers (27/28; 98% on T-loose).** The layer is
   tuned to the strict wavelength (near-all-flag); against realistically-clean
   moving answers it is useless as a gate. First measurable FP rate in the
   program — his "layer is stagnant, our questions are moving" was right at
   the verifier level (gold level had been refuted separately).

**Recorded fork (run 18 candidate, ~$1-2): retrain the verifier as a FATAL-
FLAW detector on RULER-T labels (T1-only). Run 16 proved detection trains
small (0.99); the failed certification target may simply have been the wrong
wavelength. Labels derivable $0 from existing caches. A working T1-gate +
20-38% base clean-rate makes gated-regeneration arithmetic viable for the
first time (E[attempts to clean] ~ 3-5).**
