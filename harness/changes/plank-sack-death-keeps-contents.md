---
slug: plank-sack-death-keeps-contents
track: server
title: 'Plank sack: death keeps contents'
prio: P3
role: server-dev
stage: ready
hold:
  kind: decision
  reason: 'held (user 2026-10-24): settle open PRs first; client changes wait for BlueStacks; unhold when ready'
  since: '2026-10-25T00:39:45Z'
deps: []
branch: fix/plank-sack-death-keeps-contents
commit: null
local_only: false
owner: null
created: '2026-10-20T01:42:42Z'
updated: '2026-10-25T00:39:45Z'
---
## Change
Plank sack gap vs OSRS (merged #357): the sack keeps its contents on death. One fix, one PR; no tests-only PR.

## Definition of done
- [ ] behaviour matches the wiki text and date cited in the spec, checked in game
- [ ] accuracy/plank-sack-death-keeps-contents.md on the fork's docs branch (wiki/cache baseline per rule, RSProx comparison recorded)
- [ ] fork PR open with green CI at the handed-over commit
- [ ] one change only, branch off upstream main (no stacking)

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: plank-sack-death-keeps-contents
- 2026-10-22T02:08:34Z triage: parity gap, small; after the user's plugins' content
- 2026-10-22T02:16:31Z branch fix/<slug> (grooming)
- 2026-10-25T00:39:45Z hold decision: held (user 2026-10-24): settle open PRs first; client changes wait for BlueStacks; unhold when ready
