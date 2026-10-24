---
slug: problem-doc
track: harness
title: 'docs/PROBLEM.md: the minimal source of truth for the problem, constraints, assumptions, business logic and workflow'
prio: P0
role: harness-dev
stage: live
hold: null
deps: []
branch: main
commit: 1cac8c8ddc1cbfdd8ce80602ba1e51b15a55234a
local_only: false
owner: null
evidence: /home/alex/osrs-harness/docs
summary: docs/PROBLEM.md added, PRD.md removed, iteration protocol in CLAUDE.md and harness-dev role; merged into main.
live_commit: 1cac8c8ddc1cbfdd8ce80602ba1e51b15a55234a
cost:
  runs: 1
  turns: 0
  tokens: 0
  minutes: 0
created: '2026-10-24T23:16:06Z'
updated: '2026-10-24T23:21:28Z'
---
## Change
docs/PROBLEM.md: the minimal source of truth for the problem, constraints, assumptions, business logic and workflow

## Definition of done
- [x] docs/PROBLEM.md exists: problem definition, constraints, assumptions, business logic (the rules that still hold, numbered), and the workflow/process of the three tracks and the PR/change model, all stated as current truth only; minimal; no justification of changes, no history, no incident stories (those stay in docs/ISSUES.md)
- [x] docs/PRD.md rules that still hold are folded into PROBLEM.md and PRD.md is removed (one home per fact); every kept rule carries a stable id so code and tests can reference it
- [x] docs/ARCHITECTURE.md describes only how the system implements PROBLEM.md (components, data, lifecycle mechanism); no rule is stated in both; CLAUDE.md layout list and read-first line name PROBLEM.md, ARCHITECTURE.md, HANDOFF.md, ISSUES.md
- [x] Iteration protocol in CLAUDE.md and the harness-dev role file: every iteration starts by reading PROBLEM.md and ends by updating it; code, tests, policy keys and docs not traceable to a PROBLEM.md rule are pruned as dead logic in the same iteration (list what was pruned in the hand-over, not in the docs)
- [x] Tests per rule touched (the PRD rule ids referenced in tests keep working or are renamed), full suite passes; no push, no daemon restart

## Log
- 2026-10-24T23:16:06Z created (ready)
- 2026-10-24T23:16:06Z USER 2026-10-24: one more doc: PROBLEM. Like ARCHITECTURE it is the most concise source of truth. It contains our knowns of the PROBLEM DEFINITION, CONSTRAINTS, ASSUMPTIONS, business logic and the description of the workflow/process. It is used BETWEEN ITERATIONS so we can prune any dead logic. Minimal, without justification of changes. Sources: docs/PRD.md (BR rules), docs/ARCHITECTURE.md, docs/ISSUES.md (what not to repeat; not copied in), CLAUDE.md, the memory rules in /home/alex/.claude/projects/-home-alex-osrs-harness/memory/ (the user's rules: fork actions free, upstream actions need the user's OK, gate before upstream, PR = bucket of maintainer interaction, change = atomic action, server priority = unblock client dev, no time-based mechanisms, harness contained in this repo, docs concise current truth), and the v6-orchestration and gate-before-upstream change logs (target state: write PROBLEM.md for the TARGET process, mark nothing as 'planned'; ARCHITECTURE.md says what is built).
- 2026-10-24T23:16:06Z ready -> dev: dispatched to hd17
- 2026-10-24T23:16:06Z run hd17 started (harness-dev, stage dev)
- 2026-10-24T23:16:46Z USER 2026-10-24 constraint to include in PROBLEM.md: up to two agents run their own RuneLite clients concurrently (own ports and accounts); no instance locks; further client-running agents wait for a free slot.
- 2026-10-24T23:18:03Z USER DECISIONS 2026-10-24 (take all recommendations): (1) no-loop predicate: a dev is booked only if the head SHA or the finding set differs from the last booked run, else a durable decision hold in 'needs you'; a maintainer finding is filed once keyed by comment/review id. (2) approval bound to the commit SHA, checked by the hook; publish_gate/github_scope rewritten for the local QA record; a resumed sequence continues only the exact approved commit. (3) PR done = ready with no open items; merge observed afterward; change = unit of work, PR = bucket. (4) 'settle open PRs first' outranks blocker-derived priority; capacity classes build, client (2), image. (5) delete every *_minutes/*_seconds knob; failure only on facts that mean a result cannot arrive; away mode event-driven (notification), built last. (6) moving a PR to draft on a maintainer finding: ask each time.
- 2026-10-24T23:18:50Z dod ticked: 1, 2, 3, 4, 5
- 2026-10-24T23:19:06Z run hd17 ended: ? turns, ? tokens, exit ok
- 2026-10-24T23:19:17Z dev -> ready: run hd17 ended without a hand-over
- 2026-10-24T23:19:27Z ready -> dev: hand-over recorded
- 2026-10-24T23:19:27Z handover main@1cac8c8dd: docs/PROBLEM.md added, PRD.md removed, iteration protocol in CLAUDE.md and harness-dev role; merged into main.
- 2026-10-24T23:20:23Z dev -> checked: hand-over check PASS
- 2026-10-24T23:20:23Z ship: already on main
- 2026-10-24T23:21:28Z checked -> live: observed
