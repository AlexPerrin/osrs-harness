---
slug: goblin-diplomacy-review-367
track: server
title: 'Goblin Diplomacy #367: atomic armour hand-in'
prio: P0
role: server-dev
stage: ready
hold: null
deps: []
branch: content/goblin-diplomacy
commit: null
local_only: false
owner: null
instances: []
network: true
created: '2026-10-24T19:31:52Z'
updated: '2026-10-24T19:31:52Z'
---
## Change
Upstream #367 review P2 (eaglepurerocketgrape 2026-10-22 11:42). Head content/goblin-diplomacy d77ac2b76, mergeable. Replaces the open work in `goblin-diplomacy-unstacked` for #367.

## Definition of done
- [ ] handIn (GoblinDiplomacy.kt ~513-525): consuming the armour and committing quest progress/reward cannot be split by dialogue cancellation (orange, blue, brown), as #366 does for wool; completion failure does not lose the armour
- [ ] test: walk away on each dialogue page of the hand-in keeps the armour or the progress, never one without the other
- [ ] fork CI green; pushed onto the #367 head content/goblin-diplomacy after the user's OK

## Log
- 2026-10-24T19:31:52Z created (ready)
