---
slug: gpu-plugin-feasibility
track: client
title: 'Stretch goal: RuneLite''s GPU plugin on the Android app (feasibility)'
prio: P2
role: client-dev
stage: dev
hold: null
deps: []
branch: client/gpu-plugin-feasibility
commit: null
local_only: false
owner: cd57
booked:
  dev: '|da39a3ee5e6b'
cost:
  runs: 1
  turns: 0
  minutes: 0.0
  usd: 0
created: '2026-10-20T04:39:08Z'
updated: '2026-10-25T04:06:37Z'
---
## Change
Stretch goal: RuneLite's GPU plugin on the Android app (feasibility)

## Definition of done
- [ ] how the official Android client renders today (GLES version, context ownership, frame submission, the libnb translation layer), from the reverse/agent with offsets or symbols
- [ ] what the GPU plugin needs (GL version and extensions, compute shaders or its non-compute path, DrawCallbacks and scene upload, isGpu) against what the app's GL context offers
- [ ] a ranked plan for the smallest path to a GPU-plugin frame on the device, with blockers and a rough size; written to docs and linked from README

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: client-gpu-plugin-feasibility
- 2026-10-22T02:08:34Z triage: stretch goal (user): its own spike; after the user's plugins' client work
- 2026-10-22T02:16:31Z renamed from client-gpu-plugin-feasibility (grooming: slug = the branch slug, BR-C1)
- 2026-10-24T20:09:15Z ready -> dev: dispatched to cd51
- 2026-10-24T20:09:15Z run cd51 started (client-dev, stage dev, instances device)
- 2026-10-24T21:08:22Z run cd51 ended: ? turns, 0.0 min, $0, exit cancelled
- 2026-10-24T21:08:40Z dev -> ready: run cd51 ended without a hand-over
- 2026-10-25T00:39:45Z hold decision: held (user 2026-10-24): settle open PRs first; client changes wait for BlueStacks; unhold when ready
- 2026-10-25T02:18:02Z hold decision cleared: BlueStacks is open (user 2026-10-24): client work resumes
- 2026-10-25T04:06:37Z ready -> dev: dispatched to cd57
- 2026-10-25T04:06:37Z run cd57 started (client-dev, stage dev)
