"""
run13b_report.py — RUN 13B observability report (RUNBOOK13B deliverable).

Reads out/run13b/{events.jsonl, transcript13b.json, round*.json, results.json}
and writes out/run13b/report.html — a self-contained page: bar verdicts, per-arm
scoreboards, the lexical-vs-semantic sin histogram, every D' repair trajectory,
per-problem drill-downs with speeches and flags inline, cross-run wall history,
and judge-cost accounting. The knowledge layer for run 14.

  python scripts/run13b_report.py
"""
from __future__ import annotations
import html, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out/run13b"


def esc(s):
    return html.escape(str(s))


def load():
    d = {}
    d["res"] = json.loads((OUT / "results.json").read_text())
    d["t"] = json.loads((OUT / "transcript13b.json").read_text())
    d["r1"] = json.loads((OUT / "round1.json").read_text())
    d["r2"] = json.loads((OUT / "round2.json").read_text())["rows"]
    d["r3"] = json.loads((OUT / "round3.json").read_text())["rows"]
    d["ev"] = [json.loads(l) for l in (OUT / "events.jsonl").open()]
    d["man"] = {json.loads(l)["pid"]: json.loads(l)
                for l in (ROOT / "data/run13/staged_problems.jsonl").open()}
    return d


def flag_chips(row):
    chips = [f'<span class="chip lex">{esc(k)}</span>' for k, _ in row["code_flags"]]
    j = row.get("judge")
    if j:
        if j["coherent"]:
            chips.append('<span class="chip ok">judge: coherent</span>')
        else:
            chips += [f'<span class="chip sem">{esc(f[:90])}</span>' for f in j["flaws"]]
    elif not row["code_flags"]:
        chips.append('<span class="chip warn">not judged</span>')
    if row.get("verbosity"):
        chips.append(f'<span class="chip warn">verbosity: {esc(row["verbosity"])}</span>')
    return " ".join(chips) or '<span class="chip ok">clean</span>'


def bar_row(label, value, ok=None):
    cls = "" if ok is None else (" pass" if ok else " fail")
    badge = "" if ok is None else (f'<span class="badge{cls}">{"PASS" if ok else "FAIL"}</span>')
    return f'<div class="bar-line"><b>{esc(label)}</b> {esc(value)} {badge}</div>'


def hist_bars(pairs, cls):
    total = max((n for _, n in pairs), default=1) or 1
    out = []
    for name, n in pairs:
        w = int(100 * n / total)
        out.append(f'<div class="hrow"><span class="hlabel">{esc(name)}</span>'
                   f'<span class="htrack"><span class="hbar {cls}" style="width:{w}%"></span></span>'
                   f'<span class="hnum">{n}</span></div>')
    return "".join(out)


def main():
    d = load()
    res, r1 = d["res"], d["r1"]
    rows_a = [r for r in r1["rows"] if r["arm"] == "A"]
    rows_c = [r for r in r1["rows"] if r["arm"] == "C"]
    dp_final = {r["pid"]: dict(r, attempt=1) for r in rows_a}
    traj = {r["pid"]: [dict(r, attempt=1)] for r in rows_a}
    for rows in (d["r2"], d["r3"]):
        for r in rows:
            dp_final[r["pid"]] = r
            traj[r["pid"]].append(r)

    def clean(r):
        return not r["code_flags"] and r.get("judge") and r["judge"]["coherent"]

    # sin histogram: lexical classes from code, semantic = judged flaw counts
    lex = {}
    sem_count = 0
    for r in r1["rows"] + d["r2"] + d["r3"]:
        for k, _ in r["code_flags"]:
            lex[k] = lex.get(k, 0) + 1
        if r.get("judge") and not r["judge"]["coherent"]:
            sem_count += len(r["judge"]["flaws"])
    judge_ev = [e for e in d["ev"] if e.get("stage") == "judge"]
    n_cached = sum(1 for e in judge_ev if e.get("cached"))

    b2 = res["bar2_wall_A"]
    parts = ["""<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Run 13B — fusion wall observability</title><style>
:root{--bg:#101216;--fg:#d8dce3;--mut:#8b93a1;--card:#181b21;--line:#262b34;
--ok:#3fb96f;--bad:#e05c5c;--lex:#d9a441;--sem:#c46ad4;--acc:#5b9dd9}
@media (prefers-color-scheme: light){:root{--bg:#f6f6f3;--fg:#23272e;--mut:#68707c;
--card:#fff;--line:#e2e2dc;--ok:#1e7c46;--bad:#b03434;--lex:#9a6d10;--sem:#8b3f9e;--acc:#2b6cb0}}
body{background:var(--bg);color:var(--fg);font:15px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace;
margin:0;padding:2rem 1rem;display:flex;justify-content:center}
main{max-width:60rem;width:100%}h1{font-size:1.3rem}h2{font-size:1.05rem;margin-top:2.2rem;
border-bottom:1px solid var(--line);padding-bottom:.3rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:1rem;margin:.8rem 0}
.badge{padding:.05rem .5rem;border-radius:4px;font-weight:700;font-size:.8rem}
.badge.pass{background:var(--ok);color:#fff}.badge.fail{background:var(--bad);color:#fff}
.bar-line{margin:.35rem 0}.chip{display:inline-block;padding:.05rem .45rem;margin:.12rem;
border-radius:4px;font-size:.78rem;border:1px solid var(--line)}
.chip.lex{color:var(--lex);border-color:var(--lex)}.chip.sem{color:var(--sem);border-color:var(--sem)}
.chip.ok{color:var(--ok);border-color:var(--ok)}.chip.warn{color:var(--mut)}
table{border-collapse:collapse;width:100%}td,th{border:1px solid var(--line);
padding:.35rem .6rem;text-align:left;font-variant-numeric:tabular-nums}
.hrow{display:flex;align-items:center;gap:.6rem;margin:.25rem 0}
.hlabel{width:14rem;color:var(--mut);font-size:.82rem;flex-shrink:0}
.htrack{flex:1;background:var(--line);border-radius:3px;height:.7rem}
.hbar{display:block;height:100%;border-radius:3px}.hbar.lex{background:var(--lex)}
.hbar.sem{background:var(--sem)}.hnum{width:2.5rem;text-align:right}
details{margin:.5rem 0;border:1px solid var(--line);border-radius:6px;padding:.4rem .8rem;
background:var(--card)}summary{cursor:pointer;color:var(--acc)}
pre{white-space:pre-wrap;background:var(--bg);border:1px solid var(--line);
border-radius:4px;padding:.6rem;font-size:.82rem;overflow-x:auto}
.mut{color:var(--mut)}.traj{border-left:3px solid var(--acc);padding-left:.8rem;margin:.6rem 0}
</style><main>"""]
    parts.append("<h1>Run 13B — fusion wall, hybrid instrument</h1>")
    parts.append('<div class="card">')
    sa = res["bar1_spot_audit"]
    parts.append(bar_row("Bar 1 · precision spot-audit",
                         f'{sa["confirmed"]}/{sa["n"]} code flags confirmed',
                         sa["shortcut_stands"]))
    parts.append(bar_row("Bar 2 · THE WALL (arm A, official)",
                         f'{b2["clean"]}/24 hybrid-clean ({b2["rate"]:.0%}, '
                         f'CI {b2["ci95"][0]:.0%}–{b2["ci95"][1]:.0%})'))
    parts.append(bar_row("Bar 3 · size dissolve (14B)",
                         f'{res["bar3_C"]["clean"]}/24 (need ≥18 and ≥A+8)',
                         res["bar3_C"]["pass"]))
    parts.append(bar_row("Bar 4 · harness dissolve (judge-in-loop repair)",
                         f'{res["bar4_Dp"]["clean_within_3"]}/24 within ≤3 attempts (need ≥20)',
                         res["bar4_Dp"]["pass"]))
    parts.append(bar_row("Bar 6 · delivery means", esc(res["bar6_delivery"])))
    parts.append("</div>")

    parts.append("<h2>Scoreboard</h2><table><tr><th>arm</th><th>hybrid-clean</th>"
                 "<th>code-flagged</th><th>judge-incoherent</th><th>delivery</th></tr>")
    for label, rows in (("A · baseline 4B", rows_a), ("C · 14B spokesman", rows_c),
                        ("D′ · repair final", list(dp_final.values()))):
        ck = sum(1 for r in rows if clean(r))
        cf = sum(1 for r in rows if r["code_flags"])
        ji = sum(1 for r in rows if r.get("judge") and not r["judge"]["coherent"])
        ds = [r["judge"]["delivery"] for r in rows if r.get("judge")]
        dm = f"{sum(ds)/len(ds):.2f}" if ds else "—"
        parts.append(f"<tr><td>{esc(label)}</td><td>{ck}/24</td><td>{cf}</td>"
                     f"<td>{ji}</td><td>{dm}</td></tr>")
    parts.append("</table>")

    parts.append("<h2>Sin taxonomy — what the errors actually are</h2><div class='card'>")
    parts.append("<p class='mut'>Lexical (code-caught, free) vs semantic "
                 "(judge-caught — invisible to regex).</p>")
    parts.append(hist_bars(sorted(lex.items(), key=lambda x: -x[1]), "lex"))
    parts.append(hist_bars([("semantic flaws (judge)", sem_count)], "sem"))
    parts.append("</div>")

    parts.append("<h2>Repair trajectories (arm D′)</h2>")
    for pid in sorted(traj):
        steps = traj[pid]
        status = "clean" if clean(dp_final[pid]) else "STILL DIRTY"
        parts.append(f"<details><summary>problem {pid:02d} — {len(steps)} attempt(s), "
                     f"{status}</summary>")
        for r in steps:
            parts.append(f'<div class="traj"><b>attempt {r["attempt"]}</b> '
                         f'({r["words"]} words)<br>{flag_chips(r)}</div>')
        parts.append("</details>")

    parts.append("<h2>Per-problem drill-down</h2>")
    runs = {r["pid"]: r for r in d["t"]["runs"]}
    for pid in sorted(runs):
        run, pr = runs[pid], d["man"][pid]
        ra = next(r for r in rows_a if r["pid"] == pid)
        rc = next(r for r in rows_c if r["pid"] == pid)
        parts.append(f"<details><summary>problem {pid:02d} · {esc(pr['arch'])} · "
                     f"{esc(pr['counterparty'])} / {esc(pr['dead_token'])}</summary>")
        parts.append(f"<pre>{esc(pr['problem'])}\n\n{esc(pr['update'])}</pre>")
        for name in ("audit", "read", "plan", "motion"):
            parts.append(f"<p class='mut'>{name.upper()}</p><pre>{esc(run[name])}</pre>")
        parts.append(f"<p class='mut'>SPEECH A (4B)</p>{flag_chips(ra)}"
                     f"<pre>{esc(run['fusion_A'])}</pre>")
        parts.append(f"<p class='mut'>SPEECH C (14B)</p>{flag_chips(rc)}"
                     f"<pre>{esc(run['fusion_C'])}</pre>")
        parts.append("</details>")

    parts.append("<h2>Cross-run wall history</h2><table>"
                 "<tr><th>run</th><th>instrument</th><th>wall reading</th></tr>"
                 "<tr><td>12 (stage 1)</td><td>judge only, n=3</td>"
                 "<td>0/3 clean transcripts — ~1 error per 3 free-prose steps</td></tr>"
                 "<tr><td>13</td><td>code only (invalid: recall)</td>"
                 "<td>unofficial — judge-strict much worse than 1-in-3</td></tr>"
                 f"<tr><td><b>13B</b></td><td>hybrid (code filter + judge certify)</td>"
                 f"<td><b>{b2['clean']}/24 clean "
                 f"({b2['rate']:.0%}, CI {b2['ci95'][0]:.0%}–{b2['ci95'][1]:.0%})</b></td></tr>"
                 "</table>")

    parts.append(f"<h2>Judge economics</h2><div class='card'>"
                 f"{len(judge_ev)} judge reads this run · {n_cached} served from cache "
                 f"($0) · {len(judge_ev) - n_cached} billed</div>")
    parts.append("</main>")
    (OUT / "report.html").write_text("".join(parts))
    print(f"report -> {OUT/'report.html'}")


if __name__ == "__main__":
    main()
