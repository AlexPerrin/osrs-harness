---
slug: v6-driver-and-tracks
track: harness
title: 'v6 part B: driver automation, track modules in their own repos, harness contained, docs pass'
prio: P1
role: harness-dev
stage: ready
hold:
  kind: decision
  reason: part B starts after v6 part A merges (core conflicts)
  since: '2026-10-25T00:16:40Z'
deps: []
branch: null
commit: null
local_only: false
owner: null
created: '2026-10-25T00:16:40Z'
updated: '2026-10-25T00:16:40Z'
---
## Change
v6 part B: driver automation, track modules in their own repos, harness contained, docs pass

## Definition of done
- [ ] hd drive: separate PLAN (prioritised triage of upstream state and client blockers) and APPROVAL QUEUE (a new PR, or a change on a PR) lists; one card format with fixed fields; stable --json; an intent table in the drive skill (status, approve, hold, unhold, dispatch, reprioritise)
- [ ] Run bookkeeping automatic: a SubagentStop hook calls hd run-end (turns/tokens from the payload where available) and a spawn helper links runs; stale stop requests resolve themselves; no manual run-link/run-end/run-stopped
- [ ] Track modules live in their own repos behind the track interface, loaded via policy tracks.<track> pinned to a commit: the server track module (contribution workflow, CI equivalence, QA aggregate, integrator and train) in the fork on local/server-tools, the client track module (release flow) in the client repo (any client repo edit is proposed to the user first); the harness repo holds the core and the harness track
- [ ] harness-self-contained: evidence dirs live in this repo, every read/write outside it is a configured product boundary in policy, the client checkout is a target not a home
- [ ] docs pruned against PROBLEM.md: dead logic, tests, policy keys and docs not traceable to a rule are removed (listed in the hand-over only); the full suite passes; the user gates the deployment

## Log
- 2026-10-25T00:16:40Z created (ready)
- 2026-10-25T00:16:40Z hold decision: part B starts after v6 part A merges (core conflicts)
