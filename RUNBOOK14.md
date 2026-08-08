# RUNBOOK 14 — the honest fusion wall: train the fusion seat on the loop's own certified behavior

**Question:** the wall is measured (25% clean at 4B, 54% at 14B; repair 19/24).
Prompting, size, and code-guided repair are falsified as dissolutions. ONE
mechanism remains untested: **in-distribution self-distillation** — harvest the
loop's own judge-certified clean speeches (born-clean + repair-fixed) as
training targets and train a dedicated fusion adapter. Nikhil's directive
(2026-08-08): mimic the actual loop end-to-end; if fusion stays immature, the
match (run 15 = stage 2) is not worth running.

**Why this bet differs from runs 10/11 (recorded honestly):** those trained on a
FOREIGN teacher's distribution (DeepSeek prose) and failed on fidelity. Run 14
distills the 4B's OWN achieved-good outputs, produced inside the exact pipeline
where the skill must perform (same prompts, same seats, same motion loop).
Precedent risk stands: two prior training-for-fidelity failures. This is the
last training door; if it fails, the wall is falsified against prompting +
size + repair + training, and fork (c) closes the program with full evidence.

## Corpus (loop-mimicking, self-generated, $0 OpenRouter)

- **Problems:** 160 fresh staged problems, generator seed 14, pools FULLY
  DISJOINT from the eval set's (new surnames, new codenames — verified no
  overlap with the frozen 24). Same archetypes + one new one for variety.
- **Pipeline per problem (the REAL loop, verbatim prompts from run13b_pod):**
  audit(V) → read(F) → plan(V) → UPDATE → motion(V) → fusion attempt (keep100)
  → judge reads (session S) → if incoherent: repair with judge flaws verbatim
  (≤3 attempts, the 13B mechanism) → **harvest = every speech the judge
  certifies coherent** (born-clean at attempt 1 or repaired at 2/3).
- **Training pair:** user = the exact FUSE prompt (problem, update, audit, read,
  motion) · assistant = the certified speech. Judge CERTIFIES, never writes —
  generator≠judge family wall intact. Expected yield ~70-85% → ~115-135 pairs;
  yield floor 100 pairs (below → STOP and report before training).
- **Code checker role:** advisory only (13B finding) — its flags join the repair
  feedback text but never gate. The judge decides everything.
- **Diet:** harvested pairs only (no static mix — the adapter has ONE job).
  keep-0.6 band masking, 1.25 epochs, r64 — the fixed recipe. Adapter:
  **wrk_fusion_14_qwen**.

## EVAL (the same strict sense — instrument unchanged)

- **Held-out:** the frozen 24 staged problems (md5 b4c23eb357c9a6d9691f6c1fd50388d1),
  seed-13 pools, disjoint from training by construction. Fresh segments
  generated on the run-14 pod (one pod, one dataset).
- **Arms:** **F14** (wrk_fusion_14_qwen speaks fusion) vs **A** (keep100
  baseline, regenerated). Greedy, single attempt each — NO repair loop in the
  eval; the question is whether the SKILL trained into the weights.
- **Instrument:** judge-everything (session T, Sonnet frozen discipline, cached,
  all-or-discard), code flags advisory. Same certifier prompt byte-reused.
- **FROZEN BARS:**
  1. **Dissolve:** F14 judge-clean ≥ 18/24 (75%) AND ≥ A + 8. Pass → propose
     run-12 stage-1 seam rerun with F14 in the fusion seat → run 15 (stage 2).
  2. **Partial signal (reported, no unlock):** F14 ≥ A + 5 but under bar 1 —
     training moved fidelity but not enough; fork decision returns to Nikhil.
  3. **Null:** F14 < A + 5 → training falsified in-distribution; the wall
     stands against all four mechanisms; recommendation = fork (c).
  4. Delivery reported per arm; an F14 pass with delivery mean < 3.0 must say
     so in the same sentence. Verbosity 60-200 reported.
- **Regression guard (reported):** F14's 24 speeches must keep the tagged
  ESTIMATE line ≥ 22/24 (format retention).

## Budget (≈ $8-10 · OpenRouter $0)

Pod (A40-class): corpus relay 160 × ~55s ≈ 2.5h + repair rounds ≈ 0.4h +
train ≈ 0.5h + eval gens ≈ 0.4h → ~3.8h ≈ $1.9. Anthropic: corpus certify+
repair ≈ 160 + ~120 + ~50 reads + eval 48 + margin ≈ $6-7. All judge verdicts
cached (out/run14/judge_cache.jsonl).

## Isolation & naming

`data/run14/`, `out/run14/`, scripts `run14_*`, judge sessions S (corpus) and
T (eval). Adapter wrk_fusion_14_qwen. Training scripts reused verbatim:
loss_band_gate.py, build_masked_dataset.py, train_masked.py. No bench problems
touched; eval set never enters training.

*Frozen 2026-08-08 pre-spend. Awaiting build verification + Nikhil's GPU.*
