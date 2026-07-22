"""
train_masked.py — LoRA SFT on a PRE-TOKENIZED masked dataset ({"input_ids","labels"} jsonl
from build_masked_dataset.py). Pod, GPU.

Mirrors train_lora.py's recipe exactly (r64/alpha64/lr2e-4/cosine/warmup.05/bf16/5ep/bs8/
gc/adamw/seed42/max_len1024) — the only difference is that labels arrive pre-masked, so
loss lands only on the kept completion tokens. The keep_frac=1.0 dataset through THIS
script is the pipeline control: it must reproduce dense60's result or the pipeline is
not faithful and nothing downstream may be trusted.

  python train_masked.py --data masked/worker_keep40.jsonl --out adapters/wrk_keep40
"""
from __future__ import annotations
import argparse, os

import torch
from datasets import load_dataset
from transformers import (AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments)
from peft import LoraConfig, get_peft_model

BASE = os.environ.get("LORA_BASE", "ibm-granite/granite-4.0-micro")


def collate(batch, pad_id):
    L = max(len(b["input_ids"]) for b in batch)
    input_ids, labels, attn = [], [], []
    for b in batch:
        n = len(b["input_ids"])
        input_ids.append(b["input_ids"] + [pad_id] * (L - n))
        labels.append(b["labels"] + [-100] * (L - n))
        attn.append([1] * n + [0] * (L - n))
    return {"input_ids": torch.tensor(input_ids), "labels": torch.tensor(labels),
            "attention_mask": torch.tensor(attn)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=float, default=5.0)
    ap.add_argument("--r", type=int, default=64)
    ap.add_argument("--alpha", type=int, default=64)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--bs", type=int, default=8)
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(BASE)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.bfloat16, device_map="cuda")
    if hasattr(model.config, "router_aux_loss_coef"):
        model.config.router_aux_loss_coef = 0.0  # same granite mis-ID guard as train_lora (§5 fix)

    peft_cfg = LoraConfig(r=args.r, lora_alpha=args.alpha, lora_dropout=0.05, bias="none",
                          task_type="CAUSAL_LM", target_modules="all-linear")
    model = get_peft_model(model, peft_cfg)
    model.enable_input_require_grads()  # needed for gradient checkpointing + LoRA

    ds = load_dataset("json", data_files=args.data, split="train")

    targs = TrainingArguments(
        output_dir=args.out, num_train_epochs=args.epochs,
        per_device_train_batch_size=args.bs, learning_rate=args.lr,
        lr_scheduler_type="cosine", warmup_ratio=0.05, logging_steps=10,
        save_strategy="no", bf16=True, gradient_checkpointing=True,
        optim="adamw_torch", seed=42, report_to="none",
        remove_unused_columns=False,
    )
    pad_id = tok.pad_token_id
    trainer = Trainer(model=model, args=targs, train_dataset=ds,
                      data_collator=lambda b: collate(b, pad_id))
    trainer.train()
    model.save_pretrained(args.out)
    tok.save_pretrained(args.out)
    print(f"SAVED adapter -> {args.out}")


if __name__ == "__main__":
    main()
