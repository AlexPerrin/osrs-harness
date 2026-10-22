---
slug: 75-coal-bag-messages
track: server
title: 'style: spotlessApply on the files this branch touches'
prio: P3
role: server-dev
stage: live
hold:
  kind: blocked
  reason: upstream gate needs accuracy/<slug>.md first (spec-fix-06-76 writes the specs for the pre-v3 fixes)
  since: '2026-10-22T02:08:33Z'
deps:
- spec-fix-06-76
branch: fix/75-coal-bag-messages
commit: 0514e670446a248c5405dc433dfbaa7c77421e43
local_only: false
owner: null
instances: []
live_commit: 0514e670446a248c5405dc433dfbaa7c77421e43
created: '2026-10-21T00:25:19Z'
updated: '2026-10-22T02:08:34Z'
---
## Change
Branch `fix/75-coal-bag-messages` carried by the live server at its pin; no v2 task.

## Definition of done
- [x] in integration

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: (integration.txt), gate-coal-bag-messages
- 2026-10-22T02:08:33Z hold blocked: upstream gate needs accuracy/<slug>.md first (spec-fix-06-76 writes the specs for the pre-v3 fixes)
