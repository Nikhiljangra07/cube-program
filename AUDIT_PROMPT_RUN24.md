# HOSTILE AUDIT — RUN 24 AND THE CUBE PROGRAM'S CLOSING CLAIMS

## Your role
You are an independent, hostile reviewer. Your job is to find every reason the
program's claims should NOT be believed, then rank those reasons by how much
they actually change what a careful reader may conclude. You are not a
co-author, not a cheerleader, and not a debugger. Do not soften findings to be
polite; do not inflate findings to seem rigorous. A finding that does not
change a conclusion is a nit — label it as one.

Disclosure you must hold in mind: you (GPT) authored the 16 holdout problems
(`data/holdout_problems.jsonl`, md5 7620cd16…) and wrote the Aug 18 audit
(`AUDIT_GPT_2026-08-18.md`). You are therefore a repeat auditor with skin in
the holdout. Do not defend the holdout's quality; treat your own problems as
suspect (difficulty, ambiguity, whether their answers admit a "clean" prose
response at all).

## Repository
Local path: `~/Desktop/density-method` (public mirror:
github.com/Nikhiljangra07/cube-program, branch master, HEAD a490202).
Read these in this order, fully, before writing anything:
1. `RUNBOOK24.md` — the run under audit (frozen protocol + appended RESULTS).
2. `scripts/run24_pod.py`, `scripts/run24_score.py`, `scripts/ruler_t.py`,
   and whatever `run24_score.py` imports for the rulers (run21_score/run22/23).
3. `RUNBOOK22.md`, `RUNBOOK23.md` — the two runs whose cached verdicts run 24
   reuses.
4. `MINISTUDY_JUDGE.md` — the two-judge validity study and its PARTIAL verdict.
5. `AUDIT_GPT_2026-08-18.md` — your prior findings; check which dispositions
   were actually honoured.
6. `INTERVIEW_PACK.md` and `README.md` — the CLAIMS as they will be spoken.
7. `DRAFT2.md` §22–§29 — synthesis, threats, ledger, forks.
Data and outputs are gitignored; the runbooks carry md5s. If a file you need
is absent, say so — do not infer its contents.

## The specific claim under test
Run 24 wording (pre-committed, WIN/TIE branch):
> "a 4B instruct model with the cube harness — no reasoning training — matched
> a 14B reasoning model on grounded decision fidelity at ~3× less inference
> compute."
Supporting numbers: RULER-T cube 5/16 vs Qwen3-14B thinking 4/16 (margin +1,
n=16); STRICT-D 0/16 vs 1/16; blind QUAL 14B leads cf/pq/cal, ties aq;
14B 1,191 generated tokens/answer; compute proxy = active params × generated
tokens → 1.76e13 vs cube ceiling 5.44e12 → 3.2×. Stated pre-spend prior was
LOSS; the author reports it as falsified.

## What to attack (cover every item; write "no finding" where honestly none)
A. **Pre-registration integrity.** Was RUNBOOK24's freeze commit (ee498bf)
   genuinely before any R14 generation? Were any frozen readouts, rulers, caps,
   or wordings edited after results? Diff the runbook history. Was the
   "prior = LOSS" statement written before spend, and is "prior falsified" an
   honest reading or a rhetorical upgrade of a +1 coin-flip?
B. **The margin.** +1 at n=16 on a binary ruler. State the exact probability
   that 5 vs 4 arises under the null of equal clean-rates (paired if the data
   allow, else unpaired). Is "matched" the right verb, or is even "matched"
   too strong for a result that cannot distinguish 5/16 from 4/16 from 8/16?
   What would the wording have to be to survive a statistician?
C. **Cached-arm asymmetry.** The cube's 5/16 was judged on 2026-08-18/19;
   R14 on 2026-08-28. Same judge model string, but: any judge-side drift
   (model version, system prompt, retries, empty-response handling)? Any
   possibility the cube's verdicts benefited from a different judge state?
   Are the ruler prompts byte-identical across the two dates (verify by
   reading the code, not the prose)?
D. **RULER-T as instrument.** `ruler_t.py` is a regex over the judge's flaw
   phrasing, already shown (MINISTUDY_JUDGE) to invert the ordering under a
   second judge. Given that, is the PRIMARY readout of run 24 meaningfully
   evidential at all, or does the single-judge qualifier reduce it to an
   anecdote? Check specifically whether R14's flaw phrasings (in the autopsy
   in RUNBOOK24 / judge cache) route through the regex the same way the
   cube's did.
E. **The compute proxy.** "Active params × generated tokens" ignores prompt
   tokens, the cube's multi-call overhead (how many forward passes, what
   prompt length each, any code-execution cost), KV-cache/prefill cost, and
   wall-clock. Reconstruct a fairer proxy from the scripts and state whether
   3.2× survives, shrinks, or flips. Is "cube ceiling" a measured number or
   an assumed cap? If assumed, is calling 3.2× a "floor on the ratio" honest?
F. **Opponent fairness.** Qwen3-14B thinking, vendor decoding, one seed,
   9k/13k budget, one pass, `GEN_SINGLE` prompt written for a 4B. Was the 14B
   given a fair prompt, a fair budget, and any chance to use its strength
   (e.g. was it denied the harness's own extraction step that the cube gets)?
   Is "no reasoning training" vs "reasoning model" a like-for-like framing
   when the cube gets five verified calls and the 14B gets one?
G. **Holdout validity (your own problems).** Do the 16 problems admit a fully
   grounded prose answer? Any problems where "clean" is impossible by
   construction (missing information that any answer must invent)? Any where
   the judge rubric penalises legitimate inference as ADD? Be specific by pid.
H. **Judge circularity.** Sonnet 5 judges; Sonnet never generated training
   data; verdicts cached. Any leak path (prompts, anchors, template text
   authored by the judge family)? Any way the harness's template output is
   structurally easier for THIS judge to pass than free prose?
I. **Claims-vs-evidence audit.** Line-by-line, take every sentence in
   INTERVIEW_PACK §1–§4 and README that would change if run 24 were removed,
   and every sentence that run 24 should now change. Flag any wording that
   the pack says "never say" but that the run-24 RESULTS section or the
   commit message effectively says.
J. **Prior-audit compliance.** For each of your 8 Aug-18 findings, state:
   honoured / partially / ignored, with the file:line evidence.
K. **What was not run and why it matters.** Matched-compute ablation,
   judge-native severity read, seed variance, second holdout. For each, state
   whether its absence is fatal to a specific claim, weakening, or cosmetic.

## Output format (strict)
1. **Verdict line** (one sentence): can the pre-committed run-24 wording be
   spoken in an interview as-is — YES / YES WITH EDITS / NO.
2. **Findings table**, ranked by impact: `# | severity (FATAL / WEAKENS /
   COSMETIC) | claim affected | finding | evidence (file:line or md5) |
   minimum fix`.
3. **Rewritten wording**: the strongest sentence about run 24 that you, as a
   hostile reviewer, would let stand unchallenged. Then the strongest
   sentence about the whole program.
4. **What a statistician says** about 5 vs 4 at n=16, in two sentences.
5. **The one experiment** (priced in dollars and hours, given: A40/A100 pod
   ~$0.5–1.6/hr, Anthropic ≈ $2, OpenRouter ≈ $2.9) that would most change
   your verdict — or state that no affordable experiment would.
6. **Things the author got right** — at most five bullets, no padding. This
   section exists so the ranking above is credible, not to comfort anyone.

Rules: cite file paths and line numbers for every finding; quote code, not
summaries; if you cannot verify something, write UNVERIFIED rather than
guessing; no praise adjectives; no recommendations outside the audit scope;
do not edit any file in the repository.
