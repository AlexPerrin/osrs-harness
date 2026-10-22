---
slug: ground-item-relogin-timers
track: server
title: 'Ground items: OBJ_ADD after re-login carries no despawn timer (0xFFFF) for the player''s own drops'
prio: P2
role: server-dev
stage: ready
hold: null
deps: []
branch: null
commit: null
local_only: false
owner: null
instances: []
created: '2026-10-22T00:51:11Z'
updated: '2026-10-22T02:08:34Z'
---
## Change
Repro on the test server (2026-10-21, client hub-ground-items-despawn, re/evidence/hub-ground-items-despawn/clue-juggling-logcat.txt): ::item 10180 1, drop it (OBJ_ADD reads timeUntilDespawn 6100, ownership self, neverBecomesPublic), let the client idle-logout (5 min) or log out, log back in on the same tile. The re-sent OBJ_ADD for the still-present clue decodes on the Android client as despawn tick 65535 (host log: 'ground item spawned: TileItem[10180 x1] ... tick 6: visible in -6, despawn in 65529 ticks, ownership 1, private'), i.e. the 0xFFFF 'no timer' value, so RuneLite's Ground Items shows a ~10.9 h timer and Clue Juggling Timers falls back to its saved timer. Expected: the re-sent OBJ_ADD carries the remaining timeUntilDespawn/timeUntilPublic (the live path Obj.timeUntilDespawn(cycle) does; the login/zone re-send path appears to build the prot from a copy without timers, cf. the open despawn-copy-owner-id item in ground-item-despawn-times). Source: OSRS Wiki 'Drop' (untradeable/clue timers; 'This timer pauses if logged out' for untradeables, so the remaining time should also be frozen while the owner is offline, to be confirmed against RSProx re-login recordings). Also check a tradeable (Lobster 379) dropped, relog within 100 ticks: expected remaining private/despawn ticks.

## Definition of done
- [ ] Repro on the test server: after a relog the player's own dropped clue and tradeable are re-sent with their remaining timeUntilDespawn (and timeUntilPublic), not 0xFFFF
- [ ] Whether the despawn timer of untradeables/clues pauses while the owner is logged out follows the OSRS source cited in the accuracy spec
- [ ] Android check: host log 'ground item spawned' after relog shows the remaining ticks (client dev re-checks in hub-ground-items-despawn's follow-up or a new client change)

## Log
- 2026-10-22T00:51:11Z created (ready)
- 2026-10-22T02:08:34Z triage: a client repro (hub-ground-items-despawn) depends on it: Ground Items is one of the user's built-in plugins
