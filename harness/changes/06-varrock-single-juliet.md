---
slug: 06-varrock-single-juliet
track: server
title: 'fix: Spawn only one Juliet'
prio: P3
role: server-dev
stage: live
hold:
  kind: failed
  reason: 'spec missing: accuracy/06-varrock-single-juliet.md on the fork''s docs branch before the upstream gate (the hand-over stays at d5cea8a96)'
  since: '2026-10-22T02:16:31Z'
deps: []
branch: fix/06-varrock-single-juliet
commit: d5cea8a961393c8b4fe18f993e46005fa54c1c27
local_only: false
owner: null
instances: []
live_commit: d5cea8a961393c8b4fe18f993e46005fa54c1c27
created: '2026-10-21T00:25:19Z'
updated: '2026-10-22T02:16:31Z'
---
## Change
Branch `fix/06-varrock-single-juliet` carried by the live server at its pin; no v2 task.

## Definition of done
- [x] in integration

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: (integration.txt)
- 2026-10-22T02:08:33Z hold blocked: upstream gate needs accuracy/<slug>.md first (spec-fix-06-76 writes the specs for the pre-v3 fixes)
- 2026-10-22T02:16:31Z hold failed: spec missing: accuracy/06-varrock-single-juliet.md on the fork's docs branch before the upstream gate (the hand-over stays at d5cea8a96)
