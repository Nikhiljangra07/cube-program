# RUNBOOK 13B — fusion wall, hybrid instrument (the three fixes + observability)

**Question:** run 13 died by its own instrument bar — the code checker has 100%
precision but misses SEMANTIC sins (concept revival, self-contradiction,
prediction leakage). 13B applies the three known fixes and re-asks the two live
questions with an instrument that can actually answer them:
(1) **is the wall a 4B wall?** (14B spokesman, this time judge-certified), and
(2) **does the wall dissolve into harness engineering when the detector is a
judge instead of a regex?** (judge-in-loop repair).
Nikhil's directive (2026-08-07): fix it properly, build an observability layer
— "the knowledge is what gives us what to do for the next one."

## The three fixes (from run-13's autopsy, all frozen here)

1. **Hybrid instrument.** Code filter first (run13_checker verbatim — proven
   100% precision, $0): any code flag = DIRTY, no judge read needed. Speeches
   the code calls clean go to JUDGE CERTIFICATION — Sonnet reads them with the
   Session-Q prompt (byte-reused from run13_calibrate.py; the verdict
   instrument is quoted verbatim, program law). **Hybrid-clean = code-clean AND
   judge-coherent.** Precision spot-audit guards the shortcut: 6 code-flagged
   speeches (quota: 2 per arm A/C/D') are also judge-read; if <5/6 confirmed,
   the shortcut is revoked and EVERYTHING gets judge-read (cost note, not a
   stop).
2. **Per-arm quotas.** No sorted-selection bias anywhere: every certification
   and audit sample is quota'd per arm by construction. Arm C cannot escape
   judge evidence this time.
3. **Judge-in-loop repair (arm D').** Attempt 1 = arm A's speech. If dirty
   (code flag OR judge-incoherent), the retry prompt carries BOTH the code
   feedback and the judge's named flaws verbatim. ≤3 attempts total. Tests
   whether adequate detection turns the wall into a retry-cost problem.

**Dropped: arm B (few-shot).** It lost to baseline on the code layer alone
(12/24 vs 16/24, 18 revival flags — exemplars taught mention-not-negate); the
hybrid layer is strictly harsher. No path to a dissolution bar. Recorded, not
re-run.

## Design

- **Problems:** the 24 frozen staged problems, byte-identical (md5
  b4c23eb357c9a6d9691f6c1fd50388d1). Never trained, reused.
- **Fresh single-pod dataset:** ALL segments and speeches regenerate on the 13B
  pod (greedy). No cross-pod byte-identity assumption — run-13 outputs are not
  reused as data, only as design evidence. One pod, one coherent dataset.
- **Arms:** A (baseline keep100 fusion) · C (Qwen3-14B fusion, non-thinking) ·
  D' (judge-in-loop repair of A). Segments shared across arms per problem.
- **Repair mechanics:** driver (local) pulls speeches, filters+certifies,
  writes feedback_r{2,3}.json {pid: feedback}; pod regenerates ONLY listed
  pids with the feedback appended (greedy). Keys never leave the local machine
  — the pod never sees an API key.

## FROZEN BARS

1. **Precision spot-audit:** at most ONE audited code flag unconfirmed (≥5/6
   at full quota, scaling down if fewer speeches were flagged) → shortcut
   stands; else judge-everything fallback (run continues, cost noted).
2. **Wall measurement (arm A, official):** hybrid-clean rate at n=24 with 95%
   Wilson CI. This is a MEASUREMENT (no pass/fail) — it replaces run-12's
   n=3 and run-13's uninstrumented estimate as the program's number for the
   wall. Reported beside it: lexical-vs-semantic split of every flaw.
3. **C-dissolve (size):** C hybrid-clean ≥ 18/24 AND ≥ A + 8 → the wall is a
   4B wall; propose run-12 stage-1 rerun with a 14B fusion seat (frozen seam
   gate unchanged).
4. **D'-dissolve (harness):** ≥ 20/24 problems reach hybrid-clean within ≤3
   attempts → the wall is an engineering problem given semantic detection;
   propose stage-1 rerun with judge-in-loop coach (with the honest note that a
   production coach then carries a per-speech judge cost).
5. **Verbosity (soft):** ≥ 20/24 in 60–200 words per arm. **Delivery
   (reported):** judge delivery mean per arm; any dissolution claim with mean
   < 3.0 must say so in the same sentence.

Coverage law: judge sessions are all-or-discard per round. Judge verdicts are
CACHED keyed (arm, pid, attempt, md5(speech)) — the run-11 cache law; a rerun
never re-bills a recorded verdict.

## Observability layer (deliverable, not a bar)

- **events.jsonl** — every stage emits structured events: generation (arm,
  pid, attempt, seconds, words), code filter (flags), judge (verdict, flaws,
  delivery, cached?), repair (round, feedback size), cost (per judge call).
- **report.html** — self-contained local page built from the events + data:
  run summary and bar verdicts; per-arm scoreboards; the sin taxonomy
  histogram split lexical (code-caught) vs semantic (judge-caught); repair
  trajectories (attempt 1 flaw → feedback → attempt 2 …) for every D'
  problem; per-problem drill-down showing the full relay chain and every
  speech attempt with its flags inline; cross-run wall history (run 12 n=3 →
  run 13 unofficial → 13B official). The knowledge layer for run 14.

## Budget (≤ $3)

Pod ~1h ≈ $0.5–0.9 (relay ~30 min + 2 repair rounds ~10 min + driver wait).
Anthropic ≈ $1–1.5: ~16–24 certifications × arms + spot-audit 6 + D' rounds
(~40–60 reads at ~$0.01–0.02, all cached against reruns). OpenRouter **$0**.

## Isolation & naming

`out/run13b/`, scripts `run13b_*`, judge session R (certification+audit,
cached). Same three adapters (only keep100 used for fusion; F/V for segments),
same staged problems. No training. Pod uploads: run13b_pod.py,
staged_problems.jsonl, adapters (as run 13).

*Frozen 2026-08-07 pre-spend. Awaiting build verification + Nikhil's GPU.*

## RESULTS (2026-08-07, pod lonely_pink_toucan A40, relay 33 min; total ≈$1.6)

**Bar 1 (spot-audit): FAILED — 4/6 code flags confirmed → shortcut revoked,
judge-everything fallback executed as frozen** (26 rows re-read, 20 billed;
cleanliness decided by the judge alone, code flags demoted to advisory). Run-13's
"code precision 100%" did not replicate on fresh speeches: 2/6 audited flags were
judge-dismissed. Code is a useful pre-screen, not even a trustworthy dirty-verdict.

**Official judge-only verdicts (n=24 per arm):**
- **Bar 2 — THE WALL (arm A, 4B baseline): 6/24 clean = 25% (CI 12–45%).** The
  program's official wall number. Fluent throughout (delivery 4.42) — the flaws
  are invisible to surface reading.
- **Bar 3 — size (Qwen3-14B spokesman): 13/24 (54%). FAIL** (needed ≥18 and
  ≥A+8=14; missed both, the relative leg by one). Size HELPS (+29 points) but
  does not dissolve the wall — 3.5× the parameters halves the error rate,
  nothing more.
- **Bar 4 — judge-in-loop repair (D'): 19/24 within ≤3 attempts. FAIL by ONE
  problem** (bar 20). Trajectory: 6 clean at attempt 1, +11 at attempt 2, +2 at
  attempt 3, 5 never clean. Repair fixed 13/18 dirty speeches (72%) once the
  detector could see semantically — vs run-13's code-guided repair which fixed
  only what regex saw. Diminishing returns are sharp (11 → 2), and a 5-problem
  hard core resisted three semantically-informed rewrites.
- Delivery RISES with repair (4.79) and with size (4.75) — quality and
  fidelity remain uncorrelated.

**Per the frozen grid: no dissolution bar passed → the run-12 seam gate stays
blocked; no stage-1 rerun is proposed from this run.** The near-miss is recorded
as a near-miss, not promoted — the program does not bend bars after seeing data.

**What 13B settles (the knowledge layer):**
1. The wall is now measured properly: 25% clean at 4B, 54% at 14B — deep, real,
   and only weakly size-dependent. Not a prompting artifact, not a 4B quirk.
2. Semantic detection + retry is the strongest known lever (72% repair rate) but
   plateaus by attempt 3; the residue is a hard core, not noise.
3. Deterministic lexical checking does not transfer across speech distributions
   (100% precision on run-13 speeches → 67% on 13B speeches). Any production
   gate needs the judge, full stop.
4. Delivery/fluency carries zero signal about fidelity (4.4–4.9 across all arms).

**Fork (Nikhil's, recorded):**
(a) 13C micro-iteration: raise repair cap to 5 attempts + fresh-rewrite-on-
    attempt-3 (new frozen bar, ~$1.5) — justified by the 19/20 near-miss ONLY
    if he judges the trajectory evidence worth one more cheap shot;
(b) fork (b) proper — train the fusion adapter (~$10–15, now with the option of
    mining integration exemplars from open data + judge-certifying them);
(c) accept the wall as measured and write up runs 7–13B (the arc is complete
    and publishable: mechanics + routing + motion + specialists + a
    properly-instrumented wall).

**Cost actuals:** pod ≈$0.35 (42 min A40) · Anthropic ≈$1.2 (51 judge reads
across session R incl. judge-everything) · OpenRouter $0. Observability:
out/run13b/report.html (147KB, self-contained), events.jsonl (full trace),
judge_cache.jsonl (51 verdicts, rerun-free). Pod safe to terminate.
