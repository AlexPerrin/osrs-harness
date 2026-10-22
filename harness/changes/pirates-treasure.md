---
slug: pirates-treasure
track: server
title: content/pirates-treasure (in integration since before v3)
prio: P3
role: server-dev
stage: live
hold:
  kind: failed
  reason: 'spec missing (spec-pirates-treasure): Accuracy spec + internal gate for content/pirates-treasure (fork STATE.md task 4; see also cleanup-pirates-treasure). Then the upstream gate where the branch
    goes upstream.'
  since: '2026-10-21T00:25:19Z'
deps: []
branch: content/pirates-treasure
commit: ca5b0d335cbfa4d503a15b686f6bb5d67af2c4eb
local_only: false
owner: null
instances: []
live_commit: ca5b0d335cbfa4d503a15b686f6bb5d67af2c4eb
created: '2026-10-21T00:25:19Z'
updated: '2026-10-22T02:08:34Z'
---
## Change
Branch `content/pirates-treasure` carried by the live server at its pin; no v2 task.


Also needed before the gate (from `cleanup-pirates-treasure`): content/pirates-treasure on the fork: squash the fixup commit and rebase onto the quest test fixture once it is merged upstream.

## Definition of done
- [x] in integration

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: (integration.txt), spec-pirates-treasure
- 2026-10-21T00:25:19Z hold failed: spec missing (spec-pirates-treasure): Accuracy spec + internal gate for content/pirates-treasure (fork STATE.md task 4; see also cleanup-pirates-treasure). Then the upstream gate where the branch goes upstream.
- 2026-10-22T02:08:33Z folded cleanup-pirates-treasure in (triage)
