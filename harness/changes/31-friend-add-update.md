---
slug: 31-friend-add-update
track: server
title: 'fix: Friends: send the added friend back after FRIENDLIST_ADD'
prio: P3
role: server-dev
stage: live
hold:
  kind: failed
  reason: 'spec missing: accuracy/31-friend-add-update.md on the fork''s docs branch before the upstream gate (the hand-over stays at f397f8f7a)'
  since: '2026-10-22T02:16:31Z'
deps: []
branch: fix/31-friend-add-update
commit: f397f8f7af2faa15d38be06b7308c470b4cfeb9c
local_only: false
owner: null
instances: []
live_commit: f397f8f7af2faa15d38be06b7308c470b4cfeb9c
created: '2026-10-21T00:25:19Z'
updated: '2026-10-22T02:16:31Z'
---
## Change
Branch `fix/31-friend-add-update` carried by the live server at its pin; no v2 task.

## Definition of done
- [x] in integration

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: (integration.txt)
- 2026-10-22T02:08:33Z hold blocked: upstream gate needs accuracy/<slug>.md first (spec-fix-06-76 writes the specs for the pre-v3 fixes)
- 2026-10-22T02:16:31Z hold failed: spec missing: accuracy/31-friend-add-update.md on the fork's docs branch before the upstream gate (the hand-over stays at f397f8f7a)
