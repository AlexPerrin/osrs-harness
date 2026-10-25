---
slug: ci-game-cache-key
track: server
kind: local
title: 'CI: game-data actions cache key must change with the cache revision'
priority: P2
created: '2026-10-22T00:42:23Z'
branch: local/ci-game-cache-key
---
## Change
CI: game-data actions cache key must change with the cache revision

## Definition of done
- [ ] ci.yml (and the other workflows using game-cache-v2-*) key the game-data cache on the cache tool / revision inputs (e.g. hashFiles('game.example.yml','gradle/libs.versions.toml') or the revision), so a branch's entry saved at revision 240 is not restored after the 241 bump
- [ ] fork CI green on a branch that had a stale pre-241 cache entry, without deleting the entry by hand
- [ ] fork PR with green CI; accuracy spec not needed (CI only)
