#!/bin/bash
# RUN 8 orchestration — generated foresight face on one RTX PRO 6000.
# 1 train (wrk_faceF_gen, keep-0.6, 1.25 epochs) -> 3 gen sets (Session-G card):
# faceF_gen + faceG (run-7 adapter, threads REGENERATED on-card) + anchor keep100.
# Uploads required in /workspace/div:
#   scripts: loss_band_gate.py build_masked_dataset.py train_masked.py gen_threads.py
#            dav_eval_v5.py
#   faces/faceF_gen/worker_train.jsonl        (md5 must match e87ca5344586b60dec74b73663639ca5)
#   bench_data/eval_problems.jsonl            (48-problem bench)
#   adapters/dec_keep1.0  adapters/wrk_keep1.0  adapters/wrk_faceG   (run-7 artifacts)
cd /workspace/div
set -o pipefail
mkdir -p out adapters masked

echo "===== RUN8 START $(date +%H:%M:%S)"
echo "e87ca5344586b60dec74b73663639ca5  faces/faceF_gen/worker_train.jsonl" | md5sum -c - || { echo "DIET MD5 MISMATCH — ABORT"; exit 1; }
wc -l faces/faceF_gen/worker_train.jsonl bench_data/eval_problems.jsonl
for A in dec_keep1.0 wrk_keep1.0 wrk_faceG; do
  [ -f adapters/$A/adapter_model.safetensors ] || { echo "MISSING ADAPTER $A — ABORT"; exit 1; }
done

echo "===== SCORE per-token $(date +%H:%M:%S)"
python loss_band_gate.py --data faces/faceF_gen/worker_train.jsonl --out out/faceFgen_pertok.jsonl --per-token

echo "===== BUILD masked keep-0.6 $(date +%H:%M:%S)"
python build_masked_dataset.py --src faces/faceF_gen/worker_train.jsonl --scores out/faceFgen_pertok.jsonl \
    --keep-frac 0.6 --policy band --out masked/faceFgen.jsonl
wc -l masked/faceFgen.jsonl

echo "===== TRAIN 1.25 epochs $(date +%H:%M:%S)"
python train_masked.py --data masked/faceFgen.jsonl --out adapters/wrk_faceF_gen --epochs 1.25 > out/train_faceFgen.log 2>&1
[ -f adapters/wrk_faceF_gen/adapter_model.safetensors ] || { echo "RETRY faceF_gen"; python train_masked.py --data masked/faceFgen.jsonl --out adapters/wrk_faceF_gen --epochs 1.25 > out/train_faceFgen.log 2>&1; }
[ -f adapters/wrk_faceF_gen/adapter_model.safetensors ] || { echo "TRAIN FAILED — ABORT"; exit 1; }
echo "TRAIN DONE faceF_gen $(date +%H:%M:%S)"

echo "===== GENS Session-G card: 2-parallel then 1 $(date +%H:%M:%S)"
gen() { V5_DATA=/workspace/div/bench_data V5_WRK_MAXNEW=512 python gen_threads.py --label "$1" --dec adapters/dec_keep1.0 --wrk "$2" > "out/gen_$1.log" 2>&1; }
# V5_WRK_MAXNEW=512: faceF_gen writes 4-6 sentence chains; 256 would truncate mid-chain.
# EOS-stopping makes the larger cap a no-op for the short-thread arms (card-class control holds).
gen faceF_gen adapters/wrk_faceF_gen &
gen faceG_r8 adapters/wrk_faceG &
wait
gen anchor_keep100_r8 adapters/wrk_keep1.0
grep -h "THREADS DONE" out/gen_*.log
wc -l out/eval_*_v5_threads.jsonl

echo "===== BUNDLE $(date +%H:%M:%S)"
tar czf /workspace/run8_bundle.tgz adapters/wrk_faceF_gen out/eval_faceF_gen_v5_threads.jsonl \
    out/eval_faceG_r8_v5_threads.jsonl out/eval_anchor_keep100_r8_v5_threads.jsonl out/train_faceFgen.log
md5sum /workspace/run8_bundle.tgz
echo "RUN8 POD COMPLETE $(date +%H:%M:%S)"
