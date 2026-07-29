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
  3-5 sentences, cold and analytical. "Plan with what you hold, not what you wish."
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
regenerated on-card — card-class control) + `faceV_10_qC` + `anchor_10_qC`.
V5_WRK_MAXNEW=512. Bundle `run10_bundle.tgz`.

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

- **Format:** 24 problems (prototype-grade N, documented as such). Each = a
  concrete decision scenario in a modern real-world setting + an explicit
  INVENTORY of what the actor actually holds (funds, people and their actual
  commitment level, the actor's seat/authority, hard deadlines) + at least one
  TEMPTING move that exceeds the inventory (the trap — a high-upside option the
  actor cannot actually resource; mirror of B's innocent counter-signal). Generated
  by DeepSeek (family separation), OOD from all training problems, md5-frozen
  before any face thread exists.
- **Task per arm:** same two-seat harness, same worker prompts as Eval A — no
  arm-specific prompting; the inventory arrives as part of the problem text.
- **Judge (Sonnet 5, new rubric, frozen in judge_run10.py):** 5 dims, 1-5 —
  - resource_grounding: does every step spend only items in the inventory, with
    nothing invented beyond it (and the trap move either avoided or explicitly
    re-scoped to fit the inventory)?
  - seat_fidelity: does the actor act only from the position/authority the
    inventory grants (no moves requiring a seat they do not hold)?
  - causal_soundness: does each step actually produce the next — no step whose
    success depends on another party's unforced cooperation stated as certain?
  - friction_realism: does the plan name real-world friction (legal, human,
    timeline) and carry an answer to it, rather than a zero-friction world?
  - decisive_completeness: does the thread still COMMIT and resolve the decision —
    audit as foundation for action, never as an excuse to hedge?
  overall-C = mean of 5. Coverage all-or-discard-whole-session, single session,
  direct API, no temperature param, max_tokens 12000, retry-on-empty.
- **C BAR (prototype-grade, single session J→L, documented as such):**
  overall-C(face) ≥ overall-C(anchor) + 0.20 AND resource_grounding(face) ≥
  anchor (the anti-trap leg — C must never reward confident plans that spend
  beyond the inventory).

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

DeepSeek generation ~$1.5-2.5 (OpenRouter) · Eval C problems ~$0.5 · admission gate
~$3.5 (Anthropic) · pod ~$1 (RunPod) · Session K ~$2.5 · Session L ~$1.5 · K2
only-if-pass ~$2.5 → **~$10.5-14** total. Budget confirmed replenished by Nikhil
(2026-07-26: "we got the budget… GPU as well as the Anthropic").

## Isolation & naming

`data/run10/`, `out/run10/`, adapter `wrk_faceV_10_qwen`, threads `*_10_q*`,
scripts `run10_*`, judge sessions K/K2/L, backup `density_run10/run10_bundle.tgz`.
No generalist work this run (phase-one discipline). No name collisions with any
prior artifact — verified against runs 7/8/9/9b namespaces.
