"""
gen_threads.py — bench THREAD GENERATION ONLY (pod, GPU, NO API keys needed).

Reuses dav_eval_v5's Harness/prompts byte-identically (imports them — zero duplication) and
writes the same eval_{label}_v5_threads.jsonl row shape the baselines have, with judge=None.
The inline judge is skipped on purpose: the verdict judge is the local single-session
Sonnet 5 pass (rejudge_arms.py), so no key ever needs to touch the pod.

  V5_DATA=/workspace/div/bench_data python gen_threads.py --label bench_dense60 \
      --dec adapters/dec_dense60 --wrk adapters/wrk_dense60
"""
from __future__ import annotations
import argparse, json

import torch
import dav_eval_v5 as E


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--dec", required=True)
    ap.add_argument("--wrk", required=True)
    ap.add_argument("--n", type=int, default=48)
    args = ap.parse_args()

    torch.manual_seed(42)  # same seed as dav_eval_v5.main
    probs = [json.loads(l) for l in (E.DATA / "eval_problems.jsonl").open()][:args.n]
    H = E.Harness(args.dec, args.wrk)
    E.OUTD.mkdir(parents=True, exist_ok=True)
    out = E.OUTD / f"eval_{args.label}_v5_threads.jsonl"

    n_ok = n_fail = 0
    with out.open("w") as f:
        for i, p in enumerate(probs):
            r = H.run(p["problem"])
            if not r:
                n_fail += 1; print(f"  [{i+1}/{len(probs)}] FAIL (decomp/format)", flush=True); continue
            facets, angles, threads = r
            # same guard as dav_eval_v5.main so thread sets stay comparable to the baselines
            if any(len(t.split()) < 8 for t in threads):
                n_fail += 1; print(f"  [{i+1}/{len(probs)}] FAIL (empty thread)", flush=True); continue
            f.write(json.dumps({"problem": p["problem"], "angles": angles,
                                "threads": threads, "judge": None}) + "\n")
            n_ok += 1
            print(f"  [{i+1}/{len(probs)}] ok", flush=True)
    print(f"THREADS DONE {args.label}: {n_ok} ok, {n_fail} fail -> {out}", flush=True)


if __name__ == "__main__":
    main()
