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

## RESULTS (2026-08-19 — 48 Gemini reads ≈ $0.5, cap held)

| label | agreement | kappa |
|---|---|---|
| strict-coherent | **97.9%** (47/48) | 0.00 (base-rate degenerate) |
| RULER-T-clean | **70.8%** (34/48) | 0.13 |

**Frozen band: PARTIAL (60–79%).** Per-arm RULER-T-clean counts:

| arm | Sonnet | Gemini |
|---|---|---|
| C cube | 5/16 | 1/16 |
| R Thinking | 2/16 | 7/16 |
| G instruct naked | 1/16 | 4/16 |

### Honest reading
1. **What is judge-robust:** flaw DETECTION and the strict island. Both
   judges agree at 97.9% that these answers contain flaws (the one
   disagreement is R pid 14, Sonnet's lone strict-clean, which Gemini
   flags). Every strict-band conclusion in runs 22–23 — the island is
   empty for the whole weight class — survives the second judge intact.
2. **What is NOT judge-robust: the realistic-band ORDERING.** Under
   Gemini's readings as classified by our regex, the per-arm ordering
   INVERTS (C 1 · R 7 · G 4 vs Sonnet's C 5 · R 2 · G 1) — the 5–2
   reasoning-model win and the 5× naked edge do not survive as stated.
   Until disambiguated, those claims carry a mandatory single-judge
   qualifier.
3. **The mechanism is visibly (at least partly) an instrument artifact,
   and it confirms DRAFT2 threat 6 empirically.** RULER-T-clean is derived
   by a regex (ruler_t.py) tuned on SONNET's flaw phrasing. The
   disagreement autopsy shows the two judges describing the SAME defects in
   different house styles: Gemini frequently phrases what Sonnet calls
   states-as-fact/contradiction as "Invented event/number" (→ classified
   ADD → clean), and phrases what Sonnet passes as decoration as
   "Self-contradiction" (→ T1 → dirty). Detection agrees; severity
   PHRASING routes through the regex differently per judge. This is
   exactly the failure mode threat 6 predicted ("any successor should
   freeze a severity-tiered rubric and have the judge classify directly").
4. **Recorded disambiguation (labeled amendment candidate, NOT run —
   awaiting authorization):** re-read the same 48 answers asking EACH judge
   to classify its own flaws fatal-vs-decoration directly (judge-native
   severity, no regex). ~48 Gemini reads ≈ $0.5–1 within the remaining
   OpenRouter balance (Sonnet's side derivable from cached prose or ~$1
   Anthropic re-read). If judge-native severity agrees, the ordering
   claims are restored; if it disagrees, the realistic-band ordering is
   permanently single-judge-scoped.

**Program consequence as it stands: strict conclusions (walls, island,
laws) are two-judge robust; the holdout's realistic-band ordering claims
(5–2, 5×) are single-judge results pending disambiguation, and resume
wording must say so.**
