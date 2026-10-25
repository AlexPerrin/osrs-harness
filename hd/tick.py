"""One pass (ARCHITECTURE 1, 8): under the state lock, repair, then do the first unmet script step of every change
whose dependencies are live, then file maintainer findings. `run(F, dry)` returns the lines it would print.
"""
import glob
import json
import os
import shutil

from . import server, steps, store
from .facts import Facts, sh

LIVE_IMAGES = "osrs-openrune"
RECORD = {"handover": "handover", "verdict": "verdict", "measure": "measure"}


# --- the run's end, read from the agent's transcript ---------------------------------------------------------------------

def _lines(path):
    try:
        with open(path or "", errors="replace") as f:
            for line in f:
                try:
                    yield json.loads(line)
                except ValueError:
                    continue
    except OSError:
        return



def usage(path):
    out = {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0, "turns": 0}
    keys = {"input_tokens": "input", "output_tokens": "output", "cache_read_input_tokens": "cache_read",
            "cache_creation_input_tokens": "cache_creation"}
    for e in _lines(path):
        u = (e.get("message") or {}).get("usage") if e.get("type") == "assistant" else None
        if u:
            out["turns"] += 1
            for k, name in keys.items():
                if isinstance(u.get(k), (int, float)):
                    out[name] += int(u[k])
    return out


def handed_back(path):
    """The agent called SubagentHandback: its work is over. A stop without it is a pause for background work."""
    for e in _lines(path):
        if e.get("type") == "assistant":
            for b in (e.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "SubagentHandback":
                    return True
    return False


def end_run(run, last=""):
    """The run is over: `record` says whether the role's record exists and is newer than the start."""
    kind = RECORD.get((store.config().get("roles") or {}).get(run.get("role"), {}).get("record") or "")
    rec = store.record(run["change"], kind) if kind else None
    produced = None if not kind else bool(rec) and (rec.get("ts") or "") >= (run.get("started") or "")
    run.update(ended=store.now(), record=produced, last=last, usage=usage(run.get("transcript")))
    store.save_run(run)
    store.event("run", action="end", run=run["name"], role=run.get("role"), change=run["change"], record=produced, **run["usage"])
    return run



def repairs(ctx, dry=False):
    out, F = [], ctx.F
    for r in ctx.runs:
        if r.get("ended"):
            continue
        if r.get("transcript") and handed_back(r["transcript"]):
            out.append(f"run {r['name']}: handed back; ended")
            if not dry:
                end_run(r, last="hand-back seen by the pass")
        elif not F.alive(r.get("console_pid"), r.get("console_start")):
            out.append(f"run {r['name']}: console died; ended")
            if not dry:
                r.update(ended=store.now(), record=None, last="console died", reason="console-died")
                store.save_run(r)
                store.event("run", action="end", run=r["name"], change=r.get("change"), reason="console-died")
    t = steps.train_state()
    if t.get("pid") and not t.get("ended") and not F.alive(t["pid"], t.get("start")):
        out.append(f"train: process {t['pid']} died during {t.get('step')}; will rerun")
        if not dry:
            t.update(ended=store.now(), detail=f"process died during {t.get('step')}")
            store.write(t, "train.json")
    ended = {r["name"] for r in ctx.runs if r.get("ended")}
    for c in F.containers() or []:
        n = c["name"]
        orphan = (n.startswith("qa-dev-") and n[len("qa-dev-"):] in ended) or (n.startswith("hd-boot-") and not steps._train_alive(ctx))
        if orphan:
            out.append(f"container {n}: owner gone; removed")
            if not dry:
                sh(["docker", "rm", "-f", n], timeout=120)
                store.event("repair", what="container", name=n)
    for d in glob.glob(os.path.join(ctx.cfg["paths"]["work"], "agents", "*")):
        if os.path.basename(d) in ended:
            out.append(f"clone {d}: run ended; removed")
            if not dry:
                shutil.rmtree(d, ignore_errors=True)
                store.event("repair", what="clone", name=d)
    live = store.read("live.json") or {}
    keep = {live.get("image"), live.get("rollback")}
    for img in F.images(LIVE_IMAGES) or []:
        if img.startswith(f"{LIVE_IMAGES}:integration-") and img not in keep and live.get("image") and not steps._train_alive(ctx):
            out.append(f"image {img}: neither live nor rollback; removed")
            if not dry:
                sh(["docker", "rmi", img], timeout=120)
                store.event("repair", what="image", name=img)
    if not dry:
        for repo in (ctx.cfg["paths"]["client"], ctx.cfg["paths"]["fork"], store.HD_HOME):
            F.git(repo, "worktree", "prune")
    return out


def alerts(ctx):
    out = []
    if not ctx.F.docker_ok():
        out.append("Docker is down: no train, image or deploy runs")
    if not ctx.F.gh_ok():
        out.append("gh is not authenticated: no GitHub step runs")
    return out


def run(F=None, dry=False):
    cfg = store.config()
    F = F or Facts(cfg)
    with store.locked():
        ctx = steps.Ctx(cfg, F)
        out = repairs(ctx, dry)
        for ch, step in steps.next_steps(ctx):
            if step.actor(ctx, ch) != "script":
                continue
            if dry:
                out.append(f"{ch['slug']} {step.name}: would run")
                continue
            detail = step.do(ctx, ch)
            store.write({"step": step.name, "head": steps.head(ctx, ch), "detail": detail[:300], "ts": store.now()}, ch["slug"], "step.json")
            store.event("step", change=ch["slug"], step=step.name, detail=detail[:300])
            out.append(f"{ch['slug']} {step.name}: {detail}")
        if not dry:
            out += [f"filed {s}" for s in server.findings(ctx)]
    return out
