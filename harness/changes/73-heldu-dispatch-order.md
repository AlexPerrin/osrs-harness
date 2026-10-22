---
slug: 73-heldu-dispatch-order
track: server
title: 'fix: let item-on-item scripts for the pair win over "used on anything" defaults'
prio: P3
role: server-dev
stage: live
hold:
  kind: blocked
  reason: upstream gate needs accuracy/<slug>.md first (spec-fix-06-76 writes the specs for the pre-v3 fixes)
  since: '2026-10-22T02:08:33Z'
deps:
- spec-fix-06-76
branch: fix/73-heldu-dispatch-order
commit: b2f2fbb297dc308a504a2d3d90841d6f824dd33d
local_only: false
owner: null
instances: []
live_commit: b2f2fbb297dc308a504a2d3d90841d6f824dd33d
created: '2026-10-21T00:25:19Z'
updated: '2026-10-22T02:08:34Z'
---
## Change
Branch `fix/73-heldu-dispatch-order` carried by the live server at its pin; no v2 task.

## Definition of done
- [x] in integration

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: (integration.txt), gate-heldu-dispatch-order
- 2026-10-22T02:08:33Z hold blocked: upstream gate needs accuracy/<slug>.md first (spec-fix-06-76 writes the specs for the pre-v3 fixes)
