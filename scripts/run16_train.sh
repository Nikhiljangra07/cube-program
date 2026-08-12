#!/bin/bash
# RUN 16 pod step — verifier LoRA train + frozen-bar eval, one detached job.
# Plain full-token SFT (no band masking — the target is a short verdict string;
# every assistant token IS the label). r64 for recipe consistency.
# Usage: bash run16_train.sh <train_md5> <eval_md5>
export LORA_BASE="Qwen/Qwen3-4B-Instruct-2507"
cd /workspace/div
set -o pipefail
mkdir -p out
TRAIN="${3:-verifier_train.jsonl}"; EVAL="${4:-verifier_eval.jsonl}"
ADAPTER="${5:-adapters/ver_16_qwen}"
[ -n "$1" ] && { echo "$1  $TRAIN" | md5sum -c - || { echo "TRAIN MD5 MISMATCH — ABORT"; exit 1; }; }
[ -n "$2" ] && { echo "$2  $EVAL" | md5sum -c - || { echo "EVAL MD5 MISMATCH — ABORT"; exit 1; }; }
wc -l "$TRAIN" "$EVAL"
# bs 2 x grad_accum 4 (effective 8) + gradient checkpointing: TRL 1.9 chunked-CE
# float32 logits on Qwen's 151k vocab OOM a 48GB card at the default bs 8
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
python train_lora.py --data "$TRAIN" --out "$ADAPTER" \
    --epochs 2 --r 64 --alpha 128 --router_aux -1 --bs 2 --grad_accum 4 --gc \
    > out/train_ver16.log 2>&1
[ -f "$ADAPTER/adapter_model.safetensors" ] || { echo "RETRY"; \
    python train_lora.py --data "$TRAIN" --out "$ADAPTER" \
    --epochs 2 --r 64 --alpha 128 --router_aux -1 --bs 1 --grad_accum 8 --gc \
    > out/train_ver16.log 2>&1; }
[ -f "$ADAPTER/adapter_model.safetensors" ] || { echo "TRAIN FAILED — ABORT"; exit 1; }
echo "RUN16 TRAIN COMPLETE"
python run16_eval.py --adapter "$ADAPTER" --data "$EVAL"
