"""The console's work list (v4): `hd drive` prints everything the console session must do now, computed from run
records, change files, batches and git/GitHub state. The console session is the only thing that spawns agents and the
only thing that acts upstream; this is its one input.

  work(obs=None) -> {spawn, stop, actions, decisions, exceptions}
    spawn        runs the daemon booked that the console has not linked yet (no `agent_id`): name, role, change,
                 stage, brief (path), worktree (spawn with isolation worktree), link/end commands
    stop         ended runs (run-end or the daemon's stop) whose agent the console has not TaskStopped (`stop_done`
                 unset): name, agent_id, why; skipped when the run was never linked (nothing to stop)
    actions      actions.pending_actions(): upstream actions and releases that need the user's OK, with commands
    decisions    changes on a `decision` hold: the question the user answers, and the command that clears it
    exceptions   what needs the console itself: a train at `exception` whose integrator ended, a change on an
                 `exception` hold, a `failed` hold that no dev run will pick up
  render(w)      the list as text

Nothing here is recorded: a spawn request disappears when the run is linked, a stop when `hd run-stopped` marks it, an
action when git/GitHub show it done, a decision or exception when its hold or batch step changes.
"""
from . import HD_HOME, actions, agents, batches, policy, stages, store

HD = f"python3 {HD_HOME}/hd.py"


def _spawn(runs):
    out = []
    for r in runs:
        if r.get("ended") or r.get("agent_id"):
            continue
        out.append({"name": r["name"], "role": r["role"], "change": r.get("change"), "stage": r.get("stage"),
                    "brief": r.get("log"), "worktree": bool(policy.role(r["role"]).get("worktree")),
                    "link": f"{HD} run-link {r['name']} <agent-id>",
                    "end": f"{HD} run-end {r['name']} --tokens <n> --turns <n>"})
    return out


def _stop(runs):
    out = []
    for r in runs:
        why = str(r.get("exit") or "")
        if r.get("ended") and r.get("agent_id") and not r.get("stop_done"):
            out.append({"name": r["name"], "agent_id": r["agent_id"], "why": why.removeprefix("stopped:"),
                        "done": f"{HD} run-stopped {r['name']}"})
    return out


def _decisions(idx):
    return [{"change": ch["slug"], "question": ch.hold_reason,
             "clear": f'{HD} unhold {ch["slug"]} "<the user\'s answer>"'}
            for ch in idx.values() if ch.hold == "decision"]


def _integrator_ended(b, runs):
    """A train at `exception` whose integrator(s) since the exception all ended. Before any integrator ran, dispatch
    books one and it shows under `spawn`."""
    since = next((x.get("started") for x in reversed(b.get("steps") or []) if x.get("step") == "exception"), None)
    mine = [r for r in runs if r.get("role") == "integrator" and r.get("batch") == b["id"]
            and (since is None or (r.get("started") or "") >= since)]
    return bool(mine) and all(r.get("ended") for r in mine)


def _exceptions(idx, runs):
    out = []
    for b in batches.open_batches("train"):
        if b.get("step") == "exception" and _integrator_ended(b, runs):
            out.append({"what": f"train {b['id']} is at exception after its integrator ended",
                        "detail": str(b.get("exception") or "")[:300],
                        "commands": [f'{HD} resume {b["id"]}   (after fixing)',
                                     f'{HD} resolve {b["id"]} "<note>"']})
    for ch in idx.values():
        if ch.hold == "exception":
            out.append({"what": f"{ch['slug']} is on an exception hold", "detail": ch.hold_reason,
                        "commands": [f'{HD} unhold {ch["slug"]} "<why>"']})
        elif ch.hold == "failed" and not ch.get("owner") and not stages.next_executor(ch, idx):
            out.append({"what": f"{ch['slug']} ({ch.stage}) is on a failed hold no dev run will pick up",
                        "detail": ch.hold_reason, "commands": [f'{HD} unhold {ch["slug"]} "<why>"']})
    return out


def work(obs=None):
    runs = store.rec_all(agents.RUNS)
    idx = store.index()
    return {"spawn": _spawn(runs), "stop": _stop(runs), "actions": actions.pending_actions(obs, idx),
            "decisions": _decisions(idx), "exceptions": _exceptions(idx, runs)}


def render(w):
    out = []
    if w["spawn"]:
        out.append("== Spawn (Agent tool: subagent_type = role; isolation worktree only where marked)")
        for s in w["spawn"]:
            out.append(f"  {s['name']}  role {s['role']}  change {s['change']} ({s['stage']})"
                       f"  isolation: {'worktree' if s['worktree'] else 'none'}")
            out.append(f"    brief (the agent's prompt): {s['brief']}")
            out.append(f"    then: {s['link']}   on completion: {s['end']}")
    if w["stop"]:
        out.append("== Stop (TaskStop)")
        for s in w["stop"]:
            out.append(f"  {s['name']}  agent {s['agent_id']}  why: {s['why']}   then: {s['done']}")
    if w["actions"]:
        out.append("== Needs the user's OK in chat (run the commands only after a yes)")
        for a in w["actions"]:
            out.append(actions.render(a))
    if w["decisions"]:
        out.append("== Needs you (decision holds)")
        for d in w["decisions"]:
            out.append(f"  {d['change']}: {d['question']}\n    clear: {d['clear']}")
    if w["exceptions"]:
        out.append("== Exceptions for the console")
        for e in w["exceptions"]:
            out.append(f"  {e['what']}\n    {e['detail']}")
            out += [f"    $ {c}" for c in e["commands"]]
    return "\n".join(out) if out else "nothing to do"
