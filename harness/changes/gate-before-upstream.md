---
slug: gate-before-upstream
track: harness
title: 'Redesign the server lifecycle: dev -> gate -> upstream action; the gate runs before any upstream push, on the exact local commit'
prio: P1
role: harness-dev
stage: dev
hold: null
deps: []
branch: null
commit: null
local_only: false
owner: hd18
created: '2026-10-24T22:49:07Z'
updated: '2026-10-24T23:18:43Z'
---
## Change
Redesign the server lifecycle: dev -> gate -> upstream action; the gate runs before any upstream push, on the exact local commit

## Definition of done
- [ ] The gate (server-qa) runs on a handed-over commit before the upstream action (open-pr, update-pr, ready-pr, comment). It reads the commit from the dev's clone (hand-over --repo), merged with current upstream main in a scratch clone; no push is needed for a gate
- [ ] A review fix on an open PR is a first-class flow: dev -> gate -> user's OK in chat -> push to the PR head (fast-forward, or a merge commit when the branch was rebuilt; never a force-push) -> comment -> ready -> request review
- [ ] The test-server train and 'live' are independent of the upstream flow (deploy for client work does not gate upstream, and the upstream gate does not wait for live); stages and holds simplified accordingly, lingering rules for gate runs follow the new stage
- [ ] The gate record is a local file in the evidence dir, written by the gate; the fork docs branch is not required; CI evidence is the upstream PR check after the push, or the fork run where the branch is current with main
- [ ] Tests per rule touched, full suite passes; docs state current truth only (ARCHITECTURE.md lifecycle diagram updated); incidents in docs/ISSUES.md; no push, no daemon restart

## Log
- 2026-10-24T22:49:07Z created (ready)
- 2026-10-24T22:49:07Z USER 2026-10-24: the gate runs before we make the upstream contribution, not after. Rebuilds are cheap: redesign the server lifecycle (hd/stages.py, tick, check, agents lingering rules, actions) instead of patching. No approval before building; the console gates the deployment (merge into main and daemon restart) with the user. Start after drop-instance-locks (hd14) and the docs trim (hd13) merge, to avoid conflicts.
- 2026-10-24T22:52:19Z USER 2026-10-24 workflow: the QA agent does ALL checks (accuracy, CI on the fork on a scratch branch merged with current upstream main, scope, PR text, no test files, in game on its own client) on the exact commit. Drop the checked stage; hd handover refuses incomplete hand-overs (ticked DoD, evidence, branch at commit) and the gate is the only verifier. After PASS the commit may be pushed to the upstream PR head (fast-forward, or merge commit when rebuilt; never force) with the PR still draft, no ask needed. Only comment, move out of draft and request review wait for the user's OK in chat.
- 2026-10-24T22:53:41Z USER 2026-10-24 CORRECTION to the entry above: after the gate PASS the user still approves the commit in chat; a push onto a branch backing an upstream PR is an upstream action and needs that OK. Fork actions (scratch/gate branches, docs, fork PRs, fork CI) need no approval. Gate scratch branches and fork CI are part of the gate.
- 2026-10-24T22:57:07Z USER 2026-10-24 (final workflow): dev = local fork commit; QA gate = all checks on the exact commit (accuracy, CI on a fork scratch branch merged with main, scope, PR text, in game); the user approves the commit in chat; then ONE atomic upstream sequence, no further asks: push to the upstream PR branch, wait for upstream CI green at that commit (observed), comment, move out of draft, request review. Build it as a single console-run command/procedure (hd contribute <slug>): preconditions = gate PASS at the commit + the user's approval recorded in the chat turn (not a stored approval); steps are observed facts; if CI does not go green it stops before the comment and reports (the PR stays draft); idempotent re-run resumes at the first unobserved step. Replaces the per-action open-pr/update-pr/ready-pr/comment items in hd actions.
- 2026-10-24T22:57:43Z LESSON 2026-10-24: gates failed serially (goblin: head regression, then style comments) because QA stopped at the first failure. The gate agent collects EVERY finding (source review, scope, AGENTS.md/CONTRIBUTING rules incl. comments, CI on the scratch branch, in game) and reports them together; a dev self-checks the diff against upstream AGENTS.md and CONTRIBUTING before hand-over.
- 2026-10-24T22:58:59Z ready -> dev: dispatched to hd15
- 2026-10-24T22:58:59Z run hd15 started (harness-dev, stage dev, instances none)
- 2026-10-24T22:59:15Z hold decision: starts after drop-instance-locks is merged (both rewrite the core; avoid conflicts); unhold then
- 2026-10-24T22:59:55Z dev -> ready: run hd15 ended without a hand-over
- 2026-10-24T23:00:14Z hold decision cleared: drop-instance-locks merged; feature, autonomous
- 2026-10-24T23:02:21Z ISSUE 2026-10-24: the role hook denies agents every push ('Only the orchestrator does pushes'), including a fork scratch branch for the gate's CI; the console pushed it. Design: the gate's scratch branch push and CI dispatch are fork actions (no approval); let server-qa push only gate/* branches (hook allow-list) or give hd a 'hd gate-ci <slug>' command the daemon/console runs (scratch merge, push, dispatch, wait, observe). Also: the daemon heals gate runs on non-live changes as lingering (stop requests) until the lifecycle moves the gate before upstream.
- 2026-10-24T23:16:06Z ready -> dev: dispatched to hd18
- 2026-10-24T23:16:06Z run hd18 started (harness-dev, stage dev)
- 2026-10-24T23:18:03Z USER DECISIONS 2026-10-24 (take all recommendations): (1) no-loop predicate: a dev is booked only if the head SHA or the finding set differs from the last booked run, else a durable decision hold in 'needs you'; a maintainer finding is filed once keyed by comment/review id. (2) approval bound to the commit SHA, checked by the hook; publish_gate/github_scope rewritten for the local QA record; a resumed sequence continues only the exact approved commit. (3) PR done = ready with no open items; merge observed afterward; change = unit of work, PR = bucket. (4) 'settle open PRs first' outranks blocker-derived priority; capacity classes build, client (2), image. (5) delete every *_minutes/*_seconds knob; failure only on facts that mean a result cannot arrive; away mode event-driven (notification), built last. (6) moving a PR to draft on a maintainer finding: ask each time.
- 2026-10-24T23:18:43Z LESSON 2026-10-24: sq48 called an import move 'stray' that spotless requires (sorted imports, ratchet on touched files); the gate must RUN spotlessCheck on every touched module and judge hunks by the formatter, not by eye. A dev runs spotlessCheck before hand-over. QA could not push gate/<slug> (hook): the console pushes scratch branches until the hook allow-list or hd gate-ci exists.
