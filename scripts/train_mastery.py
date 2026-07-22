"""
train_mastery.py — MASTERY-GATED repetition on a pre-masked dataset (Nikhil's regime, run 2b).

Pages (rows) are sampled from the UNMASTERED pool only; a page is mastered when its most
recent visit scores >= --mastery token accuracy on the graded (non--100) positions — the
85% rule exit (Wilson et al. 2019), which keeps repetition inside Muennighoff's paying zone
and blocks photographic memorization. Compute is MATCHED to the fixed-epoch arm via
--max-steps (same optimizer steps, same lr schedule length): the regimes differ only in
WHERE the repetition goes — uniform (fixed) vs where-the-model-still-fails (mastery).
If every page reaches mastery before the cap, training stops early (report the savings).

  python train_mastery.py --data masked/wrk_keep0.6.jsonl --out adapters/wrk_mastery60 --max-steps 685
  python train_mastery.py --data masked/dec_keep0.6.jsonl --out adapters/dec_mastery60 --max-steps 170
"""
from __future__ import annotations
import argparse, json, math, os, random
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, get_cosine_schedule_with_warmup
from peft import LoraConfig, get_peft_model

BASE = os.environ.get("LORA_BASE", "ibm-granite/granite-4.0-micro")


def collate(batch, pad_id, device):
    L = max(len(b["input_ids"]) for b in batch)
    ids, labels, attn = [], [], []
    for b in batch:
        n = len(b["input_ids"])
        ids.append(b["input_ids"] + [pad_id] * (L - n))
        labels.append(b["labels"] + [-100] * (L - n))
        attn.append([1] * n + [0] * (L - n))
    t = lambda x: torch.tensor(x, device=device)
    return t(ids), t(labels), t(attn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-steps", type=int, required=True, help="compute cap = fixed-epoch arm's steps")
    ap.add_argument("--mastery", type=float, default=0.85)
    ap.add_argument("--bs", type=int, default=8)
    ap.add_argument("--r", type=int, default=64)
    ap.add_argument("--alpha", type=int, default=64)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed); torch.manual_seed(args.seed)
    device = "cuda"
    tok = AutoTokenizer.from_pretrained(BASE)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.bfloat16, device_map=device)
    if hasattr(model.config, "router_aux_loss_coef"):
        model.config.router_aux_loss_coef = 0.0
    peft_cfg = LoraConfig(r=args.r, lora_alpha=args.alpha, lora_dropout=0.05, bias="none",
                          task_type="CAUSAL_LM", target_modules="all-linear")
    model = get_peft_model(model, peft_cfg)
    model.enable_input_require_grads()
    model.gradient_checkpointing_enable()
    model.train()

    rows = [json.loads(l) for l in Path(args.data).open()]
    # pages with zero graded tokens can never be mastered — count them mastered from the start
    gradable = [any(x != -100 for x in r["labels"]) for r in rows]
    mastered = [not g for g in gradable]
    visits = [0] * len(rows)

    opt = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=args.lr)
    sched = get_cosine_schedule_with_warmup(opt, int(0.05 * args.max_steps), args.max_steps)

    step = 0
    while step < args.max_steps:
        pool = [i for i in range(len(rows)) if not mastered[i]]
        if not pool:
            print(f"ALL PAGES MASTERED at step {step}/{args.max_steps} — stopping early", flush=True)
            break
        batch_idx = random.sample(pool, min(args.bs, len(pool)))
        ids, labels, attn = collate([rows[i] for i in batch_idx], tok.pad_token_id, device)
        out = model(input_ids=ids, labels=labels, attention_mask=attn)
        out.loss.backward()
        torch.nn.utils.clip_grad_norm_((p for p in model.parameters() if p.requires_grad), 1.0)
        opt.step(); sched.step(); opt.zero_grad()

        # per-page mastery check from this pass's logits (graded positions only)
        with torch.no_grad():
            preds = out.logits[:, :-1].argmax(-1)
            tgt = labels[:, 1:]
            for j, i in enumerate(batch_idx):
                m = tgt[j] != -100
                if int(m.sum()) == 0:
                    mastered[i] = True; continue
                acc = float((preds[j][m] == tgt[j][m]).float().mean())
                visits[i] += 1
                if acc >= args.mastery:
                    mastered[i] = True
        step += 1
        if step % 25 == 0:
            n_m = sum(mastered)
            print(f"step {step}/{args.max_steps} | mastered {n_m}/{len(rows)} | "
                  f"loss {float(out.loss):.3f}", flush=True)

    n_m = sum(mastered)
    vs = sorted(visits, reverse=True)
    print(json.dumps({"steps_used": step, "max_steps": args.max_steps,
                      "mastered": n_m, "pages": len(rows),
                      "max_visits": vs[0] if vs else 0,
                      "mean_visits": round(sum(visits) / max(len(visits), 1), 2)}))
    model.save_pretrained(args.out)
    tok.save_pretrained(args.out)
    print(f"SAVED adapter -> {args.out}")


if __name__ == "__main__":
    main()
