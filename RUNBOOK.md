# RUNBOOK — density test run 1 (dense60 vs rand60 vs on-disk baselines)

Pod: RTX 6000 Ada 49GB (~$0.79/hr), same as every micro run. Total wall ≈ 2h ≈ $1.60 pod + ~$3 API.
Baselines (base, v5full) are NOT retrained or regenerated — their bench threads are on disk.

## 0. Pod setup (identical pins to the v3/v5 runs)
```bash
pip install --break-system-packages -U "transformers==5.12.1" "peft==0.19.1" "trl==1.7.0" \
    "torch==2.8.0" datasets accelerate httpx numpy
mkdir -p /workspace/div/data_src /workspace/div/out /workspace/div/adapters
```

## 1. Upload scripts + source data (from laptop, in ~/Desktop/density-method)
```bash
scp scripts/loss_band_gate.py scripts/train_lora.py scripts/dav_eval_v5.py <pod>:/workspace/div/
scp data/src/worker_train.jsonl data/src/decomposer_train.jsonl <pod>:/workspace/div/data_src/
```

## 2. Score (the one GPU pass of the density gate — no keys needed)
```bash
cd /workspace/div
python loss_band_gate.py --data data_src/decomposer_train.jsonl --out out/decomposer_scored.jsonl
python loss_band_gate.py --data data_src/worker_train.jsonl     --out out/worker_scored.jsonl
```
Sanity: skipped rows should be ~0. If skipped > 2% STOP — the chat-template prefix
assumption broke; do not train on a silently mis-scored corpus.

## 3. Build arms (LOCAL — laptop, ~/Desktop/density-method)
```bash
scp <pod>:/workspace/div/out/decomposer_scored.jsonl <pod>:/workspace/div/out/worker_scored.jsonl out/
python3 scripts/build_arms.py --src data/src/decomposer_train.jsonl --scores out/decomposer_scored.jsonl \
    --out-dir data/arms --name decomposer_train
python3 scripts/build_arms.py --src data/src/worker_train.jsonl --scores out/worker_scored.jsonl \
    --out-dir data/arms --name worker_train
```
Check both manifests: `mass_match_pct` ≈ 100, dense60 tokens ≈ 60% of pool. Then push:
```bash
scp -r data/arms/dense60 data/arms/rand60 <pod>:/workspace/div/
```

## 4. Train 2 arms × 2 adapters (recipe LOCKED to the v5 baseline: r64/5ep)
```bash
cd /workspace/div
python train_lora.py --data dense60/decomposer_train.jsonl --out adapters/dec_dense60 --r 64 --epochs 5
python train_lora.py --data dense60/worker_train.jsonl     --out adapters/wrk_dense60 --r 64 --epochs 5
python train_lora.py --data rand60/decomposer_train.jsonl  --out adapters/dec_rand60  --r 64 --epochs 5
python train_lora.py --data rand60/worker_train.jsonl      --out adapters/wrk_rand60  --r 64 --epochs 5
```
Record `num_tokens` from each final log line into PLAN.md §6 — that is the real
tokens-seen figure for the paper trail (v5full baseline: dec 1.149e6, wrk 4.107e6 over 5ep).

## 5. Bench thread generation (48 OOD problems — same harness that made the baselines)
The bench problems stand in as eval_problems for the harness, exactly like the original bench run:
```bash
# on laptop: scp data/bench/problems.jsonl <pod>:/workspace/div/bench_data/eval_problems.jsonl
# KEYS PATHWAY: on the laptop run `source ~/Desktop/reasoningEngine/load_keys.sh`, then start the
# pod shell with the key injected (never typed/pasted):
#   ssh <pod> "export ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY; exec bash"
cd /workspace/div
V5_DATA=/workspace/div/bench_data python dav_eval_v5.py --label bench_dense60 --n 48 \
    --dec adapters/dec_dense60 --wrk adapters/wrk_dense60
V5_DATA=/workspace/div/bench_data python dav_eval_v5.py --label bench_rand60 --n 48 \
    --dec adapters/dec_rand60 --wrk adapters/wrk_rand60
```
(The inline Haiku judge scores it prints are DIAGNOSTIC ONLY — the verdict judge is step 7.
Greedy decoding is baked into the harness; do not enable sampling — §round-2 lesson.)

## 6. Pull artifacts, kill pod
```bash
scp <pod>:/workspace/div/out/eval_bench_dense60_v5* <pod>:/workspace/div/out/eval_bench_rand60_v5* out/
scp <pod>:/workspace/div/out/*_scored.jsonl out/   # if not already pulled
# adapters optional (~500MB): scp -r <pod>:/workspace/div/adapters ~/Desktop/divergent-model-backups/density_run1/
```

## 7. Verdict judge — single Gemini session, all four arms (LOCAL)
```bash
cd ~/Desktop/density-method/scripts
source ~/Desktop/reasoningEngine/load_keys.sh   # central vault — exports GEMINI_API_KEY et al.
python3 rejudge_arms.py
```
Reads base + v5full threads from data/bench and the two new arms from out/.
Writes out/rejudge_summary.json and prints the Signal A / Signal B read (PLAN.md §5).

## Guards
- Do NOT touch `~/Desktop/divergence-formula` — all inputs were copied here already.
- Do NOT retrain or regenerate base/v5full — comparability comes from reusing their threads
  and re-judging everything in one session.
- If a train diverges (loss not < 1.0 by end like the v5 log), stop and compare the arm's
  manifest before burning eval budget.
- Keys: single vault = ~/Desktop/reasoningEngine/.env. Load with
  `source ~/Desktop/reasoningEngine/load_keys.sh` (exports all, prints count only, never values).
  A gitignored `.env` symlink at this repo's root serves the python-dotenv scripts. Never
  copy keys into any repo; never echo them.
