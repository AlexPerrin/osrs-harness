---
slug: 56-misthalin-mystery-mandy-guards
track: server
title: 'fix: Misthalin Mystery: Mandy''s reward talk only at the waiting stage'
prio: P3
role: server-dev
stage: live
hold:
  kind: failed
  reason: 'spec missing: accuracy/56-misthalin-mystery-mandy-guards.md on the fork''s docs branch before the upstream gate (the hand-over stays at 10035c3ea)'
  since: '2026-10-22T02:16:31Z'
deps: []
branch: fix/56-misthalin-mystery-mandy-guards
commit: 10035c3ea63a67a61588b13bf4bcee36a2b3d0b0
local_only: false
owner: null
instances: []
live_commit: 10035c3ea63a67a61588b13bf4bcee36a2b3d0b0
created: '2026-10-21T00:25:19Z'
updated: '2026-10-22T02:16:31Z'
---
## Change
Branch `fix/56-misthalin-mystery-mandy-guards` carried by the live server at its pin; no v2 task.

## Definition of done
- [x] in integration

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: (integration.txt)
- 2026-10-22T02:08:33Z hold blocked: upstream gate needs accuracy/<slug>.md first (spec-fix-06-76 writes the specs for the pre-v3 fixes)
- 2026-10-22T02:16:31Z hold failed: spec missing: accuracy/56-misthalin-mystery-mandy-guards.md on the fork's docs branch before the upstream gate (the hand-over stays at 10035c3ea)
