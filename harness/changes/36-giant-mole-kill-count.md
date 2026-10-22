---
slug: 36-giant-mole-kill-count
track: server
title: 'fix: Giant Mole kill count'
prio: P3
role: server-dev
stage: live
hold:
  kind: failed
  reason: 'spec missing: accuracy/36-giant-mole-kill-count.md on the fork''s docs branch before the upstream gate (the hand-over stays at f66170105)'
  since: '2026-10-22T02:16:31Z'
deps: []
branch: fix/36-giant-mole-kill-count
commit: f661701058bd8b2be46a476372e40fbf9889e69f
local_only: false
owner: null
instances: []
live_commit: f661701058bd8b2be46a476372e40fbf9889e69f
created: '2026-10-21T00:25:19Z'
updated: '2026-10-22T02:16:31Z'
---
## Change
Branch `fix/36-giant-mole-kill-count` carried by the live server at its pin; no v2 task.

## Definition of done
- [x] in integration

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: (integration.txt)
- 2026-10-22T02:08:33Z hold blocked: upstream gate needs accuracy/<slug>.md first (spec-fix-06-76 writes the specs for the pre-v3 fixes)
- 2026-10-22T02:16:31Z hold failed: spec missing: accuracy/36-giant-mole-kill-count.md on the fork's docs branch before the upstream gate (the hand-over stays at f66170105)
