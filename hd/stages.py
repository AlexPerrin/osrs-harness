"""The lifecycle (docs/PROBLEM.md section 4: dev -> gate -> done), generic over the tracks: each track gives its chain of
stages and the observed facts for the stages after `gate` (hd/tracks/); this module climbs the chain on those facts.

`backlog -> ready -> dev` are recorded (dispatch); `hd handover` records `gate`; from `gate` on the facts decide, and a
fact that could not be read never regresses a stage. Rules encoded here: BR-C2 (a new commit on the branch re-enters at
ready and voids every later fact), BR-C4 (ready needs every dep live; a change waiting on a dep is derived, not held), BR-S2 (stages are observed), BR-S9 (no loops: a
dev or a verifier is booked only for a head or finding set not booked before).
"""
import hashlib

from . import tracks
from .util import same_commit


def terminal(ch):
    return ch.terminal


def deps_met(ch, idx):
    """BR-C4: every dep is live; returns (ok, [open deps])."""
    open_ = []
    for d in ch.get("deps") or []:
        dep = idx.get(d)
        if dep is None or not dep.reached("live"):
            open_.append(d)
    return (not open_), open_


# --- booking keys (BR-S9) --------------------------------------------------------------------------------------------

def booking_key(ch, executor):
    """What a booked run was given: the head and, for a dev, the finding set the track reports. The same key twice means
    no new facts."""
    commit = ch.get("commit") or ""
    if executor != "dev":
        return commit
    found = sorted(tracks.of(ch).finding_set(ch))
    return commit + "|" + hashlib.sha1("\n".join(found).encode()).hexdigest()[:12]


def would_loop(ch, executor):
    """True when this executor was already booked for exactly these facts (BR-S9)."""
    return (ch.get("booked") or {}).get(executor) == booking_key(ch, executor)


# --- derive ----------------------------------------------------------------------------------------------------------

def derive(ch, obs, idx):
    """(stage, waiting_on, moved_commit): the stage the change has reached and the first unmet precondition. Below
    `gate` the recorded stage stands; from `gate` on the track's facts decide. `moved_commit` is the branch tip when it
    differs from the handed-over commit (BR-C2), only while the change is before its last stage."""
    track = tracks.of(ch)
    rec = ch.stage
    chain = ch.chain()
    facts = track.facts(ch, obs) if ch.get("branch") and ch.get("commit") else {}
    tip = facts.get("tip", (None, ""))[0]
    commit = ch.get("commit")
    open_ = rec in track.open_stages(ch) and not track.moves_expected(ch)
    moved = tip if (open_ and tip and commit and not same_commit(tip, commit)) else None
    if rec in ("backlog", "ready", "dev"):
        ok, open_deps = deps_met(ch, idx)
        if rec == "backlog":
            return "backlog", "no definition of done" if not ch.has_dod() else "backlog", moved
        if not ok:
            return rec, "waiting for " + ", ".join(f"{d} ({idx[d].stage if d in idx else 'missing'})" for d in open_deps), moved
        if rec == "ready":
            return "ready", "a free slot", moved
        return "dev", f"agent {ch.get('owner') or '?'}", moved
    if rec not in chain:
        return rec, "", moved
    stage, waiting = "gate", ""
    for s in chain[chain.index("gate") + 1:]:
        met, why = facts.get(s, (None, "not observed"))
        if met is None:
            if ch.reached(s):
                stage, waiting = s, why
                continue
            waiting = why
            break
        if not met:
            waiting = why
            break
        stage, waiting = s, ""
    if stage == chain[-1]:
        return stage, "", moved
    label = track.waiting(stage, ch)
    return stage, label + (f" ({waiting})" if label and waiting else waiting if not label else ""), moved


def next_executor(ch, idx=None):
    """Which agent role a change needs now, if any: dev (ready, or a `failed` hold from the gate on), else what the track
    asks (`gate`). A `decision` or `exception` hold needs nothing, nor does a change before `gate` with an open dep
    (blocked is derived from `idx`, never held)."""
    if ch.hold in ("decision", "exception"):
        return None
    if idx is not None and ch.stage in ("backlog", "ready", "dev") and not deps_met(ch, idx)[0]:
        return None
    if ch.stage == "ready" or (ch.hold == "failed" and ch.reached("gate")):
        return "dev"
    return tracks.of(ch).executor(ch)
