---
slug: 70-missing-mesanims
track: server
title: 'fix: missing server mesanims (scared, sleep) that throw mid-dialogue'
prio: P3
role: server-dev
stage: live
hold:
  kind: failed
  reason: 'spec missing: accuracy/70-missing-mesanims.md on the fork''s docs branch before the upstream gate (the hand-over stays at f38f4a793)'
  since: '2026-10-22T02:16:31Z'
deps: []
branch: fix/70-missing-mesanims
commit: f38f4a79356b8bf01a170cf2cf58d0deb7e8de55
local_only: false
owner: null
instances: []
live_commit: f38f4a79356b8bf01a170cf2cf58d0deb7e8de55
created: '2026-10-21T00:25:19Z'
updated: '2026-10-22T02:16:31Z'
---
## Change
Branch `fix/70-missing-mesanims` carried by the live server at its pin; no v2 task.

## Definition of done
- [x] in integration

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: (integration.txt)
- 2026-10-22T02:08:33Z hold blocked: upstream gate needs accuracy/<slug>.md first (spec-fix-06-76 writes the specs for the pre-v3 fixes)
- 2026-10-22T02:16:31Z hold failed: spec missing: accuracy/70-missing-mesanims.md on the fork's docs branch before the upstream gate (the hand-over stays at f38f4a793)
