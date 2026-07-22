"""
build_book_pages.py — RUN 3: turn a raw book into PAGE rows (Nikhil's restricted-section
design). Local, no GPU, no deps beyond stdlib.

Each row = one PAGE: the model sees a short tail of the previous page as context (user turn)
and the page itself as the completion (assistant turn). One row shape serves all three arms —
arms differ only in label masks (plain / band-blanks / band-blanks+mastery), so the ENTIRE
existing pipeline (loss_band_gate --per-token, build_masked_dataset, train_masked,
train_mastery, heldout_nll) runs on these rows UNCHANGED.

Held-out split: every Nth page is held out (never trained by any arm) for the free metric.
Front/back matter (Gutenberg header, contents, translator notes) is trimmed by marker.

  python build_book_pages.py --book ~/Desktop/lora-corpus-source/english/diplomacy-and-war/clausewitz-on-war.txt \
      --out data/book --page-words 300 --context-words 120 --heldout-every 10
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

SYS = "You are studying a classic treatise on strategy. Continue the passage faithfully."
USR = "Continue this passage from the treatise:\n\n...{context}"


def clean_book(text: str) -> str:
    # trim Gutenberg boilerplate + front matter up to Book I; trim license tail if present
    ms = list(re.finditer(r"BOOK I\.?\s+ON THE NATURE OF WAR", text))
    if ms:  # first hit is usually the table of contents; the body is the last hit
        text = text[ms[-1].start():]
    m = re.search(r"End of the Project Gutenberg|END OF (THE|THIS) PROJECT GUTENBERG", text, re.I)
    if m:
        text = text[:m.start()]
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

    text = clean_book(Path(args.book).read_text(errors="ignore"))
    words = text.split()
    pages = [" ".join(words[i:i + args.page_words])
             for i in range(0, len(words), args.page_words)]
    if len(pages[-1].split()) < args.page_words // 3:
        pages = pages[:-1]

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    train_f = (out / "book_pages_train.jsonl").open("w")
    held_f = (out / "book_pages_heldout.jsonl").open("w")
    n_train = n_held = 0
    for k, page in enumerate(pages):
        context = " ".join(pages[k - 1].split()[-args.context_words:]) if k > 0 \
            else "(the treatise opens)"
        row = {"messages": [
            {"role": "system", "content": SYS},
            {"role": "user", "content": USR.format(context=context)},
            {"role": "assistant", "content": page},
        ], "page_idx": k}
        if args.heldout_every > 0 and k % args.heldout_every == args.heldout_every - 1:
            held_f.write(json.dumps(row) + "\n"); n_held += 1
        else:
            train_f.write(json.dumps(row) + "\n"); n_train += 1
    train_f.close(); held_f.close()

    manifest = {"book": args.book, "total_words": len(words), "pages": len(pages),
                "page_words": args.page_words, "context_words": args.context_words,
                "train_pages": n_train, "heldout_pages": n_held,
                "est_train_tokens": int(n_train * args.page_words * 1.35)}
    (out / "book_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
