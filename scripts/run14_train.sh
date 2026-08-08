#!/bin/bash
# RUN 14 pod training step — fixed recipe (keep-0.6 band, 1.25 epochs, r64).
# Requires in /workspace/div: faces/fusion14/worker_train.jsonl (uploaded by
# driver after harvest), loss_band_gate.py, build_masked_dataset.py,
# train_masked.py. Usage: bash run14_train.sh <diet_md5>
export LORA_BASE="Qwen/Qwen3-4B-Instruct-2507"
cd /workspace/div
set -o pipefail
mkdir -p out masked
DIET_MD5="$1"
[ -n "$DIET_MD5" ] && { echo "$DIET_MD5  faces/fusion14/worker_train.jsonl" | md5sum -c - || { echo "DIET MD5 MISMATCH — ABORT"; exit 1; }; }
wc -l faces/fusion14/worker_train.jsonl
python loss_band_gate.py --data faces/fusion14/worker_train.jsonl --out out/fusion14_pertok.jsonl --per-token || exit 1
python build_masked_dataset.py --src faces/fusion14/worker_train.jsonl --scores out/fusion14_pertok.jsonl \
    --keep-frac 0.6 --policy band --out masked/fusion14.jsonl || exit 1
python train_masked.py --data masked/fusion14.jsonl --out adapters/wrk_fusion_14_qwen --epochs 1.25 > out/train_fusion14.log 2>&1
[ -f adapters/wrk_fusion_14_qwen/adapter_model.safetensors ] || { echo "RETRY"; python train_masked.py --data masked/fusion14.jsonl --out adapters/wrk_fusion_14_qwen --epochs 1.25 > out/train_fusion14.log 2>&1; }
[ -f adapters/wrk_fusion_14_qwen/adapter_model.safetensors ] || { echo "TRAIN FAILED — ABORT"; exit 1; }
echo "RUN14 TRAIN COMPLETE"
