---
slug: stile-approach
track: server
title: 'Stile: approach from the outside tile'
prio: P1
role: server-dev
stage: checked
hold: null
deps: []
branch: fix/stile-approach
commit: 68ddd1b6c0de78e18788b22dc52ff6df2909d348
local_only: false
owner: null
instances:
- desktop
evidence: /home/alex/osrs-plugins-reverse/re/evidence/fix-stile-approach
pr: https://github.com/AlexPerrin/OpenRune-Server/pull/21
ci: https://github.com/AlexPerrin/OpenRune-Server/actions/runs/39363600299
upstream_pr: 406
summary: '68ddd1b6c drops StileScriptTest from 513144d3d (maintainer precedent on #366: these tests can be removed); no other change. #406 head; PR body updated. User OK 2026-10-24.'
gated_commit: 513144d3dfcfcfd5613123bbe3457b952192c384
live_commit: 513144d3dfcfcfd5613123bbe3457b952192c384
published_commit: 513144d3dfcfcfd5613123bbe3457b952192c384
batch: int-20261024-2
cost:
  runs: 5
  turns: 16
  minutes: 2.9
  usd: 11.77
  tokens: 0
created: '2026-10-20T01:42:40Z'
updated: '2026-10-24T22:36:06Z'
---
## Change
fix/stile-approach 8a8c0ca7a failed the internal gate: the player walks onto the stile's own blocking tile, so it never climbs. Fix: start the climb from the tile outside the stile on the player's side, in line with it; check in game; update the PR text. Covers the #366 review item 'stile jump from too far away (player not always in the pen)'.

## Definition of done
- [x] Climbing the stile from either side, from any approach angle, walks to the in-line tile outside the stile first and then climbs; never from afar (17 crossings at 513144d3d, own RSProx transcript)
- [x] internal gate PASS (qa/stile-approach.md on fork docs) after the FAIL at 8a8c0ca7a (dev's check PASS at 513144d3d in fork docs 52233ff59)
- [x] PR text updated and reviewed (pr-texts/stile-approach.upstream.body in fork docs 52233ff59; fork PR #21 title and body updated)
- [x] accuracy/fix-stile-approach.md on the fork's docs branch (wiki/cache baseline per rule, RSProx comparison recorded) (as accuracy/stile-approach.md, the branch slug handover-check reads; in fork docs 52233ff59)
- [x] fork PR open with green CI at the handed-over commit (#21 head 513144d3d; CI 39363600299, Formatting 39363603819)
- [x] one change only, branch off upstream main (no stacking) (3 commits on 829b9477d, 3 files in generic-locs/stile)

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: fix-stile-approach
- 2026-10-22T00:28:38Z run sq32 started (server-qa, stage gate, instances desktop)
- 2026-10-22T00:30:32Z run sq32 ended: ? turns, 0.0 min, $0, exit stopped:redundant: upstream #366 is open at this commit (the observer missed fork PRs by branch)
- 2026-10-22T00:30:34Z run sq33 started (server-qa, stage gate, instances desktop)
- 2026-10-22T01:17:50Z gate PASS claimed: upstream gate PASS at 513144d3d: accuracy re-read (cache 12982 1x2 solid, 1718 t2327-2333), 10 in-game crossings on main e85278c9a + branch at the 1718 ticks (own RSProx transcript), CI green, one fix, no upstream overlap, PR text true; record qa/stile-approach.md on fork docs (the record on docs is what counts)
- 2026-10-22T01:18:26Z gate PASS claimed: record qa/stile-approach.md pushed to fork docs 91dcc82c4 (the earlier gate call ran before the push went through) (the record on docs is what counts)
- 2026-10-22T01:18:56Z live -> gated: observed
- 2026-10-22T01:18:57Z run sq33 ended: 16 turns, 2.9 min, $11.77, exit ok
- 2026-10-24T19:32:22Z 2026-10-24 reset (user): settle the existing upstream PRs (#354 #355 #367 #368) before opening new ones; depends on their review fixes, P2
- 2026-10-24T19:42:49Z 2026-10-24 user: P1, runs first; dependency on the four review fixes removed (it fixes the stile bug reported on merged #366)
- 2026-10-24T19:45:12Z approval stile-approach-open-pr-513144d executed (open-pr): https://github.com/OpenRune/OpenRune-Server/pull/406
- 2026-10-24T19:46:29Z gated -> published: observed
- 2026-10-24T19:51:51Z published -> ready: branch moved to 68ddd1b6c past 513144d3d: hand over again (BR-C2)
- 2026-10-24T21:10:22Z ready -> dev: hand-over recorded
- 2026-10-24T21:10:22Z handover fix/stile-approach@68ddd1b6c: 68ddd1b6c drops StileScriptTest from 513144d3d (maintainer precedent on #366: these tests can be removed); no other change. #406 head; PR body updated. User OK 2026-10-24.
- 2026-10-24T21:12:45Z dev -> ready: hand-over check FAIL (1): the next dev fixes exactly those items
- 2026-10-24T21:57:22Z ready -> dev: dispatched to sd47
- 2026-10-24T21:57:22Z run sd47 started (server-dev, stage dev, instances desktop)
- 2026-10-24T21:58:28Z dev -> ready: hand-over check FAIL (1): the next dev fixes exactly those items
- 2026-10-24T21:58:28Z run sd47 ended: ? turns, ? tokens, exit stopped:lingering: owner is None (change at ready)
- 2026-10-24T21:59:32Z ready -> dev: dispatched to sd48
- 2026-10-24T21:59:32Z run sd48 started (server-dev, stage dev, instances desktop)
- 2026-10-24T22:00:40Z dev -> ready: hand-over check FAIL (1): the next dev fixes exactly those items
- 2026-10-24T22:00:41Z run sd48 ended: ? turns, ? tokens, exit stopped:lingering: owner is None (change at ready)
- 2026-10-24T22:01:47Z ready -> dev: dispatched to sd49
- 2026-10-24T22:01:47Z run sd49 started (server-dev, stage dev, instances desktop)
- 2026-10-24T22:05:06Z dev -> ready: hand-over check FAIL (1): the next dev fixes exactly those items
- 2026-10-24T22:05:06Z run sd49 ended: ? turns, ? tokens, exit stopped:lingering: owner is None (change at ready)
- 2026-10-24T22:24:37Z ready -> dev: dispatched to sd66
- 2026-10-24T22:24:37Z run sd66 started (server-dev, stage dev, instances desktop)
- 2026-10-24T22:25:05Z dev -> checked: hand-over check PASS
- 2026-10-24T22:36:06Z in train int-20261024-2: integration 4cac9f4d7 pushed; gate, image and deploy pending
