#!/bin/bash
# RUN 5 orchestration — headroom test (Federalist Papers) on pod A (RTX PRO 6000 Blackwell).
# Exact run-3 C06 recipe on a never-trained book: score per-token -> keep-0.6 band ->
# + anchor keep-1.0 -> mastery train at matched steps -> gens (fedH + anchor_keep100) ->
# heldout NLL (base vs fedH) on never-trained Federalist pages.
# Uploads required in /workspace/div:
#   scripts (loss_band_gate, build_masked_dataset, train_mastery, gen_threads, dav_eval_v5,
#            heldout_nll)
#   data_src/fed_pages_train.jsonl  data_src/fed_pages_heldout.jsonl  data_src/anchor_300.jsonl
#   bench_data/eval_problems.jsonl   (48-problem bench)
#   adapters/dec_keep1.0  adapters/wrk_keep1.0
cd /workspace/div
set -o pipefail
mkdir -p out adapters masked

echo "===== RUN5 START $(date +%H:%M:%S)"
md5sum data_src/fed_pages_train.jsonl
wc -l data_src/fed_pages_train.jsonl data_src/fed_pages_heldout.jsonl bench_data/eval_problems.jsonl

echo "===== SCORE fed+anchor per-token $(date +%H:%M:%S)"
python loss_band_gate.py --data data_src/fed_pages_train.jsonl --out out/fed_pertok.jsonl --per-token
python loss_band_gate.py --data data_src/anchor_300.jsonl --out out/anchor_pertok.jsonl --per-token

echo "===== BUILD masked keep-0.6 $(date +%H:%M:%S)"
python build_masked_dataset.py --src data_src/fed_pages_train.jsonl --scores out/fed_pertok.jsonl \
    --keep-frac 0.6 --policy band --out masked/fed_keep0.6.jsonl
python build_masked_dataset.py --src data_src/anchor_300.jsonl --scores out/anchor_pertok.jsonl \
    --keep-frac 1.0 --policy band --out masked/anchor_keep1.0.jsonl
cat masked/fed_keep0.6.jsonl masked/anchor_keep1.0.jsonl > masked/wrk_fedH.jsonl
ROWS=$(wc -l < masked/wrk_fedH.jsonl)
STEPS=$(( (ROWS + 7) / 8 * 5 ))
echo "rows=$ROWS matched_steps=$STEPS"

echo "===== TRAIN fedH mastery $(date +%H:%M:%S)"
python train_mastery.py --data masked/wrk_fedH.jsonl --out adapters/wrk_fedH --max-steps $STEPS > out/train_fedH.log 2>&1
[ -f adapters/wrk_fedH/adapter_model.safetensors ] || { echo "RETRY fedH"; python train_mastery.py --data masked/wrk_fedH.jsonl --out adapters/wrk_fedH --max-steps $STEPS > out/train_fedH.log 2>&1; }
grep -h "SAVED adapter\|mastery telemetry" out/train_fedH.log | tail -3

echo "===== GENS 2-parallel $(date +%H:%M:%S)"
gen() { V5_DATA=/workspace/div/bench_data python gen_threads.py --label "$1" --dec adapters/dec_keep1.0 --wrk "$2" > "out/gen_$1.log" 2>&1; }
gen fedH           adapters/wrk_fedH &
gen anchor_keep100 adapters/wrk_keep1.0 &
wait
grep -h "THREADS DONE" out/gen_*.log

echo "===== HELDOUT NLL base vs fedH $(date +%H:%M:%S)"
python heldout_nll.py --data data_src/fed_pages_heldout.jsonl                          > out/nll_base.log 2>&1
python heldout_nll.py --data data_src/fed_pages_heldout.jsonl --adapter adapters/wrk_fedH > out/nll_fedH.log 2>&1
tail -2 out/nll_base.log out/nll_fedH.log
echo "RUN5 STAGE1 COMPLETE $(date +%H:%M:%S)"
