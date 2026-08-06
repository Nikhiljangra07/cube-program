#!/bin/bash
# RUN 13 pod orchestration — fusion wall test (RUNBOOK13). NO training.
# Uploads required in /workspace/div:
#   run13_relay.py  run13_checker.py  staged_problems.jsonl
#   adapters/wrk_faceF_9b_qwen  adapters/wrk_faceV_10_qwen  adapters/wrk_keep100_qwen
# Usage: bash run13.sh <staged_problems_md5>
export LORA_BASE="Qwen/Qwen3-4B-Instruct-2507"
export RUN13_BIG="Qwen/Qwen3-14B"
cd /workspace/div
set -o pipefail
mkdir -p out
PROB_MD5="$1"

echo "===== RUN13 START $(date +%H:%M:%S)  BASE=$LORA_BASE  BIG=$RUN13_BIG"
[ -n "$PROB_MD5" ] && { echo "$PROB_MD5  staged_problems.jsonl" | md5sum -c - || { echo "PROBLEMS MD5 MISMATCH — ABORT"; exit 1; }; }
wc -l staged_problems.jsonl
for A in wrk_faceF_9b_qwen wrk_faceV_10_qwen wrk_keep100_qwen; do
  [ -f adapters/$A/adapter_model.safetensors ] || { echo "MISSING ADAPTER $A — ABORT"; exit 1; }
done

echo "===== CHECKER SELF-TEST (must be 8/8) $(date +%H:%M:%S)"
python run13_checker.py || { echo "CHECKER SELF-TEST FAILED — ABORT"; exit 1; }

echo "===== RELAY: 24 problems, arms A/B/D on 4B then C on 14B $(date +%H:%M:%S)"
python run13_relay.py 2>&1 | tee out/relay.log
grep -q "RUN13 RELAY COMPLETE" out/relay.log || { echo "RELAY INCOMPLETE — ABORT"; exit 1; }

echo "===== BUNDLE $(date +%H:%M:%S)"
tar czf /workspace/run13_bundle.tgz out/run13_transcript.json out/relay.log
md5sum /workspace/run13_bundle.tgz
echo "RUN13 POD COMPLETE $(date +%H:%M:%S)"
