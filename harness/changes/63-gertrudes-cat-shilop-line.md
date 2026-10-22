---
slug: 63-gertrudes-cat-shilop-line
track: server
title: 'fix: Gertrude''s Cat: Gertrude asks about Shilop after the boys are paid'
prio: P3
role: server-dev
stage: live
hold:
  kind: failed
  reason: 'spec missing: accuracy/63-gertrudes-cat-shilop-line.md on the fork''s docs branch before the upstream gate (the hand-over stays at bc1100c30)'
  since: '2026-10-22T02:16:31Z'
deps: []
branch: fix/63-gertrudes-cat-shilop-line
commit: bc1100c30ef7ad26f9dd7a9af94c1f1e537aca7f
local_only: false
owner: null
instances: []
live_commit: bc1100c30ef7ad26f9dd7a9af94c1f1e537aca7f
created: '2026-10-21T00:25:19Z'
updated: '2026-10-22T02:16:31Z'
---
## Change
Branch `fix/63-gertrudes-cat-shilop-line` carried by the live server at its pin; no v2 task.

## Definition of done
- [x] in integration

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: (integration.txt)
- 2026-10-22T02:08:33Z hold blocked: upstream gate needs accuracy/<slug>.md first (spec-fix-06-76 writes the specs for the pre-v3 fixes)
- 2026-10-22T02:16:31Z hold failed: spec missing: accuracy/63-gertrudes-cat-shilop-line.md on the fork's docs branch before the upstream gate (the hand-over stays at bc1100c30)
