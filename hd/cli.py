"""The nine commands (ARCHITECTURE 1). `hd` is `python3 ~/osrs-harness/hd.py`.

  hd [--json]                              the console's list: goals, spawns, cards, questions, alerts, running, changes
  hd tick [--dry-run]                      one pass (the timer and the stop hook run it)
  hd new <slug> --track t --title x [--kind change|release|local] [--priority P1] [--deps a,b] [--goal g]
         [--branch b] [--pr n] [--version vX.Y.Z] [--body text | stdin]        a change definition (a goal is a file)
  hd handover <slug> <sha> [--summary s]   the dev's record; refused unless the dev ref is at <sha> and evidence exists
  hd verdict <slug> <sha> PASS|FAIL [finding ...]   the reviewer's record; refused unless <sha> is the head
  hd ask <slug> "<question>" [--options a,b]        a question for the user; the change waits
  hd answer <slug> "<text>"                the user's answer, appended to the definition; the question is removed
  hd measure <goal> <value> --evidence <report>     the orchestrator's measurement, bound to the track's live tip
  hd approve <slug> <sha>                  the user's yes, bound to <sha> (the console alone)
"""
import argparse
import json
import os
import sys

from . import steps, store, tick
from .facts import Facts


def _ctx():
    cfg = store.config()
    return steps.Ctx(cfg, Facts(cfg))


def _change(ctx, slug):
    ch = ctx.by_slug.get(slug) or next((g for g in ctx.goals if g["slug"] == slug), None)
    if ch is None:
        sys.exit(f"no change or goal {slug}")
    return ch


def _refuse(why):
    sys.exit("refused: " + "; ".join(why))


def _last_script(ctx, ch):
    """What the pass's script did last on a step that is still the next one: a pending or failing step says why."""
    s = ctx.rec(ch, "step") or {}
    return s.get("detail") if s.get("step") in steps.stage(ctx, ch) else None


def cmd_list(a):
    ctx = _ctx()
    spawns = []
    os.makedirs(store.path("briefs"), exist_ok=True)
    for ch, step, role, name in steps.dispatch(ctx):
        text = steps.brief(ctx, ch, step, name)
        p = store.path("briefs", f"{name}.md")
        with open(p, "w") as f:
            f.write(text)
        spawns.append({"name": name, "role": role, "change": ch["slug"], "step": step.name, "brief": p,
                       "worktree": bool((ctx.cfg["roles"].get(role) or {}).get("worktree"))})
    out = {
        "goals": [{"slug": g["slug"], "value": (ctx.rec(g, "measure") or {}).get("value"), "target": g["target"],
                   "serving": [c["slug"] for c in steps._serving(ctx, g)]} for g in ctx.goals],
        "spawn": spawns,
        "cards": [{"change": s, "text": t} for s, t in steps.cards(ctx)],
        "questions": [{"change": s, "text": t} for s, t in steps.questions(ctx)],
        "alerts": tick.alerts(ctx),
        "running": [{"name": r["name"], "role": r.get("role"), "change": r.get("change"), "since": r.get("started")}
                    for r in steps.alive_runs(ctx)],
        "changes": [{"slug": c["slug"], "track": c["track"], "priority": c.get("priority"), "stage": steps.stage(ctx, c),
                     "last": _last_script(ctx, c)} for c in ctx.changes if steps.done(ctx, c) is not True],
    }
    if a.json:
        print(json.dumps(out, indent=1))
        return
    for g in out["goals"]:
        print(f"goal {g['slug']}: {g['value']} / {g['target']}" + (f"  serving: {', '.join(g['serving'])}" if g["serving"] else ""))
    for s in out["spawn"]:
        print(f"spawn {s['name']}: {s['role']} for {s['change']} ({s['step']}){' worktree' if s['worktree'] else ''}  brief {s['brief']}")
    for c in out["cards"]:
        print("card\n" + c["text"])
    for q in out["questions"]:
        print(f"question {q['change']}: {q['text']}")
    for al in out["alerts"]:
        print(f"alert: {al}")
    for r in out["running"]:
        print(f"running {r['name']}: {r['role']} on {r['change']} since {r['since']}")
    for c in out["changes"]:
        print(f"{c['priority']} {c['track']:7} {c['slug']}: {' | '.join(c['stage'])}" + (f"  ({c['last']})" if c["last"] else ""))


def cmd_tick(a):
    for line in tick.run(dry=a.dry_run):
        print(line)


def cmd_new(a):
    meta = {"slug": a.slug, "track": a.track, "kind": a.kind, "title": a.title, "priority": a.priority,
            "deps": [d for d in (a.deps or "").split(",") if d], "created": store.now()}
    for k in ("goal", "branch", "pr", "version"):
        if getattr(a, k):
            meta[k] = getattr(a, k)
    body = a.body if a.body is not None else (sys.stdin.read() if not sys.stdin.isatty() else "")
    body = body.strip() or "## Change\n\n## Definition of done\n"
    print(store.save_definition("changes", a.slug, meta, body))


def cmd_handover(a):
    ctx = _ctx()
    ch = _change(ctx, a.slug)
    h, why = steps.head(ctx, ch), []
    if h is None:
        why.append("the dev ref cannot be read (fetch failed)")
    elif h != a.sha:
        why.append(f"the dev ref {ctx.track(ch)['head'].replace('<slug>', ch['slug'])} is at {h[:9] if h else 'nothing'}, not {a.sha[:9]}")
    ev = steps.evidence(ch)
    if not (os.path.isdir(ev) and os.listdir(ev)):
        why.append(f"no evidence in {ev}")
    if why:
        _refuse(why)
    store.save_record(ch["slug"], "handover", {"head": h, "base": steps.base(ctx, ch), "evidence": ev, "summary": a.summary or ""})
    store.drop_record(ch["slug"], "ask")
    print(f"handover {ch['slug']} {h[:9]}")


def cmd_verdict(a):
    ctx = _ctx()
    ch = _change(ctx, a.slug)
    h, why = steps.head(ctx, ch), []
    if h != a.sha:
        why.append(f"the head is {h[:9] if h else 'nothing'}, not {a.sha[:9]}")
    if a.result == "FAIL" and not a.findings:
        why.append("a FAIL names its findings")
    if why:
        _refuse(why)
    store.save_record(ch["slug"], "verdict", {"head": h, "base": steps.base(ctx, ch), "pass": a.result == "PASS", "findings": a.findings})
    print(f"verdict {ch['slug']} {h[:9]} {a.result}")


def cmd_ask(a):
    ctx = _ctx()
    ch = _change(ctx, a.slug)
    store.save_record(ch["slug"], "ask", {"question": a.question, "options": [o for o in (a.options or "").split(",") if o]})
    print(f"asked on {ch['slug']}")


def cmd_answer(a):
    ctx = _ctx()
    ch = _change(ctx, a.slug)
    body = ch["body"].rstrip() + ("\n\n## Answers\n" if "## Answers" not in ch["body"] else "\n") + f"- {store.now()} {a.text}\n"
    meta = {k: v for k, v in ch.items() if k not in ("body", "hash", "path")}
    store.save_definition("goals" if "target" in ch else "changes", ch["slug"], meta, body)
    store.drop_record(ch["slug"], "ask")
    store.event("answer", change=ch["slug"], text=a.text[:300])
    print(f"answered {ch['slug']}")


def cmd_measure(a):
    ctx = _ctx()
    g = _change(ctx, a.goal)
    b = steps.base(ctx, {"slug": g["slug"], "track": g["track"]})
    if b is None:
        _refuse(["the track's live tip cannot be read"])
    if not os.path.exists(a.evidence):
        _refuse([f"no report at {a.evidence}"])
    store.save_record(g["slug"], "measure", {"value": a.value, "base": b, "evidence": a.evidence})
    print(f"measured {g['slug']} = {a.value} at {b[:9]}")


def cmd_approve(a):
    ctx = _ctx()
    ch = _change(ctx, a.slug)
    h = steps.head(ctx, ch)
    why = []
    if h != a.sha:
        why.append(f"the head is {h[:9] if h else 'nothing'}, not {a.sha[:9]}: approve the current commit")
    if steps.REVIEW.done(ctx, ch) is not True:
        why.append("no passing review at this head")
    if why:
        _refuse(why)
    store.save_record(ch["slug"], "approval", {"head": h})
    print(f"approved {ch['slug']} {h[:9]}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="hd")
    p.add_argument("--json", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    t = sub.add_parser("tick")
    t.add_argument("--dry-run", action="store_true")
    n = sub.add_parser("new")
    n.add_argument("slug")
    n.add_argument("--track", required=True, choices=["client", "server", "harness"])
    n.add_argument("--title", required=True)
    n.add_argument("--kind", default="change", choices=["change", "release", "local"])
    n.add_argument("--priority", default="P2", choices=["P0", "P1", "P2", "P3"])
    for k in ("--deps", "--goal", "--branch", "--version", "--body"):
        n.add_argument(k)
    n.add_argument("--pr", type=int)
    h = sub.add_parser("handover")
    h.add_argument("slug")
    h.add_argument("sha")
    h.add_argument("--summary")
    v = sub.add_parser("verdict")
    v.add_argument("slug")
    v.add_argument("sha")
    v.add_argument("result", choices=["PASS", "FAIL"])
    v.add_argument("findings", nargs="*")
    q = sub.add_parser("ask")
    q.add_argument("slug")
    q.add_argument("question")
    q.add_argument("--options")
    an = sub.add_parser("answer")
    an.add_argument("slug")
    an.add_argument("text")
    m = sub.add_parser("measure")
    m.add_argument("goal")
    m.add_argument("value", type=float)
    m.add_argument("--evidence", required=True)
    ap = sub.add_parser("approve")
    ap.add_argument("slug")
    ap.add_argument("sha")
    a = p.parse_args(argv)
    {None: cmd_list, "tick": cmd_tick, "new": cmd_new, "handover": cmd_handover, "verdict": cmd_verdict, "ask": cmd_ask,
     "answer": cmd_answer, "measure": cmd_measure, "approve": cmd_approve}[a.cmd](a)
    return 0
