---
slug: witchs-potion-review-368
track: server
title: 'Witch''s Potion #368: net diff is Witch''s Potion only, mergeable'
prio: P0
role: server-dev
stage: ready
hold: null
deps: []
branch: content/witchs-potion
commit: null
local_only: false
owner: null
instances: []
network: true
created: '2026-10-24T19:31:52Z'
updated: '2026-10-24T19:31:52Z'
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
