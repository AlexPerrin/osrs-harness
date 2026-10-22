---
slug: 07-juliet-house-stairs
track: server
title: 'fix: Handle the tall stairs in Juliet''s house'
prio: P3
role: server-dev
stage: live
hold:
  kind: failed
  reason: 'spec missing: accuracy/07-juliet-house-stairs.md on the fork''s docs branch before the upstream gate (the hand-over stays at 2e39d2189)'
  since: '2026-10-22T02:16:31Z'
deps: []
branch: fix/07-juliet-house-stairs
commit: 2e39d2189c86fc168cf5c9fce7b6db9c9377ac25
local_only: false
owner: null
instances: []
live_commit: 2e39d2189c86fc168cf5c9fce7b6db9c9377ac25
created: '2026-10-21T00:25:19Z'
updated: '2026-10-22T02:16:31Z'
---
## Change
Branch `fix/07-juliet-house-stairs` carried by the live server at its pin; no v2 task.

## Definition of done
- [x] in integration

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: (integration.txt)
- 2026-10-22T02:08:33Z hold blocked: upstream gate needs accuracy/<slug>.md first (spec-fix-06-76 writes the specs for the pre-v3 fixes)
- 2026-10-22T02:16:31Z hold failed: spec missing: accuracy/07-juliet-house-stairs.md on the fork's docs branch before the upstream gate (the hand-over stays at 2e39d2189)
