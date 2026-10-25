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
owner: hd32
booked:
  dev: '|da39a3ee5e6b'
cost:
  runs: 1
  turns: 0
  tokens: 0
  minutes: 0
created: '2026-10-25T01:16:56Z'
updated: '2026-10-25T04:05:33Z'
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
- 2026-10-25T01:30:00Z USER 2026-10-24: NO QUICK FIXES NOW. Defects seen during the cutover period go on the v7 list instead of being patched; collect these into the v7 section of docs/HANDOFF.md and as dated entries in docs/ISSUES.md (one line each, where to look): (a) hd contribute/hd gate evidence dir is the change's own name (fix-stile-approach), not the slug; (b) the batch lists cannon-review-354 twice in includes; (c) imaging failure restarts on the old clone (resume rebuilds only for a gating failure); (d) fork-only changes (check-cache-stock-limit) get a QA run booked though they have no upstream PR (no local-only close); (e) a hand-contributed change must be re-handed over on the PR head branch name to reach review, and its DoD items about the contribution step must be ticked before hand-over; (f) stale stop requests in hd drive for finished runs (run-stopped by hand); (g) hd gate-ci does not dispatch the Formatting workflow; (h) a QA agent cannot push gate/<slug> reliably under the role hook (the console pushed scratch branches); (i) the local clone 'origin' is the shared local clone, not upstream (scratch merges merged the wrong main once); (j) qa.sh full-gate mode and the shared cs2 volume going stale (fork tools); (k) review request via API is impossible for the fork author (404); (l) client class capacity also counts QA desktop clients, so client-dev cannot be held separately; (m) doc of the harness in the fork tooling branch not versioned with pins.
- 2026-10-25T02:01:29Z USER 2026-10-24: the docs are now THREE sources of truth (PROBLEM, PRD, ARCHITECTURE; change three-source-docs restructures them): the docs audit and the HANDOFF must follow that structure; run handoff-v6 AFTER three-source-docs merges.
- 2026-10-25T02:03:01Z USER 2026-10-24 ADDENDUM for the v7 brief: v7 (a major revision) is judged by reducing to the LEAST COMPLEX, MOST EFFICIENT solution that meets docs/PRD.md: fewer concepts, steps, special cases, files and knobs; iterate quickly; the docs hold only the source of truth, no revision history or justification. State this at the top of the v7 section.
- 2026-10-25T03:10:22Z hold decision: runs last, after v6 part B and the cutover work settle (the brief describes the final state); unhold then
- 2026-10-25T03:10:22Z run hd21 ended: ? turns, ? tokens, exit ok
- 2026-10-25T03:10:43Z dev -> ready: run hd21 ended without a hand-over
- 2026-10-25T04:05:13Z hold decision cleared: user 2026-10-25: wrap up, shut down, hand off to v7; part B is folded into the v7 brief
- 2026-10-25T04:05:33Z ready -> dev: dispatched to hd32
- 2026-10-25T04:05:33Z run hd32 started (harness-dev, stage dev)
