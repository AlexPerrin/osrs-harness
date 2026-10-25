---
slug: handoff-v6
track: harness
title: docs/HANDOFF.md rewritten as the brief for a fresh console session (current state, how to run, open work, standing rules)
prio: P1
role: harness-dev
stage: dev
hold: null
deps: []
branch: null
commit: null
local_only: false
owner: hd21
booked:
  dev: '|da39a3ee5e6b'
created: '2026-10-25T01:16:56Z'
updated: '2026-10-25T01:20:11Z'
---
## Change
docs/HANDOFF.md rewritten as the brief for a fresh console session (current state, how to run, open work, standing rules)

## Definition of done
- [ ] docs/HANDOFF.md is the only thing a fresh console session needs after CLAUDE.md: what is live (harness v6 part A), what is held and why, how to run (daemon, hd drive, the drive skill loop), the approval rules (fork free, upstream needs the user's OK per change, one atomic hd contribute), the PR/change model, the track repos, and the open work in the user's order; current truth only, no justification or history, no hand-kept counts that go stale (point at commands)
- [ ] A short 'start prompt' section (3-6 lines) the console launcher passes to the new session; the user's standing rules are listed by pointing at the memory directory files by name
- [ ] Facts verified against hd status, hd drive and the repo before writing; full suite passes; no push, no daemon restart

## Log
- 2026-10-25T01:16:56Z created (ready)
- 2026-10-25T01:16:56Z USER 2026-10-24: cutover to v6 when our work is done: bring osrs-harness up to local (origin/main = local main; the user merges draft PR #1 / progress branch), and start a fresh console session (the console starts it with claude --bg in ~/osrs-harness once nothing is in flight). This change prepares the brief. Write from the actual state at the time (run hd status, hd drive, hd batches, gh pr list for the OpenRune PRs #354 #367 #406 #407 #355 #368, git log). Memory files with the user's rules: /home/alex/.claude/projects/-home-alex-osrs-harness/memory/*.md (list them in the doc by name, do not copy their content). Docs rule: concise current truth, no revision justification, no incident stories (those live in docs/ISSUES.md).
- 2026-10-25T01:16:56Z ready -> dev: dispatched to hd21
- 2026-10-25T01:16:56Z run hd21 started (harness-dev, stage dev)
- 2026-10-25T01:20:11Z USER 2026-10-24 (scope addition): the cutover of v6 leads straight into a MAJOR REVISION v7 in the fresh console session. On exit the system docs and the handoff must all be documented: (1) AUDIT docs/PROBLEM.md, docs/ARCHITECTURE.md and docs/ISSUES.md against the deployed code (read hd/, hd/tracks/, policy.yaml, hooks/, train/, tests names) and fix every statement that is not true of the code; remove dead rules; BR ids referenced by code or tests must exist; docs stay concise current truth, no justification; (2) docs/HANDOFF.md = the fresh console's brief AND the v7 starting brief: a 'v7' section with what v7 should address, drawn from: v6 part B leftovers (driver cards plan/queue lists, automatic run bookkeeping, track repos with pinned modules, harness-self-contained, local-only changes closing, evidence dir naming read by hd gate), the open items in docs/ISSUES.md and the change logs under harness/changes (grep 'v7', 'v5 candidate', 'next iteration', 'left for part B'), timed knobs left in observe/heal/metrics (subprocess timeouts, HD_POLL_SECONDS, stall_minutes), imaging failure restarting on the old clone, qa.sh idle stop in the fork tools, the stale shared cs2 volume, the hd drive stale-stop requests, review step in contribute.py (no reviewers), the cross-repo module update path; each item one line with where to look, no justification. The v7 section is a brief, not a design. Rules for v7 are the user's: rebuild over patch, major revision deployment gated by the user, docs concise.
