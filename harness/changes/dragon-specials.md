---
slug: dragon-specials
track: server
title: content/dragon-specials (in integration since before v3)
prio: P3
role: server-dev
stage: live
hold:
  kind: failed
  reason: 'spec missing (spec-dragon-specials): Accuracy spec + internal gate for the dragon-specials branch (fork STATE.md task 4). Overlaps upstream #313 (see overlap-specials-313). Then the upstream
    gate where the branch goes upstream.'
  since: '2026-10-21T00:25:19Z'
deps: []
branch: content/dragon-specials
commit: d4d3dde846fa2133f8cf5d9590e8a6c97aae8c85
local_only: false
owner: null
instances: []
live_commit: d4d3dde846fa2133f8cf5d9590e8a6c97aae8c85
created: '2026-10-21T00:25:19Z'
updated: '2026-10-22T02:08:34Z'
---
## Change
Branch `content/dragon-specials` carried by the live server at its pin; no v2 task.


Upstream overlap (from `overlap-specials-313`): Our dragon-specials overlaps upstream #313: upstream as a draft PR only, referencing #313 (user, 2026-10-18). Depends on the gates.

## Definition of done
- [x] in integration

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: (integration.txt), spec-dragon-specials
- 2026-10-21T00:25:19Z hold failed: spec missing (spec-dragon-specials): Accuracy spec + internal gate for the dragon-specials branch (fork STATE.md task 4). Overlaps upstream #313 (see overlap-specials-313). Then the upstream gate where the branch goes upstream.
- 2026-10-22T02:08:33Z folded overlap-specials-313 in (triage)
