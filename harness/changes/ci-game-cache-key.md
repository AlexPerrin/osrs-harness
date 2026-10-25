---
slug: ci-game-cache-key
track: server
title: 'CI: game-data actions cache key must change with the cache revision'
prio: P2
role: server-dev
stage: dev
hold: null
deps: []
branch: local/ci-game-cache-key
commit: null
local_only: true
owner: null
booked:
  dev: '|da39a3ee5e6b'
cost:
  runs: 1
  turns: 0
  tokens: 0
  minutes: 0
created: '2026-10-22T00:42:23Z'
updated: '2026-10-25T04:13:09Z'
---
## Change
CI: game-data actions cache key must change with the cache revision

## Definition of done
- [ ] ci.yml (and the other workflows using game-cache-v2-*) key the game-data cache on the cache tool / revision inputs (e.g. hashFiles('game.example.yml','gradle/libs.versions.toml') or the revision), so a branch's entry saved at revision 240 is not restored after the 241 bump
- [ ] fork CI green on a branch that had a stale pre-241 cache entry, without deleting the entry by hand
- [ ] fork PR with green CI; accuracy spec not needed (CI only)

## Log
- 2026-10-22T00:42:23Z created (ready)
- 2026-10-22T02:08:34Z triage: every fork CI run depends on it; next server dev slot after the user's content
- 2026-10-22T02:16:31Z fork-only: the fork's CI workflow (local/, BR-C7)
- 2026-10-25T04:07:34Z ready -> dev: dispatched to sd87
- 2026-10-25T04:07:34Z run sd87 started (server-dev, stage dev)
- 2026-10-25T04:13:09Z run sd87 ended: 0 turns, 0 tokens, exit ok
