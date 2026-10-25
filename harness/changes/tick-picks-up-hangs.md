---
slug: tick-picks-up-hangs
track: harness
title: 'The tick picks up hangs: stop qa-dev containers of ended runs; a finished agent that is still running appears as a stop item until stopped'
prio: P0
role: harness-dev
stage: dev
hold: null
deps: []
branch: null
commit: null
local_only: false
owner: hd26
booked:
  dev: '|da39a3ee5e6b'
created: '2026-10-25T02:11:48Z'
updated: '2026-10-25T02:11:48Z'
---
## Change
The tick picks up hangs: stop qa-dev containers of ended runs; a finished agent that is still running appears as a stop item until stopped

## Definition of done
- [ ] heal stops (docker stop) a running qa-dev-<name> container when the run <name> has ended, has no run record, or its change left the stage it served (facts from the run records), and never touches a container whose run is alive; tested with a fake docker
- [ ] When a run ends (hd run-end, or the daemon stops it) and it has a linked agent id, hd drive lists that agent under Stop until hd run-stopped clears it, so a finished agent still running background work is never left unstopped; entries clear when the console records the stop; tested
- [ ] No timers or elapsed-time checks; PRD healing requirement states the two rules in one line each (BR-H*), ARCHITECTURE heal row updated, one dated entry in docs/ISSUES.md; full suite passes; no push, no daemon restart

## Log
- 2026-10-25T02:11:48Z created (ready)
- 2026-10-25T02:11:48Z USER 2026-10-24: sq59 stayed live 1h11m after its run ended (an agent waiting on its own background work; the harness tracks run records, not agent liveness) and qa-dev-sd42 sat 5h. 'Tick should pick up the hang.' Facts to use: runs/<name>.json (ended, agent_id, change, stage), docker ps names qa-dev-<name>. hd/heal.py _containers handles only qa-or-* and hd-boot-*. Keep it minimal and fact-based; the stop hook (SubagentStop -> run-end) is v6 part B, not this change. Work in a worktree: git reset --hard main first. Docs: three source docs (PROBLEM/PRD/ARCHITECTURE), minimal, no history.
- 2026-10-25T02:11:48Z ready -> dev: dispatched to hd26
- 2026-10-25T02:11:48Z run hd26 started (harness-dev, stage dev)
