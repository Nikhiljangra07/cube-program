"""
build_fed_pages.py — RUN 5 (headroom): turn the Federalist Papers into PAGE rows.

Isolated sibling of build_book_pages.py (run 3, Clausewitz) — same page logic, same row
shape, only clean_book() and the system line differ. Kept as a SEPARATE script per the
no-mixing mandate: run-3 files stay frozen.

The Federalist source file has no Gutenberg boilerplate; front matter is a table of
contents that ends at the body marker "THE FEDERALIST.\nNo. I." — slice from there.

  python build_fed_pages.py \
      --book ~/Desktop/lora-corpus-source/english/political-philosophy/federalist-papers.txt \
      --out data/book_fed --page-words 300 --context-words 120 --heldout-every 10
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

SYS = "You are studying a classic treatise on government and strategy. Continue the passage faithfully."
USR = "Continue this passage from the treatise:\n\n...{context}"


def clean_book(text: str) -> str:
    m = re.search(r"THE FEDERALIST\.\s*\n+No\. I\.", text)
    if m:
        text = text[m.start():]
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--page-words", type=int, default=300)
    ap.add_argument("--context-words", type=int, default=120)
    ap.add_argument("--heldout-every", type=int, default=10)
    args = ap.parse_args()

    text = clean_book(Path(args.book).expanduser().read_text())
    words = text.split()
    pages = [" ".join(words[i:i + args.page_words])
             for i in range(0, len(words), args.page_words)]
    if len(pages[-1].split()) < args.page_words // 3:
        pages[-2] = pages[-2] + " " + pages[-1]
        pages = pages[:-1]

    outd = Path(args.out)
    outd.mkdir(parents=True, exist_ok=True)
    train_f = (outd / "fed_pages_train.jsonl").open("w")
    held_f = (outd / "fed_pages_heldout.jsonl").open("w")
    n_train = n_held = 0
    for k, page in enumerate(pages):
        context = " ".join(pages[k - 1].split()[-args.context_words:]) if k > 0 \
            else "(start of the treatise)"
        row = {"messages": [
            {"role": "system", "content": SYS},
            {"role": "user", "content": USR.format(context=context)},
            {"role": "assistant", "content": page},
        ], "page_idx": k}
        if args.heldout_every and (k + 1) % args.heldout_every == 0:
            held_f.write(json.dumps(row) + "\n"); n_held += 1
        else:
            train_f.write(json.dumps(row) + "\n"); n_train += 1
    train_f.close(); held_f.close()

    manifest = {"book": args.book, "total_words": len(words), "pages": len(pages),
                "page_words": args.page_words, "context_words": args.context_words,
                "heldout_every": args.heldout_every, "train": n_train, "heldout": n_held,
                "est_train_tokens": int(n_train * args.page_words * 1.35)}
    (outd / "fed_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
