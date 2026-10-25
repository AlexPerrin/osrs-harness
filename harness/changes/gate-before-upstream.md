---
slug: gate-before-upstream
track: harness
title: 'Redesign the server lifecycle: dev -> gate -> upstream action; the gate runs before any upstream push, on the exact local commit'
prio: P1
role: harness-dev
stage: live
hold: null
deps: []
branch: main
commit: 23f4fe4378c191df94b05e8589e7b09c57e6ed0a
local_only: false
owner: null
evidence: /home/alex/osrs-harness/docs
summary: 'Merged into main (23f4fe4) and deployed: server lifecycle dev -> QA aggregate -> approval card -> hd contribute; the server track isolated in hd/tracks/server/; 235 tests pass.'
live_commit: 23f4fe4378c191df94b05e8589e7b09c57e6ed0a
cost:
  runs: 1
  turns: 0
  tokens: 0
  minutes: 0
created: '2026-10-24T22:49:07Z'
updated: '2026-10-25T00:05:47Z'
---
## Change
Redesign the server lifecycle: dev -> gate -> upstream action; the gate runs before any upstream push, on the exact local commit

## Definition of done
- [x] The gate (server-qa) runs on a handed-over commit before the upstream action (open-pr, update-pr, ready-pr, comment). It reads the commit from the dev's clone (hand-over --repo), merged with current upstream main in a scratch clone; no push is needed for a gate
- [x] A review fix on an open PR is a first-class flow: dev -> gate -> user's OK in chat -> push to the PR head (fast-forward, or a merge commit when the branch was rebuilt; never a force-push) -> comment -> ready -> request review
- [x] The test-server train and 'live' are independent of the upstream flow (deploy for client work does not gate upstream, and the upstream gate does not wait for live); stages and holds simplified accordingly, lingering rules for gate runs follow the new stage
- [x] The gate record is a local file in the evidence dir, written by the gate; the fork docs branch is not required; CI evidence is the upstream PR check after the push, or the fork run where the branch is current with main
- [x] Tests per rule touched, full suite passes; docs state current truth only (ARCHITECTURE.md lifecycle diagram updated); incidents in docs/ISSUES.md; no push, no daemon restart

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
- 2026-10-24T23:29:09Z USER 2026-10-24 CLARIFICATION: we only need to gate on the APPROVAL to make a change action upstream. QA AGGREGATES the checks that occur for the approval: it runs them (accuracy, CI and Formatting on the scratch merge with upstream main, scope, style, in game where relevant) and the results go on the approval card (PASS/FAIL per check, all findings, evidence links). A QA finding does not itself block, fail a hold or re-dispatch a dev; the user decides on the card, and a dev fix is filed when the user wants one. So: no gate stage that returns a change to ready; the lifecycle is dev -> (QA aggregates) -> approval card -> the user's decision -> atomic contribution. hd gate records the aggregate, it is not a stage precondition.
- 2026-10-24T23:35:15Z USER 2026-10-24 CI RULE: if our fork's CI (a copy of upstream's: ci.yml and Formatting on a scratch branch merged with current upstream main) is not green, the change is not ready for upstream and does not enter the approval queue. After the push we are waiting for upstream CI knowing it will go green; its green triggers the final actions (comment, move out of draft, request review). Fork CI green is a precondition of the approval card (QA aggregate shows it first).
- 2026-10-24T23:36:55Z USER 2026-10-24 CI EQUIVALENCE: identify which fork check is equivalent to which upstream check, to avoid double runs or blocking; it tells the gate where each check occurs. Data table in harness/policy.yaml (ci_equivalence: fork workflow -> upstream check name): CI (ci.yml) -> 'build & boot'; Formatting -> 'spotless (advisory)'; Gameval Conflict Check -> 'gameval-conflicts' (verify the names against a real PR's statusCheckRollup). The QA aggregate runs each check ONCE, at the fork on the scratch branch merged with current upstream main; a green fork check satisfies its upstream twin; after the push, hd contribute only confirms the upstream twins (observed), never re-runs them and never blocks on a check without a twin (advisory checks do not block). Fork red = not ready for upstream. Document the table in PROBLEM.md (constraint) and ARCHITECTURE.md (mechanism).
- 2026-10-24T23:39:15Z USER 2026-10-24 ARCHITECTURE: the harness only ORCHESTRATES between the three tracks (client, server, harness): changes, deps/blockers, priority, capacity, dispatch, holds, run bookkeeping, the console driver. The upstream contribution workflow (PR bucket, GitHub observer, CI equivalence, QA aggregate, approval card, hd contribute, maintainer-finding filer, scratch-branch gate CI, publish_gate/github_scope logic) is ISOLATED in the server dev track as a module behind a narrow track interface (derive stage, what a change still needs, the track's needs-you items). The core imports no GitHub/CI/PR code. Client track owns the release flow, harness track owns the merge into main, same interface; per-track settings under each track's policy section.
- 2026-10-24T23:54:03Z dod ticked: 1, 2, 3, 4, 5
- 2026-10-25T00:00:47Z run hd18 ended: ? turns, ? tokens, exit ok
- 2026-10-25T00:01:08Z dev -> ready: run hd18 ended without a hand-over
- 2026-10-25T00:04:42Z ready -> gate: hand-over recorded
- 2026-10-25T00:04:42Z handover main@23f4fe437: Merged into main (23f4fe4) and deployed: server lifecycle dev -> QA aggregate -> approval card -> hd contribute; the server track isolated in hd/tracks/server/; 235 tests pass.
- 2026-10-25T00:05:47Z gate -> live: observed
