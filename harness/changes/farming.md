---
slug: farming
track: server
title: fin/farming (in integration since before v3)
prio: P3
role: server-dev
stage: live
hold:
  kind: decision
  reason: 'branch fin/farming is not one-change-one-branch (BR-C1): fold into content/farming (changes the upstream PR head: your OK per PR), then point integration at it'
  since: '2026-10-21T00:25:19Z'
deps: []
branch: fin/farming
commit: 1788d0561e255580814a5c7d3897714958fd3aad
local_only: false
owner: null
instances: []
live_commit: 1788d0561e255580814a5c7d3897714958fd3aad
created: '2026-10-21T00:25:19Z'
updated: '2026-10-22T02:08:34Z'
---
## Change
Branch `fin/farming` carried by the live server at its pin; no v2 task.


Upstream overlap (from `overlap-farming-231`): Our farming work overlaps upstream #231: upstream as a draft PR only, referencing #231 (user, 2026-10-18). Depends on the gates.

## Definition of done
- [x] in integration

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: (integration.txt)
- 2026-10-21T00:25:19Z hold decision: branch fin/farming is not one-change-one-branch (BR-C1): fold into content/farming (changes the upstream PR head: your OK per PR), then point integration at it
- 2026-10-22T02:08:33Z folded overlap-farming-231 in (triage)
