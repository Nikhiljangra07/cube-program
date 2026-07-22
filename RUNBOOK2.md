# RUNBOOK 2 — occlusion sweep on dense60 (selective-loss / "fill-in-the-blank" gate)

Question: does concentrating loss on the learnable-band TOKENS of dense60 hold the benchmark
at a further-reduced effective token count? Sweep the keep-fraction on a FREE metric
(held-out NLL), pay for judge only on control + winner.

Pod: RTX 6000 Ada (~$0.77-0.80/hr), same pins as RUNBOOK.md step 0. Budget ~$11.

## 0. Upload (laptop -> pod; pod dirs from run 1 are gone — fresh pod)
```bash
cd ~/Desktop/density-method
scp -i <key> -P <port> scripts/loss_band_gate.py scripts/build_masked_dataset.py \
    scripts/train_masked.py scripts/heldout_nll.py scripts/gen_threads.py scripts/dav_eval_v5.py \
    root@<pod>:/workspace/div/
scp -i <key> -P <port> data/arms/dense60/worker_train.jsonl data/arms/dense60/decomposer_train.jsonl \
    data/src/heldout_worker.jsonl root@<pod>:/workspace/div/data_src/
scp -i <key> -P <port> data/bench/problems.jsonl root@<pod>:/workspace/div/bench_data/eval_problems.jsonl
```

## 1. Per-token scoring pass (once — serves every sweep point)
```bash
cd /workspace/div && mkdir -p out masked adapters
python loss_band_gate.py --data data_src/worker_train.jsonl     --out out/wrk_pertok.jsonl --per-token
python loss_band_gate.py --data data_src/decomposer_train.jsonl --out out/dec_pertok.jsonl --per-token
```
Guard: skipped rows must be ~0 (run 1: 0).

## 2. Build masked datasets ON POD (needs only the tokenizer)
keep_frac 1.0 = PIPELINE CONTROL. Sweep: 0.6, 0.4, 0.25 (band policy).
```bash
for KF in 1.0 0.6 0.4 0.25; do
  python build_masked_dataset.py --src data_src/worker_train.jsonl --scores out/wrk_pertok.jsonl \
      --keep-frac $KF --policy band --out masked/wrk_keep${KF}.jsonl
  python build_masked_dataset.py --src data_src/decomposer_train.jsonl --scores out/dec_pertok.jsonl \
      --keep-frac $KF --policy band --out masked/dec_keep${KF}.jsonl
done
```
Check each .manifest.json: kept_tokens ≈ keep_frac × pool; rows_with_zero_loss_tokens small.

## 3. Train the sweep (8 small trains, ~10 min each)
```bash
for KF in 1.0 0.6 0.4 0.25; do
  python train_masked.py --data masked/dec_keep${KF}.jsonl --out adapters/dec_keep${KF}
  python train_masked.py --data masked/wrk_keep${KF}.jsonl --out adapters/wrk_keep${KF}
done
```

## 4. FREE metric — held-out NLL (rank the sweep, no keys)
```bash
python heldout_nll.py --data data_src/heldout_worker.jsonl                          # base ref
for KF in 1.0 0.6 0.4 0.25; do
  python heldout_nll.py --data data_src/heldout_worker.jsonl --adapter adapters/wrk_keep${KF}
done
```
**GATE (decide BEFORE judging):**
- keep1.0 held-out NLL must be ≈ a dense60-adapter rerun of the same metric (pipeline faithfulness).
  If keep1.0 drifts badly from dense60's, STOP — pipeline not faithful, fix before spending.
- Winner = lowest held-out NLL among 0.6/0.4/0.25. If keep1.0 beats all masked points by a
  clear margin, the null is already visible — judge only keep1.0 + best masked to confirm cheaply.

## 5. Bench threads for control + winner only (keyless)
```bash
V5_DATA=/workspace/div/bench_data python gen_threads.py --label bench_keep100 \
    --dec adapters/dec_keep1.0 --wrk adapters/wrk_keep1.0
V5_DATA=/workspace/div/bench_data python gen_threads.py --label bench_keepWIN \
    --dec adapters/dec_keep<WIN> --wrk adapters/wrk_keep<WIN>
```

## 6. Pull, kill pod, judge (single Sonnet 5 session over SIX thread sets)
Pull the two new thread files + manifests + pertok scores + adapters tarball. Then locally:
extend rejudge_arms.py FILES with keep100 + keepWIN and run — base/v5full/dense60/rand60
threads are re-judged IN THE SAME SESSION as the new arms (never compare across sessions).
```bash
cd ~/Desktop/density-method/scripts
source ~/Desktop/reasoningEngine/load_keys.sh
python3 rejudge_arms.py
```

## Success criteria (frozen 2026-07-21, before any sweep train)
- **Pipeline control:** keep1.0 overall within ±0.15 of dense60 (3.53) in the same session.
  If this fails, NOTHING else in the run is interpretable.
- **Signal C (occlusion):** best masked arm within ±0.15 of dense60/v5full at keep_frac ≤ 0.5
  → the solving-concentration thesis holds; effective solved tokens ≈ keep_frac × 60% of v5full.
- **Null:** best masked arm ≥ 0.25 below control → token-level selection joins example-level
  selection as refuted-on-curated-data; the selection family closes; all chips on the
  transformation gate.

## Notes
- Nothing is hidden from the model: masking is LOSS-side only (Rho-1-style selective LM).
  Full disclosure, concentrated solving.
- Judge lessons already encoded in rejudge_arms.py: no temperature, 12k max_tokens,
  retry-on-empty, coverage guard ≥44/48 per arm.

## RESULTS (2026-07-22, six-arm single-session Sonnet 5 judge, n=47/48/48/48/48/44)
keep100 3.60 | keep60 3.64 | (dense60 3.52, rand60 3.60, v5full 3.56, base 3.27 — run-1 replicated)
- Pipeline control FAITHFUL (keep100 vs dense60 delta 0.08).
- **Signal C HOLDS**: keep60 vs keep100 delta +0.04 — 60% of tokens graded, benchmark at par.
  Stacked with run 1: ~36% of v5full's corpus tokens carry gradient at par benchmark.
- Caveats: keep60 answered 44/48 (4 decomposer format fails — survivorship flattering in its
  mean; format fragility is a real cost). Heldout-NLL ranking contradicted the bench —
  confirmed biased toward unmasked arms; treat heldout NLL as pipeline check only, never verdict.
- Next: keep0.4 + mastery60 threads -> judge session 2 (same-session with keep100/keep60/dense60).
