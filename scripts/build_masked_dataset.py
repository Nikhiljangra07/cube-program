"""
build_masked_dataset.py — the OCCLUSION (selective-loss) dataset builder. Local, no GPU.

Takes a messages jsonl + its PER-TOKEN score file (loss_band_gate.py --per-token) and emits a
pre-tokenized dataset {"input_ids", "labels"} where labels are -100 everywhere EXCEPT the kept
completion tokens. The model still READS every token (full disclosure); it only SOLVES the
kept ones (concentrated gradient — Rho-1's selective LM, applied to SFT).

Keep policy "band": rank all completion tokens globally by NLL, drop from the easy end and
the hard end at EASY_BIAS:1 until keep_frac of tokens remain (token-level twin of build_arms).
Keep policy "random": keep the same NUMBER of tokens, chosen uniformly (control), seed 42.
keep_frac 1.0 = pipeline control (labels on ALL completion tokens — must reproduce dense60).

  python build_masked_dataset.py --src data/arms/dense60/worker_train.jsonl \
      --scores out/worker_dense60_pertok.jsonl --keep-frac 0.4 --policy band \
      --out data/masked/worker_keep40.jsonl
"""
from __future__ import annotations
import argparse, json, random
from pathlib import Path

from transformers import AutoTokenizer
import os

BASE = os.environ.get("LORA_BASE", "ibm-granite/granite-4.0-micro")
MAX_LEN = 1024  # must stay == scorer and trainer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--scores", required=True)
    ap.add_argument("--keep-frac", type=float, required=True)
    ap.add_argument("--policy", choices=["band", "random"], default="band")
    ap.add_argument("--easy-bias", type=float, default=3.0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(BASE)
    src_rows = [json.loads(l) for l in Path(args.src).open()]
    scores = [json.loads(l) for l in Path(args.scores).open()]
    assert len(scores) == len(src_rows), "score/src length mismatch"

    # global pool of (row_idx, comp_token_idx, nll)
    pool = []
    for s in scores:
        if "nll" not in s:
            continue
        for i, v in enumerate(s["nll"]):
            pool.append((s["idx"], i, v))
    n_keep = round(args.keep_frac * len(pool))

    if args.keep_frac >= 0.999:
        kept = {(r, i) for r, i, _ in pool}
    elif args.policy == "random":
        rng = random.Random(args.seed)
        kept = set((r, i) for r, i, _ in rng.sample(pool, n_keep))
    else:
        by_nll = sorted(pool, key=lambda x: x[2])
        lo, hi = 0, len(by_nll) - 1
        dropped_easy = dropped_hard = 0
        n_drop = len(pool) - n_keep
        while dropped_easy + dropped_hard < n_drop and lo < hi:
            if dropped_easy <= args.easy_bias * dropped_hard:
                dropped_easy += 1; lo += 1
            else:
                dropped_hard += 1; hi -= 1
        kept = {(r, i) for r, i, _ in by_nll[lo:hi + 1]}
        band = (by_nll[lo][2], by_nll[hi][2])

    score_by_idx = {s["idx"]: s for s in scores if "nll" in s}
    out_path = Path(args.out); out_path.parent.mkdir(parents=True, exist_ok=True)
    n_rows = n_zero = 0
    total_labels = 0
    with out_path.open("w") as f:
        for idx, row in enumerate(src_rows):
            s = score_by_idx.get(idx)
            if s is None:
                continue  # skipped by scorer — excluded from every arm identically
            ids = tok.apply_chat_template(row["messages"], add_generation_prompt=False,
                                          return_tensors=None)
            if hasattr(ids, "input_ids"):
                ids = ids.input_ids  # transformers 5.x BatchEncoding
            ids = list(ids)[:MAX_LEN]
            n_prompt = s["n_prompt"]
            labels = [-100] * len(ids)
            row_kept = 0
            for i in range(s["n_comp_tokens"]):
                pos = n_prompt + i
                if pos >= len(ids):
                    break
                if (idx, i) in kept:
                    labels[pos] = ids[pos]
                    row_kept += 1
            if row_kept == 0:
                n_zero += 1  # keeps context value only; logged, not dropped
            total_labels += row_kept
            f.write(json.dumps({"input_ids": ids, "labels": labels}) + "\n")
            n_rows += 1

    manifest = {"src": args.src, "policy": args.policy, "keep_frac": args.keep_frac,
                "pool_tokens": len(pool), "kept_tokens": len(kept) if args.keep_frac < 0.999 else len(pool),
                "label_tokens_written": total_labels, "rows": n_rows,
                "rows_with_zero_loss_tokens": n_zero}
    if args.policy == "band" and args.keep_frac < 0.999:
        manifest["nll_band"] = [round(band[0], 3), round(band[1], 3)]
    Path(str(out_path) + ".manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
