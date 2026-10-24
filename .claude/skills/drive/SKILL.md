---
name: drive
description: "The console loop: run `hd drive`, spawn the agents it lists, link and end their runs, ask the user in chat before any upstream action or release, repeat. Use in the console session whenever the harness daemon is running or the user says to drive, continue or check the harness."
---
# Drive the harness (console session only)

The daemon (`hd start --interval 60`) decides and books; you are its hands. Agents are spawned only from here, with the
Agent tool, and upstream actions run only after the user's yes in this chat. `hd` is `python3 ~/osrs-harness/hd.py`.

## The loop
1. `hd drive` (add `--json` to parse it). It prints one list; do the sections in this order.
2. **Spawn** (each item: name, role, change, brief path, isolation): call the Agent tool with
   `subagent_type` = the role and `prompt` = the contents of the brief file (it names the change and the agent). Set
   `isolation: "worktree"` only where the item says `worktree` (client-dev, client-qa, harness-dev). Start it in the
   background, then `hd run-link <name> <agent-id>` with the id the tool returned. NEVER call EnterWorktree in the
   console session: it moves this session's cwd and breaks the subagents' Bash.
3. **When an agent finishes** (its completion notification): `hd run-end <name> --tokens <n> --turns <n>` (add
   `--exit error` if it failed). That frees its locks and owner; the next tick moves the change on.
4. **Stop** (a run the daemon found lingering): TaskStop its `agent_id`, then `hd run-stopped <name>`.
5. **Needs the user's OK** (upstream PR open/update/ready, client release): show the user, in chat, what the item
   says: the action, the PR title and body (or release notes), the gate record, the diff, the caveats, the exact
   commands. Ask with AskUserQuestion (Yes / No / Change). Only after a yes, run the listed commands yourself, one by
   one, stopping at the first failure. No yes, no commands. A "no" or "change" needs no record: the item stays in the
   list until the world changes, so say what you did not do and move on (`hd fail <slug> "why"` puts a decision hold on
   the change if the user wants it parked). A release without a tag (`choose-tag`): ask the user for the version, then
   `hd release-request vX.Y.Z`.
6. **Decisions** (a change on a `decision` hold): ask the user the question with AskUserQuestion, then
   `hd unhold <slug> "<answer>"` (and `hd note "<answer>" --kind user`). Do the change's follow-up yourself or leave it
   to the next dev run.
7. **Exceptions** (an integrator ended without clearing a train, an `exception` hold, a `failed` hold no dev picks up):
   read the detail, fix or ask the user, then the commands listed (`hd resume`, `hd resolve`, `hd unhold`).
8. Repeat. Pace it with `/loop` or ScheduleWakeup (the daemon ticks every 60 s, so a few minutes between rounds is
   plenty); an empty list prints `nothing to do`. Record what the user says with `hd note "<text>" --kind user`.

## Rules
- Decide on observed facts; completion of an action is what the remotes show, never a record you write.
- Never push upstream, comment, ready, tag or release without the user's yes in this session. Agents cannot (the role
  hooks deny it); you can, and that is exactly why you ask first.
- Deploys, trains and re-pins are the daemon's; never run them from here unless the user asks (`hd train --now`).
- Keep this context small: delegate anything beyond a couple of quick commands to an agent and read verdicts from
  `hd status`, not logs.
- Times for the user are US Eastern.
