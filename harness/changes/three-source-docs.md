---
slug: three-source-docs
track: harness
title: 'Docs: PROBLEM, PRD and ARCHITECTURE as the three minimal sources of truth'
prio: P0
role: harness-dev
stage: dev
hold: null
deps: []
branch: null
commit: null
local_only: false
owner: hd25
booked:
  dev: '|da39a3ee5e6b'
created: '2026-10-25T02:01:29Z'
updated: '2026-10-25T02:03:01Z'
---
## Change
Docs: PROBLEM, PRD and ARCHITECTURE as the three minimal sources of truth

## Definition of done
- [ ] docs/PROBLEM.md is the problem definition only: the business context, the GOALS of each track (client, server, harness) and the process/workflow of each track in human language (including the PR as bucket, the change as the atomic action, the approval and review flow); no rule ids, no mechanism, no UML
- [ ] docs/PRD.md is restored as the requirements: the first principles the solution must meet, as the BR-* rules moved out of PROBLEM.md (same ids, current rules only, each testable and traceable to a goal), grouped by track and by cross-cutting concern; PROBLEM.md and ARCHITECTURE.md no longer carry the rules; code and tests that cite BR ids still resolve
- [ ] docs/ARCHITECTURE.md is the implementation that meets the PRD: components, data model, lifecycle, the core/track split, the train, hooks; UML (component, class/ER, state) and sequence diagrams for the main application flows (dispatch and hand-over, QA aggregate and contribution, train and deploy, drive loop), each diagram checked against the code; it names which PRD requirement each mechanism satisfies
- [ ] CLAUDE.md layout and iteration protocol: the three documents are the source of truth for each iteration; each iteration starts by reading them and ends by updating them; each iteration aims to reduce complexity, increase efficiency and streamline the implementation: anything in code, tests, policy or docs not traceable to a PRD requirement is pruned (listed in the hand-over only); the harness-dev role file says the same
- [ ] All three docs are concise current truth with no revision justification; incidents only in docs/ISSUES.md; full suite passes; no push, no daemon restart

## Log
- 2026-10-25T02:01:29Z created (ready)
- 2026-10-25T02:01:29Z USER 2026-10-24 (verbatim intent): the solution is tracked in PROBLEM, PRD and ARCHITECTURE, all minimal sources of truth. PROBLEM = all business context, the goals of each track, the process/workflow of each track in human language: the problem definition. PRD = the requirements, the first principles the solution must solve. ARCHITECTURE = the technical implementation that meets the requirements, with UML and sequence diagrams for the application. These are the source of truth each iteration builds on; each iteration tries to reduce complexity, increase efficiency and streamline the implementation. Current docs: docs/PROBLEM.md (has the BR rules folded in; split them back out into docs/PRD.md, restore the file from git history: git show 1cac8c8^:docs/PRD.md, then rewrite to current truth, do not copy stale text), docs/ARCHITECTURE.md (already has diagrams; verify each against the code, add the missing ones). Read the memory files in /home/alex/.claude/projects/-home-alex-osrs-harness/memory/ for the user's rules and keep every still-true rule. Do this in a worktree: git reset --hard main first.
- 2026-10-25T02:01:29Z ready -> dev: dispatched to hd25
- 2026-10-25T02:01:29Z run hd25 started (harness-dev, stage dev)
- 2026-10-25T02:03:01Z USER 2026-10-24 ADDENDUM: each iteration reduces our ad hoc work surface and process and iterates quickly; a major revision must reduce to the least complex, most efficient solution; the docs are minimal, only the source of truth, no revision history or justification.
