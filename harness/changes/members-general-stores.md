---
slug: members-general-stores
track: server
title: 'Members'' general stores: handlers verified from RSProx'
prio: P2
role: server-dev
stage: ready
hold:
  kind: decision
  reason: 'new feature dispatch held (user 2026-10-24): settle open PRs and harness fixes first; unhold when ready'
  since: '2026-10-24T22:48:22Z'
deps: []
branch: fix/members-general-stores
commit: null
local_only: false
owner: null
instances:
- desktop
cost:
  runs: 1
  turns: 0
  minutes: 0.0
  usd: 0
created: '2026-10-20T03:00:41Z'
updated: '2026-10-24T22:48:22Z'
---
## Change
Members' general stores: handlers verified from RSProx

## Definition of done
- [ ] transcribe the ~19 candidate RSProx recordings (keeper npc + interface 300) and confirm each keeper -> inv
- [ ] add a handler for every store a recording confirms; resolve Port Phasmatys (233 vs 235) and Quartermaster (159 vs 160) or leave them out
- [ ] unconfirmed stores listed as caveats or left out; league-only recordings marked
- [ ] one PR off upstream main, independent of #371 (no stacking)
- [ ] accuracy spec + green fork CI + Trade checked in game

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: members-general-stores
- 2026-10-22T01:56:35Z ready -> dev: dispatched to sd39
- 2026-10-22T01:56:35Z run sd39 started (server-dev, stage dev, instances desktop)
- 2026-10-22T02:16:31Z branch fix/<slug> (grooming)
- 2026-10-22T02:19:27Z spec committed: accuracy/members-general-stores.md (7 stores confirmed by RSProx: Razmire 3088, Void Knight 4012, Dorgesh-Kaan 3192/3189, Quartermaster 2972 (inv 160 live; 159 opened, same stock), Burthorpe 3248, Aurel 3060, Fossil Island 3035; 6 league-only, 15 unconfirmed incl. Port Phasmatys)
- 2026-10-24T19:32:22Z 2026-10-24 reset: upstream merged #375 (general stores buy any tradeable), #382 and #394 (11 shop invs from captures) since the pin; re-check this against main for overlap before more work
- 2026-10-24T20:08:33Z run sd39 ended: ? turns, 0.0 min, $0, exit cancelled
- 2026-10-24T20:09:15Z dev -> ready: run sd39 ended without a hand-over
- 2026-10-24T22:25:05Z ready -> dev: dispatched to sd67
- 2026-10-24T22:25:05Z run sd67 started (server-dev, stage dev, instances desktop)
- 2026-10-24T22:26:45Z hold blocked: new feature dispatch held (user): settle the open PRs first
- 2026-10-24T22:27:11Z hold blocked cleared: every dep is live
- 2026-10-24T22:27:11Z dev -> ready: run sd67 ended without a hand-over
- 2026-10-24T22:48:22Z hold decision: new feature dispatch held (user 2026-10-24): settle open PRs and harness fixes first; unhold when ready
