---
slug: 10-login-welcome-message
track: server
title: 'fix: Send the OSRS welcome message on login'
prio: P3
role: server-dev
stage: live
hold:
  kind: blocked
  reason: upstream gate needs accuracy/<slug>.md first (spec-fix-06-76 writes the specs for the pre-v3 fixes)
  since: '2026-10-22T02:08:33Z'
deps:
- spec-fix-06-76
branch: fix/10-login-welcome-message
commit: 520b573c273e00dedf68488b742e963b9db42c18
local_only: false
owner: null
instances: []
live_commit: 520b573c273e00dedf68488b742e963b9db42c18
created: '2026-10-21T00:25:19Z'
updated: '2026-10-22T02:08:34Z'
---
## Change
Branch `fix/10-login-welcome-message` carried by the live server at its pin; no v2 task.

## Definition of done
- [x] in integration

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: (integration.txt)
- 2026-10-22T02:08:33Z hold blocked: upstream gate needs accuracy/<slug>.md first (spec-fix-06-76 writes the specs for the pre-v3 fixes)
