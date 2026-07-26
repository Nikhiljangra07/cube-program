# RUNBOOK 9 — base-model swap: the same face on Qwen3-4B-Instruct-2507

**Question (single variable):** run 8's face FAILED on granite-4.0-micro with a dual
diagnosis — (1) gate-vs-bench definition mismatch, (2) realism decay along deep chains
at 3.4B (converging with divergent-v3's granite ceiling). But every "capacity" data
point in the program comes from ONE model family, and granite-4.0-micro is the weakest
reasoner in its weight class (Qwen3-4B-2507: MMLU-Redux 83.7, MATH-500 97.0). Run 9
re-runs run 8 with EXACTLY ONE variable changed: the base model. Same decomposer data,
same anchor data, same face diet (byte-identical, md5-pinned), same recipe, same bench,
same judge. If the face passes → capacity was the binding cause and the cube reopens on
Qwen. If it fails the same way → the data/bench-definition is binding → run 9b
regenerates the corpus with gate = bench judge verbatim before ANY capacity conclusion.

**Model choice (researched 2026-07-26):** Qwen/Qwen3-4B-Instruct-2507 — Apache 2.0,
text-only dense (no vision tower), non-thinking variant (no <think> blocks), supported
by transformers ≥4.51 (our pinned 4.57.6 stack works unchanged), top of the 3-4B
text-only class. Chosen over Qwen3.5-4B (multimodal + new-arch version risk) and
Gemma 4 E4B (elastic-arch exoticism) to minimize engineering risk. Model identity is
set via the existing `LORA_BASE` env override (built for the H-Small fork) — zero code
changes; LoRA targets are `all-linear` (model-agnostic).

## Ladder (everything retrains from the new base — pod, one card)

| adapter | data (md5-pinned) | keep | epochs |
|---|---|---|---|
| `dec_qwen` | decomposer_train.jsonl, 457 rows (86fffad3…) | 1.0 | 1.25 |
| `wrk_keep100_qwen` (anchor) | worker_train.jsonl, 1,828 rows (b31ae16f…) | 1.0 | 1.25 |
| `wrk_faceF_gen_qwen` | run-8 diet, 1,030 rows (e87ca534…) — BYTE-IDENTICAL | 0.6 band (recomputed under Qwen base — band is base-relative by design) | 1.25 |

r64/α64/lr2e-4/bs8/seq1024/--gc unchanged. Note (annotated, not a bar): the granite
dec/anchor were trained in run 2 under the pre-mastery recipe; the Qwen ladder uses the
program's 1.25-epoch number uniformly. Face-vs-anchor is same-session same-ladder, so
the FACE BAR comparison is internally fair; cross-model anchor comparisons are
reported with this caveat.

## Pod sequence (run9.sh, ~2h ≈ $4)

R0 PREFLIGHT (abort pod if fails): tokenizer chat-template smoke (4.x/5.x-robust) +
24-token generation sanity on the raw base. Then: md5 gate on all 3 data files →
per-token scoring ×3 under Qwen base → masked builds → 3 trains (existence-checked,
1 retry) → gens: `faceF_gen_q` + `anchor_keep100_q` (2 arms, one card, Session-H
card-class control, `V5_WRK_MAXNEW=512`) → bundle `run9_bundle.tgz` + md5.

## Judge Session H (+ H2 only-if-pass)

2 arms × 48, Sonnet 5 (judge frozen — comparability with runs 1-8), max_tokens 12000,
no temperature param, coverage ≥44/48 per arm or discard whole. Direct API (batch
rejected 2026-07-26: 24h-stall risk unacceptable). **H2 replicate runs ONLY if H
passes** (a fail cannot be rescued by the both-sessions bar — run-8 lesson).

## Frozen reads

1. **R1 LADDER SANITY:** both arms reach ≥44/48 parseable thread-sets. Fail → Qwen
   harness problem, fix-and-rerun pod stage, no judging.
2. **R2 ANCHOR READ (reported, not a bar):** anchor_qwen overall + foresight vs granite
   anchor (3.57 / 2.92, cross-session annotated). Headroom check: if anchor foresight
   > 4.3, the +0.20 lane bar collides with the 1-5 scale ceiling — annotate loudly.
3. **R3 FACE BAR (the verdict, unchanged from RUNBOOK8):** foresight(face) ≥
   foresight(anchor) + 0.20 AND overall(face) ≥ overall(anchor) − 0.15, in H AND H2.
4. **VERDICT GRID:**
   - PASS both sessions → **capacity was binding** — first real face exists; cube +
     dispatcher path reopens on Qwen (V/D faces, run 10); granite retired.
   - Face foresight ≤ anchor again → **data/bench-def binding** — run 9b: regenerate
     corpus with gate = bench JUDGE prompt verbatim (1-2-step realism density), still
     on Qwen; capacity conclusions deferred until that runs.
   - In between (+0.00 < Δ < +0.20) → partial capacity effect; report both causes
     live; decide 9b vs write-up with Nikhil.

## Isolation & naming

`out/run9/`, adapters `*_qwen`, `scripts/run9.sh`, `scripts/judge_run9.py`, backup
`density_run9/run9_bundle.tgz`. Granite artifacts untouched. V corpus stays paused
(65/880); no OpenRouter spend this run.

## Budget

Pod ~$4 (RunPod ~$72) · Session H ~$2.5 · H2 only-if-pass ~$2.5 → **$7-9 total**,
Anthropic balance ~$13 → margin ~$4-6. Stage gates: preflight fails → terminate pod
immediately; ladder sanity fails → no judging; H fails → no H2.

---

## RESULTS (2026-07-26, Session H, 48/48 both arms; pod 41 min, preflight 'READY')

| arm | overall | foresight | distinctness | viability |
|---|---|---|---|---|
| faceF_gen_qwen | 3.56 | **2.79** | 3.25 | 3.04 |
| anchor keep100_qwen | 3.73 | 3.12 | 3.65 | 2.94 |

**R3 FACE BAR: FAIL — worse than granite.** Foresight −0.33 vs anchor (granite run 8:
−0.23); overall 3.56 vs floor 3.58 (floor now fails too). H2 skipped (both-session bar).

**R2 ANCHOR READ (the run's positive result):** Qwen anchor 3.73 overall / 3.12
foresight vs granite anchor 3.57 / 2.92 (cross-session, annotated) — same data, same
recipe, stronger base → better generalist across the board. No scale-ceiling issue
(3.12 « 4.3). **Qwen3-4B-Instruct-2507 qualifies as the program's base going forward.**

### Verdict-grid outcome: DATA/BENCH-DEFINITION IS BINDING, not capacity

The single-variable design did its job. A dramatically stronger base (+0.16 overall,
+0.20 foresight at the anchor) trained on the byte-identical deep-chain diet was
dragged BELOW its own anchor by MORE than granite was (−0.33 vs −0.23). If capacity had
been the binding cause of run 8, the stronger model should have converted the same diet
into a smaller deficit or a gain. Instead the diet transfers a style (127 words/thread
vs anchor 84 — restrained relative to granite's 156) that the bench's foresight rubric
("a move or two ahead, WITHOUT over-reach") actively penalizes — and its uniform-chain
voice also drags distinctness (3.25 vs 3.65, dist≥4% 41.7 vs 64.6). **The deep-chain
corpus is bench-toxic on ANY base.** Run 8's cause-1 (gate ≠ bench instrument) is the
binding cause; the capacity story is deferred, not confirmed — divergent-v3's granite
ceiling stands as separate single-family evidence only.

**Pre-registered next step (verdict grid): run 9b** — regenerate the face corpus with
the admission gate = the bench JUDGE prompt verbatim (1-2-step realism density, no
depth mandate), on Qwen, then train + Session I (+I2 only-if-pass). No other change.

Costs: pod $1.6 · Session H ~$2.3. Bundle run9_bundle.tgz md5 708862dc… (3 qwen
adapters + threads + logs).
