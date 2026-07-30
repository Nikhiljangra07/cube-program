#!/bin/bash
# RUN 11 orchestration — delta-derivation viability face (RUNBOOK11).
# Train wrk_faceVD_11_qwen -> faceVD_11 base threads on 16 eval base problems ->
# Eval D revisions (3 arms x 32 twins, greedy) -> Eval A regression pair.
# Uploads required in /workspace/div:
#   scripts: loss_band_gate.py build_masked_dataset.py train_masked.py gen_threads.py
#            dav_eval_v5.py run11_pod_gen.py run11_common.py
#   faces/faceVD_11/worker_train.jsonl        (md5 checked below, set at upload)
#   bench_data/eval_problems.jsonl            (Eval A, 48)
#   bench_data_c/eval_problems.jsonl          (32 inventory problems)
#   bench_data_c16/eval_problems.jsonl        (first 16 = twin base problems)
#   twins/boost_twins.jsonl twins/nerf_twins.jsonl
#   priors/eval_faceV_10_qC_v5_threads.jsonl priors/eval_anchor_10_qC_v5_threads.jsonl
#   adapters/dec_qwen adapters/wrk_keep100_qwen adapters/wrk_faceV_10_qwen
export LORA_BASE="Qwen/Qwen3-4B-Instruct-2507"
cd /workspace/div
set -o pipefail
mkdir -p out adapters masked
DIET_MD5="$1"

echo "===== RUN11 START $(date +%H:%M:%S)  BASE=$LORA_BASE"
[ -n "$DIET_MD5" ] && { echo "$DIET_MD5  faces/faceVD_11/worker_train.jsonl" | md5sum -c - || { echo "DIET MD5 MISMATCH — ABORT"; exit 1; }; }
wc -l faces/faceVD_11/worker_train.jsonl twins/boost_twins.jsonl twins/nerf_twins.jsonl
for A in dec_qwen wrk_keep100_qwen wrk_faceV_10_qwen; do
  [ -f adapters/$A/adapter_model.safetensors ] || { echo "MISSING ADAPTER $A — ABORT"; exit 1; }
done

echo "===== SCORE + BUILD keep-0.6 $(date +%H:%M:%S)"
python loss_band_gate.py --data faces/faceVD_11/worker_train.jsonl --out out/face11_pertok.jsonl --per-token
python build_masked_dataset.py --src faces/faceVD_11/worker_train.jsonl --scores out/face11_pertok.jsonl \
    --keep-frac 0.6 --policy band --out masked/face11.jsonl
wc -l masked/face11.jsonl

echo "===== TRAIN 1.25 epochs $(date +%H:%M:%S)"
python train_masked.py --data masked/face11.jsonl --out adapters/wrk_faceVD_11_qwen --epochs 1.25 > out/train_face11.log 2>&1
[ -f adapters/wrk_faceVD_11_qwen/adapter_model.safetensors ] || { echo "RETRY"; python train_masked.py --data masked/face11.jsonl --out adapters/wrk_faceVD_11_qwen --epochs 1.25 > out/train_face11.log 2>&1; }
[ -f adapters/wrk_faceVD_11_qwen/adapter_model.safetensors ] || { echo "TRAIN FAILED — ABORT"; exit 1; }
echo "TRAIN DONE wrk_faceVD_11_qwen $(date +%H:%M:%S)"

echo "===== BASE THREADS: faceVD_11 on 16 twin base problems $(date +%H:%M:%S)"
V5_DATA=/workspace/div/bench_data_c16 V5_WRK_MAXNEW=512 python gen_threads.py --label faceVD_11_qc16 \
    --dec adapters/dec_qwen --wrk adapters/wrk_faceVD_11_qwen --n 16 > out/gen_c16.log 2>&1
grep -h "THREADS DONE" out/gen_c16.log

echo "===== EVAL D REVISIONS: 3 arms x 32 twins, greedy $(date +%H:%M:%S)"
python run11_pod_gen.py

echo "===== EVAL A PAIR $(date +%H:%M:%S)"
V5_DATA=/workspace/div/bench_data V5_WRK_MAXNEW=512 python gen_threads.py --label faceVD_11_qA \
    --dec adapters/dec_qwen --wrk adapters/wrk_faceVD_11_qwen --n 48 > out/gen_A_face.log 2>&1 &
V5_DATA=/workspace/div/bench_data V5_WRK_MAXNEW=512 python gen_threads.py --label anchor_11_qA \
    --dec adapters/dec_qwen --wrk adapters/wrk_keep100_qwen --n 48 > out/gen_A_anchor.log 2>&1 &
wait
grep -h "THREADS DONE" out/gen_A_*.log

echo "===== BUNDLE $(date +%H:%M:%S)"
tar czf /workspace/run11_bundle.tgz adapters/wrk_faceVD_11_qwen out/evalD_raw.jsonl \
    out/eval_faceVD_11_qc16_v5_threads.jsonl out/eval_faceVD_11_qA_v5_threads.jsonl \
    out/eval_anchor_11_qA_v5_threads.jsonl out/train_face11.log
md5sum /workspace/run11_bundle.tgz
echo "RUN11 POD COMPLETE $(date +%H:%M:%S)"
