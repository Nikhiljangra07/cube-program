#!/bin/bash
# RUN 6 orchestration — exposure sweep on pod B (RTX PRO 6000 Blackwell 96GB).
# Data: byte-identical masked/wrk_laneF.jsonl from run 4. Five fixed-schedule arms
# (train_masked, NOT mastery — mastery self-stops and would collapse x2/x4 into x1).
# Two parallel train tracks (run-3 precedent: dual trains fit a PRO 6000), then gens
# 2-parallel. All thread sets generated on THIS card for the single Session-S judge.
# Uploads required in /workspace/div:
#   scripts (train_masked, gen_threads, dav_eval_v5 + deps)
#   masked/wrk_laneF.jsonl
#   bench_data/eval_problems.jsonl   (the 48-problem bench — NOT the 20-row v5 file)
#   adapters/dec_keep1.0  adapters/wrk_keep1.0
cd /workspace/div
set -o pipefail
mkdir -p out adapters

echo "===== RUN6 START $(date +%H:%M:%S)"
md5sum masked/wrk_laneF.jsonl
wc -l masked/wrk_laneF.jsonl bench_data/eval_problems.jsonl

tr() { # tr <epochs> <name> ; retry once if adapter missing
  python train_masked.py --data masked/wrk_laneF.jsonl --out "adapters/wrk_swp_$2" --epochs "$1" > "out/train_swp_$2.log" 2>&1
  [ -f "adapters/wrk_swp_$2/adapter_model.safetensors" ] || { echo "RETRY swp_$2"; python train_masked.py --data masked/wrk_laneF.jsonl --out "adapters/wrk_swp_$2" --epochs "$1" > "out/train_swp_$2.log" 2>&1; }
  echo "TRAIN DONE swp_$2 $(date +%H:%M:%S)"
}

echo "===== TRAINS: track1=x4 alone, track2=x025->x05->x1->x2 $(date +%H:%M:%S)"
tr 20 x4 &
T1=$!
( tr 1.25 x025; tr 2.5 x05; tr 5 x1; tr 10 x2 ) &
T2=$!
wait $T1 $T2
ls adapters/ | grep swp_

echo "===== GENS 2-parallel, 3 rounds $(date +%H:%M:%S)"
gen() { V5_DATA=/workspace/div/bench_data python gen_threads.py --label "$1" --dec adapters/dec_keep1.0 --wrk "$2" > "out/gen_$1.log" 2>&1; }
gen swp_x025 adapters/wrk_swp_x025 &
gen swp_x05  adapters/wrk_swp_x05 &
wait
gen swp_x1 adapters/wrk_swp_x1 &
gen swp_x2 adapters/wrk_swp_x2 &
wait
gen swp_x4 adapters/wrk_swp_x4 &
gen anchor_keep100 adapters/wrk_keep1.0 &
wait
grep -h "THREADS DONE" out/gen_*.log
echo "RUN6 STAGE1 COMPLETE $(date +%H:%M:%S)"
