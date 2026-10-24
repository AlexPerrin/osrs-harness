"""Agents are stage executors (BR-G1..G4): one change, one stage, a fresh context, a brief generated from the
change. v4: agents are spawned from the console session only. The daemon decides and books a run (record, owner, an `agent request` event with the brief's path); the console session (`hd drive`) spawns it with
the Agent tool, links it (`hd run-link`), and reports its end (`hd run-end`). Roles: client-dev, server-dev, client-qa,
server-qa, integrator, harness-dev (harness/policy.yaml).

Run record `harness/state/runs/<name>.json`:
  {name, role, change, stage, console: True, started, log (the brief), ended, exit, turns, minutes, tokens,
   result, agent_id, batch}
Agent names: policy `agents.names` prefix + a counter (`harness/state/counters.json`), continuing v2's gens.

  brief(ch, role, stage)              the spawn prompt (the change file, the name, how to hand over)
  spawn(ch, role, stage)              set owner, write the brief to the log, record the run, emit the request; returns the run record. For stage `train` the record passed is the
                                      batch (its id names the change).
  running()                           run records not ended
  link(name, agent_id)                the Agent-tool id of a run (for TaskStop on a stop-request)
  end(name, exit, turns, tokens, minutes, result)   `hd run-end`: the console reports the run ended
  stop(name, why)                     books the end and emits a `stop-request` for the console to TaskStop
  lingering(ch_index)                 [(run, why)] for agents whose change left the stage they execute (BR-G2), on
                                      the atomic fact alone (the owner field, the batch step)
Isolation: roles with policy `worktree: true` are spawned with isolation worktree by the console.
"""
import os

from . import HD_HOME, events, fork_clone, evidence_dir, leases, policy, stages, store, tracks
from .util import iso, read_json, write_json

RUNS = "runs"
HD = f"python3 {HD_HOME}/hd.py"   # absolute: agents run in the fork clone and in worktrees


def _counters_path():
    from . import state_dir
    return os.path.join(state_dir(), "counters.json")


def _log_path(name):
    from . import state_dir
    return os.path.join(state_dir(), RUNS, f"{name}.log")


def next_name(role):
    counters = {"cd": 47, "sd": 30, "sq": 30, "cq": 1, "ig": 0, "hd": 0}
    counters.update(read_json(_counters_path(), {}) or {})
    p = policy.get()["agents"]["names"][role]
    counters[p] = counters.get(p, 0) + 1
    write_json(_counters_path(), counters)
    return f"{p}{counters[p]}"


def _slug(ch):
    return ch.get("slug") or ch.get("id")


# --- the brief ----------------------------------------------------------------------------------------------------

def _stage_text(ch, stage, name):
    slug, branch = _slug(ch), ch.get("branch") or "<branch>"
    if stage == "dev":
        track = tracks.of(ch)
        lines = [f"Stage `dev`: build the change on branch `{branch}` until its definition of done is ticked, commit it",
                 "locally, then hand it over on disk, not in chat:",
                 f"  {HD} handover {slug} --branch {branch} --commit <sha> --evidence {_evidence(ch)} --summary \"...\""
                 + (" --repo <your clone>" if track.records_repo else ""),
                 "The hand-over runs its check at once and refuses an incomplete one (nothing is recorded): fix the items it",
                 "prints and run it again.",
                 f"Blocked by the other track: file the blocker, then `{HD} block {slug} --by <other-slug> \"why\"`:",
                 f"  {HD} new --track server --slug <x> --title \"...\" --dod \"repro on the test server\" --dod \"...\"",
                 f"Cannot finish: `{HD} fail {slug} \"why\"`."]
        lines += track.brief(ch, "dev")
    elif stage == "gate":
        if ch.get("batch") and ch.get("batch") == ch.get("id"):
            lines = [f"Stage `gate`: run the gate on batch `{ch.get('batch')}` (the role file says which gate and how). A release "
                     "gate copies its build (base.apk, split.apk, THIRD_PARTY_NOTICES.md, the repack log) into the evidence dir "
                     "before it ends: the worktree is removed with the run and the release attaches those copies.",
                     f"End with `{HD} gate {slug} PASS|FAIL \"note\"`. You never write the code you check."]
        else:
            lines = tracks.of(ch).brief(ch, "gate")
    else:
        lines = [f"Stage `train`: batch `{slug}` stopped on an exception. Record a resolution (or drop one change with a",
                 f"note) and end with `{HD} resolve {slug} \"note\"`. You never push integration or deploy.",
                 "Exception:", (ch.get("exception") or "(see the batch log)").rstrip()]
    hold = ch.get("hold") or {}
    if hold.get("kind") == "failed" and stage == "dev":
        lines.append(f"Hold `failed`: {hold.get('reason')}")
        lines.append(f"The fix is a new commit on the SAME branch `{branch}` (BR-C2, BR-S3): no second branch, no suffix; hand "
                     "over again and the hold clears.")
    return lines


def _evidence(ch):
    return os.path.join(evidence_dir(), _slug(ch))


RULES = ("Rules (the user's, standing): read game state through the data tools (osrs-devtools, osrs-devtools-desktop, "
         "osrs-mcp), never screenshots unless the user asks; evidence is a logcat extract or a data-tool dump. Start your own "
         "client (its own port and account state) when you need one and stop it when you are done. Keep scripts and temp files under `<scratchpad>/<your-name>/`, never at the scratchpad's top "
         "level. Report a denied action, never work around it. Once you have handed over, gated, resolved, blocked or "
         "failed, stop every background job you started (your client too), send one line and exit; start nothing new "
         "and never wait on CI after the hand-over.")


def brief(ch, role, stage):
    """The spawn prompt. Its first line names the change (hooks find the slug in the transcript); the role file is
    loaded by --agent, so role rules stay out of it."""
    slug, name = _slug(ch), ch.get("owner") or "<name>"
    head = [f"Harness change `{slug}` ({ch.get('track') or 'server'} track, stage `{stage}`). Your name is `{name}`, "
            f"role `{role}`."]
    if isinstance(ch, store.Change):
        head.append(f"Change file: {ch.path} (the change, its definition of done and the log). Read it first.")
    lines = head + _stage_text(ch, stage, name)
    lines.append(f"Evidence goes in {_evidence(ch)}/ (the main checkout; never a scratchpad or a worktree's re/).")
    if role == "integrator":
        lines.append(f"Work from the OpenRune fork clone {fork_clone()}, not the client checkout; the client repo is for client work only.")
    lines.append(RULES)
    body = getattr(ch, "body", "") or ""
    text = "\n".join(lines) + "\n"
    if body:
        text += "\n" + body.split("## Log")[0].rstrip() + "\n"
    return text


# --- spawn --------------------------------------------------------------------------------------------------------

def _persist(ch):
    if isinstance(ch, store.Change):
        store.save(ch)
    else:
        from .batches import BATCHES
        store.rec_save(BATCHES, ch["id"], ch)


def spawn(ch, role, stage):
    slug = _slug(ch)
    name = next_name(role)
    ch["owner"] = name
    if isinstance(ch, store.Change):
        if stage == "dev" and ch.stage == "ready":
            store.set_stage(ch, "dev", f"dispatched to {name}")
        store.add_log(ch, f"run {name} started ({role}, stage {stage})")
    log = _log_path(name)
    rec = {"name": name, "role": role, "change": slug, "stage": stage, "console": True, "started": iso(), "log": log,
           "ended": None, "exit": None}
    if isinstance(ch, store.Change) and stage in ("dev", "gate"):
        rec["commit"] = ch.get("commit")
        ch["booked"] = dict(ch.get("booked") or {}, **{stage: stages.booking_key(ch, stage)})   # BR-S9
    # A batch gate (the release pseudo-change: its id is the batch) follows the batch's step; a change's own gate does
    # not, though a live change carries the `batch` it went live in (its step `live` would stop the run at once).
    if stage == "train" or (ch.get("batch") and ch.get("batch") == ch.get("id")):
        rec["batch"] = slug if stage == "train" else ch.get("batch")
    os.makedirs(os.path.dirname(log), exist_ok=True)
    with open(log, "w") as f:
        f.write(brief(ch, role, stage))
    _persist(ch)
    store.rec_save(RUNS, name, rec)
    events.emit("agent", action="start", name=name, role=role, change=slug, stage=stage)
    events.emit("agent", action="request", name=name, role=role, change=slug, stage=stage, log=log,
                worktree=bool(policy.role(role).get("worktree")))
    return rec


# --- the end of a run ---------------------------------------------------------------------------------------------

def running():
    return [r for r in store.rec_all(RUNS) if not r.get("ended")]


def link(name, agent_id):
    r = store.rec_load(RUNS, name)
    if r:
        r["agent_id"] = agent_id
        store.rec_save(RUNS, name, r)
    return r


def _free_locks(name):
    for res, r in leases.status_all().items():
        if r.get("holder") == name:
            leases.release(res, name)


def _end(r, exit_, turns=None, tokens=None, minutes=None, result=""):
    """Bookkeeping for a run that is over: the record, the change's cost and owner, locks, event."""
    r.update(ended=iso(), exit=exit_, turns=turns, minutes=minutes, tokens=tokens, result=(result or "")[-500:])
    store.rec_save(RUNS, r["name"], r)
    name, slug = r["name"], r.get("change")
    if slug and store.exists(slug):
        ch = store.load(slug)
        cost = ch.get("cost") or {}
        cost["runs"] = cost.get("runs", 0) + 1
        cost["turns"] = (cost.get("turns") or 0) + (turns or 0)
        cost["tokens"] = (cost.get("tokens") or 0) + (tokens or 0)
        cost["minutes"] = round((cost.get("minutes") or 0) + (minutes or 0), 1)
        ch["cost"] = cost
        if ch.get("owner") == name:
            ch["owner"] = None
        store.add_log(ch, f"run {name} ended: {turns if turns is not None else '?'} turns, "
                          f"{tokens if tokens is not None else '?'} tokens, exit {exit_}")
        store.save(ch)
    events.emit("agent", action="end", name=name, role=r.get("role"), change=slug, stage=r.get("stage"),
                turns=turns, minutes=minutes, tokens=tokens, exit=exit_)
    _free_locks(name)
    return r


def end(name, exit_="ok", turns=None, tokens=None, minutes=None, result=""):
    """`hd run-end`: the console session reports that an Agent-tool run ended."""
    r = store.rec_load(RUNS, name)
    if not r or r.get("ended"):
        return r
    return _end(r, exit_, turns, tokens, minutes, result)


def stop(name, why):
    """Book the end of a run and ask the console to TaskStop its agent (an `agent stop-request` event)."""
    r = store.rec_load(RUNS, name)
    if not r or r.get("ended"):
        return r
    events.emit("agent", action="stop-request", name=name, agent_id=r.get("agent_id"), why=why)
    return _end(r, f"stopped:{why}")


# --- lingering -----------------------------------------------------------------------------------------

def _batch(bid):
    from .batches import BATCHES
    return store.rec_load(BATCHES, bid) if bid else None


def _left_stage(r, idx):
    """Why a run's subject no longer needs it: (why, when it changed) or None."""
    stage, name = r.get("stage"), r["name"]
    if stage == "train" or (stage == "gate" and r.get("batch")):
        b = _batch(r.get("batch"))
        want = "exception" if stage == "train" else "gating"
        if b is None:
            return "batch record missing", None
        if b.get("step") != want:
            return f"batch at {b.get('step')}", b.get("updated")
        return None
    ch = idx.get(r.get("change"))
    if ch is None:
        return "change missing", None
    if stage == "dev":
        # A dev run executes on a change at dev, or at a later stage under a `failed` hold (BR-S3: the fix is a new
        # commit); it lingers once the change no longer names it as owner (a run-end or a re-entry cleared it), not
        # merely because the stage is not `dev`.
        if ch.get("owner") != name:
            return f"owner is {ch.get('owner')} (change at {ch.stage})", ch.get("updated")
        return None
    # a verifier run is valid while the track says so (the server's: at `gate`, the booked commit, no record yet)
    why = tracks.of(ch).run_valid(r, ch)
    return (why, ch.get("updated")) if why else None


def lingering(idx):
    """Runs whose subject no longer needs them, on the atomic fact alone (the owner field, the batch step), with no
    grace period (feedback-atomic-not-time)."""
    out = []
    for r in running():
        left = _left_stage(r, idx)
        if left:
            out.append((r, f"lingering: {left[0]}"))
    return out


def mark_stopped(name):
    """`hd run-stopped`: the console TaskStopped the agent of a stopped run; it leaves the drive list."""
    r = store.rec_load(RUNS, name)
    if r:
        r["stop_done"] = iso()
        store.rec_save(RUNS, name, r)
    return r
