---
slug: host-worldentity-api
track: client
title: 'Host: the WorldEntity API (WorldEntity, WorldEntityConfig, WorldView.getYellowClickAction) for Sailing and Barracuda Trials plugins'
prio: P3
role: client-dev
stage: ready
hold:
  kind: decision
  reason: 'held (user 2026-10-24): settle open PRs first; client changes wait for BlueStacks; unhold when ready'
  since: '2026-10-25T00:39:45Z'
deps: []
branch: null
commit: null
local_only: false
owner: null
created: '2026-10-22T02:08:34Z'
updated: '2026-10-25T00:39:45Z'
---
## Change
The user's sailing and barracuda-trials-pathfinder hub plugins start but call WorldEntity/WorldEntityConfig getters and WorldView.getYellowClickAction the host stubs (re/evidence/hub-batch-next/user-plugins.md). The server content (content-sailing) is separate and larger.

## Definition of done
- [ ] the WorldEntity getters the sailing and barracuda-trials-pathfinder plugins call resolve on the host (stubcheck clean)
- [ ] verified against desktop RuneLite semantics (ab-test) where the server has no boats yet
- [ ] built (host/build.sh + ninja + repack), repack log 7 telemetry lines

## Log
- 2026-10-22T02:08:34Z created (ready)
- 2026-10-25T00:39:45Z hold decision: held (user 2026-10-24): settle open PRs first; client changes wait for BlueStacks; unhold when ready
