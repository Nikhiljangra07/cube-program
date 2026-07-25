# TEACH-GAP READING LIST (verified 2026-07-25)

> Concept under conceptualization (Nikhil): value an SFT row by the gap between the
> model's OWN attempt at the prompt and the row's target response — a row only teaches
> if its response is decisively better than what the model already produces ("not yet
> learnt," measured at the response/skill level, not token-loss level). Status: reading
> phase only — no implementation until the concept settles. Candidate first use: run 7
> stage 0.5 audit (sample face subsets, blind pairwise vs generalist's own answers).

Every entry verified against arXiv/ACL/PMLR (title, authors, venue, ID). Ordered by
relevance to the teach-gap.

**1. From Quantity to Quality: Boosting LLM Performance with Self-Guided Data Selection
for Instruction Tuning** — Li et al., NAACL 2024 — arXiv:2308.12032
Introduces IFD (Instruction-Following Difficulty): ratio of the model's conditioned loss
on the target answer to its unconditioned loss; 5-10% of Alpaca selected by IFD beats the
full set. Closest published ancestor — row value is explicitly model-relative — but the
gap lives in loss space over reference tokens; it never generates the model's own answer
and compares pairwise.

**2. Prioritized Training on Points that are Learnable, Worth Learning, and Not Yet
Learnt (RHO-Loss)** — Mindermann et al., ICML 2022 — arXiv:2206.07137
Reducible holdout loss formalizes "learnable ∧ worth learning ∧ not yet learnt." The
teach-gap's exact theoretical frame, operating at token-loss level with a holdout
reference model rather than at skill/response level.

**3. Selective Reflection-Tuning: Student-Selected Data Recycling for LLM
Instruction-Tuning** — Li et al., Findings of ACL 2024 — arXiv:2402.10110
A teacher rewrites rows; the STUDENT decides via IFD/r-IFD whether the rewrite is more
teachable for it. Strongest verified pairwise version-A-vs-B valuation from the student's
perspective — still scored through loss ratios, not judged generations. (Predecessor:
Reflection-Tuning, arXiv:2310.11716.)

**4. Self-Play Fine-Tuning Converts Weak Language Models to Strong Language Models
(SPIN)** — Chen et al., ICML 2024 — arXiv:2401.01335
Trains the model to distinguish its own responses from human references on the same
prompts; converges when they match. The teach-gap operationalized as a TRAINING signal
(reference teaches only while discriminably better) — used to drive the objective, not
to select rows.

**5. Superfiltering: Weak-to-Strong Data Filtering for Fast Instruction-Tuning** —
Li et al., ACL 2024 — arXiv:2402.00530
A weak model's IFD rankings ≈ a strong model's, so cheap models can filter. Practical
support for cheap scoring — and a warning: if weak and strong agree, the score measures
row properties more than the specific student's current gap.

**6. RAFT: Reward rAnked FineTuning** — Dong et al., TMLR 2023 — arXiv:2304.06767
Rejection sampling: generate candidates, keep top-reward, SFT on survivors. Mirror image
of the teach-gap — ranks the model's own samples against each other, never asks whether
the reference beats the model.

**7. LESS: Selecting Influential Data for Targeted Instruction Tuning** — Xia et al.,
ICML 2024 — arXiv:2402.04333
Gradient-influence selection toward a target capability (few-shot examples of the lane).
Answers "worth learning for THIS lane" via gradient geometry; cannot say whether the
reference is better than the model's own attempt.

**8. Dataset Cartography** — Swayamdipta et al., EMNLP 2020 — arXiv:2009.10795
Confidence/variability maps over training dynamics; easy region ≈ "already learnt."
Foundational model-relative data valuation; classification-era, needs a full training
run, no response-quality notion.

Context: **LIMA** (arXiv:2305.11206) — value concentrates in few rows (why selection
matters). **Deita** (arXiv:2312.15685) — the model-AGNOSTIC quality pole; the opposite
of teach-gap's model-relative stance.

**Gap in the literature (verified by the sweep):** no paper surfaced that does exactly
generate-the-model's-response → blind pairwise LLM-judge vs the reference → select rows.
Selective Reflection-Tuning and SPIN are the nearest neighbors. The specific mechanism
appears underexplored — if the run-7 audit validates it, that is a contribution, not a
replication.
