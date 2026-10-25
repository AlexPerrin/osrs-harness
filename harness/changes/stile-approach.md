---
slug: stile-approach
track: server
title: 'Stile: approach from the outside tile'
prio: P1
role: server-dev
stage: gate
hold: null
deps: []
branch: fix/stile-approach
commit: caacbf4cefa6f8491c8afa2d3fc7fc624d581a57
repo: /home/alex/src/openrune-work/agents/sd79/or
local_only: false
owner: sq58
evidence: /home/alex/osrs-plugins-reverse/re/evidence/stile-approach
summary: 'caacbf4ce restores StileScript.kt class KDoc to main''s text (fix: commit on 68ddd1b6c, fast-forward); PR body normalised (template checklist verbatim, notes plain, in-game claim restated to 513144d3d)
  in fork docs 7ec42523c; accuracy Tests section removed; spotlessCheck generic-locs PASS'
live_commit: 68ddd1b6c0de78e18788b22dc52ff6df2909d348
booked:
  gate: caacbf4cefa6f8491c8afa2d3fc7fc624d581a57
batch: int-20261024-2
cost:
  runs: 7
  turns: 16
  minutes: 2.9
  usd: 11.77
  tokens: 0
created: '2026-10-20T01:42:40Z'
updated: '2026-10-25T00:34:52Z'
upstream_pr: 406
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
- 2026-10-25T00:02:54Z run sq56 started (server-qa, stage gate)
- 2026-10-25T00:13:01Z live on the test server: live integration 4cac9f4d7 carries 68ddd1b6c
- 2026-10-25T00:24:59Z QA aggregate FAIL at 68ddd1b6c (7 finding(s)): KDoc rewritten (AGENTS), commit subject prefix, PR checklist lines not verbatim, wording of tested commit
- 2026-10-25T00:25:52Z gate -> contribute: observed
- 2026-10-25T00:25:54Z run sq56 ended: ? turns, ? tokens, exit stopped:lingering: change at contribute
- 2026-10-25T00:33:04Z QA AGGREGATE (sq56, 2026-10-24) at 68ddd1b6c: accuracy/ci/format/scope PASS, ingame PASS (carried over: production code identical to 513144d3d, verified by sq33). FIX FIRST (user): (1) style: StileScript.kt's existing class KDoc (already on main) was rewritten and grown from 2 to 4 lines: restore main's KDoc exactly (AGENTS.md: no new comments) in a NEW commit on fix/stile-approach (no force-push; the commit subject of 68ddd1b6c cannot change without a rewrite, the PR is squash-merged: give the new commit a 'fix:' subject); (2) text: normalise the PR body to the upstream template: the checklist lines verbatim and in template order, all items present, ticks only when true, explanations as plain notes (no checkboxes), the stale 'In game on this commit' claim restated to the commit the in-game run was at (513144d3d; production code identical since), the attribution line last; (3) the accuracy spec's Tests section still describes the dropped StileScriptTest: remove it; (4) read AGENTS.md and CONTRIBUTING and self-check the whole net diff, run spotlessCheck on the touched module. Fork pushes (fix/stile-approach, fork docs) need no approval; the live PR #406 body and the push onto the PR head go through the user's approval card afterwards. Do NOT touch upstream. The normaliser used for the other bodies: /home/alex/.claude/jobs/24c56aeb/tmp/normalise.py with the template at /home/alex/.claude/jobs/24c56aeb/tmp/template.md (copy them into your clone dir; they are in /home/alex/.claude/jobs/24c56aeb/tmp/).
- 2026-10-25T00:33:04Z hold failed: fix first (user 2026-10-24): style (KDoc growth) and text (checklist, stale in-game claim)
- 2026-10-25T00:33:04Z run sd79 started (server-dev, stage dev)
- 2026-10-25T00:34:37Z contribute -> gate: hand-over recorded
- 2026-10-25T00:34:37Z hold failed cleared: handed over (BR-S3)
- 2026-10-25T00:34:37Z handover fix/stile-approach@caacbf4ce: caacbf4ce restores StileScript.kt class KDoc to main's text (fix: commit on 68ddd1b6c, fast-forward); PR body normalised (template checklist verbatim, notes plain, in-game claim restated to 513144d3d) in fork docs 7ec42523c; accuracy Tests section removed; spotlessCheck generic-locs PASS
- 2026-10-25T00:34:52Z run sd79 ended: ? turns, ? tokens, exit ok
- 2026-10-25T00:34:52Z run sq58 started (server-qa, stage gate)
