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
- (none — zero edits, zero crashes; pod ran end-to-end on the frozen code)

## RESULTS (2026-08-18 — pod favourable_sapphire_quelea, A40, ~15 min; judge 96 reads ~$2.2)

| arm | strict | STRICT-D | RULER-T | cf / pq / aq / cal |
|---|---|---|---|---|
| C cube-v2 generalized | 0/16 | **0/16** | **5/16** | **2.31** / 2.31 / **2.44** / 1.69 |
| G generalist naked | 0/16 | 0/16 | 1/16 | 2.06 / **2.38** / 2.25 / **2.06** |

**PRIMARY: FAIL** (needed cube >= 6/16 and >= GEN+4; got 0 vs 0).
**Registered prediction (cube >= gen on constraint_fidelity): HELD** (2.31 vs 2.06).
**Template-solver clause: NOT triggered** — extraction did not collapse
(10.4 verified facts/problem avg, 0.0 dropped, compare 12/16, span 13/16,
options 2.1/problem, no estimate injections either arm). The harness
generalized mechanically; the strict-band result did not.

### Honest reading
1. **The run-21 STRICT-D result does not transfer to independently authored
   problems.** Cube fell 6/16 -> 0/16; the generalist stayed 0 -> 0. GPT
   audit finding #3 (template circularity) is CONFIRMED at the strict band:
   the locked 6/16 depended on generator-shaped problems.
2. **Confound, recorded:** the holdout is also intrinsically harder (10+
   facts, ~3 options, deliberate distractors and fact-tension pairs vs the
   generator's sparser frames), so distribution shift and difficulty rise
   are entangled. The G-arm floor (0 on both distributions) cannot separate
   them. No design change can fix this post-hoc; noted for any replication.
3. **The surviving signal:** at RULER-T (realistic severity) cube 5/16 vs
   gen 1/16, and the blind constraint-fidelity rubric held (2.31 vs 2.06),
   plus action_quality 2.44 vs 2.25. The architecture still buys measurable
   fidelity on natural problems — but the edge lives at the tolerant band,
   not the strict one. Calibration went the other way (1.69 vs 2.06): the
   anchored ESTIMATE stage is worse than the naked model's on free prose.
4. **Failure anatomy (autopsy):** C's fatal flaws on natural problems are
   dominated by CROSS-STAGE CONTRADICTIONS — judgment names a binding
   constraint, choice then violates or reverses it (pids 01, 02, 04, 05,
   15); plus small-arithmetic slips (six days called five, 30-day window
   misdated). On dense multi-option problems the independently generated
   stages diverge, and assembly stitches the divergence into visible
   self-contradiction. This is the run-21 modal-inconsistency residue
   generalized: the pipeline verifies FACTS but nothing verifies AGREEMENT
   BETWEEN STAGES. G's flaws are the familiar class: invented actors,
   figures, and events (every G answer that failed).
5. **Echo of run 17B:** on natural-prose problems the strict island is
   closed for the whole 4B weight class (17B: 0/40 all arms; 22: 0/32 both
   arms). Run 21's island was real but generator-local.

**Verdict for the record: cube-v2 is an architecture, not a template
parser (integrity clause), and it retains a tolerant-band fidelity edge on
held-out problems (5x RULER-T, cf rubric held) — but the headline
strict-band win does NOT generalize. Resume/claims must say so.**
