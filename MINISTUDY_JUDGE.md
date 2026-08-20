# MINI-STUDY — JUDGE VALIDITY (2026-08-19, frozen pre-spend)

**The question (audit finding 5 / §22.5):** every verdict in seventeen runs
comes from one judge family (Claude Sonnet 5). Does an independent judge
family agree?

## Design
- **Sample: ALL 48 holdout answers** (run 22 arms C+G, run 23 arm R) — the
  answers underpinning the program's surviving claims (the 5×/RULER-T edge
  and the 5–2 reasoning-model win). No sampling, no selection.
- **Second judge: Gemini 2.5 Pro via OpenRouter** — a third family that is
  neither the program judge (Anthropic), the contestant (Qwen), nor the
  holdout author (GPT). Native Gemini is banned (wallet policy); OpenRouter
  route only. Precedent: run-1 rejudge used the same model/session pattern.
- **Instrument: STRICT_ONE ruler prompt, byte-identical** (imported from
  run21_score.RULERS["one"]) — the exact prompt whose Sonnet verdicts we are
  validating. One read per answer, 48 reads total, cached, retry-on-invalid.
- **Comparison, two derived labels per answer:**
  1. strict-coherent (the raw boolean), Sonnet vs Gemini;
  2. RULER-T-clean (coherent OR all flaws classify ADD via the frozen
     ruler_t.py), Sonnet vs Gemini.
- **Reported: raw agreement % and Cohen's kappa for both labels**, plus the
  disagreement list verbatim (answer id, both verdicts, both flaw texts).

## Frozen interpretation (stated before any read)
- RULER-T-clean agreement ≥ 80%: judge validity SUPPORTED — the program's
  verdicts do not depend on an idiosyncratic judge.
- 60–79%: PARTIAL — claims stand but carry a judge-variance caveat.
- < 60%: judge validity FLAGGED — the holdout claims must be re-stated as
  single-judge results and the disagreements published.
No bar favors us; all three outcomes are recorded outcomes.

## Budget
48 reads × (~1,100 tokens in / ~300 out) on Gemini 2.5 Pro ≈ $0.5–1.0.
HARD CAP: 60 requests. Wallets at freeze: OpenRouter $3.46 · Anthropic
≈ $0.6 (untouched by this study) · no GPU involved.

*Frozen 2026-08-19 before the first OpenRouter read.*
