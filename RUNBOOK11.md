# RUNBOOK 11 — the delta-derivation viability face (variables in motion)

**Question:** run 10 proved fidelity-as-constraint doesn't train at 4B; probe 3
proved the derivation capability EXISTS when the shift is shown (ack 12/16,
direction 79%, the pair-5 bottleneck hold). Run 11 trains the missing TRIGGER as a
structure — Nikhil's design: "variables are not stagnant… in motion we can add
derivation, a little change in a certain direction, and manage the maneuvering."
If it passes, the cube has its second specialist and run 12 is the first full
prototype (faceF_9b + delta face + keep100 working together).

**Design center (Nikhil, 2026-07-30):** viability lives in motion. A plan is
audited once, then the variables MOVE; the specialist must (1) notice the named
shift, (2) re-derive the plan around it (reallocate what freed up, absorb what
tightened), (3) re-derive the estimate — proportionately, holding when the
binding constraint didn't move (the pair-5 behavior), dropping when it tightened.

**Probe-3 evidence base (why this is licensed):** face vs anchor on identical
shifts — proportionate +15 median move vs anchor's sycophantic +55-to-ceiling;
3 holds vs 1; estimate-clause linkage 17/32 vs 12/32; pair-5 reallocated freed
cash while correctly holding 40% because the binding constraint (neighbor)
never moved. Capability present; trigger untrained.

**Budget law (Nikhil):** ~$5 OpenRouter per top-up, make every dollar count.
Run-11 plan fits one top-up: OpenRouter ~$4.0 · Anthropic ~$3 · pod ~$0.5.

## Corpus (the delta diet)

- **Format = probe-3 format, single-turn** (no trainer changes): user prompt =
  PROBLEM + YOUR PREVIOUS PLAN (generator-authored turn-1 thread, audit-style) +
  UPDATE (one named shift) + revise instruction; assistant = the re-derivation.
  Final line of every assistant target, exactly: `ESTIMATE: NN%` (tagged — the
  parser lesson from probe 3's 45%-price-premium artifact).
- **Problems:** the 189 gate-admitted run-10 V-carve problems (already admitted
  by the bench judge — reused, $0).
- **Shifts:** authored by DeepSeek in the same call, ONE named change each,
  **bidirectional by construction: 50% boosts (resource added / friction
  removed), 50% nerfs (resource removed / friction added / deadline tightened)**.
  Direction label recorded in metadata — never shown to the judge or trainer.
- **Scale:** ~300 sequences (150 problems × 1 boost + 1 nerf each; one DeepSeek
  call generates turn-1 + update + revision together). Est. ~$3.5.
- **Admission gate (objective-first, strict):** CODE gate on every sequence —
  (1) tagged ESTIMATE line present in both turns, (2) direction sane vs the
  shift label: boost → new ≥ old, nerf → new ≤ old, holds allowed BOTH ways
  ONLY when the revision names a non-shifted binding constraint (regex: hold ⇒
  must cite a constraint word from the problem absent from the update), (3)
  update-signature cited in revision, (4) revision actually re-plans (≥1
  concrete change vs turn-1, checked as non-trivial diff). Plus a **Sonnet
  sample-audit of 30 random admitted sequences** (~$0.5): quality read only,
  reported; if >20% junk → STOP and report before training.
- **Diet:** admitted delta rows + the existing 945-row static faceV_10 diet
  (viability voice retained, $0) → ~1,200-1,250 rows, keep-0.6 band, 1.25 epochs.
  Adapter: **wrk_faceVD_11_qwen** (D for delta; no collision with any prior name).

**AMENDMENT (2026-07-30, corpus-quality battle, pilots 1-3):** v1 corpus (temp
0.75) audited 47% junk — invention class ("promotion panel", "steward's
understudy") — the frozen 20% stop line fired BEFORE training; v1 archived. Fix 1:
CLOSED WORLD hard rule → pilot-2 junk 44%, class shifted to coherence
(contradicted counts, unexplained arithmetic, ignored refusals). Fix 2: temp
0.75→0.45 + arithmetic-coherence/consistency/estimate-justification rules →
pilot-3 junk 20% (at the line, code gate 30/30). Gate promoted from
sample-and-stop to **audit-ALL-as-filter**: every code-admitted sequence is
Sonnet-audited; junk is DROPPED from the diet, not trained. Global sanity stop
at >35% junk; diet floor 180 sound sequences. Cost delta: ~+$4.5 Anthropic
(session M becomes full-corpus), justified — the diet enters training certified
sound by the strict instrument. Lesson recorded: re-derivation is harder for the
teacher than static threads; audit at pilot stage ALWAYS (v1's junk was caught
only at full-corpus audit).

## EVAL D — the motion bench (strict, refactored, frozen BEFORE any output)

- **Held-out problems:** the 16 frozen twin base problems (Eval C, never trained)
  + their 16 existing BOOST twins (md5 d3ec49d5) + **16 NEW NERF twins** built
  deterministically (one weakening UPDATE line appended to the byte-identical
  base, same construction law, byte-verified minimal pairs, md5-frozen). 32
  shift-pairs total, bidirectional.
- **Protocol (probe-3 elicited format, greedy, reproducible):** each arm sees
  problem + ITS OWN base-problem thread + UPDATE → revise; eval prompt requires
  final line `ESTIMATE: NN%`; parser reads ONLY that tagged line — the last-%
  artifact is dead.
- **Arms:** subject **wrk_faceVD_11_qwen**; references keep100 (sycophancy
  control) and wrk_faceV_10_qwen (proves the delta training added the trigger
  vs static training). All on one card.
- **FROZEN BARS (subject arm; all four required):**
  1. Tagged-estimate parseability ≥ 30/32 pairs (the format is trained; missing
     it is a fail, not noise).
  2. Boost direction ≥ 75% correct (new ≥ old).
  3. **Nerf direction ≥ 75% correct (new ≤ old)** — the leg an always-up
     sycophant mathematically fails (keep100 predicted <40% here; reported as
     the discriminator).
  4. Acknowledgment ≥ 75% of pairs (update-signature cited).
- **Delta-vs-static read (reported):** faceVD_11 must beat faceV_10 on nerf
  direction by ≥ 25 points, else the delta diet added nothing over probe-3
  elicitation of the static face.
- **Eval A regression guard (report-only, ~$2.5 Anthropic):** faceVD_11 on the
  frozen v5 bench, 48 problems, single session vs regenerated keep100 anchor —
  overall must not fall below faceV_10's 3.53; a delta face that forgets how to
  answer static problems is not a seat.

## Pod (~30-40 min on an A40-class card, ~$0.4)

Train wrk_faceVD_11_qwen (delta diet, fixed recipe). Gens: faceVD_11 base
threads on the 16 eval base problems; revisions on all 32 twins × 3 arms
(faceV_10 + keep100 reuse their run-10 base threads as priors); + Eval A pair
(faceVD_11 + anchor, 48 each). Bundle run11_bundle.tgz.

## Verdict grid (frozen)

- ALL four bars pass + regression guard holds → **second specialist real** →
  RUN 12 = first cube prototype (faceF_9b + faceVD_11 + keep100; composition +
  dispatcher design; the full loop: foresight reads → viability tracks motion →
  derived percentage out).
- Bars 1-2-4 pass, nerf fails → the face learned "shift = adjust up" not
  derivation → one iteration allowed ONLY on diet mix (more nerfs), no new
  mechanism, ≤ one $5 top-up.
- Parseability or ack fails → format didn't train → inspect diet, report, stop.
- Regression guard breaks → delta skill came at the cost of the static seat →
  report; diet-mix decision (more static rows) is Nikhil's call.

## Isolation & naming

`data/run11/`, `out/run11/`, adapter `wrk_faceVD_11_qwen`, scripts `run11_*`,
nerf twins `data/run11/nerf_twins.jsonl` (16/16, md5 8cd693cf3d15183fcb0d5ce46c30e0e5, determinism byte-checked), bundle
`density_run11/run11_bundle.tgz`. Judge sessions: M (Sonnet sample-audit),
N (Eval A regression). No collisions with runs 7-10 namespaces (verified).

*Frozen 2026-07-30 pre-spend. Awaiting Nikhil's $5 OpenRouter top-up + go.*
