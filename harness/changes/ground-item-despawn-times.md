---
slug: ground-item-despawn-times
track: server
kind: change
title: Ground item despawn times (OSRS Drop rules)
priority: P2
deps:
- cannon-review-354
- genie-review-355
- goblin-diplomacy-review-367
- witchs-potion-review-368
created: '2026-10-20T01:42:40Z'
branch: fix/ground-item-despawn-times
---
## Change
Every player drop currently despawns after 200 ticks (constants.lootdrop_duration). Match OSRS Wiki 'Drop': tradeables become public after 60 s and despawn after a further 120 s (300 ticks total); untradeables 180 s; clue scrolls 61 min. Repro: ::item 10180 1, drop, gone 115 s later. Unblocks client: Clue Juggling Timers, Ground Items despawn (gen 44, scratchpad/g44/).

Ground items: keep the owner when an obj is copied (ObjRegistry.singleCopy, ZoneUpdateTransformer.copy)

## Definition of done
- [x] Drop of a tradeable on the test server becomes public after 100 ticks and despawns after 300 ticks
- [x] Drop of an untradeable despawns after 300 ticks (180 s); a dropped clue scroll stays 61 min
- [x] Unblocks client task hub-ground-items-despawn (the client dev verifies it there after the deploy)
- [x] accuracy/ground-item-despawn-times.md on the fork's docs branch (wiki/cache baseline per rule, RSProx comparison recorded)
- [x] fork PR open with green CI at the handed-over commit
- [x] one change only, branch off upstream main (no stacking)
- [x] on fix/ground-item-despawn-times (same branch as fork PR #23, a new commit, no new branch): pass ownerId as the 5th Obj(...) argument in ObjRegistry.singleCopy and ZoneUpdateTransformer.copy; a unit test; fork CI green
- [x] sd28's spec (accuracy/ground-item-despawn-times.md) no longer lists the copy-owner bug as open
