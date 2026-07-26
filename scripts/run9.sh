#!/bin/bash
# RUN 9 orchestration — same face, new base (Qwen3-4B-Instruct-2507) on one RTX PRO 6000.
# Single-variable swap vs run 8: base model only. Ladder retrains from scratch.
# Uploads required in /workspace/div:
#   scripts: loss_band_gate.py build_masked_dataset.py train_masked.py gen_threads.py
#            dav_eval_v5.py
#   data/decomposer_train.jsonl  data/worker_train.jsonl  faces/faceF_gen/worker_train.jsonl
#   bench_data/eval_problems.jsonl
export LORA_BASE="Qwen/Qwen3-4B-Instruct-2507"
cd /workspace/div
set -o pipefail
mkdir -p out adapters masked

echo "===== RUN9 START $(date +%H:%M:%S)  BASE=$LORA_BASE"
md5sum -c - <<'EOF' || { echo "DATA MD5 MISMATCH — ABORT"; exit 1; }
86fffad338cc20b7a09c72bc7dc54925  data/decomposer_train.jsonl
b31ae16f414601f5188dcf205b89601a  data/worker_train.jsonl
e87ca5344586b60dec74b73663639ca5  faces/faceF_gen/worker_train.jsonl
EOF
wc -l data/*.jsonl faces/faceF_gen/worker_train.jsonl bench_data/eval_problems.jsonl

echo "===== R0 PREFLIGHT: template + generation smoke $(date +%H:%M:%S)"
python - <<'EOF' || { echo "PREFLIGHT FAILED — ABORT (terminate pod)"; exit 1; }
import os, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
B = os.environ["LORA_BASE"]
tok = AutoTokenizer.from_pretrained(B)
msgs = [{"role": "system", "content": "You are terse."},
        {"role": "user", "content": "Say READY and nothing else."}]
enc = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt")
ids = enc if torch.is_tensor(enc) else enc["input_ids"]
assert ids.shape[1] > 4, "template produced no tokens"
model = AutoModelForCausalLM.from_pretrained(B, torch_dtype=torch.bfloat16, device_map="cuda")
out = model.generate(ids.to("cuda"), max_new_tokens=24, do_sample=False,
                     pad_token_id=tok.eos_token_id)
txt = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()
print(f"PREFLIGHT generation: {txt!r}")
assert len(txt) > 0, "empty generation"
assert "<think>" not in txt, "thinking blocks present — wrong variant"
print("PREFLIGHT OK")
EOF

echo "===== SCORE per-token x3 (Qwen base) $(date +%H:%M:%S)"
python loss_band_gate.py --data data/decomposer_train.jsonl   --out out/dec_pertok.jsonl    --per-token
python loss_band_gate.py --data data/worker_train.jsonl       --out out/anchor_pertok.jsonl --per-token
python loss_band_gate.py --data faces/faceF_gen/worker_train.jsonl --out out/face_pertok.jsonl --per-token

echo "===== BUILD masked $(date +%H:%M:%S)"
python build_masked_dataset.py --src data/decomposer_train.jsonl   --scores out/dec_pertok.jsonl    --keep-frac 1.0 --policy band --out masked/dec.jsonl
python build_masked_dataset.py --src data/worker_train.jsonl       --scores out/anchor_pertok.jsonl --keep-frac 1.0 --policy band --out masked/anchor.jsonl
python build_masked_dataset.py --src faces/faceF_gen/worker_train.jsonl --scores out/face_pertok.jsonl --keep-frac 0.6 --policy band --out masked/face.jsonl
wc -l masked/*.jsonl

echo "===== TRAINS 3x sequential, 1.25 epochs $(date +%H:%M:%S)"
train() {
  python train_masked.py --data "$1" --out "adapters/$2" --epochs 1.25 > "out/train_$2.log" 2>&1
  [ -f "adapters/$2/adapter_model.safetensors" ] || { echo "RETRY $2"; python train_masked.py --data "$1" --out "adapters/$2" --epochs 1.25 > "out/train_$2.log" 2>&1; }
  [ -f "adapters/$2/adapter_model.safetensors" ] || { echo "TRAIN $2 FAILED — ABORT"; exit 1; }
  echo "TRAIN DONE $2 $(date +%H:%M:%S)"
}
train masked/dec.jsonl    dec_qwen
train masked/anchor.jsonl wrk_keep100_qwen
train masked/face.jsonl   wrk_faceF_gen_qwen

echo "===== GENS Session-H card: 2-parallel $(date +%H:%M:%S)"
gen() { V5_DATA=/workspace/div/bench_data V5_WRK_MAXNEW=512 python gen_threads.py --label "$1" --dec adapters/dec_qwen --wrk "$2" > "out/gen_$1.log" 2>&1; }
gen faceF_gen_q adapters/wrk_faceF_gen_qwen &
gen anchor_keep100_q adapters/wrk_keep100_qwen &
wait
grep -h "THREADS DONE" out/gen_*.log
wc -l out/eval_*_q_v5_threads.jsonl

echo "===== BUNDLE $(date +%H:%M:%S)"
tar czf /workspace/run9_bundle.tgz adapters/dec_qwen adapters/wrk_keep100_qwen adapters/wrk_faceF_gen_qwen \
    out/eval_faceF_gen_q_v5_threads.jsonl out/eval_anchor_keep100_q_v5_threads.jsonl out/train_*.log
md5sum /workspace/run9_bundle.tgz
echo "RUN9 POD COMPLETE $(date +%H:%M:%S)"
