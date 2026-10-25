"""One pass (ARCHITECTURE 1, 8): under the state lock, repair, then do the first unmet script step of every change
whose dependencies are live, then file maintainer findings. `run(F, dry)` returns the lines it would print.
"""
import glob
import os
import shutil

from . import server, steps, store
from .facts import Facts, sh

LIVE_IMAGES = "osrs-openrune"


def repairs(ctx, dry=False):
    out, F = [], ctx.F
    for r in ctx.runs:
        if not r.get("ended") and not F.alive(r.get("console_pid"), r.get("console_start")):
            out.append(f"run {r['name']}: console died; ended")
            if not dry:
                r.update(ended=store.now(), record=None, last="console died")
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
        for repo in (ctx.cfg["paths"]["client"], store.HD_HOME):
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
            store.write({"step": step.name, "detail": detail[:300], "ts": store.now()}, ch["slug"], "step.json")
            store.event("step", change=ch["slug"], step=step.name, detail=detail[:300])
            out.append(f"{ch['slug']} {step.name}: {detail}")
        if not dry:
            out += [f"filed {s}" for s in server.findings(ctx)]
    return out
