---
slug: witchs-potion-review-368
track: server
title: 'Witch''s Potion #368: net diff is Witch''s Potion only, mergeable'
prio: P0
role: server-dev
stage: ready
hold:
  kind: decision
  reason: 'work done: fork branch content/witchs-potion-368 at c407c2272f54 (fork PR https://github.com/AlexPerrin/OpenRune-Server/pull/32), docs commit pushed; blocked only on fork CI (workflow_dispatch
    422 ''Actions has been disabled for this repository''); no qa.sh available for local gate. Re-run handover with --branch content/witchs-potion-368 --commit c407c2272f54 --pr .../pull/32 once Actions
    is enabled. Push onto #368 head still needs user OK.'
  since: '2026-10-24T21:16:59Z'
deps: []
branch: content/witchs-potion
commit: null
local_only: false
owner: null
instances:
- desktop
network: true
cost:
  runs: 1
  turns: 0
  minutes: 0.0
  usd: 0
created: '2026-10-24T19:31:52Z'
updated: '2026-10-24T21:17:08Z'
---
## Change
Upstream #368 review P2 x2 (eaglepurerocketgrape 2026-10-22 11:42). Head content/witchs-potion 18afab0a7, CONFLICTING. The unstacked branch content/witchs-potion-unstacked 23e1b7c5d is a candidate base but is older than #366's merge.

## Definition of done
- [ ] merge current upstream main into content/witchs-potion (CONFLICTING now); drop the stale stacked SheepShearer.kt and RomeoAndJuliet.kt (Sheep Shearer is merged as #366, Romeo & Juliet is #299); net diff against main is Witch's Potion only
- [ ] no add/add conflicts or duplicate NPC op subscriptions; gameval ids renumbered against main (fix_gameval_conflicts.py)
- [ ] rat-tail drop gate works in the default assume-completed mode, or the PR text states why it cannot
- [ ] PR description no longer says it follows #366's f69c8ed4c
- [ ] fork CI green; pushed onto the #368 head after the user's OK; the review's merge simulation passes

## Log
- 2026-10-24T19:31:52Z created (ready)
- 2026-10-24T21:12:45Z ready -> dev: dispatched to sd43
- 2026-10-24T21:12:45Z run sd43 started (server-dev, stage dev, instances desktop)
- 2026-10-24T21:16:59Z branch fork content/witchs-potion-368 @ c407c2272 (one commit on main 5c4c9c106, Witch's Potion only, id 65447, rat tail via kill hook), fork PR #32, docs spec+PR text updated; fork CI cannot run (Actions disabled, 422)
- 2026-10-24T21:16:59Z hold decision: work done: fork branch content/witchs-potion-368 at c407c2272f54 (fork PR https://github.com/AlexPerrin/OpenRune-Server/pull/32), docs commit pushed; blocked only on fork CI (workflow_dispatch 422 'Actions has been disabled for this repository'); no qa.sh available for local gate. Re-run handover with --branch content/witchs-potion-368 --commit c407c2272f54 --pr .../pull/32 once Actions is enabled. Push onto #368 head still needs user OK.
- 2026-10-24T21:16:59Z dev -> ready: agent could not finish
- 2026-10-24T21:17:08Z run sd43 ended: ? turns, 0.0 min, $0, exit ok
