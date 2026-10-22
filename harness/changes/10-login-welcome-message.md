---
slug: 10-login-welcome-message
track: server
title: 'fix: Send the OSRS welcome message on login'
prio: P3
role: server-dev
stage: live
hold:
  kind: failed
  reason: 'spec missing: accuracy/10-login-welcome-message.md on the fork''s docs branch before the upstream gate (the hand-over stays at 520b573c2)'
  since: '2026-10-22T02:16:31Z'
deps: []
branch: fix/10-login-welcome-message
commit: 520b573c273e00dedf68488b742e963b9db42c18
local_only: false
owner: null
instances: []
live_commit: 520b573c273e00dedf68488b742e963b9db42c18
created: '2026-10-21T00:25:19Z'
updated: '2026-10-22T02:16:31Z'
---
## Change
Branch `fix/10-login-welcome-message` carried by the live server at its pin; no v2 task.

## Definition of done
- [x] in integration

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: (integration.txt)
- 2026-10-22T02:08:33Z hold blocked: upstream gate needs accuracy/<slug>.md first (spec-fix-06-76 writes the specs for the pre-v3 fixes)
- 2026-10-22T02:16:31Z hold failed: spec missing: accuracy/10-login-welcome-message.md on the fork's docs branch before the upstream gate (the hand-over stays at 520b573c2)
