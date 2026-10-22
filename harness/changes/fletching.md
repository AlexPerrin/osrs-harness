---
slug: fletching
track: server
title: content/fletching (in integration since before v3)
prio: P3
role: server-dev
stage: live
hold:
  kind: failed
  reason: 'spec missing (spec-fletching): Accuracy spec + internal gate for the fletching branch (fork STATE.md task 4). Overlaps upstream #262 (see overlap-fletching-262). Then the upstream gate where
    the branch goes upstream.'
  since: '2026-10-21T00:25:19Z'
deps: []
branch: content/fletching
commit: 7e1f7b4bef43fab2a1030b63f607efec758cbf00
local_only: false
owner: null
instances: []
live_commit: 7e1f7b4bef43fab2a1030b63f607efec758cbf00
created: '2026-10-21T00:25:19Z'
updated: '2026-10-22T02:08:34Z'
---
## Change
Branch `content/fletching` carried by the live server at its pin; no v2 task.


Upstream overlap (from `overlap-fletching-262`): Our fletching overlaps upstream #262: upstream as a draft PR only, referencing #262 (user, 2026-10-18). fix/06, 07, 69 stay local until #299 merges. Depends on the gates.

## Definition of done
- [x] in integration

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: (integration.txt), spec-fletching
- 2026-10-21T00:25:19Z hold failed: spec missing (spec-fletching): Accuracy spec + internal gate for the fletching branch (fork STATE.md task 4). Overlaps upstream #262 (see overlap-fletching-262). Then the upstream gate where the branch goes upstream.
- 2026-10-22T02:08:33Z folded overlap-fletching-262 in (triage)
