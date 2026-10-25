"""The dashboard: one HTML page the pass writes after each real pass (harness/state/dashboard/index.html), served
read-only on localhost by the hd-dashboard unit. Nothing here decides anything: it shows what `hd` shows (the task
queue), the agents' activity read from their run records and transcripts, and the status of the goal, the train, the
test server and the upstream PRs.
"""
import html
import json
import os

from . import store, steps
from .tick import _lines

PAGE = store.path("dashboard", "index.html")
ET = __import__("zoneinfo").ZoneInfo("America/New_York")   # times for the user are US Eastern


def _et(ts):
    """'2026-10-25T23:56:31Z' -> '2026-10-25 19:56 EDT'; '' for none."""
    import datetime
    if not ts:
        return ""
    try:
        d = datetime.datetime.fromisoformat(str(ts).replace("Z", "+00:00")[:25])
    except ValueError:
        return str(ts)[:16]
    return d.astimezone(ET).strftime("%Y-%m-%d %H:%M %Z")


def _activity(run):
    """(last activity time, last thing the agent said) from its transcript."""
    ts, said = run.get("started"), ""
    for e in _lines(run.get("transcript")):
        ts = e.get("timestamp") or ts
        if e.get("type") == "assistant":
            for b in (e.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "text" and b.get("text", "").strip():
                    said = b["text"].strip()
    return _et(ts), said[-240:]


def _table(head, rows):
    e = html.escape
    th = "".join(f"<th>{e(h)}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{e(str(c))}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{tr or '<tr><td colspan=9>none</td></tr>'}</tbody></table>"


def render(ctx):
    from .cli import view
    v = view(ctx, briefs=False)
    e = html.escape
    running = []
    for r in steps.alive_runs(ctx):
        ts, said = _activity(r)
        running.append((r["name"], r.get("role"), r.get("change"), _et(r.get("started")), ts, said))
    ended = sorted((r for r in ctx.runs if r.get("ended")), key=lambda r: r["ended"], reverse=True)[:12]
    recent = [(r["name"], r.get("role"), _et(r["ended"]), {True: "yes", False: "no", None: "-"}[r.get("record")],
               (r.get("last") or "")[-160:]) for r in ended]
    prs = []
    for c in ctx.changes:
        pr = steps._pr(ctx, c) if c["track"] == "server" and c.get("kind") == "change" else None
        if pr and pr.get("number") not in [p[0] for p in prs]:
            prs.append((pr["number"], c["slug"], pr.get("state"), "draft" if pr.get("draft") else "ready", (pr.get("head") or "")[:9]))
    t = steps.train_state()
    live = store.read("live.json") or {}
    goals = "".join(f"<div class=stat><b>{e(g['slug'])}</b> {e(str(g['value']))} / {g['target']}"
                    f"<span>{len(g['serving'])} changes serving</span></div>" for g in v["goals"])
    stat = (goals + f"<div class=stat><b>train</b> {e(str(t.get('step')))}{' FAILED at ' + e(str(t.get('failed_step'))) if t.get('failed_step') else ''}"
            f"<span>ended {e(_et(t.get('ended')) or 'running')}</span></div>"
            f"<div class=stat><b>test server</b> {e(str(live.get('image', '-')))}<span>since {e(_et(live.get('since')) or '-')}</span></div>")
    alerts = "".join(f"<p class=alert>{e(a)}</p>" for a in v["alerts"])
    waiting = "".join(f"<details open><summary>{e(q['change'])}</summary><pre>{e(q['text'])}</pre></details>" for q in v["questions"]) + \
              "".join(f"<details><summary>approval: {e(c['change'])}</summary><pre>{e(c['text'])}</pre></details>" for c in v["cards"])
    busy = {r.get("change"): r["name"] for r in steps.alive_runs(ctx)}
    nxt = {}
    for ch, step in steps.next_steps(ctx):   # who acts next on each change: an agent, the pass, the user, or upstream
        who = step.actor(ctx, ch)
        nxt.setdefault(ch["slug"], []).append({"script": "the pass", "user": "you", steps.WAIT: "upstream"}.get(who, who) + f" ({step.name})")
    queue = _table(("#", "pri", "track", "change", "stage", "next", "last script step"),
                   [(i + 1, c["priority"], c["track"], c["slug"], " | ".join(c["stage"]),
                     f"running: {busy[c['slug']]}" if c["slug"] in busy else ", ".join(nxt.get(c["slug"], ["waiting on a dependency"])),
                     c["last"] or "") for i, c in enumerate(v["changes"])])
    return f"""<!doctype html><html><head><meta charset=utf-8><meta http-equiv=refresh content=30>
<meta name=viewport content="width=device-width,initial-scale=1"><title>osrs-harness</title><style>
:root{{--bg:#fff;--fg:#1d1d1f;--mut:#6e6e73;--line:#e3e3e8;--card:#f6f6f8;--warn:#b3261e}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151517;--fg:#ececf0;--mut:#9a9aa2;--line:#2e2e33;--card:#1e1e22;--warn:#ff8a80}}}}
body{{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif;margin:0 auto;max-width:1200px;padding:16px}}
h1{{font-size:20px;margin:0 0 4px}} h2{{font-size:15px;margin:22px 0 8px;color:var(--mut);text-transform:uppercase;letter-spacing:.04em}}
.stats{{display:flex;flex-wrap:wrap;gap:10px}} .stat{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px}}
.stat span{{display:block;color:var(--mut);font-size:12px}} table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}} th{{color:var(--mut);font-weight:600}}
pre{{white-space:pre-wrap;background:var(--card);padding:10px;border-radius:6px;font-size:12px}} .alert{{color:var(--warn);font-weight:600}}
.wrap{{overflow-x:auto}} small{{color:var(--mut)}}</style></head><body>
<h1>osrs-harness</h1><small>written by the pass at {e(_et(store.now()))}; refreshes every 30 s</small>{alerts}
<h2>Status</h2><div class=stats>{stat}</div>
<h2>Waiting for you</h2>{waiting or '<small>nothing</small>'}
<h2>Agents running</h2><div class=wrap>{_table(("run", "role", "change", "started", "last activity", "last said"), running)}</div>
<h2>Next to spawn</h2><div class=wrap>{_table(("run", "role", "change", "step"), [(s["name"], s["role"], s["change"], s["step"]) for s in v["spawn"]])}</div>
<h2>Task queue</h2><small>in execution order: priority, then age (the order the harness spawns in)</small><div class=wrap>{queue}</div>
<h2>Upstream PRs</h2><div class=wrap>{_table(("PR", "change", "state", "draft", "head"), prs)}</div>
<h2>Recent runs</h2><div class=wrap>{_table(("run", "role", "ended", "record", "last message"), recent)}</div>
</body></html>"""


def write(ctx):
    os.makedirs(os.path.dirname(PAGE), exist_ok=True)
    with open(PAGE + ".tmp", "w") as f:
        f.write(render(ctx))
    os.replace(PAGE + ".tmp", PAGE)
