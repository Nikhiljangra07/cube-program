#!/bin/bash
# RUN 10 orchestration — audit-grounded viability face on one RTX PRO 6000 (Qwen base).
# 1 train (wrk_faceV_10_qwen) -> 5 gen sets: {face, anchor} x {Eval A 48, Eval C 32}
# + face-only Eval C twins 16 (calibration probe), all one card (Sessions K + L
# card-class control).
# Uploads required in /workspace/div:
#   scripts: loss_band_gate.py build_masked_dataset.py train_masked.py gen_threads.py dav_eval_v5.py
#   faces/faceV_10/worker_train.jsonl         (md5 0bc1fbc36fdf694cd8af29aa8e58fc4f)
#   bench_data/eval_problems.jsonl            (Eval A, 48)
#   bench_data_c/eval_problems.jsonl          (Eval C inventory, 32, source md5 ea0707a5)
#   bench_data_ct/eval_problems.jsonl         (Eval C twins, 16, source md5 d3ec49d5)
#   adapters/dec_qwen  adapters/wrk_keep100_qwen   (run9 bundle artifacts, no retrain)
export LORA_BASE="Qwen/Qwen3-4B-Instruct-2507"
cd /workspace/div
set -o pipefail
mkdir -p out adapters masked

echo "===== RUN10 START $(date +%H:%M:%S)  BASE=$LORA_BASE"
echo "0bc1fbc36fdf694cd8af29aa8e58fc4f  faces/faceV_10/worker_train.jsonl" | md5sum -c - || { echo "DIET MD5 MISMATCH — ABORT"; exit 1; }
wc -l faces/faceV_10/worker_train.jsonl bench_data/eval_problems.jsonl bench_data_c/eval_problems.jsonl bench_data_ct/eval_problems.jsonl
for A in dec_qwen wrk_keep100_qwen; do
  [ -f adapters/$A/adapter_model.safetensors ] || { echo "MISSING ADAPTER $A — ABORT"; exit 1; }
done

echo "===== SCORE + BUILD keep-0.6 $(date +%H:%M:%S)"
python loss_band_gate.py --data faces/faceV_10/worker_train.jsonl --out out/face10_pertok.jsonl --per-token
python build_masked_dataset.py --src faces/faceV_10/worker_train.jsonl --scores out/face10_pertok.jsonl \
    --keep-frac 0.6 --policy band --out masked/face10.jsonl
wc -l masked/face10.jsonl

echo "===== TRAIN 1.25 epochs $(date +%H:%M:%S)"
python train_masked.py --data masked/face10.jsonl --out adapters/wrk_faceV_10_qwen --epochs 1.25 > out/train_face10.log 2>&1
[ -f adapters/wrk_faceV_10_qwen/adapter_model.safetensors ] || { echo "RETRY"; python train_masked.py --data masked/face10.jsonl --out adapters/wrk_faceV_10_qwen --epochs 1.25 > out/train_face10.log 2>&1; }
[ -f adapters/wrk_faceV_10_qwen/adapter_model.safetensors ] || { echo "TRAIN FAILED — ABORT"; exit 1; }
echo "TRAIN DONE wrk_faceV_10_qwen $(date +%H:%M:%S)"

echo "===== GENS: Eval A pair, Eval C pair, twins — 2-parallel each $(date +%H:%M:%S)"
genA()  { V5_DATA=/workspace/div/bench_data    V5_WRK_MAXNEW=512 python gen_threads.py --label "$1" --dec adapters/dec_qwen --wrk "$2" --n 48 > "out/gen_$1.log" 2>&1; }
genC()  { V5_DATA=/workspace/div/bench_data_c  V5_WRK_MAXNEW=512 python gen_threads.py --label "$1" --dec adapters/dec_qwen --wrk "$2" --n 32 > "out/gen_$1.log" 2>&1; }
genCT() { V5_DATA=/workspace/div/bench_data_ct V5_WRK_MAXNEW=512 python gen_threads.py --label "$1" --dec adapters/dec_qwen --wrk "$2" --n 16 > "out/gen_$1.log" 2>&1; }
genA faceV_10_qA adapters/wrk_faceV_10_qwen &
genA anchor_10_qA adapters/wrk_keep100_qwen &
wait
genC faceV_10_qC adapters/wrk_faceV_10_qwen &
genC anchor_10_qC adapters/wrk_keep100_qwen &
wait
genCT faceV_10_qCtwin adapters/wrk_faceV_10_qwen
grep -h "THREADS DONE" out/gen_*.log
wc -l out/eval_*10_q*_v5_threads.jsonl

echo "===== BUNDLE $(date +%H:%M:%S)"
tar czf /workspace/run10_bundle.tgz adapters/wrk_faceV_10_qwen out/eval_*10_q*_v5_threads.jsonl out/train_face10.log
md5sum /workspace/run10_bundle.tgz
echo "RUN10 POD COMPLETE $(date +%H:%M:%S)"
