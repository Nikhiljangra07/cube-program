# The Cube Program

**A 24-run study of staged inference and verification harnesses for small language models, with frozen protocols, model-assisted audits, and published corrections.**

Solo work by [Nikhil Jangra](https://github.com/Nikhiljangra07) ·
Historical study: July 20–August 28, 2026 · approximately $209 compute · Qwen3-4B weight class.

## Current interpretation

**Read the [October 14 statistical and claims amendment](ERRATA_2026-10-14.md) before quoting the historical reports.** It supersedes older p-values, holdout-win summaries, cross-judge agreement claims, and explanations that attributed failure exclusively to model capacity. The amendment was published here on October 27, 2026; historical runbooks and reports remain preserved as the record of the original work.

On Run21's 16-case set, the staged harness passed the study's locked STRICT-D criterion on **6/16 answers versus 0/16** for its one-pass control using the same model weights. The corrected exact two-sided paired p-value is **0.03125**. This was a small-sample comparison and **failed the registered absolute target of ten passes**; the descriptive p-value does not make that target a success.

The holdout evidence does **not** establish a robust win. Historical regex-derived tolerant counts favored Cube over the reasoning sibling under Sonnet (**5 versus 2**) but reversed under Gemini (**1 versus 7**). The much-quoted **47/48 strict judge agreement largely reflected shared failures** (kappa 0.00), rather than validation of clean-answer certification. The registered strict-band transfer claim failed.

The work demonstrates an evaluation and systems-building process: frozen comparisons, staged inference, provenance and arithmetic checks, saved failures, and revisions after scrutiny. It does not establish that architecture substitutes for model scale, that these checks certify semantic truth, or that a larger model is necessary to resolve the remaining failures.

## How to read this repository

| Start here | What it is |
|---|---|
| [ERRATA_2026-10-14.md](ERRATA_2026-10-14.md) | Current corrections and limits on interpreting historical results |
| [DRAFT2.md](DRAFT2.md) | Historical record, runs 7–23; read its conclusions with the amendment above |
| [DRAFT.md](DRAFT.md) | Volume I, runs 1–6: the data-density and storage experiments |
| [AUDIT_GPT_2026-08-18.md](AUDIT_GPT_2026-08-18.md) · [AUDIT_GPT_2026-08-28.md](AUDIT_GPT_2026-08-28.md) | Two adversarial GPT reviews, with findings and dispositions; these are model-assisted reviews, not independent human audits |
| [MINISTUDY_JUDGE.md](MINISTUDY_JUDGE.md) | Historical two-judge study, including disagreement and unsuccessful results |
| RUNBOOK*.md | Frozen protocols, declared success bars, and appended results |

## Method and reproducibility

The historical runbooks record success criteria before the corresponding runs. In the final experiments, the harness was frozen by git commit before a separate model generated the holdout: commit `4093a26` predates the problem seal, md5 `7620cd16…`. A model-generated holdout is not an independently curated human benchmark.

The harness operates on complete generated stages: extraction, checks, reasoning, and assembly. It is not a per-token mixture-of-experts system. Provenance and arithmetic checks address specific failure modes; implementation bugs found in later review limit attribution to any individual stage or to the model weights alone.

Some datasets and model outputs are gitignored. Their fingerprints in the runbooks document the intended frozen inputs, but this public repository alone is not a complete reproduction bundle. Subsequent local repair code and exploratory training are not included in this historical release.

## Other results and limits

- **Run24 was a non-result:** 5 versus 4 RULER-T-clean answers against a 14B reasoning model, with paired McNemar p=1.0. The earlier "matched" conclusion was retracted after review.
- **The adapted 8/16 result is exploratory:** it is distinct from the locked 6/16 comparison and cannot replace it as the registered result.
- **Agreement is not validity:** shared judge failures do not prove that a whole model class cannot produce grounded answers.
- **Failure attribution remains unresolved:** information-flow, lexical-verification, and arithmetic bugs prevent isolating capacity as the cause. More data or a larger model might help, but necessity is not established.

*Built and run solo on rented GPUs and a laptop. Current summary updated October 27, 2026; historical artifacts are retained rather than silently rewritten.*
