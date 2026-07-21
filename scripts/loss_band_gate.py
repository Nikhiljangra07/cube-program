"""
loss_band_gate.py — THE DENSITY GATE (pod script, needs GPU).

Scores every training row's completion tokens under the BASE model (granite-4.0-micro):
mean per-token NLL over the assistant completion only (prompt masked), truncated at 1024
tokens — byte-matched to what train_lora.py's SFT loss actually sees (max_length=1024,
completion-only labels).

Motivation (PLAN.md §2): the learnable band. Low-NLL rows are tokens the base model
already predicts — near-zero gradient, "coherence" in the auditory-stream analogy.
Extreme-high-NLL rows are noise/underdetermined — "already segregated". The band between
the two boundaries is where solving (= gradient) lives. This script only SCORES;
band selection happens locally in build_arms.py, so the expensive GPU pass runs ONCE.

  python loss_band_gate.py --data data_src/worker_train.jsonl     --out out/worker_scored.jsonl
  python loss_band_gate.py --data data_src/decomposer_train.jsonl --out out/decomposer_scored.jsonl

Output: one JSON line per input row: {"idx", "mean_nll", "n_comp_tokens", "n_total_tokens"}
Rows the chat-template prefix check fails on get {"idx", "skip": "<reason>"} (counted, never silent).
Runtime: ~1.8k rows ≈ 5-10 min on RTX 6000 Ada. No API keys needed.
"""
from __future__ import annotations
import argparse, json, os
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

BASE = os.environ.get("LORA_BASE", "ibm-granite/granite-4.0-micro")
MAX_LEN = 1024  # must stay == train_lora.py max_length


@torch.no_grad()
def score_row(model, tok, messages, device):
    prompt_ids = tok.apply_chat_template(messages[:-1], add_generation_prompt=True,
                                         return_tensors="pt")[0]
    full_ids = tok.apply_chat_template(messages, add_generation_prompt=False,
                                       return_tensors="pt")[0]
    n_prompt = prompt_ids.shape[0]
    # prefix sanity: the training collator masks by this same boundary; if the template
    # breaks the prefix property the score would silently include prompt tokens — refuse instead.
    if full_ids.shape[0] <= n_prompt or not torch.equal(full_ids[:n_prompt], prompt_ids):
        return None
    full = full_ids[:MAX_LEN].unsqueeze(0).to(device)
    if full.shape[1] <= n_prompt:  # completion fully truncated away
        return None
    logits = model(full).logits
    logprobs = torch.log_softmax(logits[:, :-1].float(), dim=-1)
    targets = full[:, 1:]
    nll = -logprobs.gather(-1, targets.unsqueeze(-1)).squeeze(-1)  # [1, L-1]
    comp = nll[:, n_prompt - 1:]  # tokens predicted at positions >= prompt end
    return float(comp.mean()), int(comp.shape[1]), int(full.shape[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    device = "cuda"
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.bfloat16,
                                                 device_map=device).eval()

    out_path = Path(args.out); out_path.parent.mkdir(parents=True, exist_ok=True)
    n_ok = n_skip = 0
    with out_path.open("w") as f:
        for idx, line in enumerate(Path(args.data).open()):
            row = json.loads(line)
            try:
                r = score_row(model, tok, row["messages"], device)
            except Exception as e:
                r = None
            if r is None:
                f.write(json.dumps({"idx": idx, "skip": "prefix_or_truncation"}) + "\n")
                n_skip += 1
            else:
                mean_nll, n_comp, n_total = r
                f.write(json.dumps({"idx": idx, "mean_nll": round(mean_nll, 5),
                                    "n_comp_tokens": n_comp,
                                    "n_total_tokens": n_total}) + "\n")
                n_ok += 1
            if (idx + 1) % 100 == 0:
                print(f"  {idx + 1} scored ({n_skip} skipped)", flush=True)
    print(f"DONE {args.data}: {n_ok} scored, {n_skip} skipped -> {args.out}", flush=True)


if __name__ == "__main__":
    main()
