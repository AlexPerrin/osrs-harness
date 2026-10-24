---
slug: harness-self-contained
track: harness
title: 'Keep the harness contained in this repo: no dependency on the client checkout''s paths'
prio: P2
role: harness-dev
stage: ready
hold:
  kind: decision
  reason: after the PROBLEM doc and gate-before-upstream (one harness build at a time)
  since: '2026-10-24T23:16:06Z'
deps: []
branch: null
commit: null
local_only: false
owner: null
created: '2026-10-24T22:19:05Z'
updated: '2026-10-24T23:17:05Z'
---
## Change
Keep the harness contained in this repo: no dependency on the client checkout's paths

## Definition of done
- [ ] Evidence dirs live in this repo (git-ignored or under harness/), not in the client checkout's re/evidence/<slug>/; every change's evidence field, hd brief, hand-over check and role files use the new path; existing evidence is migrated or left with a pointer
- [ ] Audit and list every place the harness reads or writes outside this repo (HD_CLIENT_ROOT default ~/osrs-plugins-reverse, the client shims, ~/src clones, re/out); each is either removed, made a configured path in harness/policy.yaml, or listed as an intentional product boundary (the client repo is a target, not a home)
- [ ] The client repo's shims (tools/harness/hd.py, tools/hooks/*.py, tools/device-lock.sh) keep working or are replaced in a way the user approves; no edit to the client repo without the user's OK
- [ ] Tests per rule touched, full suite passes; ARCHITECTURE.md (docs/) states the boundary in a few lines; no root files beyond what must be at the root

## Log
- 2026-10-24T22:19:05Z created (ready)
- 2026-10-24T23:00:07Z ready -> dev: dispatched to hd16
- 2026-10-24T23:00:07Z run hd16 started (harness-dev, stage dev, instances none)
- 2026-10-24T23:16:06Z hold decision: after the PROBLEM doc and gate-before-upstream (one harness build at a time)
- 2026-10-24T23:17:05Z dev -> ready: run hd16 ended without a hand-over
