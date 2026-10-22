---
slug: host-camera-setters
track: client
title: 'Host: the Camera plugin''s setters (speed, invert, mouse mask, pitch relaxer, shake) and getIndexScripts'
prio: P2
role: client-dev
stage: ready
hold:
  kind: decision
  reason: 'your open decision (HANDOFF 7): add the Camera setters to the host (touch camera: some may not apply)? Approve to make it ready, deny to drop.'
  since: '2026-10-22T02:08:34Z'
deps: []
branch: null
commit: null
local_only: false
owner: null
instances: []
created: '2026-10-22T02:08:34Z'
updated: '2026-10-22T02:08:34Z'
---
## Change
The user runs the built-in Camera plugin; on Android it is not added (7 setters and getIndexScripts stubbed; most are desktop mouse control). HANDOFF 7 listed 'client setters for Camera' as an open user decision.

## Definition of done
- [ ] the 7 camera setters and getIndexScripts implemented or documented as not applicable on Android (touch camera)
- [ ] Camera plugin switched on and running on the device
- [ ] built (host/build.sh + ninja + repack), repack log 7 telemetry lines

## Log
- 2026-10-22T02:08:34Z created (ready)
- 2026-10-22T02:08:34Z hold decision: your open decision (HANDOFF 7): add the Camera setters to the host (touch camera: some may not apply)? Approve to make it ready, deny to drop.
