"""
rejudge_arms.py — SINGLE-SESSION judge over all four arms (local; keys via the vault symlink).

JUDGE = Claude Sonnet 5 (Nikhil's call, 2026-07-21), temp 0, byte-identical JUDGE_PROMPT +
thread formatting + JSON parsing from head2head_v5.py — only the model behind the prompt
changed. NOTE: absolute scores are NOT comparable to the historical Gemini-judged numbers
in WORKING_PAPER (§12 measured ~0.9 judge-family skew); comparability here comes from all
four arms being judged by the SAME judge in the SAME session:

  base       — untrained granite-4.0-micro   (threads already on disk, from the v5 bench run)
  v5full     — v5 SFT, full corpus ~1.05M tk (threads already on disk — THE baseline)
  dense60    — v5 SFT, learnable-band ~60% tk (new)
  rand60     — v5 SFT, random ~60% tk         (new control)

  export GEMINI_API_KEY=...   # from ~/Desktop/reasoningEngine/.env — do NOT echo it
  python rejudge_arms.py

Reads thread files from ../data/bench and ../out; writes ../out/rejudge_summary.json.
Cost: 4 x 48 judge calls ≈ $2-3. Non-destructive, safe to re-run.
"""
from __future__ import annotations
import asyncio, json
from pathlib import Path

import numpy as np
import httpx

import head2head_v5 as H

JUDGE_MODEL = "claude-sonnet-5"


async def sonnet_call(client, prompt, max_tokens=12000):
    # Sonnet 5 is a thinking model: thinking tokens count toward max_tokens, so the budget
    # must be VERY generous or the JSON never arrives (4000 still lost 20/48 on one arm).
    # NOTE: `temperature` is deprecated/rejected on Sonnet 5 — omit it (judge is one session
    # regardless; exact decoding determinism is no longer a controllable knob on this family).
    body = {"model": JUDGE_MODEL, "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]}
    async with H.SEM:
        for a in range(4):
            try:
                r = await client.post("https://api.anthropic.com/v1/messages",
                                      headers={"x-api-key": H.ANTHROPIC_KEY,
                                               "anthropic-version": "2023-06-01",
                                               "content-type": "application/json"},
                                      json=body, timeout=120)
                r.raise_for_status()
                d = r.json()
                text = "".join(p.get("text", "") for p in d.get("content", [])
                               if p.get("type") == "text").strip()
                if not text:
                    print(f"    [judge empty: stop={d.get('stop_reason')}]", flush=True)
                    continue  # retry — empty text (thinking ate the budget or refusal)
                return text
            except Exception:
                await asyncio.sleep(2 * (a + 1))
    return None


async def sonnet_judge(client, problem, angles, threads):
    # identical formatting + parsing to H.judge — only the model call differs
    block = "\n".join(f"{i+1}. [{H.fam_of(a)}] {t}" for i, (a, t) in enumerate(zip(angles, threads)))
    out = await sonnet_call(client, H.JUDGE_PROMPT.format(problem=problem, threads=block))
    j = H.parse_json(out)
    if not j:
        return None
    try:
        s = {d: int(j[d]) for d in H.DIMS}
    except Exception:
        return None
    s["mean"] = round(sum(s[d] for d in H.DIMS) / 6, 2)
    return s


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FILES = {
    # SESSION 3 (2026-07-22): book run — all 7 sets generated on the SAME card (RTX PRO 6000);
    # anchors regenerated on-card per RUNBOOK3 Amendment 2 (card-class control).
    "book_A":    ROOT / "out/eval_book_A_v5_threads.jsonl",
    "book_B04":  ROOT / "out/eval_book_B04_v5_threads.jsonl",
    "book_B06":  ROOT / "out/eval_book_B06_v5_threads.jsonl",
    "book_C04":  ROOT / "out/eval_book_C04_v5_threads.jsonl",
    "book_C06":  ROOT / "out/eval_book_C06_v5_threads.jsonl",
    "keep100":   ROOT / "out/eval_anchor_keep100_v5_threads.jsonl",
    "mastery60": ROOT / "out/eval_anchor_mastery60_v5_threads.jsonl",
    # session-2 set (Ada-generated — do NOT mix into a PRO-6000 session):
    # "dense60":   ROOT / "out/eval_bench_dense60_v5_threads.jsonl",
    # "keep60":    ROOT / "out/eval_bench_keep60_v5_threads.jsonl",
    # "keep40":    ROOT / "out/eval_bench_keep40_v5_threads.jsonl",
}


def agg(rows):
    ok = [r for r in rows if r.get("judge")]
    a = {d: round(float(np.mean([r["judge"][d] for r in ok])), 2) for d in H.DIMS}
    a["overall"] = round(float(np.mean([r["judge"]["mean"] for r in ok])), 2)
    a["dist>=4%"] = round(100 * float(np.mean([r["judge"]["distinctness"] >= 4 for r in ok])), 1)
    a["n"] = len(ok)
    return a


async def main():
    for label, p in FILES.items():
        if not p.exists():
            raise SystemExit(f"missing thread file for '{label}': {p}")
    out = {}
    async with httpx.AsyncClient() as client:
        for label, path in FILES.items():
            rows = [json.loads(l) for l in path.open()]
            res = []

            async def one(r):
                j = await sonnet_judge(client, r["problem"], r["angles"], r["threads"])
                res.append({"problem": r["problem"], "judge": j})

            await asyncio.gather(*[one(r) for r in rows if r.get("threads")])
            out[label] = agg(res)
            print(f"{label:8s} {json.dumps(out[label])}", flush=True)

    summary = ROOT / "out/rejudge_summary.json"
    summary.write_text(json.dumps(out, indent=2))
    print(f"\nWROTE {summary}")
    ns = [v["n"] for v in out.values()]
    print("\n--- READ (RUNBOOK3 frozen criteria) ---")
    if min(ns) < 44:
        print(f"COVERAGE INSUFFICIENT (n={ns}) — do not read signals until all arms >= 44/48")
    bA = out.get("book_A", {})
    b04, b06 = out.get("book_B04", {}), out.get("book_B06", {})
    c04, c06 = out.get("book_C04", {}), out.get("book_C06", {})
    k1, ms = out.get("keep100", {}), out.get("mastery60", {})
    book_arms = {"book_A": bA, "book_B04": b04, "book_B06": b06, "book_C04": c04, "book_C06": c06}
    if all([bA, b04, b06, c04, c06, k1]):
        # Signal D headline: mastery-blanks vs plain reading (best C arm vs A, +0.20)
        best_c_label, best_c = max((("book_C04", c04), ("book_C06", c06)), key=lambda t: t[1]["overall"])
        dd = round(best_c["overall"] - bA["overall"], 2)
        print(f"[run3] Signal D: {best_c_label} {best_c['overall']} vs book_A {bA['overall']} "
              f"(delta {dd}) -> {'HOLDS' if dd >= 0.20 else 'FAILS'}")
        print(f"[run3]   blanks' share: B04 {b04['overall']} / B06 {b06['overall']} vs A {bA['overall']}; "
              f"mastery's share: C04-B04 {round(c04['overall'] - b04['overall'], 2)}, "
              f"C06-B06 {round(c06['overall'] - b06['overall'], 2)}")
        # Fraction curve: does 0.4 match 0.6?
        print(f"[run3] Fraction curve: C04 {c04['overall']} vs C06 {c06['overall']} "
              f"(delta {round(c04['overall'] - c06['overall'], 2)}) -> "
              f"{'0.4 PAR — keep-0.3/0.35 licensed' if c04['overall'] - c06['overall'] >= -0.15 else '0.4 BELOW — floor is between 0.4 and 0.6'}")
        # Book value check vs in-session keep100 anchor
        best_label, best = max(book_arms.items(), key=lambda t: t[1]["overall"])
        print(f"[run3] Book value: best book arm {best_label} {best['overall']} vs keep100 anchor "
              f"{k1['overall']} -> {'BOOK ADDED VALUE' if best['overall'] > k1['overall'] else 'NO MEASURABLE BOOK VALUE on this bench'}")
        # CHECKPOINT 1 WATCH: foresight >= keep100 foresight + 0.25 AND >= 3.25 absolute
        fs_label, fs_arm = max(book_arms.items(), key=lambda t: t[1].get("foresight", 0))
        fs, fk = fs_arm.get("foresight", 0), k1.get("foresight", 0)
        claimed = fs >= fk + 0.25 and fs >= 3.25
        print(f"[run3] CHECKPOINT 1 foresight: best {fs_label} {fs} vs anchor keep100 {fk} "
              f"(needs >= {round(fk + 0.25, 2)} AND >= 3.25) -> "
              f"{'CLAIMED' if claimed else 'watch continues'}")
    if ms and k1:
        print(f"[run3] Anchor sanity (same-card regen): mastery60 {ms['overall']} vs keep100 {k1['overall']} "
              f"(delta {round(ms['overall'] - k1['overall'], 2)}; run-2 read was par)")


if __name__ == "__main__":
    asyncio.run(main())
