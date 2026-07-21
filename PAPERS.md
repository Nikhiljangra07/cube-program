# PAPERS — the research grounding the density methodology

> Compiled 2026-07-21 from a 4-agent verified literature sweep (each claim checked against
> the primary source; residual uncertainties marked [unverified] in the agent dossiers).
> Organized by the pillar of OUR methodology each paper grounds — not by field.
> Read top-to-bottom within a pillar; the ★ papers are the load-bearing citations.

---

## Pillar I — The learnable band (the SELECTION gate; what step zero tests)

★ **Marion et al. 2023 — "When Less is More: Investigating Data Pruning for Pretraining LLMs at Scale"** — [arXiv:2309.04564](https://arxiv.org/abs/2309.04564)
THE direct precedent. Rank pretraining data by reference-model perplexity, keep the **middle**
of the distribution → beats keeping easiest, hardest, or everything. "Middle 50% → 0.97%
perplexity improvement; middle 30% nearly the same (0.80%)." Simple perplexity beat fancier
EL2N/memorization scores. Our loss_band_gate.py is this idea, applied to SFT rows.

★ **Mindermann et al. 2022 — RHO-Loss ("learnable, worth learning, not yet learnt")** — ICML — [arXiv:2206.07137](https://arxiv.org/abs/2206.07137)
The theory of WHY a band: low-loss points are already learnt (no gradient), high-loss points
are often noise (unlearnable). Reducible-holdout-loss selection = 18x fewer steps on
Clothing-1M. Our static NLL band is the cheap proxy for their dynamic criterion.

★ **Lin et al. 2024 — Rho-1: "Not All Tokens Are What You Need"** — NeurIPS 2024 best-paper runner-up — [arXiv:2404.07965](https://arxiv.org/abs/2404.07965)
Token-granularity version: a reference model scores tokens, loss is applied only to
high-value ones → matches DeepSeekMath with **3% of the tokens**. The strongest published
"density per token is real" result. Cite as nearest prior art; our gate is example-level.

**Paul et al. 2021 — "Deep Learning on a Data Diet" (EL2N/GraNd)** — NeurIPS — [arXiv:2107.07075](https://arxiv.org/abs/2107.07075)
The score-family ancestor: per-example error magnitude early in training predicts importance;
prune 50% of CIFAR-10 and slightly IMPROVE accuracy.

**Sorscher et al. 2022 — "Beyond Neural Scaling Laws"** — NeurIPS Outstanding Paper — [arXiv:2206.14486](https://arxiv.org/abs/2206.14486)
Good pruning metrics can break power-law scaling toward exponential. CRITICAL nuance:
"with abundant (scarce) initial data, retain only hard (easy) examples" — the band's
placement is REGIME-DEPENDENT. The mid band is the interior solution.

**Ankner et al. 2024 — "Perplexed by Perplexity"** — [arXiv:2405.20541](https://arxiv.org/abs/2405.20541)
A 125M reference model can prune for a 3B trainee (+2.04 pts downstream). WARNING built in:
mid-band won on Dolma, HIGH-band won on the Pile — "the best selection criteria from one
dataset does not transfer to another." Our measured band edges are corpus-specific facts.

**Also:** DoReMi (domain-level excess-loss weighting, [arXiv:2305.10429](https://arxiv.org/abs/2305.10429)) ·
Ask-LLM + Density (LLM-judged quality vs coverage sampling, 19-sampler benchmark,
[arXiv:2402.09668](https://arxiv.org/abs/2402.09668)) · D4/SemDeDup (the orthogonal diversity/dedup axis,
[arXiv:2308.12284](https://arxiv.org/abs/2308.12284), [arXiv:2303.09540](https://arxiv.org/abs/2303.09540)).

**The gap step zero fills:** every mid-band result above is pretraining-scale. Mid-band NLL
gating for SFT of small models is NOT established in this literature — our run is a new
datapoint, not a replication.

---

## Pillar II — Quality over quantity (the JUDGE gate we already run)

★ **Zhou et al. 2023 — LIMA: "Less Is More for Alignment"** — NeurIPS — [arXiv:2305.11206](https://arxiv.org/abs/2305.11206)
1,000 curated pairs align a 65B model. Founding claim + the "Superficial Alignment
Hypothesis." Read WITH its rebuttals (below) — holds for style/persona, not capability.

★ **Chen et al. 2023 — AlpaGasus** — ICLR 2024 — [arXiv:2307.08701](https://arxiv.org/abs/2307.08701)
ChatGPT-as-judge scores 52k Alpaca rows, keep the top 9k → beats training on all 52k.
Our 6-dim judge gate, published. **Liu et al. 2023 — Deita** ([arXiv:2312.15685](https://arxiv.org/abs/2312.15685)):
multi-dimensional judge (complexity/quality/diversity), 6k rows ≈ 10x more data — closest
analogue to a multi-dim rubric; lesson: diversity must be enforced SEPARATELY from quality.

★ **phi series — "Textbooks Are All You Need" → phi-4** — [arXiv:2306.11644](https://arxiv.org/abs/2306.11644), [arXiv:2404.14219](https://arxiv.org/abs/2404.14219), [arXiv:2412.08905](https://arxiv.org/abs/2412.08905)
The pretraining-scale existence proof: 1.3B on 7B curated+synthetic tokens → 50.6% HumanEval;
phi-3-mini (3.8B) rivals Mixtral/GPT-3.5 "entirely [via] the dataset"; phi-4 outscores its
own teacher on GPQA/MATH with >50% synthetic tokens.

**Penedo et al. 2024 — FineWeb-Edu** ([arXiv:2406.17557](https://arxiv.org/abs/2406.17557)) — LLM-judge gating at
1.3T-token scale. **Li et al. 2024 — DataComp-LM** ([arXiv:2406.11794](https://arxiv.org/abs/2406.11794)) — the
gold-standard CONTROLLED design (fixed recipe, vary only corpus): model-based filtering is
the single biggest intervention; 7B→64% MMLU with 6.6x less compute than Llama-3-8B. Our
fixed-recipe/vary-corpus ablations mirror this design.

---

## Pillar III — The TRANSFORMATION gate (essence → scenes; the actual vision, iteration 1b)

★ **Maini et al. 2024 — WRAP: "Rephrasing the Web"** — ICML — [arXiv:2401.16380](https://arxiv.org/abs/2401.16380)
Paraphrase web text into denser styles, mix with real → ~3x pretraining speedup, >10% ppl
gain. The gain is density/style normalization, NOT new knowledge. Closest published
validation of "same information, denser rendering → more learning per token."

★ **Su et al. 2024 — Nemotron-CC** — [arXiv:2412.02595](https://arxiv.org/abs/2412.02595)
Industrial version: 1.9T synthetic tokens via 4-5 rewrite formats (Q&A, distilled summary,
knowledge list, knowledge-dense rewrite) → +5 MMLU or 4x effective data. Their public
prompt suite is a production essence-extraction gate — steal from it for 1b.

★ **Allen-Zhu & Li 2024 — Physics of LMs 3.3: "Knowledge Capacity Scaling Laws"** — ICLR 2025 — [arXiv:2404.05405](https://arxiv.org/abs/2404.05405)
LMs store ~2 bits/param given ~1000 exposures per fact; junk-mixed data degrades rare-fact
capacity ~an order of magnitude. Companion 3.1 ([arXiv:2309.14316](https://arxiv.org/abs/2309.14316)): facts must
appear in DIVERSE PARAPHRASES to be extractable, not just memorized. The theoretical
justification for one-essence-many-scenes.

**Fujii et al. 2025 — SwallowMath/Code** ([arXiv:2505.02881](https://arxiv.org/abs/2505.02881)) — full-rewrite into
self-contained units: +17 HumanEval, +12.4 GSM8K at fixed budget; "restore missing context +
make self-contained" beat filtering alone — exactly the completeness property our scenes need.
**BeyondWeb 2025** ([arXiv:2508.10975](https://arxiv.org/abs/2508.10975)) — the design manual: style diversity of
rewrites matters more than rewriter size. **ProX** ([arXiv:2409.17115](https://arxiv.org/abs/2409.17115)) — a 0.3B
model emitting edit-programs already buys big gains: the cheap end of the spectrum.
**Orca 1/2** ([arXiv:2306.02707](https://arxiv.org/abs/2306.02707)) — explanation TRACES are the dense tokens:
render mechanics, not conclusions. **Instruction backtranslation** ([arXiv:2308.06259](https://arxiv.org/abs/2308.06259)) —
treat a real source passage as the answer, synthesize the situation that produces it — a
grounded way to sceneify books. **Farzi** ([arXiv:2310.09983](https://arxiv.org/abs/2310.09983)) — autoregressive
dataset distillation reaching 98-120% of full-data performance from a tiny synthetic set:
the ceiling argument for 50M→15-25M.

### Failure modes (tape to the wall before building 1b)
- **Model collapse** — Shumailov et al., Nature 2024 ([arXiv:2305.17493](https://arxiv.org/abs/2305.17493)):
  recursive training on model output loses distribution tails. Antidote (Gerstgrasser 2024,
  [arXiv:2404.01413](https://arxiv.org/abs/2404.01413)): ACCUMULATE synthetic alongside real, never replace;
  single-generation rewriting grounded in real source text (WRAP regime) is the safe zone.
- **Style homogenization** — Padmakumar & He, ICLR 2024 ([arXiv:2309.05196](https://arxiv.org/abs/2309.05196)):
  one rewriter imprints one voice on everything. Fix: multiple styles per essence unit +
  raw-text fraction in the mix. Matches our own corpus-voice-diversity feedback rule.
- **Judge length bias** — Zhao et al., ICML 2024 "Long Is More" ([arXiv:2402.04833](https://arxiv.org/abs/2402.04833)):
  keeping the 1,000 LONGEST rows beats LIMA and AlpaGasus under LLM judging. Any judge gate
  must beat this dumb baseline to prove it selects on substance.
- **Capability vs style** — Scale AI 2024 ([arXiv:2410.03717](https://arxiv.org/abs/2410.03717)): capability gains
  scale as a power law in example count; curation moves the intercept, not the exponent.
  Berkeley "False Promise" ([arXiv:2305.15717](https://arxiv.org/abs/2305.15717)): win-rate evals overstate
  style transfer as capability. Pair judge scores with objective evals.

---

## Pillar IV — Scaling-law framing (how the paper positions itself)

★ **Hoffmann et al. 2022 — Chinchilla** — [arXiv:2203.15556](https://arxiv.org/abs/2203.15556)
Compute-optimal params:tokens ≈ 1:20, derived on a FIXED corpus — tokens treated as
interchangeable. Our positioning: the data-quality axis Chinchilla holds constant.
(Kaplan 2020, [arXiv:2001.08361](https://arxiv.org/abs/2001.08361), is the precedent that scaling conclusions
flip when a held-constant variable is corrected.)

★ **Muennighoff et al. 2023 — "Scaling Data-Constrained LMs"** — NeurIPS — [arXiv:2305.16264](https://arxiv.org/abs/2305.16264)
Up to ~4 epochs of repeated data ≈ fresh data. The license for "fewer, denser tokens ×
more passes": repetition is not the tax — low density is.

**Goyal et al. 2024 — "Scaling Laws for Data Filtering"** — CVPR — [arXiv:2404.07177](https://arxiv.org/abs/2404.07177)
Quality and repetition interact: curated data loses utility with reuse; optimal filtering
aggressiveness depends on compute budget. Quality shifts the CURVE, not just the intercept.

---

## Pillar V — The cognitive precedent (the analogies, with real citations)

★ **van Noorden 1975 (thesis, [PDF](https://pure.tue.nl/ws/files/3389175/152538.pdf)) + Bregman 1990, *Auditory Scene Analysis*** —
The ABA streaming paradigm: **fission boundary** (below = always one stream) and **temporal
coherence boundary** (above = always two), with a bistable ambiguous region between where
organization is actively computed. Our band edges now have their perceptual names.

★ **Wilson et al. 2019 — "The Eighty Five Percent Rule for optimal learning"** — Nature Communications — [link](https://www.nature.com/articles/s41467-019-12552-4)
For SGD-based learners on binary tasks, learning is fastest at ~85% training accuracy
(optimal error 15.87%, derived analytically). The quantified anchor: optimal difficulty
falls out of gradient math, not just pedagogy.

**Bjork & Bjork — desirable difficulties** ([PDF](https://bjorklab.psych.ucla.edu/wp-content/uploads/sites/13/2016/04/EBjork_RBjork_2011.pdf)) + **Roediger & Karpicke 2006 — testing effect**:
effortful retrieval beats fluent re-exposure at 2 days and 1 week. **Slamecka & Graf 1978 —
generation effect**: generated answers are remembered better than read ones — "the solving
is the training," 1978 edition. **Vygotsky — zone of proximal development**: the original
learnable band.

---

## Priority reading order (if reading only ten)

1. Marion 2023 (the mid-band result itself)
2. Rho-1 (density at token granularity, the nearest prior art)
3. RHO-Loss (the why of the band)
4. WRAP (rewriting works — the 1b thesis)
5. Nemotron-CC (rewriting at industrial scale + the prompt suite)
6. Physics of LMs 3.3 + 3.1 (bits per param, paraphrase-extractability)
7. Muennighoff 2023 (epochs over dense data are near-free)
8. Wilson 2019 (the 85% rule — quantified band)
9. Shumailov Nature 2024 + Gerstgrasser (collapse and its antidote)
10. Zhao "Long Is More" (the baseline every judge gate must beat)

## What the sweep changes about OUR next steps

- Step zero's framing upgrades from "toy test" to "novel SFT-scale datapoint of the Marion
  mid-band result" — pretraining-scale precedent exists, SFT-scale does not.
- The 1b transformation gate inherits five design rules straight from the literature:
  ground every scene in real source text at generation depth 1; render each essence unit in
  MULTIPLE styles; keep a raw-text fraction; keep the verifier stage; measure diversity
  explicitly (homogenization, not information loss, is the documented killer).
- Two new controls to schedule eventually: the LENGTH baseline (Zhao) for the judge gate,
  and a band-placement sensitivity check (Ankner: bands don't transfer between corpora).
