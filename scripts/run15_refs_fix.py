"""
run15_refs_fix.py — refs-leg quality fix (generation only, no judging, ~$0).

Problems found in the night pass (recorded honestly, raw files preserved):
  - Qwen3.5-9B: emits plain-prose thinking (no tags) under the v5 template and
    truncates at max_new=2048 — 56/56 leaked, 21/56 lost their final thread.
    Fix: regenerate all 56 with enable_thinking=False (Qwen template kwarg;
    falls back to default + larger cap if unsupported), max_new=3072.
  - gpt-oss-20b: harmony channel markers are special tokens, so
    skip_special_tokens erased them; 38/56 keep a textual 'assistantfinal'
    seam, 18/56 truncated before the final channel. Fix: regenerate ONLY those
    18 with max_new=4096; extract the final channel by decoding WITH special
    tokens and splitting on the final-channel marker.

Writes cleaned rows over the original filenames (judge-ready); raw originals
moved to *_raw.jsonl once.
"""
from __future__ import annotations
import json, re, shutil
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

WD = Path("/workspace/div")
OUT = WD / "out"
SYS = "You write one precise, decisive, realistic reasoning thread pursuing a given strategic angle."
GEN_SINGLE = (
    "PROBLEM: {problem}\n\nWrite a single reasoning thread (6-9 sentences, cold "
    "and analytical) that: AUDITS what the actor actually holds (resources, "
    "people, authority, time — real numbers only if the problem supplies them) "
    "and names the ONE variable genuinely in the actor's favor; READS the other "
    "parties — the single most likely realistic reaction one or two moves ahead "
    "and the one observable signal that would say the read is wrong; COMMITS to "
    "a lawful plan spending ONLY audited items (who/what/when), positioned for "
    "that read, naming the ONE friction most likely to stall it and the "
    "pre-arranged answer. Final line, exactly: ESTIMATE: NN%")


def probs_list():
    return ([("dossier", json.loads(l)["problem"]) for l in (WD / "match_dossier.jsonl").open()] +
            [("inventory", json.loads(l)["problem"]) for l in (WD / "match_inventory.jsonl").open()])


def backup_once(p):
    raw = p.with_name(p.stem + "_raw.jsonl")
    if p.exists() and not raw.exists():
        shutil.copy(p, raw)


def fix_qwen35():
    mid = "Qwen/Qwen3.5-9B"
    p = OUT / "match_refs_Qwen3_5-9B.jsonl"
    backup_once(p)
    tok = AutoTokenizer.from_pretrained(mid)
    model = AutoModelForCausalLM.from_pretrained(mid, dtype="auto", device_map="cuda")
    rows = []
    for leg, prob in probs_list():
        msgs = [{"role": "system", "content": SYS},
                {"role": "user", "content": GEN_SINGLE.format(problem=prob)}]
        try:
            ids = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                          return_tensors="pt", enable_thinking=False)
            mode = "nothink"
        except TypeError:
            ids = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                          return_tensors="pt")
            mode = "default"
        ids = ids["input_ids"] if hasattr(ids, "keys") else ids
        with torch.no_grad():
            o = model.generate(ids.to("cuda"), max_new_tokens=3072, do_sample=False,
                               pad_token_id=tok.eos_token_id)
        text = tok.decode(o[0][ids.shape[1]:], skip_special_tokens=True).strip()
        if "</think>" in text:
            text = text.rsplit("</think>", 1)[1].strip()
        idx = sum(1 for r in rows if r["leg"] == leg)
        rows.append({"leg": leg, "idx": idx, "model": mid, "answer": text, "mode": mode})
        print(f"[fix qwen3.5] {leg} {idx:02d} ({mode}, {len(text.split())}w)", flush=True)
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    del model
    torch.cuda.empty_cache()
    print("QWEN3.5 FIX COMPLETE", flush=True)


def extract_final_harmony(tok, out_ids):
    """Decode WITH specials and split on the final-channel marker."""
    full = tok.decode(out_ids, skip_special_tokens=False)
    m = re.search(r"<\|channel\|>final<\|message\|>", full)
    if m:
        tail = full[m.end():]
        tail = re.split(r"<\|[a-z_]+\|>", tail)[0]
        return tail.strip(), True
    clean = tok.decode(out_ids, skip_special_tokens=True).strip()
    if "assistantfinal" in clean:
        return clean.rsplit("assistantfinal", 1)[1].strip(), True
    return clean, False


def fix_gptoss():
    mid = "openai/gpt-oss-20b"
    p = OUT / "match_refs_gpt-oss-20b.jsonl"
    backup_once(p)
    rows = [json.loads(l) for l in p.open()]
    by_key = {(r["leg"], r["idx"]): r for r in rows}
    # split existing rows that carry the textual seam; collect the truncated ones
    need = []
    for r in rows:
        if "assistantfinal" in r["answer"]:
            r["answer"] = r["answer"].rsplit("assistantfinal", 1)[1].strip()
            r["final_ok"] = True
        else:
            need.append((r["leg"], r["idx"]))
    probs = probs_list()
    by_leg = {"dossier": [], "inventory": []}
    for leg, prob in probs:
        by_leg[leg].append(prob)
    print(f"[fix gpt-oss] {len(need)} truncated rows to regenerate", flush=True)
    if need:
        tok = AutoTokenizer.from_pretrained(mid)
        model = AutoModelForCausalLM.from_pretrained(mid, dtype="auto", device_map="cuda")
        for leg, idx in need:
            prob = by_leg[leg][idx]
            msgs = [{"role": "system", "content": SYS},
                    {"role": "user", "content": GEN_SINGLE.format(problem=prob)}]
            ids = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                          return_tensors="pt")
            ids = ids["input_ids"] if hasattr(ids, "keys") else ids
            with torch.no_grad():
                o = model.generate(ids.to("cuda"), max_new_tokens=4096, do_sample=False,
                                   pad_token_id=tok.eos_token_id)
            text, ok = extract_final_harmony(tok, o[0][ids.shape[1]:])
            r = by_key[(leg, idx)]
            r["answer"], r["final_ok"] = text, ok
            print(f"[fix gpt-oss] {leg} {idx:02d} regenerated (final={ok}, "
                  f"{len(text.split())}w)", flush=True)
        del model
        torch.cuda.empty_cache()
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print("GPT-OSS FIX COMPLETE", flush=True)


if __name__ == "__main__":
    fix_qwen35()
    fix_gptoss()
    print("REFS FIX ALL COMPLETE", flush=True)
