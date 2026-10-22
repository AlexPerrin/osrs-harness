---
slug: 69-blue-moon-inn-stairs
track: server
title: 'fix: Blue Moon Inn staircase in Varrock had no handler'
prio: P3
role: server-dev
stage: live
hold:
  kind: failed
  reason: 'spec missing: accuracy/69-blue-moon-inn-stairs.md on the fork''s docs branch before the upstream gate (the hand-over stays at 0e558f9db)'
  since: '2026-10-22T02:16:31Z'
deps: []
branch: fix/69-blue-moon-inn-stairs
commit: 0e558f9db976dc09d9b04aa63194eb6b1491f3a8
local_only: false
owner: null
instances: []
live_commit: 0e558f9db976dc09d9b04aa63194eb6b1491f3a8
created: '2026-10-21T00:25:19Z'
updated: '2026-10-22T02:16:31Z'
---
## Change
Branch `fix/69-blue-moon-inn-stairs` carried by the live server at its pin; no v2 task.

## Definition of done
- [x] in integration

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: (integration.txt)
- 2026-10-22T02:08:33Z hold blocked: upstream gate needs accuracy/<slug>.md first (spec-fix-06-76 writes the specs for the pre-v3 fixes)
- 2026-10-22T02:16:31Z hold failed: spec missing: accuracy/69-blue-moon-inn-stairs.md on the fork's docs branch before the upstream gate (the hand-over stays at 0e558f9db)
