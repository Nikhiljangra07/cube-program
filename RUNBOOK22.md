# RUNBOOK 22 — THE LOCKED NON-TEMPLATE HOLDOUT (2026-08-18)

**The question (from the external audit, finding #3):** is cube-v2 an
architecture, or a template-specific solver? Every prior component (parsers,
anchors, guard) lived on the problem generator's schema. Run 22 generalizes
the harness to FREE TEXT, freezes it, and only then obtains 16 independently
authored natural-prose problems. **Zero harness edits after first contact
with the problems** (crash-only fixes permitted, each logged verbatim in this
runbook).

## Three-party separation
- **Author:** GPT (via Nikhil) — writes the holdout problems. Neither judge
  nor contestant. Problems frozen by md5 on receipt.
- **Contestant:** Qwen3-4B-Instruct-2507 + wrk_keep100 (both arms, same
  weights — the run-21 causal design).
- **Judge:** Claude Sonnet 5 — STRICT_ONE + STRICT-D byte-reused (both are
  problem-text-generic), plus a NEW blind quality rubric (audit finding #1:
  fidelity is not quality; both are now measured).

## The generalized pipeline (arm C — frozen in run22_pod.py BEFORE problems)
0. **EXTRACT (model):** list FACT lines (verbatim-copied facts) and OPTION
   lines (courses of action in the problem's own words). **Code verifies
   each FACT against the text** (every number must appear verbatim; >=60% of
   its words present) — unverified lines are DROPPED and counted. Verify-
   only-what's-verifiable: no schema assumed.
1. **COMPARE + SPAN (model proposes, code computes):** model names the single
   most decision-relevant numeric comparison ("COMPARE: A vs B") and date
   pair ("SPAN: d1 to d2"); code checks both operands appear in the problem,
   then does the arithmetic itself. Failed parses degrade gracefully (anchor
   = verified facts only; counted).
2. **ANCHOR:** verified facts + code-computed comparison/span, fixed
   template text (coach law).
3. **JUDGMENT / PREDICTION / CHOICE / ESTIMATE:** the run-21 demand-matched
   prompts, generalized (no template parameters). Digit screen (21C fixed
   version, comma-normalized; allowed = problem numbers + code-computed
   values) on prediction AND choice. **Generalized modal guard:** if the
   model's own judgment or the anchor declares an extracted OPTION
   non-executable, the choice may not verb-commit to it (one retry; counted).
4. **ASSEMBLY:** verbatim pieces + fixed BRIDGE + estimate line. Unchanged.

Arm G: the full problem, one pass (GEN_SINGLE verbatim), with_estimate law.

## FROZEN READOUTS
1. **PRIMARY (STRICT-D, locked, single run): CUBE >= 6/16 AND CUBE >= GEN+4.**
   (Calibrated to run-21's LOCKED result, 6/16 — the audit-clean baseline —
   not to the adapted 8/16.)
2. **QUALITY RUBRIC (new, both arms, blind):** constraint_fidelity /
   prediction_quality / action_quality / calibration, 1–5 each. Reported;
   registered prediction: cube >= generalist on constraint_fidelity; no bar.
3. **PIPELINE INTEGRITY:** extraction verification rate, compare/span parse
   rate, guard/screen activity. **If the generalized extraction collapses
   (<50% problems yield a usable anchor), that is the template-solver verdict
   and is recorded as such.**
4. STRICT_ONE dual-reported (comparability spine). All 16 problems judged
   whatever happens; no post-hoc exclusions.

## Budget & order of operations
1. Harness built, mock-tested, committed (this runbook + scripts) — $0.
2. GPT authoring prompt issued; problems received, frozen by md5. NO EDITS.
3. Pod (~A40, ~30 min, ~$0.3): both arms, 16 problems.
4. Judge: 32 answers x 2 rulers + 32 quality reads = 96 reads ~ $2.2
   (SPEND CAP 105). Total ~ **$2.5**. Wallet at freeze: Anthropic $5.36 ·
   RunPod ≈ $19 · OpenRouter $3.

*Frozen 2026-08-18 pre-problems, pre-spend. The zero-edit rule is the
experiment.*

## PROBLEMS RECEIVED & FROZEN (2026-08-18)
- Authored by GPT via Nikhil from the issued prompt; pasted verbatim, zero
  edits by us. `data/run22/holdout_problems.jsonl`
  **md5 7620cd1646a7466388b1811219ed2219** — 16 problems, pids 0–15,
  154–199 words each, all natural prose, varied domains (restaurant lease,
  nonprofit grant, freelance scope, lab procurement, family succession,
  touring, clinic, construction, health-tech pilot, grain co-op, festival
  sponsorship, translation rights, school buses, game publishing, museum
  loan, apparel import). Every problem contains month-day dates and dollar
  amounts (2–8 dates, 3–7 amounts). No harness file touched after receipt.
- **THE ZERO-EDIT CLOCK IS RUNNING.** Any change to run22_pod.py /
  run22_score.py from this point is crash-only and must be logged verbatim
  below.

### Crash-fix log (post-contact)
- (none)
