"""Locks for the shared resources (BR-R1): `integration` (the integration clone and its lease push, one train at a time),
`live-server` (a deploy) and `ghidra` (the one Ghidra project writer). Client instances (device, desktop) are not
resources: every agent starts its own client and stops it when done. One record per resource,
`harness/state/leases/<resource>.json`:

  {resource, holder, purpose, since, pid, container, change, run}

- A take refuses while another holder has the resource. The daemon (`harnessd`) holds `integration` for a train and
  `live-server` for a deploy; an agent takes `ghidra` for the time it writes the project.
- A lock taken by an agent the daemon spawned is bound to that agent's process (its run record's pid), unless the
  caller attaches another pid or container. `idle()` says whether a held lock shows no use: the holder's run ended, or
  its attached process or container is dead. The daemon reclaims idle locks with that evidence (BR-R2), as an event.
  A lock with nothing attached is never idle; a person reclaims it (`hd lease reclaim`).

Every action is an event (`lease`)."""
from . import events, policy, store
from .util import iso, pid_alive

DAEMON = "harnessd"
_FREE = dict(holder=None, purpose=None, since=None, pid=None, container=None, change=None, run=None)


def _rec(resource):
    r = store.rec_load("leases", resource) or {"resource": resource}
    for k, v in _FREE.items():
        r.setdefault(k, v)
    return r


def _save(r):
    store.rec_save("leases", r["resource"], r)
    return r


def known(resource):
    return resource in policy.resources()


def run_of(holder):
    """The holder's run record (an agent the daemon spawned), or None."""
    r = store.rec_load("runs", holder)
    return r if isinstance(r, dict) else None


def take(resource, holder, purpose="", pid=None, container=None, change=None):
    """(ok, message). Refused while another holder has it. A holder that is a spawned agent is bound to its run's pid
    unless the caller attaches another pid or container: whether it is in use is then a fact, not a guess."""
    if not known(resource):
        return False, f"unknown resource {resource}"
    r = _rec(resource)
    if r.get("holder") and r["holder"] != holder:
        events.emit("lease", action="deny", resource=resource, holder=holder, why=f"held by {r['holder']}")
        return False, f"DENIED: {resource} held by {r['holder']} ({r.get('purpose') or ''}, since {r.get('since')})"
    run = run_of(holder)
    if pid is None and run and run.get("pid") and not run.get("ended"):
        pid = run["pid"]
    r.update(holder=holder, purpose=purpose, since=iso(), pid=pid, container=container, change=change,
             run=holder if run else None)
    _save(r)
    events.emit("lease", action="take", resource=resource, holder=holder, purpose=purpose, change=change)
    return True, f"{resource} taken by {holder} ({purpose})"


def release(resource, holder):
    r = _rec(resource)
    if not r.get("holder"):
        return True, "already free"
    if r["holder"] != holder and holder != DAEMON:
        return False, f"DENIED: {resource} held by {r['holder']}"
    was = r["holder"]
    r.update(_FREE)
    _save(r)
    events.emit("lease", action="release", resource=resource, holder=was)
    return True, f"{resource} free"


def reclaim(resource, why):
    r = _rec(resource)
    if not r.get("holder"):
        return True, "already free"
    was = dict(r)
    r.update(_FREE)
    _save(r)
    events.emit("lease", action="reclaim", resource=resource, holder=was.get("holder"), why=why,
                purpose=was.get("purpose"), since=was.get("since"), pid=was.get("pid"))
    return True, f"{resource} reclaimed from {was.get('holder')}: {why}"


def status(resource):
    return _rec(resource)


def status_all():
    return {n: status(n) for n in policy.resources()}


def holds(resource, holder):
    return _rec(resource).get("holder") == holder


def idle(resource, container_alive=None):
    """(idle, evidence) for a held lock, decided on facts: the holder's run ended -> idle; an attached process or
    container is dead -> idle; alive -> in use; nothing attached -> not idle (never decided by elapsed time). The
    daemon's own locks are never idle (batches release them)."""
    r = _rec(resource)
    if not r.get("holder"):
        return False, "free"
    if r["holder"] == DAEMON:
        return False, "held by the daemon"
    run = run_of(r["holder"])
    if run and run.get("ended"):
        return True, f"run {r['holder']} ended ({run.get('exit')})"
    if r.get("pid"):
        if pid_alive(r["pid"]):
            return False, f"pid {r['pid']} alive"
        return True, f"attached process {r['pid']} is dead"
    if r.get("container"):
        if container_alive and container_alive(r["container"]):
            return False, f"container {r['container']} running"
        return True, f"attached container {r['container']} is not running"
    if run and run.get("pid") and not pid_alive(run["pid"]):
        return True, f"run {r['holder']} process {run['pid']} is dead"
    return False, "nothing attached"
