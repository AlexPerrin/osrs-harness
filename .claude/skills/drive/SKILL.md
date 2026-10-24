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
5. **Needs the user's OK** (a server change's contribution, a draft-pr card, a client release): show the user, in chat,
   the card: the change, the commit, the diff range, the QA verdict with every check line and every finding, the
   evidence links, the PR title, body and comment text, the caveats, the exact command, with a risk note and your
   recommendation. Ask with AskUserQuestion (Approve this commit / Fix first / No). The user's approval is bound to the
   commit sha.
   - **Approve**: run the card's one command, `hd contribute <slug> --approved <sha>`, and report what it printed
     (push, PR, CI, comment, ready, review). It waits for upstream CI itself, resumes at the first unobserved step when
     re-run, and stops before the comment when CI is not green; run it again for the same sha without a new ask, never
     for another commit.
   - **Fix first**: `hd hold <slug> failed "<what the user wants fixed, with the findings>"`; the next tick books a dev
     with the findings, and the new commit gets a new QA record and a new card.
   - **No**, or silence: nothing is recorded; the card stays in the list. `hd fail <slug> "why"` parks the change.
   - A `draft-pr` card (a maintainer finding is open on a ready PR): moving the PR to draft is the user's call each
     time; run its command only after a yes.
   - A release without a tag (`choose-tag`): ask the user for the version, then `hd release-request vX.Y.Z`.
6. **Needs you** (a change on a `decision` hold: a question from an agent, or the no-loop hold when a run would repeat
   exactly what was already booked): ask the user the question with AskUserQuestion, then
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
