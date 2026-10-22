---
slug: skip-cs2-packs
track: server
title: local/skip-cs2-packs (in integration since before v3)
prio: P3
role: server-dev
stage: checked
hold: null
deps: []
branch: local/skip-cs2-packs
commit: e493480549e6088494b3f44d6d2b4f8adf18b651
local_only: true
owner: null
instances: []
evidence: re/evidence/skip-cs2-packs
summary: 're-stacked on fix/11-dense-clientscript-ids@c2f528fca (sd35): the custom clientscript ids follow the 241.4 stock range'
live_commit: 5c7515cb90beafaede81a290dd876ec956c4f183
batch: int-20261022-5
created: '2026-10-21T00:25:19Z'
updated: '2026-10-22T02:08:34Z'
---
## Change
Branch `local/skip-cs2-packs` carried by the live server at its pin; no v2 task.

## Definition of done
- [x] in integration

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: (integration.txt)
- 2026-10-22T01:50:01Z live -> ready: branch moved to e49348054 past 5c7515cb9: hand over again (BR-C2)
- 2026-10-22T01:52:39Z ready -> dev: hand-over recorded
- 2026-10-22T01:52:39Z handover local/skip-cs2-packs@e49348054: re-stacked on fix/11-dense-clientscript-ids@c2f528fca (sd35): the custom clientscript ids follow the 241.4 stock range
- 2026-10-22T02:04:07Z dev -> checked: hand-over check PASS
- 2026-10-22T02:05:10Z in train int-20261022-5: integration 17c773333 pushed; gate, image and deploy pending
