#!/bin/bash
# RUN 3 orchestration — Clausewitz page-mastery, dual fraction (0.4 + 0.6), RTX PRO 6000 96GB.
# Paired parallel trains (~45GB each) with sequential fallback; gens 3-at-a-time (~14GB each).
cd /workspace/div
set -o pipefail

echo "===== SCORE book+anchor per-token $(date +%H:%M:%S)"
python loss_band_gate.py --data data_src/book_pages_train.jsonl --out out/book_pertok.jsonl --per-token
python loss_band_gate.py --data data_src/anchor_300.jsonl --out out/anchor_pertok.jsonl --per-token

echo "===== BUILD masked $(date +%H:%M:%S)"
for KF in 1.0 0.6 0.4; do
  python build_masked_dataset.py --src data_src/book_pages_train.jsonl --scores out/book_pertok.jsonl \
      --keep-frac $KF --policy band --out masked/book_keep$KF.jsonl
done
python build_masked_dataset.py --src data_src/anchor_300.jsonl --scores out/anchor_pertok.jsonl \
    --keep-frac 1.0 --policy band --out masked/anchor_keep1.0.jsonl

cat masked/book_keep1.0.jsonl masked/anchor_keep1.0.jsonl > masked/wrk_bookA.jsonl
cat masked/book_keep0.6.jsonl masked/anchor_keep1.0.jsonl > masked/wrk_bookB06.jsonl
cat masked/book_keep0.4.jsonl masked/anchor_keep1.0.jsonl > masked/wrk_bookB04.jsonl
ROWS=$(wc -l < masked/wrk_bookA.jsonl)
STEPS=$(( (ROWS + 7) / 8 * 5 ))
echo "rows=$ROWS matched_steps=$STEPS"

train_fixed() { python train_masked.py --data "$1" --out "$2" > "$3" 2>&1; }
train_mast()  { python train_mastery.py --data "$1" --out "$2" --max-steps $STEPS > "$3" 2>&1; }
ok() { [ -f "$1/adapter_model.safetensors" ]; }

echo "===== TRAIN pair B04 // B06 $(date +%H:%M:%S)"
train_fixed masked/wrk_bookB04.jsonl adapters/wrk_bookB04 out/train_B04.log &
train_fixed masked/wrk_bookB06.jsonl adapters/wrk_bookB06 out/train_B06.log &
wait
ok adapters/wrk_bookB04 || { echo "RETRY B04 sequential"; train_fixed masked/wrk_bookB04.jsonl adapters/wrk_bookB04 out/train_B04.log; }
ok adapters/wrk_bookB06 || { echo "RETRY B06 sequential"; train_fixed masked/wrk_bookB06.jsonl adapters/wrk_bookB06 out/train_B06.log; }

echo "===== TRAIN pair C04 // C06 mastery $(date +%H:%M:%S)"
train_mast masked/wrk_bookB04.jsonl adapters/wrk_bookC04 out/train_C04.log &
train_mast masked/wrk_bookB06.jsonl adapters/wrk_bookC06 out/train_C06.log &
wait
ok adapters/wrk_bookC04 || { echo "RETRY C04 sequential"; train_mast masked/wrk_bookB04.jsonl adapters/wrk_bookC04 out/train_C04.log; }
ok adapters/wrk_bookC06 || { echo "RETRY C06 sequential"; train_mast masked/wrk_bookB06.jsonl adapters/wrk_bookC06 out/train_C06.log; }

echo "===== TRAIN A plain $(date +%H:%M:%S)"
train_fixed masked/wrk_bookA.jsonl adapters/wrk_bookA out/train_A.log
ok adapters/wrk_bookA || { echo "RETRY A"; train_fixed masked/wrk_bookA.jsonl adapters/wrk_bookA out/train_A.log; }
grep -h "SAVED adapter" out/train_*.log

echo "===== HELDOUT book pages $(date +%H:%M:%S)"
python heldout_nll.py --data data_src/book_pages_heldout.jsonl | tee -a out/heldout3.jsonl
for A in bookA bookB04 bookB06 bookC04 bookC06; do
  python heldout_nll.py --data data_src/book_pages_heldout.jsonl --adapter adapters/wrk_$A | tee -a out/heldout3.jsonl
done

echo "===== GENS 3-parallel $(date +%H:%M:%S)"
gen() { V5_DATA=/workspace/div/bench_data python gen_threads.py --label "$1" --dec "$2" --wrk "$3" > "out/gen_$1.log" 2>&1; }
gen book_A   adapters/dec_keep1.0 adapters/wrk_bookA &
gen book_B04 adapters/dec_keep1.0 adapters/wrk_bookB04 &
gen book_B06 adapters/dec_keep1.0 adapters/wrk_bookB06 &
wait
gen book_C04 adapters/dec_keep1.0 adapters/wrk_bookC04 &
gen book_C06 adapters/dec_keep1.0 adapters/wrk_bookC06 &
gen anchor_keep100 adapters/dec_keep1.0 adapters/wrk_keep1.0 &
wait
gen anchor_mastery60 adapters/dec_mastery60 adapters/wrk_mastery60
grep -h "THREADS DONE" out/gen_*.log
echo "RUN3 STAGE1 COMPLETE $(date +%H:%M:%S)"
