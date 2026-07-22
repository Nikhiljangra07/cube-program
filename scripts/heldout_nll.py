"""
heldout_nll.py — the FREE sweep metric. Pod, GPU, no keys.

Mean completion NLL of a (base + optional adapter) model over the held-out worker rows.
Lower = better. Used to rank sweep points cheaply; only the winner + control graduate to
the paid bench+judge round.

  python heldout_nll.py --data data_src/heldout_worker.jsonl                      # base
  python heldout_nll.py --data data_src/heldout_worker.jsonl --adapter adapters/wrk_keep40
"""
from __future__ import annotations
import argparse, json, os
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

import loss_band_gate as G

BASE = os.environ.get("LORA_BASE", "ibm-granite/granite-4.0-micro")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--adapter", default=None)
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.bfloat16, device_map="cuda")
    if args.adapter:
        model = PeftModel.from_pretrained(model, args.adapter)
    model = model.eval()

    tot_nll = tot_tok = n_rows = n_skip = 0
    for line in Path(args.data).open():
        row = json.loads(line)
        try:
            r = G.score_row(model, tok, row["messages"], "cuda")
        except Exception:
            r = None
        if r is None:
            n_skip += 1; continue
        mean_nll, n_comp, _ = r
        tot_nll += mean_nll * n_comp; tot_tok += n_comp; n_rows += 1

    label = args.adapter or "BASE"
    print(json.dumps({"model": label, "heldout_mean_nll": round(tot_nll / max(tot_tok, 1), 5),
                      "rows": n_rows, "skipped": n_skip, "comp_tokens": tot_tok}))


if __name__ == "__main__":
    main()
