---
slug: parity-metric
track: harness
title: 'Server progress metric: parity with the official OSRS server (tools/harness/server_parity.py)'
prio: P2
role: harness-dev
stage: ready
hold:
  kind: decision
  reason: 'new feature dispatch held (user 2026-10-24): settle open PRs and harness fixes first; unhold when ready'
  since: '2026-10-24T22:48:22Z'
deps: []
branch: harness/parity-metric
commit: null
local_only: false
owner: null
instances: []
created: '2026-10-20T06:10:54Z'
updated: '2026-10-24T22:48:36Z'
---
## Change
Server progress metric: parity with the official OSRS server (tools/harness/server_parity.py)

## Definition of done
- [ ] a written definition (docs/server-parity.md) of what counts toward an identical copy of the OSRS server, per area: quests, skills (incl. Sailing), minigames, bosses, random events, shops, NPC dialogue, and cache coverage (locs/NPCs/objs with ops, interfaces) that have a server handler; each area's denominator from the cache (osrs-mcp, gamevals) or the OSRS Wiki, its numerator from the integration tree (content modules, onOpLoc/onOpNpc/onOpObj bindings, quest list)
- [ ] tools/harness/server_parity.py --markdown prints a table per area (implemented / total, %), an overall weighted %, and the source of every number; it reads the integration tree, never the live server; runs in under 10 min
- [ ] upstream main vs integration shown side by side (how much of our parity is still only on the fork)
- [ ] docs/progress.md shows it (progress_report.py already calls the tool when present); a test for the counting on a fixture tree

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: server-parity-metric
- 2026-10-22T02:08:34Z triage: the server progress tile; P2
- 2026-10-22T02:16:31Z renamed from server-parity-metric (grooming: slug = the branch slug, BR-C1)
- 2026-10-24T22:28:10Z ready -> dev: dispatched to hd9
- 2026-10-24T22:28:10Z run hd9 started (harness-dev, stage dev, instances none)
- 2026-10-24T22:28:21Z hold blocked: new feature dispatch held (user 2026-10-24): settle open PRs and the harness fixes first
- 2026-10-24T22:28:35Z hold blocked cleared: every dep is live
- 2026-10-24T22:28:35Z dev -> ready: run hd9 ended without a hand-over
- 2026-10-24T22:36:07Z ready -> dev: dispatched to hd12
- 2026-10-24T22:36:07Z run hd12 started (harness-dev, stage dev, instances none)
- 2026-10-24T22:48:22Z hold decision: new feature dispatch held (user 2026-10-24): settle open PRs and harness fixes first; unhold when ready
- 2026-10-24T22:48:36Z dev -> ready: run hd9 ended without a hand-over
