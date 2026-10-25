---
slug: hub-did-i-compost
track: client
title: 'Did I Compost hub plugin: treated path'
prio: P3
role: client-dev
stage: ready
hold: null
deps:
- farming-compost
branch: null
commit: null
local_only: false
owner: null
booked: null
created: '2026-10-20T01:42:43Z'
updated: '2026-10-25T02:18:02Z'
---
## Change
Did I Compost's treated path on the device once Compost on a patch works on the server (docs/client-state.md Next tasks 1).

## Definition of done
- [ ] Did I Compost marks the patch as treated after composting on the device
- [ ] built (host/build.sh + ninja + repack); changed path tried on the device with a screenshot or logcat in re/evidence/hub-did-i-compost/

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: hub-did-i-compost
- 2026-10-21T00:25:19Z hold blocked: waiting for farming-compost
- 2026-10-22T02:08:34Z triage: not on the user's plugin list
- 2026-10-25T00:39:45Z hold decision: held (user 2026-10-24): settle open PRs first; client changes wait for BlueStacks; unhold when ready
- 2026-10-25T02:18:02Z hold decision cleared: BlueStacks is open (user 2026-10-24): client work resumes
