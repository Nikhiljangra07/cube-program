# RUNBOOK 12 — the first cube prototype (relay + coach + motion loop)

**Question:** does the composed cube — two specialists + generalist + rule
dispatcher (coach) + coach-fusion + motion loop — beat the generalist alone on a
mixed bench, with honest per-seat attribution? Nikhil's verdict philosophy for
this run: "weigh how much we failed and how much we succeeded, then optimize the
next step" — per-leg reporting, no all-or-nothing collapse.

**Architecture (extracted from Nikhil's dispatcher doc, 2026-07-31, only the
elements the prototype needs):**
- **Topology (settled, §5):** runner → coach → runner. Runners never hand to each
  other; the coach owns every seam.
- **Path B (settled, §3):** pre-assignment dispatcher, segment-level; modularity
  kept. Per-token shuffling = Path A, rejected in the doc itself (joint-training
  prerequisite). The relay turns at THOUGHT boundaries, not token boundaries.
- **Rigid governor (§10):** dispatcher v1 is deterministic rules + generalist
  fallback + segment cap. The trained dispatcher-adapter is deferred (doc §9:
  only after probe + handoff results define what it must do).
- **Probe result (§8, run 2026-07-31 on real bench problems):** segments tile
  cleanly (audit→V, counterparty-prediction→F, re-plan→V) EXCEPT the final
  estimate, which is irreducibly two-colored (held + predicted → %). Resolution:
  **fusion-at-coach** (third option beyond the doc's top-1/top-2): runners stay
  single-colored; the coach's final assembly presents both seats' outputs and
  elicits one synthesis ending in the derived percentage (anchored-elicitation
  protocol, validated 93-100% in Eval D v2). Top-2 weight-blend
  (peft add_weighted_adapter) reserved as the §6 amendment if fusion seams.
- **Superseded, not carried in:** book foundations / Shumailov raw-text guard /
  generator-gate distillation test (overtaken by runs 8-11: book-grounding
  falsified, gates now bench-verbatim + audit-all).

**Seats:** faceF_9b (foresight, certified — Eval B +1.06) · faceV_10 (viability,
PROVISIONAL — failed run-10 specialist bars; best motion behaver; must earn the
chair via ablation) · keep100 (generalist + fallback). Decomposer dec_qwen
unchanged. Base Qwen3-4B-Instruct-2507.

## Pipeline

problem → dec_qwen decomposes → DISPATCHER v1 routes each segment/angle
(F-markers → faceF_9b; V-markers → faceV_10; none → keep100) → runners write in
isolation (peft set_adapter hot-swap) → outputs return to coach → [UPDATE
arrives] motion loop (prior + update + anchored estimate → re-derive) → COACH
FUSION: both seats' outputs in view → one synthesis ending `ESTIMATE: NN%` →
cube answer.

## Dispatcher v1 (two tiers, frozen)

- Tier 1 (structural): "OBSERVED OVER TIME:" → F · "WHAT YOU HOLD:" → V —
  honest for harness-rendered problems (our own render strings).
- Tier 2 (semantic, for unmarked text): dated-observation-list + behavior-verb
  density → F · resource/budget/deadline/personnel enumeration density → V ·
  neither above threshold → generalist. Deterministic scoring, no LLM.

## Stages & FROZEN BARS (all bars set here, before any output)

**Stage 0 — router offline test ($0, local).** 104 known-type problems (48 v5 →
generalist, 24 dossier → F, 32 inventory → V), MARKERS STRIPPED (tier-2 must
carry it; tier-1 alone would be a tautology). BAR: ≥ 94/104 (90%) correct.
Fail → fix rules (code iteration, still $0); no GPU until passed.

**Stage 1 — single baton pass (~$0.30, one A40, ~30 min).** 3 problems (one per
type) through the full per-segment relay: F-segment → coach → V-segment → motion
update → fusion. BARS: (a) Qwen hot-swap outputs byte-identical to fresh-load
outputs on identical prompts (greedy), swap median < 50ms (granite precedent
6.3ms); (b) fusion answer contains both facets + tagged estimate (descriptive
seam gate: proceed unless incoherent — one Sonnet read, ~$0.05, reported).

**Stage 2 — scaled eval (~$1 pod + ~$7 Anthropic).** Arms: CUBE ·
generalist-alone · CUBE-ablate (keep100 in the V seat). Legs, each frozen:
1. **Dossier leg (24):** single-answer variant of the B rubric (5 dims, same
   wording adapted from set→single, frozen in judge_run12.py before any output).
   BAR: cube ≥ generalist + 0.20 overall.
2. **Inventory leg (32):** single-answer variant of the C rubric (hard caps
   kept). BAR: cube ≥ generalist + 0.20 on core-C-single AND resource_grounding
   ≥ generalist.
3. **Motion leg (16 boost + 16 nerf twins through the cube's native loop):**
   the Eval D2 bars verbatim — parse ≥ 30/32, boost ≥ 75%, nerf ≥ 75%,
   ack ≥ 24/32.
4. **General leg (48, regression guard):** cube's routed 4-thread sets judged by
   sonnet_judge (set-level, comparable to keep100's sets). BAR: cube overall ≥
   generalist − 0.15.
5. **Attribution:** cube > cube-ablate on the inventory leg by ≥ 0.10 for
   faceV_10 to keep the seat; else the seat swaps to keep100 and the report says
   so plainly.

**Verdict philosophy (Nikhil):** per-leg scoreboard, weighed honestly — how much
failed, how much succeeded, optimize the next step. No silent averaging across
legs; a partial cube is reported as exactly which legs it won.

## Budget

Stage 0 $0 · stage 1 ~$0.35 (pod + one Sonnet read) · stage 2 ~$1 pod + ~$7
Anthropic · OpenRouter $0 (all problems exist, frozen, reused). Total ≈ **$8.5**.

## Isolation & naming

`out/run12/`, scripts `run12_*`, judge sessions O (stage-1 seam read) and P
(stage-2 legs). No new adapters trained this run. Bundle
`density_run12/run12_bundle.tgz`.

*Frozen 2026-07-31 pre-spend.*

## RESULTS — Stage 0 + Stage 1 (2026-07-31)

**Stage 0 PASS:** dispatcher v1 94/104 (bar 94) on marker-stripped problems after
3 tuning rounds. Fingerprints: V = enumerated money figures (med 7 vs 0/0.5);
F = timeline + observed-behavior verbs; G = no timeline (max 0 dates on dev).
All residual errors route toward a competent seat.

**Stage 1 — mechanics PASS, semantics FAIL the frozen seam gate (3 iterations):**
- Mechanics (every iteration): swap median 11.8ms (bar 50), hot-swap outputs
  byte-identical to fresh loads, all relays structurally complete, tagged
  estimates throughout, segments visibly consuming predecessors. **The relay
  machine works.**
- Seam reads (Session O, strict Sonnet, 3/3-clean required): INCOHERENT ×3.
  - iter 1: fusion upgraded the read's hypotheticals into facts (all 3 problems).
  - iter 2 (fact-discipline prompts): upgrade-disease cured (F relay SEAM OK);
    new flaws — one invented metric, one stale pre-update fact.
  - iter 3 (rigid-coach assembly — motion text + estimate carried verbatim by
    code, only a digit-free 2-sentence bridge generated): flaws moved into the
    remaining free-prose: bridge revived a superseded hypothetical (V), motion
    itself misattributed the update (G), fusion reassigned an actor (F).
- **The measured law (converges with run 10's structure-vs-fidelity):** at 4B,
  every FREE-PROSE step that must faithfully integrate multiple prior texts
  commits ~1 fidelity error per ~3 attempts, regardless of prompt engineering.
  Three iterations narrowed the free surface (whole fusion → bridge only) and
  the error rate per surface stayed. The cube's floor is integration fidelity,
  not mechanics, routing, or specialist quality (specialist segments were clean
  in nearly all reads).
- **Stage 2 NOT run** — the frozen gate ("proceed unless incoherent") binds; the
  program does not override frozen gates after seeing data. $8 of stage-2 budget
  unspent. Stage-1 total cost ≈ $0.85 (pod 3 iterations + 3 seam reads).

**Fork (Nikhil's, recorded honestly):**
(a) Amend the gate to a RELATIVE bar (seam errors priced by stage-2's hard-cap
    rubrics against the generalist baseline — which run 10 showed is equally
    invention-prone, resource_grounding 2.03). This is a post-hoc gate change —
    the first the program would ever make — and must be labeled as such if taken.
(b) Train the fusion/dispatcher adapter (doc §9.4) on audit-certified integration
    examples (~$10-15, run-11-style corpus discipline; uncertain — run 11 showed
    delta-training added nothing over elicitation, though fusion ≠ elicitation).
(c) Stop and write up: mechanics + routing + motion loop + specialists proven;
    the honest wall = free-prose integration fidelity at 4B. A coherent,
    publishable arc (runs 7-12).
