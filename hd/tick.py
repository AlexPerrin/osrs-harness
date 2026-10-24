"""One driver tick (problem 3f, PROBLEM.md BR-H1..H2), in this order:

  1 observe + reconcile   every change's stage re-derived from the facts each track reads (git, docker, ...); a record
                          that disagrees is repaired and logged as `drift`; a branch that moved past its hand-over
                          re-enters at ready and voids the gate (BR-C2); deps set or clear `blocked` holds (BR-C4);
                          a server change's `live_commit` follows the test server
  2 ship / train          each track's step for its handed-over changes (client and harness merge into their live
                          target; server changes the fork has join the train queue); trains advance (rebuild, gate,
                          image) one step, never blocking
  3 deploy                a gated image deploys once the daemon holds `live-server` (BR-B3); included changes are on the test server, dependents unblock
  4 re-pin                upstream main moved: fast-forward, drop merged branches, train (BR-B5)
  5 gates                 the release rule makes a release batch; a release record sets its step; the release gate agent is booked
  6 tracks                each track's own once-per-tick work (the server track files maintainer findings: BR-S4)
  7 dispatch              ready changes and gates x free slots, by priority (BR-C5); a dev or gate is booked only for a
                          head or finding set not booked before, else a durable decision hold (BR-S9)
  8 heal                  idle locks, lingering agents, dead containers, stuck batches (BR-H2)
  9 log                   the `tick` event with its actions and the stalled changes

Every step runs in its own try/except: a failure is an `error` event, the others still run. `dry_run` observes,
reconciles and reports what it would do without spawning, shipping, training or deploying."""
import time
import traceback

from . import actions, agents, batches, events, heal, leases, metrics, policy, stages, store, tracks
from .util import iso


class Ctx:
    def __init__(self, obs, dry_run):
        self.obs, self.dry_run = obs, dry_run
        self.actions, self.stalled = [], []
        self.idx = store.index()

    def act(self, text):
        self.actions.append(text if isinstance(text, str) else str(text)[:200])

    def refresh(self, slug=None):
        if slug:
            self.idx[slug] = store.load(slug)
        else:
            self.idx = store.index()


def _step(ctx, name, fn):
    try:
        fn(ctx)
    except NotImplementedError:
        ctx.act(f"{name}: not implemented yet")
    except Exception as e:   # one failing step never stops the tick
        events.emit("error", step=name, error=repr(e), trace=traceback.format_exc()[-1500:])
        ctx.act(f"{name}: error {e!r}")


# --- 1 observe + reconcile ----------------------------------------------------------------------------------------

def _reenter(ctx, slug, ch, moved):
    """BR-C2: a new commit on the branch with no run owning the change voids the hand-over, the gate and the booking."""
    events.emit("stage", change=slug, **{"from": ch.stage, "to": "ready"}, commit=moved,
                why="new commit on the branch: hand over again (BR-C2)")
    store.set_stage(ch, "ready", f"branch moved to {moved[:9]} past {str(ch['commit'])[:9]}: hand over again (BR-C2)")
    if ch.hold == "failed":
        store.clear_hold(ch, "the commit moved: the gate record is void")
    ch["commit"], ch["owner"], ch["booked"] = None, None, None
    store.save(ch)
    ctx.refresh(slug)
    ctx.act(f"{slug}: branch moved to {moved[:9]}, re-enters at ready")


def reconcile(ctx):
    waiting = {}
    for slug, ch in list(ctx.idx.items()):
        if ch.stage == "merged":
            continue
        stage, why, moved = stages.derive(ch, ctx.obs, ctx.idx)
        waiting[slug] = why
        if moved and ch.reached("gate") and not ch.get("owner") and not ctx.dry_run:
            _reenter(ctx, slug, ch, moved)
            continue
        tracks.of(ch).reconcile(ctx, slug, ch)
        ch = ctx.idx.get(slug, ch)
        if stage != ch.stage:
            direction = "drift" if ch.chain().index(stage) < ch.chain().index(ch.stage) else "stage"
            if ctx.dry_run:
                ctx.act(f"{slug}: {ch.stage} -> {stage} ({why or 'observed'}) [dry run]")
                continue
            before = ch.stage
            if stage == "live":
                ch["live_commit"] = ch["commit"]
            store.set_stage(ch, stage, "observed" if direction == "stage" else f"drift: {why}")
            store.save(ch)
            events.emit(direction, change=slug, **{"from": before, "to": stage}, commit=ch.get("commit"), why=why)
            ctx.refresh(slug)
            ctx.act(f"{slug}: {before} -> {stage}")
    store.rec_save("view", "waiting", {"waiting": waiting})
    # deps -> blocked holds (BR-C4)
    for slug, ch in list(ctx.idx.items()):
        if ch.stage not in ("backlog", "ready", "dev") or ctx.dry_run:
            continue
        ok, open_ = stages.deps_met(ch, ctx.idx)
        if not ok and ch.hold is None:
            store.set_hold(ch, "blocked", "waiting for " + ", ".join(open_))
            store.save(ch)
            events.emit("hold", change=slug, hold="blocked", reason=", ".join(open_))
            ctx.refresh(slug)
        elif ok and ch.hold == "blocked":
            store.clear_hold(ch, "every dep is live")
            store.save(ch)
            events.emit("hold", change=slug, hold="none", reason="deps live")
            ctx.refresh(slug)
            ctx.act(f"{slug}: unblocked")


# --- 2 ship / train ----------------------------------------------------------------------------------------------------

def ship_and_train(ctx):
    for slug, ch in list(ctx.idx.items()):
        if ch.get("commit") and ch.reached("gate"):
            tracks.of(ch).ship(ctx, slug, ch)
    if ctx.dry_run:
        return
    for a in batches.advance(ctx.obs) or []:
        ctx.act(a)
    ctx.refresh()


# --- 3 deploy -----------------------------------------------------------------------------------------------------------

def deploy(ctx):
    b = batches.deploy_ready(ctx.obs)
    if not b:
        return
    if ctx.dry_run:
        ctx.act(f"deploy of {b.get('id')} pending [dry run]")
        return
    if not leases.holds("live-server", leases.DAEMON):
        ok, msg = leases.take("live-server", leases.DAEMON, f"deploy {b['id']}")
        if not ok:
            ctx.act(f"deploy of {b['id']}: {msg}")
            return
    ok, msg = batches.deploy(b, ctx.obs)
    ctx.act(f"deploy {b['id']}: {msg}")


# --- 4 re-pin -------------------------------------------------------------------------------------------------------------

def repin(ctx):
    sha = batches.repin_due(ctx.obs)
    if not sha:
        return
    if ctx.dry_run:
        ctx.act(f"re-pin due: upstream main at {sha[:9]} [dry run]")
        return
    if leases.status("integration").get("holder"):
        ctx.act(f"re-pin to {sha[:9]} waits for the running train")
        return
    ctx.act(batches.repin(ctx.obs) or f"re-pin to {sha[:9]}")
    ctx.refresh()


# --- 5 gates and releases ---------------------------------------------------------------------------------------------------

def release_record(b):
    """The client release record qa/client-<version>.md in this repo with Verdict PASS at the batch's commit."""
    import os
    import re
    tag = actions.release_tag(b) or ""
    version = re.sub(r"^(client-)?v", "", tag)
    if not version:
        return None
    from . import ROOT
    p = os.path.join(ROOT, "qa", f"client-{version}.md")
    try:
        text = open(p).read()
    except OSError:
        return None
    commit = re.search(r"^- Commit: `([0-9a-f]{7,40})`", text, re.M)
    verdict = re.search(r"^## Verdict: \*\*(PASS|FAIL)\*\*", text, re.M)
    if commit and verdict and str(b.get("commit") or "").startswith(commit.group(1)):
        return verdict.group(1), p
    return None


def gates(ctx):
    if ctx.dry_run:
        return
    due = batches.release_due(ctx.idx)
    if due:
        b = batches.new_release(due)
        ctx.act(f"release batch {b.get('id')} for {len(due)} live client changes")
    running = agents.running()
    for b in batches.open_batches("release"):
        if b.get("step") == "gated" and actions.release_published(b, ctx.obs):
            b["step"] = "published"
            store.rec_save("batches", b["id"], b)
            events.emit("batch", batch=b["id"], step="published", detail=actions.release_tag(b), batch_kind="release")
            ctx.act(f"release {b['id']}: published ({actions.release_tag(b)})")
            continue
        if b.get("step") in ("queued", "gating"):
            rec = release_record(b)
            if rec:
                b["step"] = "gated" if rec[0] == "PASS" else "failed"
                b["record"] = rec[1]
                store.rec_save("batches", b["id"], b)
                events.emit("batch", batch=b["id"], step=b["step"], detail=rec[1], batch_kind="release")
                ctx.act(f"release {b['id']}: gate {rec[0]} ({rec[1]})")
                continue
            if b.get("step") == "queued" and not any(r.get("role") == "client-qa" and r.get("batch") == b["id"] for r in running):
                pseudo = {"slug": b["id"], "id": b["id"], "track": "client", "batch": b["id"], "branch": "master",
                          "commit": b.get("commit"), "title": f"release gate {b['id']}", "role": "client-qa"}
                r = agents.spawn(pseudo, "client-qa", "gate")
                b["step"] = "gating"
                store.rec_save("batches", b["id"], b)
                ctx.act(f"client-qa {r.get('name')} -> release {b['id']}")


# --- 6 tracks ----------------------------------------------------------------------------------------------------------------

def tracks_step(ctx):
    for t in tracks.every():
        t.step(ctx)


# --- 7 dispatch -----------------------------------------------------------------------------------------------------------------

def slots_free(role, running):
    pol = policy.role(role)
    track = pol["track"]
    used = sum(1 for r in running if r.get("role") == role)
    if pol["stage"] == "dev":
        return policy.track(track).get("dev_slots", 1) - used
    return 1 - used   # one QA per track, one integrator


def candidates(ctx):
    out = []
    for ch in ctx.idx.values():
        ex = stages.next_executor(ch)
        if not ex or ch.get("owner"):
            continue
        if ex == "dev" and not ch.has_dod():
            continue
        role = policy.role_for(ch["track"], ex)
        if not role:
            continue
        out.append((policy.prio_order(ch.get("prio")), ch.get("created") or "", ch, ex, role))
    out.sort(key=lambda t: (t[0], t[1]))
    return [(ch, ex, role) for _, _, ch, ex, role in out]


def hold_loop(ctx, ch, ex):
    """BR-S9: the same head and finding set were already given to a run; a new run would repeat it. A durable
    `decision` hold puts the change in the user's list (`hd unhold` clears it and resets the booking)."""
    why = (f"needs you: a {ex} run was already booked for exactly this head ({str(ch.get('commit') or 'none')[:9]}) and "
           "these findings; booking another would repeat it")
    if ctx.dry_run:
        ctx.act(f"{ch['slug']}: would hold ({ex} already booked for these facts) [dry run]")
        return
    store.set_hold(ch, "decision", why)
    store.save(ch)
    events.emit("hold", change=ch["slug"], hold="decision", reason=why, source="no-loop")
    ctx.refresh(ch["slug"])
    ctx.act(f"{ch['slug']}: decision hold ({ex} not re-booked for the same facts)")


def dispatch(ctx):
    running = agents.running()
    for b in batches.open_batches("train"):
        if b.get("step") != "exception":
            continue
        # one integrator per exception: a run started after this exception (alive, ended or stopped by an operator)
        # means it is handled; a resume that fails again makes a new exception step and a new integrator
        since = next((x.get("started") for x in reversed(b.get("steps") or []) if x.get("step") == "exception"), None)
        handled = any(r.get("role") == "integrator" and r.get("batch") == b["id"] and (since is None or (r.get("started") or "") >= since)
                      for r in store.rec_all("runs"))
        if not handled:
            if ctx.dry_run:
                ctx.act(f"would spawn an integrator for {b['id']} [dry run]")
            else:
                r = agents.spawn(b, "integrator", "train")
                if r:
                    running.append(r)
                    ctx.act(f"integrator {r.get('name')} for {b['id']}")
    cap = int(policy.get()["agents"].get("max_concurrent", 0) or 0)
    for ch, ex, role in candidates(ctx):
        if stages.would_loop(ch, ex):
            hold_loop(ctx, ch, ex)
            continue
        if (cap and len(running) >= cap) or slots_free(role, running) <= 0:
            ctx.stalled.append(ch["slug"])
            continue
        if ctx.dry_run:
            ctx.act(f"would dispatch {role} for {ch['slug']} ({ex}) [dry run]")
            continue
        r = agents.spawn(ch, role, ex)
        running.append(r)
        ctx.refresh(ch["slug"])
        ctx.act(f"{role} {r.get('name')} -> {ch['slug']} ({ex})")


# --- 8b metrics (BR-H5) ------------------------------------------------------------------------------------------------------------

def metrics_step(ctx):
    if ctx.dry_run:
        return
    went_live = any(a.endswith("-> live") and not a.startswith(("int-", "rel-")) for a in ctx.actions)
    if metrics.due(client_went_live=went_live):
        names = metrics.recount("client live" if went_live else "daily")
        ctx.act(f"recount: {len(names)} metrics")


# --- 9 heal --------------------------------------------------------------------------------------------------------------------------

def heal_step(ctx):
    if ctx.dry_run:
        return
    for a in heal.run(ctx.obs, ctx.idx) or []:
        ctx.act(f"heal: {a}")
    ctx.refresh()


# --- the tick ----------------------------------------------------------------------------------------------------------------------------

def tick(obs=None, dry_run=False, interval=60):
    if obs is None:
        obs = tracks.Observer()
    obs.reset()
    t0 = time.time()
    ctx = Ctx(obs, dry_run)
    for name, fn in (("reconcile", reconcile), ("ship", ship_and_train), ("deploy", deploy),
                     ("repin", repin), ("gates", gates), ("tracks", tracks_step), ("dispatch", dispatch),
                     ("metrics", metrics_step), ("heal", heal_step)):
        _step(ctx, name, fn)
    secs = round(time.time() - t0, 1)
    n = (store.rec_load("view", "tick") or {}).get("n", 0) + 1
    store.rec_save("view", "tick", {"n": n, "seconds": secs, "at": iso(), "actions": ctx.actions, "dry_run": dry_run})
    if not dry_run:
        events.emit("tick", n=n, seconds=secs, actions=ctx.actions, stalled=sorted(set(ctx.stalled)), interval=interval)
    return ctx.actions
