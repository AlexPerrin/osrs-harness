---
name: drive
description: "The console loop: run `hd`, spawn the agents it lists, show the cards and questions, record the user's yes or answer, repeat. Use in the console session whenever the user says to drive, continue or check the harness."
---
# Drive the harness (console session only)

The pass (`hd tick`, a systemd timer every minute and after every agent run) decides and acts; you spawn the agents and
relay the user. `hd` is `python3 ~/osrs-harness/hd.py`. Nothing depends on you staying alive: a vanished console only
pauses spawning.

## The loop
1. `hd` (or `hd --json`). It prints goals, `spawn` items, `card`s, `question`s, `alert`s, `running` and the open changes.
2. **spawn**: for each item call the Agent tool with `subagent_type` = the role and `prompt` = the contents of the
   brief file, in the background; add `isolation: "worktree"` when the item says `worktree`. The hook records the run
   from the brief's first line; nothing else to do. NEVER call EnterWorktree in the console: it moves this session's cwd
   and breaks the subagents' Bash.
3. **card**: show it to the user in full in chat (the change, head, verdict, texts, the exact command) and ask with
   AskUserQuestion (Approve this commit / Fix first / No). Approve: run the card's `hd approve <slug> <sha>`; the pass
   does the rest, one GitHub step per minute, and stops when CI is not green (the card says so). Fix first:
   `hd verdict <slug> <sha> FAIL "<the user's words>"`; the user's judgment replaces the reviewer's and the dev is
   spawned with it. No, or silence: nothing is recorded; the card stays.
4. **question**: ask the user with AskUserQuestion, then `hd answer <slug> "<their words>"`. The answer is appended to
   the definition and the dev is spawned again on the next `hd`.
5. **alert**: tell the user; only they can fix it (Docker, BlueStacks, `gh auth`).
6. Repeat with `/loop` or ScheduleWakeup; a few minutes between rounds is plenty.

## Rules
- Never run an upstream, release, train or deploy command from here; `hd approve` is the only thing you record for
  them, after the user's yes in this chat, bound to the commit sha the card shows.
- Keep this context small: delegate anything beyond a couple of quick commands to an agent.
- Times for the user are US Eastern.
