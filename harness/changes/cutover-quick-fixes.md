---
slug: cutover-quick-fixes
track: harness
title: Quick fixes found during the cutover period, applied now (batch)
prio: P0
role: harness-dev
stage: dev
hold: null
deps: []
branch: null
commit: null
local_only: false
owner: hd23
booked:
  dev: '|da39a3ee5e6b'
created: '2026-10-25T01:30:56Z'
updated: '2026-10-25T01:30:56Z'
---
## Change
Quick fixes found during the cutover period, applied now (batch)

## Definition of done
- [ ] Evidence dir: hd gate, hd gate-ci and hd contribute read the change's evidence by one rule (the slug dir; the change's recorded evidence path is honoured and copied), so a record written by QA is always found
- [ ] Train batch includes list deduplicates entries (cannon-review-354 listed twice); an imaging or deploying failure after the tools branch moved rebuilds like a gating failure (extend the _tools_moved rule), tested
- [ ] Fork-only changes (branch under local/ or local_only) never get a QA run booked and close at live without a contribute stage
- [ ] A change is observed in review by its recorded upstream PR number (not by a branch-name match), so a hand-contributed change reaches review without re-handing over under another branch name; DoD items about the contribution step do not block hand-over (they are checked by hd contribute)
- [ ] hd gate-ci also dispatches the Formatting workflow named in policy ci_equivalence and waits for it, so the aggregate's format fact is observed; the review-request step and the tracks.server.reviewers key are removed from contribute (the API refuses the fork author)
- [ ] Capacity: a separate 'device' class (Android) for client-dev with capacity 0 until BlueStacks is up; desktop client runs stay in 'client' (2), so QA is no longer coupled to client-dev; the 22 decision holds on client changes can then be lifted by the user's word, not by this change
- [ ] hd drive: stop requests for runs whose agent already ended are cleared by the daemon when the run's change has left the stage and a hand-back was recorded (or hd run-end was called), so no manual run-stopped is needed; tests per rule; full suite passes; docs concise current truth (PROBLEM/ARCHITECTURE updated only where a rule changed), the entries added to docs/ISSUES.md; no push, no daemon restart

## Log
- 2026-10-25T01:30:56Z created (ready)
- 2026-10-25T01:30:56Z USER 2026-10-24: 'No dont defer. Apply quick fixes now.' Sources: the list (a)-(m) logged on handoff-v6 (read it); items NOT in this batch: (h) QA gate/* push works under the role hook now (verified by sq56, sq59), (i) clone remote naming and (j) qa.sh full-gate mode and the stale cs2 volume are fork tooling (server-dev change qa-sh-targeted), (m) unclear, (k) is a platform limit: remove the unused reviewer step (DoD 5) and note it in docs/ISSUES.md. Minimal changes, facts-based, no timers; if a fix is really a design change, do not do it: list it in your report with the reason.
- 2026-10-25T01:30:56Z ready -> dev: dispatched to hd23
- 2026-10-25T01:30:56Z run hd23 started (harness-dev, stage dev)
