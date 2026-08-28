# The Cube Program

**A 24-run, pre-registered, twice externally audited study of one question: can
architecture substitute for scale in small language models?**

Solo work by [Nikhil Jangra](https://github.com/Nikhiljangra07) ·
Jul 20 – Aug 28, 2026 · ~$209 total compute · Qwen3-4B weight class.

## The result in three sentences

A five-stage verification harness (machine-verified fact extraction →
code-computed comparisons → anchored reasoning stages → template assembly)
took the **same 4B weights from 0/16 to 6/16 certified-clean answers**
(paired p≈0.008) against a one-pass control, and **beat the
reasoning-trained sibling of its own base model 5–2** on a holdout authored
by a third party (primary-judge criterion; strict-band conclusions
replicated across two judge families at 97.9% agreement). The pre-registered
strict-band headline **failed to transfer** to that holdout — and is
reported at equal volume with the wins. The residual failure mode is
precisely named — cross-stage judgment coherence, a weights property — with
a measured scaling prior pointing at a 14B judgment seat.

## How to read this repo

| Start here | What it is |
|---|---|
| [INTERVIEW_PACK.md](INTERVIEW_PACK.md) | The 10-minute version: claims with their qualifiers, numbers cheat-sheet, evidence index |
| [DRAFT2.md](DRAFT2.md) | The full record, runs 7–23: every frozen bar, every outcome, threats to validity, cost ledger |
| [DRAFT.md](DRAFT.md) | Volume I, runs 1–6: the data-density / storage era that led here |
| [AUDIT_GPT_2026-08-18.md](AUDIT_GPT_2026-08-18.md) · [AUDIT_GPT_2026-08-28.md](AUDIT_GPT_2026-08-28.md) | Two external adversarial audits — 8 + 10 findings with dispositions; the second retracted a pre-committed claim |
| [MINISTUDY_JUDGE.md](MINISTUDY_JUDGE.md) | Two-judge validity study — including the part that *didn't* go our way |
| RUNBOOK*.md | One frozen protocol per run, success bars written before spend, results appended after |

## The method, in one paragraph

Every run's success criterion was frozen in a runbook **before** any money
was spent, and every failed bar is published (most runs failed theirs).
The final experiments went further: the evaluation harness was frozen by
git commit *before* the holdout problems existed (commit `4093a26`
predates the problem seal, md5 `7620cd16…` — the zero-edit rule is
verifiable in history), the holdout was authored by a model that is
neither the judge nor the contestant, and the pipeline's answers were
judged *before* its final opponent was chosen. Data and outputs are
gitignored; their md5 fingerprints in the runbooks are the freeze record.

## What survives scrutiny (the honest scoreboard)

- **Two-judge robust:** the strict grounding island is empty for the whole
  4B weight class — no arm (trained, prompted, harnessed, or
  reasoning-trained) produces fully-grounded free-prose answers.
- **Pre-registered and held, twice:** blind constraint-fidelity predictions
  vs both opponents.
- **Single-judge, qualifier attached:** the realistic-band ordering
  (5/16 vs 2 vs 1) — pending a judge-native severity read.
- **Non-result, published as such:** run 24 vs a naked 14B reasoning model —
  5 vs 4 RULER-T-clean, paired McNemar p=1.0; the pre-committed "matched"
  wording was retracted after audit #2.
- **Generator-local, published as such:** the 6/16 → 8/16 strict-band
  rematch series.

*Built and run solo on rented A40s and a laptop. The most expensive run
cost about $17; most cost under $3.*
