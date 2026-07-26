#!/bin/bash
# RUN 9B orchestration — aligned-target foresight face on one RTX PRO 6000 (Qwen base).
# 1 train (wrk_faceF_9b_qwen) -> 4 gen sets: {face, anchor} x {Eval A 48, Eval B 24},
# all one card (Sessions I + J card-class control).
# Uploads required in /workspace/div:
#   scripts: loss_band_gate.py build_masked_dataset.py train_masked.py gen_threads.py dav_eval_v5.py
#   faces/faceF_9b/worker_train.jsonl        (md5 e0896b4d3a3942be49147749da69c763)
#   bench_data/eval_problems.jsonl           (Eval A, 48)
#   bench_data_b/eval_problems.jsonl         (Eval B dossiers, 24, md5-frozen de754dad on source file)
#   adapters/dec_qwen  adapters/wrk_keep100_qwen   (run9 bundle artifacts)
export LORA_BASE="Qwen/Qwen3-4B-Instruct-2507"
cd /workspace/div
set -o pipefail
mkdir -p out adapters masked

echo "===== RUN9B START $(date +%H:%M:%S)  BASE=$LORA_BASE"
echo "e0896b4d3a3942be49147749da69c763  faces/faceF_9b/worker_train.jsonl" | md5sum -c - || { echo "DIET MD5 MISMATCH — ABORT"; exit 1; }
wc -l faces/faceF_9b/worker_train.jsonl bench_data/eval_problems.jsonl bench_data_b/eval_problems.jsonl
for A in dec_qwen wrk_keep100_qwen; do
  [ -f adapters/$A/adapter_model.safetensors ] || { echo "MISSING ADAPTER $A — ABORT"; exit 1; }
done

echo "===== SCORE + BUILD keep-0.6 $(date +%H:%M:%S)"
python loss_band_gate.py --data faces/faceF_9b/worker_train.jsonl --out out/face9b_pertok.jsonl --per-token
python build_masked_dataset.py --src faces/faceF_9b/worker_train.jsonl --scores out/face9b_pertok.jsonl \
    --keep-frac 0.6 --policy band --out masked/face9b.jsonl
wc -l masked/face9b.jsonl

echo "===== TRAIN 1.25 epochs $(date +%H:%M:%S)"
python train_masked.py --data masked/face9b.jsonl --out adapters/wrk_faceF_9b_qwen --epochs 1.25 > out/train_face9b.log 2>&1
[ -f adapters/wrk_faceF_9b_qwen/adapter_model.safetensors ] || { echo "RETRY"; python train_masked.py --data masked/face9b.jsonl --out adapters/wrk_faceF_9b_qwen --epochs 1.25 > out/train_face9b.log 2>&1; }
[ -f adapters/wrk_faceF_9b_qwen/adapter_model.safetensors ] || { echo "TRAIN FAILED — ABORT"; exit 1; }
echo "TRAIN DONE wrk_faceF_9b_qwen $(date +%H:%M:%S)"

echo "===== GENS: Eval A pair then Eval B pair, 2-parallel each $(date +%H:%M:%S)"
genA() { V5_DATA=/workspace/div/bench_data   V5_WRK_MAXNEW=512 python gen_threads.py --label "$1" --dec adapters/dec_qwen --wrk "$2" --n 48 > "out/gen_$1.log" 2>&1; }
genB() { V5_DATA=/workspace/div/bench_data_b V5_WRK_MAXNEW=512 python gen_threads.py --label "$1" --dec adapters/dec_qwen --wrk "$2" --n 24 > "out/gen_$1.log" 2>&1; }
genA faceF_9b_qA adapters/wrk_faceF_9b_qwen &
genA anchor_9b_qA adapters/wrk_keep100_qwen &
wait
genB faceF_9b_qB adapters/wrk_faceF_9b_qwen &
genB anchor_9b_qB adapters/wrk_keep100_qwen &
wait
grep -h "THREADS DONE" out/gen_*.log
wc -l out/eval_*9b_q*_v5_threads.jsonl

echo "===== BUNDLE $(date +%H:%M:%S)"
tar czf /workspace/run9b_bundle.tgz adapters/wrk_faceF_9b_qwen out/eval_*9b_q*_v5_threads.jsonl out/train_face9b.log
md5sum /workspace/run9b_bundle.tgz
echo "RUN9B POD COMPLETE $(date +%H:%M:%S)"
