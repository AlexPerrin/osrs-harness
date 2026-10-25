---
slug: client-117hd-feasibility
track: client
title: 'Stretch goal: 117 HD on the Android app (feasibility)'
prio: P2
role: client-dev
stage: ready
hold:
  kind: decision
  reason: 'user 2026-10-25: wrap up and hand off to v7; no new dispatch'
  since: '2026-10-25T04:06:19Z'
deps: []
branch: null
commit: null
local_only: false
owner: null
booked:
  dev: '|da39a3ee5e6b'
cost:
  runs: 2
  turns: 0
  minutes: 0
  usd: 0
  tokens: 0
created: '2026-10-20T04:39:08Z'
updated: '2026-10-25T04:06:19Z'
---
## Change
Stretch goal: 117 HD on the Android app (feasibility)

## Definition of done
- [ ] what 117 HD needs on its own terms (its renderer, GL version and features, shaders, scene and model hooks, texture/material data, memory), independent of RuneLite's GPU plugin
- [ ] the gap against the app's GL context (GLES via libnb) and the Android device, from the reverse/agent; reuse the GPU spike's rendering notes when they exist but don't wait for them
- [ ] a ranked plan for the smallest path to a 117 HD frame on the device (e.g. a GLES port of its shaders, reduced feature set), with blockers and a rough size; written to docs and linked from README

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: client-117hd-feasibility
- 2026-10-22T01:54:43Z ready -> dev: dispatched to cd50
- 2026-10-22T01:54:43Z run cd50 started (client-dev, stage dev, instances device)
- 2026-10-24T20:08:33Z run cd50 ended: ? turns, 0.0 min, $0, exit cancelled
- 2026-10-24T20:09:15Z dev -> ready: run cd50 ended without a hand-over
- 2026-10-25T00:37:54Z ready -> dev: dispatched to cd52
- 2026-10-25T00:37:54Z run cd52 started (client-dev, stage dev)
- 2026-10-25T00:39:45Z hold decision: held (user 2026-10-24): settle open PRs first; client changes wait for BlueStacks; unhold when ready
- 2026-10-25T00:40:15Z dev -> ready: run cd52 ended without a hand-over
- 2026-10-25T02:18:02Z hold decision cleared: BlueStacks is open (user 2026-10-24): client work resumes
- 2026-10-25T03:50:40Z ready -> dev: dispatched to cd56
- 2026-10-25T03:50:40Z run cd56 started (client-dev, stage dev)
- 2026-10-25T04:05:40Z run cd56 ended: 0 turns, 0 tokens, exit ok
- 2026-10-25T04:05:50Z hold decision: user 2026-10-25: wrap up and hand off to v7; no new dispatch until the fresh console starts
- 2026-10-25T04:06:14Z dev -> ready: run cd56 ended without a hand-over
- 2026-10-25T04:06:19Z hold decision: user 2026-10-25: wrap up and hand off to v7; no new dispatch
