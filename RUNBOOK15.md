# RUNBOOK 15 — the match (stage-gated), with the harness-fusion coach

**⚠ LABELED POST-HOC GATE AMENDMENT — the first in this program's history.**
Run 12's stage-1 seam gate demanded PERFECT fusion transcripts. Runs 13/13B/14
then measured that NO arm meets that standard — the plain generalist itself is
only 25-42% clean, and fidelity is not buyable at 4B by prompting, size,
repair, or training (the four falsifications). The gate was therefore measuring
the wall, not the thesis. **Amendment (authorized by Nikhil, 2026-08-10, with
run-14 data in view): fidelity becomes a RELATIVE, measured leg — the cube must
be at least as clean as the generalist baseline, judged same-run — instead of
an absolute perfection gate.** Recorded as post-hoc forever. Every OTHER bar in
this runbook is frozen before its data, as always.

**Question:** does the composed cube — specialists + dispatcher + motion loop +
harness-fusion coach — beat the SAME generalist model running naked? Same
weights on both sides; the machine is the only variable.

## The harness-fusion coach (industry pattern: faithful-by-construction)

Fusion is no longer a model skill (run-14 verdict); it is a COACH function:
1. **Template-slot assembly (code, zero free prose):** final speech =
   [update-settlement sentence, fixed template quoting the manifest's dead
   token + "revised accordingly", digit-free] + [MOTION body verbatim, minus
   its ESTIMATE line] + [contingency bridge, fixed template: "If {counterparty}
   responds as the read anticipates, the plan is already positioned for it; if
   not, nothing in the commitment depends on that prediction."] + [ESTIMATE
   line carried verbatim from motion]. Invented numbers, revived options, and
   prediction-as-fact are UNREPRESENTABLE in the added text by construction;
   residual risk lives only inside the motion segment itself.
2. **Advisory code check + bounded motion retry (≤2):** the run-13 checker
   (advisory role) screens the motion segment; flagged motions regenerate with
   specific feedback. NO judge in the production path — the judge only ever
   evaluates (MiniCheck-class local verifier is the future upgrade).

## Stages & FROZEN BARS

**Stage 0 — offline coach test ($0).** The assembler runs over run-14's stored
transcripts (184 problems of real segments). BAR: 100% of assembled speeches
pass the code checker's fidelity classes on the added text and carry the tagged
estimate; verbosity band 60-200 on ≥95%. Pure code iteration until green.

**Stage 1 — harness smoke (~$2: pod ~40 min + 48 judge reads).** The frozen 24
eval problems, fresh segments on the pod, two arms: COACH (assembled) vs
BASELINE (keep100 free fusion). Judge-everything, session U, cached.
**BARS: coach judge-clean ≥ baseline + 4 AND coach ≥ 15/24 (62.5%).**
Delivery + verbosity reported (a pass with delivery mean < 3.0 must say so).
FAIL → stop, report; the match does not run on an unproven harness.

**Stage 2 — the match (only on a stage-1 pass; ~$8-10; separate go).** Arms:
CUBE (full pipeline + coach) · GENERALIST (keep100 naked) · ABLATE (keep100 in
the V seat, inventory leg only). Legs per RUNBOOK12 stage 2, with fidelity
folded into the dossier/inventory judge calls (one read returns rubric scores
AND coherence): dossier 24 (B-rubric single, cube ≥ gen + 0.20) · inventory 32
(C-rubric hard caps, cube ≥ gen + 0.20 core AND resource_grounding ≥ gen) ·
motion 32 twins (Eval D2 bars verbatim, code-scored, $0) · general 48
(set-level, cube ≥ gen − 0.15) · **fidelity (amended leg): cube coherent-rate
≥ generalist's, same-run** · attribution: cube > ablate by ≥ 0.10 on inventory
or the V seat swaps to keep100. Reference ladder (reasoning models:
Qwen3-4B-Thinking twin, Qwen3.5-9B, gpt-oss-20b — seating confirmed at stage-2
go) runs LAST, dossier+inventory only, reported not gated, droppable.

## Budget & spend caps

Stage 0 $0 · stage 1 ≤ $2.0 (cap: 60 billed reads, driver aborts over cap) ·
stage 2 ≈ $8-10 (own caps at its go). Anthropic available ≈ $15.3; stage-1
worst case leaves ≥ $13 for the match. OpenRouter $0. All verdicts cached
(out/run15/judge_cache.jsonl); reruns re-bill nothing.

## Isolation & naming

`out/run15/`, scripts `run15_*`, judge sessions U (smoke) and V/W (match).
Certifier prompt byte-reused (Session-Q lineage). Eval problems: the frozen 24
(md5 b4c23eb357c9a6d9691f6c1fd50388d1). No training. No bench contamination.

*Frozen 2026-08-10 pre-spend. Stage 1 authorized; stage 2 requires its own go.*

## STAGE 0-1 RESULTS (2026-08-10, pod blonde_olive_shrimp A40; stage-1 cost ≈$1)

**Stage 0 PASS:** template assembly over all 184 stored run-14 relays — ZERO
flags added by the assembled text (183/183 with tagged estimates; the 1
estimate-less motion is the retry case), verbosity 100%.

**Stage 1 PASS — decisively:** frozen 24, fresh segments, judge-everything
(session U, 48 reads, cap 60):
- **COACH 21/24 clean (87.5%) · delivery 4.83**
- **BASELINE 5/24 clean (21%) · delivery 4.04**
- Bars (≥ base+4 AND ≥ 15/24): both cleared. Delivery IMPROVED under
  templating — the stiffness fear was backwards.
- Residual 3 failures: flaws inside the motion segment that passed the
  advisory code screen — the predicted residual surface.

**Conclusion: fusion is a coach function, not a model skill — measured.** The
wall (~21-42% free-prose clean across runs) is bypassed by construction at
87.5%. Completes the weights/harness symmetry with the run-11 motion-loop
discovery. **Stage 2 (the match) is UNLOCKED; awaiting Nikhil's separate go.**

## STAGE 2 OPERATIONAL SPEC (frozen 2026-08-10, pre-spend — go given by pod
## deployment; pod ordinary_pink_wolf, A100 SXM 80GB, 154.54.102.36:13412)

Scripts: `run15_match_pod.py` (ONE detached night job, laptop-free, resume-safe
JSONL; phases dossier → inventory → motion → general → refs) +
`run15_match.py` (local conductor: --setup/--launch/--status/--judge/
--judge-refs/--mock; keys never leave the laptop).

Frozen operational choices (all fixed before any output existed):
1. **Relay seats per RUNBOOK12:** audit(V) → read(F) → plan(V); ABLATE = same
   relay with keep100 in the V seat (read stays F); prompts byte-reused from
   run13b_pod SEG. Read-target string for unmanifested problems: "the other
   parties in this problem".
2. **Coach assembly (single-answer legs), zero free prose:** AUDIT + READ +
   PLAN-minus-estimate + fixed digit-free BRIDGE ("If the other side responds
   as the read anticipates…") + last tagged ESTIMATE verbatim. Missing estimate
   after one nudge retry → "ESTIMATE: 50%" injected + flagged, judged as-is.
3. **Generalist arm:** GEN_SINGLE prompt = the union of the three segment
   demands in ONE pass (same model, same information, same asks, no machine).
   Motion leg generalist = run-11 protocol byte-reused (PLAN_USER prior +
   REVISE_USER revision, keep100).
4. **Cube motion leg:** prior = its own inventory-phase PLAN segment; V-seat
   SEG["motion"] revision; scored by run11_score logic (code, $0).
5. **General leg:** dec_qwen decomposes ONCE per problem; the SAME
   facets/angles feed both arms; cube routes each angle via run12_router.route
   (problem + " " + angle); worker prompt = dav_eval_v5 WRK_USER byte-copied;
   both arms judged same-session with H.JUDGE_PROMPT (set-level).
6. **Single-answer rubrics:** B (run-9b) and C (run-10, hard caps kept) adapted
   set→single with the SAME dimension wording, plus the FOLDED coherence read
   ("coherent" bool + "flaws" list in the same JSON) — one read carries both
   the rubric leg and the amended relative-fidelity leg. Frozen in
   run15_match.py before any transcript existed.
7. **Judge discipline:** claude-sonnet-5, max_tokens 12000, no temperature,
   retry-on-empty, depth-walking JSON parse, cache keyed leg|arm|idx|md5 with
   mock/real wall, all-or-discard coverage per leg+arm. SPEND CAPS: thesis
   ≤ 260 billed reads, refs ≤ 180; driver aborts BEFORE billing when over.
8. **Reference ladder (reported, never gated, droppable):** generated at night
   ($0 marginal); judging is a separate morning decision against remaining
   Anthropic credits.

Read budget: dossier 24×2 + inventory 32×3 + general ≤48×2 = ≤240 thesis reads
(~$5); refs ≤56/model. Bench files deterministic from frozen sources
(md5s printed at --launch: dossier 5ddfae37c6be, inventory d7af325e4752,
twins 0ffccb899acc, general 9b6d00638993).

Dry run 2026-08-10: --mock exercised the ENTIRE path (bench build, motion
scorer, 240-item judge batch under cap, all six bars, scoreboard, refs table);
rerun hit 240/240 cache, re-billed zero. Pod pure functions unit-tested
(assembly last-estimate law, digit-free bridge, decomp parse, thinking-strip,
router reachability).

## STAGE 2 RESULTS — THE MATCH (2026-08-10/11, pod ordinary_pink_wolf A100;
## 240 judge reads ≈ $5; night job ran laptop-free, zero incidents)

**Scoreboard (2/6 legs):**
- **dossier: LOST** — cube 2.67 vs gen 2.59 (+0.08, bar +0.20). faceF's edge is
  real but under the bar on single answers.
- **inventory: LOST OUTRIGHT** — core_C cube 2.51 vs gen 2.73 (−0.22);
  resource_grounding 2.00 vs 2.09.
- **motion: LOST BY A HAIR** — parse 29/32 (bar 30), ack 22/32 (bar 24);
  boost 93.3%, nerf 100% (bars 75%). Direction handling remains excellent;
  the misses are estimate-line/citation mechanics. Gen arm nearly identical
  (31/32, ack 21/32) — ack is hard for both.
- **general: HELD** — cube 3.70 vs gen 3.71 (floor −0.15). Routing costs
  nothing on neutral ground.
- **fidelity (amended leg): WON on a tie** — coherent 0.054 vs 0.054. NOTE:
  the folded criterion (any unsupported specific = incoherent) is far stricter
  than Session-Q's certifier; spot-read of flaws confirms REAL inventions in
  both arms ("12-person engineering team", "$12,400 balance", dossier
  contradictions). The coach guarantees its ADDED text; the segments still
  invent. Same 4B disease as runs 10/12/13, same rate both arms.
- **attribution: FAILED — V SEAT SWAPS TO KEEP100** — cube−ablate core_C gap
  −0.10: keep100 in the V seat BEAT faceV_10. The provisional specialist is a
  net negative on its own home leg (consistent with run 10's failed bars).

**Honest verdict:** the composed cube with the current specialists does NOT
beat the naked generalist on specialist single-answer legs at 4B. What
survived, measured: relay/routing mechanics (general leg no-regression),
motion direction handling (93/100%), the coach fidelity function (stage 1),
faceF's small positive dossier edge. What failed: faceV_10 (actionable —
frozen spec executes the swap), the +0.20 specialist bars, ack/parse by 1-2.
Absolute B/C scores are NOT comparable to run-9b/10 set-level history
(single-answer judging is mechanically harsher); all comparisons here are
same-run relative, as designed. Reference-ladder transcripts generated at
night; judging them (~$3.5, 168 reads) is a separate decision.
