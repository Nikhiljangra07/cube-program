#!/bin/bash
# RUN 4 orchestration — transformation-gate lane (foresight), single new train + on-card
# anchor regens. Card: RTX 6000 Ada class (48GB) is enough — one train with --gc, gens 2+1.
# Uploads required in /workspace/div:
#   scripts (loss_band_gate, build_masked_dataset, train_mastery, gen_threads, head2head_v5 deps)
#   data_src/lane_pages_train.jsonl   (843 scenes, gen-2 final)
#   data_src/anchor_300.jsonl
#   bench_data/                        (48 problems, v5 bench data)
#   adapters/dec_keep1.0  adapters/wrk_keep1.0     (run-2 backup)
#   adapters/wrk_bookC06                            (run-3 bundle — the ablation arm)
cd /workspace/div
set -o pipefail

echo "===== SCORE lane+anchor per-token $(date +%H:%M:%S)"
python loss_band_gate.py --data data_src/lane_pages_train.jsonl --out out/lane_pertok.jsonl --per-token
python loss_band_gate.py --data data_src/anchor_300.jsonl --out out/anchor_pertok.jsonl --per-token

echo "===== BUILD masked keep-0.6 $(date +%H:%M:%S)"
python build_masked_dataset.py --src data_src/lane_pages_train.jsonl --scores out/lane_pertok.jsonl \
    --keep-frac 0.6 --policy band --out masked/lane_keep0.6.jsonl
python build_masked_dataset.py --src data_src/anchor_300.jsonl --scores out/anchor_pertok.jsonl \
    --keep-frac 1.0 --policy band --out masked/anchor_keep1.0.jsonl
cat masked/lane_keep0.6.jsonl masked/anchor_keep1.0.jsonl > masked/wrk_laneF.jsonl
ROWS=$(wc -l < masked/wrk_laneF.jsonl)
STEPS=$(( (ROWS + 7) / 8 * 5 ))
echo "rows=$ROWS matched_steps=$STEPS"

echo "===== TRAIN laneF mastery $(date +%H:%M:%S)"
python train_mastery.py --data masked/wrk_laneF.jsonl --out adapters/wrk_laneF --max-steps $STEPS > out/train_laneF.log 2>&1
[ -f adapters/wrk_laneF/adapter_model.safetensors ] || { echo "RETRY laneF"; python train_mastery.py --data masked/wrk_laneF.jsonl --out adapters/wrk_laneF --max-steps $STEPS > out/train_laneF.log 2>&1; }
grep -h "SAVED adapter\|mastery telemetry" out/train_laneF.log | tail -3

echo "===== GENS 2-parallel then 1 $(date +%H:%M:%S)"
gen() { V5_DATA=/workspace/div/bench_data python gen_threads.py --label "$1" --dec "$2" --wrk "$3" > "out/gen_$1.log" 2>&1; }
gen laneF          adapters/dec_keep1.0 adapters/wrk_laneF &
gen anchor_keep100 adapters/dec_keep1.0 adapters/wrk_keep1.0 &
wait
gen book_C06       adapters/dec_keep1.0 adapters/wrk_bookC06
grep -h "THREADS DONE" out/gen_*.log
echo "RUN4 STAGE1 COMPLETE $(date +%H:%M:%S)"
