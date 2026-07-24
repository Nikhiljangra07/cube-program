#!/bin/bash
# RUN 5b — pod A repair + probes. Reruns the two gens that fired before the adapter upload
# landed (peft 401), runs the NLL-bias control (bookC06 vs base on CLAUSEWITZ heldout with
# the same instrument), then probe inference on all five arms.
cd /workspace/div
set -o pipefail

echo "===== RUN5B START $(date +%H:%M:%S)"
for d in dec_keep1.0 wrk_keep1.0 wrk_laneF wrk_bookC06 wrk_fedH; do
  [ -f "adapters/$d/adapter_model.safetensors" ] || { echo "MISSING adapters/$d — abort"; exit 1; }
done

echo "===== GENS 2-parallel $(date +%H:%M:%S)"
gen() { V5_DATA=/workspace/div/bench_data python gen_threads.py --label "$1" --dec adapters/dec_keep1.0 --wrk "$2" > "out/gen_$1.log" 2>&1; }
gen fedH           adapters/wrk_fedH &
gen anchor_keep100 adapters/wrk_keep1.0 &
wait
grep -h "THREADS DONE" out/gen_*.log

echo "===== NLL CONTROL: clausewitz heldout, base vs bookC06 $(date +%H:%M:%S)"
python heldout_nll.py --data data_src/book_pages_heldout.jsonl                            > out/nll_cw_base.log 2>&1
python heldout_nll.py --data data_src/book_pages_heldout.jsonl --adapter adapters/wrk_bookC06 > out/nll_cw_C06.log 2>&1
grep heldout_mean_nll out/nll_cw_base.log out/nll_cw_C06.log

echo "===== PROBES: 5 arms sequential $(date +%H:%M:%S)"
python probe_infer.py --label base                                    > out/probe_base.log 2>&1
python probe_infer.py --label keep100  --adapter adapters/wrk_keep1.0 > out/probe_keep100.log 2>&1
python probe_infer.py --label book_C06 --adapter adapters/wrk_bookC06 > out/probe_book_C06.log 2>&1
python probe_infer.py --label laneF    --adapter adapters/wrk_laneF   > out/probe_laneF.log 2>&1
python probe_infer.py --label fedH     --adapter adapters/wrk_fedH    > out/probe_fedH.log 2>&1
grep -h "PROBES DONE" out/probe_*.log
echo "RUN5B COMPLETE $(date +%H:%M:%S)"
