#!/bin/bash
# RUN 7 orchestration — face factory II on one RTX PRO 6000.
# 4 trains (tiny) -> 5 gen sets 2-parallel (the long pole, all one card for Session-F)
# -> peft hot-swap mechanics test (after gens; upgrades peft only once gens are done).
# Uploads required in /workspace/div:
#   scripts: loss_band_gate.py build_masked_dataset.py train_masked.py gen_threads.py
#            dav_eval_v5.py swap_test.py
#   faces/face_{F,D,V,G}/worker_train.jsonl
#   bench_data/eval_problems.jsonl   (48-problem bench)
#   adapters/dec_keep1.0  adapters/wrk_keep1.0
cd /workspace/div
set -o pipefail
mkdir -p out adapters masked

echo "===== RUN7 START $(date +%H:%M:%S)"
md5sum faces/face_*/worker_train.jsonl
wc -l faces/face_*/worker_train.jsonl bench_data/eval_problems.jsonl

echo "===== SCORE per-token $(date +%H:%M:%S)"
for K in F D V G; do
  python loss_band_gate.py --data faces/face_$K/worker_train.jsonl --out out/face${K}_pertok.jsonl --per-token
done

echo "===== BUILD masked $(date +%H:%M:%S)"
for K in F D V; do
  python build_masked_dataset.py --src faces/face_$K/worker_train.jsonl --scores out/face${K}_pertok.jsonl \
      --keep-frac 0.6 --policy band --out masked/face$K.jsonl
done
python build_masked_dataset.py --src faces/face_G/worker_train.jsonl --scores out/faceG_pertok.jsonl \
    --keep-frac 1.0 --policy band --out masked/faceG.jsonl
wc -l masked/face*.jsonl

echo "===== TRAINS 4x sequential, 1.25 epochs $(date +%H:%M:%S)"
for K in F D V G; do
  python train_masked.py --data masked/face$K.jsonl --out adapters/wrk_face$K --epochs 1.25 > out/train_face$K.log 2>&1
  [ -f adapters/wrk_face$K/adapter_model.safetensors ] || { echo "RETRY face$K"; python train_masked.py --data masked/face$K.jsonl --out adapters/wrk_face$K --epochs 1.25 > out/train_face$K.log 2>&1; }
  echo "TRAIN DONE face$K $(date +%H:%M:%S)"
done
ls adapters/ | grep face

echo "===== GENS 2-parallel, 3 rounds $(date +%H:%M:%S)"
gen() { V5_DATA=/workspace/div/bench_data python gen_threads.py --label "$1" --dec adapters/dec_keep1.0 --wrk "$2" > "out/gen_$1.log" 2>&1; }
gen faceF adapters/wrk_faceF &
gen faceD adapters/wrk_faceD &
wait
gen faceV adapters/wrk_faceV &
gen faceG adapters/wrk_faceG &
wait
gen anchor_keep100 adapters/wrk_keep1.0
grep -h "THREADS DONE" out/gen_*.log

echo "===== MECHANICS: peft hot-swap test $(date +%H:%M:%S)"
python swap_test.py > out/swap_test.log 2>&1
tail -20 out/swap_test.log
echo "RUN7 STAGE1 COMPLETE $(date +%H:%M:%S)"
