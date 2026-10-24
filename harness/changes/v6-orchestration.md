---
slug: v6-orchestration
track: harness
title: 'v6: one pipeline, three track profiles; the console driver renders one ''needs you'' list'
prio: P1
role: harness-dev
stage: ready
hold:
  kind: decision
  reason: 'queued: starts after gate-before-upstream and drop-instance-locks merge; unhold then'
  since: '2026-10-24T22:59:05Z'
deps: []
branch: null
commit: null
local_only: false
owner: null
created: '2026-10-24T22:59:05Z'
updated: '2026-10-24T23:18:03Z'
---
## Change
v6: one pipeline, three track profiles; the console driver renders one 'needs you' list

## Definition of done
- [ ] One change lifecycle shared by client, server and harness (ready, dev, gate, done); a track profile defines only what the gate checks and what done means (server: gate, the user's approval, the atomic contribution, test-server deploy independent; client: gate then release; harness: build, merge, major builds gated at deployment by the user); stages and holds simplified accordingly
- [ ] Cross-track orchestration: deps and filed blockers between changes of any track; one priority order and global policies as data (e.g. settle open PRs first); one shared machine capacity budget for builds and in-game clients instead of per-track slot counts
- [ ] Durable manual holds: a hold the reconciler never clears (decision) separate from dependency holds; a failing check or gate never re-dispatches a dev run on its own without new facts (no loops)
- [ ] hd drive renders a single 'needs you' card list with fixed fields (what, branch and commit, net diff, QA verdict, risk, recommendation, exact command) and a stable --json; the drive skill carries an intent table mapping chat phrases to hd commands (status, approve, hold, unhold, dispatch, reprioritise)
- [ ] Run bookkeeping is automatic: a SubagentStop hook calls hd run-end and a spawn helper links runs; stop requests are handled without manual run-stopped; away mode via a loop wake-up and a push notification when the user is needed
- [ ] Builds on gate-before-upstream and drop-instance-locks (merged first); tests per rule, docs concise current truth, incidents in docs/ISSUES.md; no push; deployment (merge into main and daemon restart) gated by the user

## Log
- 2026-10-24T22:59:05Z created (ready)
- 2026-10-24T22:59:05Z USER 2026-10-24: queue v6-orchestration. Principle: rebuilds are cheap, prefer core redesign; no approval before building; the user gates the deployment. Start after gate-before-upstream and drop-instance-locks are merged (conflict risk). Design source: console proposal (one pipeline with three profiles; daemon observes and decides and acts on harness/git/deploy; console only spawns agents, asks the user, runs the approved atomic contribution; generated approval cards).
- 2026-10-24T22:59:05Z hold decision: queued: starts after gate-before-upstream and drop-instance-locks merge; unhold then
- 2026-10-24T23:06:11Z USER 2026-10-24 MODEL: the unit of upstream contribution is the PR: one branch, many commits, a review thread, a draft/ready status and open maintainer items. Loop until merged: observe GitHub (reviews, comments, CI, draft) -> a maintainer finding books a dev -> new commit -> QA gate on the PR head -> user approves the commit -> atomic contribution (push, green CI, comment, request review). Several changes may feed one PR. Server dev's priority is unblocking client dev: a server PR's priority = the highest priority of the client changes blocked on it (hd block --by); a client blocker with no server change yet becomes one; two independent outputs per server PR: (a) deploy to the test server for client dev (integration train, no upstream gate) and (b) the gated upstream contribution (parallel, does not hold up the client). Server dev's own check targets the client's described need first, then upstream polish. Design these into v6 (the PR model, observed review events, cross-track priority).
- 2026-10-24T23:11:23Z USER 2026-10-24 REFINEMENT of the PR model: the PR is the BUCKET of interaction with the maintainers (thread, draft/ready flag, head SHA, the list of its changes); a CHANGE is the atomic action between us and the maintainers and stays the unit of work and of approval (PRD 'a change is the only unit of work' holds). Example: we open a PR for 'feat: quest'; the maintainer reports a bug; the PR goes to draft; a NEW change (kind review-fix, carrying the finding text and the comment id) is filed on that PR; it goes through the full change process again (dev, QA gate, the user's approval, atomic contribution: push, green CI, comment, ready, review). Design: a PR record (observed from GitHub) with one-to-many changes, not many-to-one; a maintainer finding is filed as a change ONCE, keyed by its comment/review id (no re-booking loops); QA and approval bind to a change's commit; the PR flips draft/ready only through the atomic contribution (and to draft when a finding arrives). Supersedes the earlier 'PR as the unit' wording.
- 2026-10-24T23:16:46Z USER 2026-10-24: up to TWO agents run their own RuneLite clients at once (own ports/accounts), never blocking on a lock. Capacity class client: 2 in the shared machine budget (v6: named classes build, client, image). Dispatch waits for a free slot, not a lock.
- 2026-10-24T23:18:03Z USER DECISIONS 2026-10-24 (take all recommendations): (1) no-loop predicate: a dev is booked only if the head SHA or the finding set differs from the last booked run, else a durable decision hold in 'needs you'; a maintainer finding is filed once keyed by comment/review id. (2) approval bound to the commit SHA, checked by the hook; publish_gate/github_scope rewritten for the local QA record; a resumed sequence continues only the exact approved commit. (3) PR done = ready with no open items; merge observed afterward; change = unit of work, PR = bucket. (4) 'settle open PRs first' outranks blocker-derived priority; capacity classes build, client (2), image. (5) delete every *_minutes/*_seconds knob; failure only on facts that mean a result cannot arrive; away mode event-driven (notification), built last. (6) moving a PR to draft on a maintainer finding: ask each time.
