---
slug: ground-item-despawn-times
track: server
title: Ground item despawn times (OSRS Drop rules)
prio: P2
role: server-dev
stage: dev
hold: null
deps:
- cannon-review-354
- genie-review-355
- goblin-diplomacy-review-367
- witchs-potion-review-368
branch: fix/ground-item-despawn-times
commit: 7e3e0dc2bdaf04cbaca30dfc4fe4d9f4d5812e3f
local_only: false
owner: sd86
evidence: /home/alex/osrs-plugins-reverse/re/evidence/ground-item-despawn-times
spec: ground-item-despawn-times
summary: spotlessApply on the touched modules (ObjRepository import order, Obj.kt blank line and HeldInteractions elvis spacing are all required by spotless); spotlessCheck clean on api:game-process, api:player,
  api:registry, api:repo, engine:game; no test file in net diff; spec Tests section updated on docs
live_commit: d0fe09c630e7456433348ee273f3e9cd8353cc82
booked:
  dev: 7e3e0dc2bdaf04cbaca30dfc4fe4d9f4d5812e3f|da39a3ee5e6b
batch: int-20261024-1
cost:
  runs: 19
  turns: 88
  minutes: 40.2
  usd: 7.78
  tokens: 0
created: '2026-10-20T01:42:40Z'
updated: '2026-10-25T04:06:14Z'
---
## Change
Every player drop currently despawns after 200 ticks (constants.lootdrop_duration). Match OSRS Wiki 'Drop': tradeables become public after 60 s and despawn after a further 120 s (300 ticks total); untradeables 180 s; clue scrolls 61 min. Repro: ::item 10180 1, drop, gone 115 s later. Unblocks client: Clue Juggling Timers, Ground Items despawn (gen 44, scratchpad/g44/).

Ground items: keep the owner when an obj is copied (ObjRegistry.singleCopy, ZoneUpdateTransformer.copy)

## Definition of done
- [x] Drop of a tradeable on the test server becomes public after 100 ticks and despawns after 300 ticks
- [x] Drop of an untradeable despawns after 300 ticks (180 s); a dropped clue scroll stays 61 min
- [x] Unblocks client task hub-ground-items-despawn (the client dev verifies it there after the deploy)
- [x] accuracy/ground-item-despawn-times.md on the fork's docs branch (wiki/cache baseline per rule, RSProx comparison recorded)
- [x] fork PR open with green CI at the handed-over commit
- [x] one change only, branch off upstream main (no stacking)
- [x] on fix/ground-item-despawn-times (same branch as fork PR #23, a new commit, no new branch): pass ownerId as the 5th Obj(...) argument in ObjRegistry.singleCopy and ZoneUpdateTransformer.copy; a unit test; fork CI green
- [x] sd28's spec (accuracy/ground-item-despawn-times.md) no longer lists the copy-owner bug as open

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: ground-item-despawn-times, despawn-copy-owner-id
- 2026-10-21T00:25:19Z hold failed: further work on the branch (despawn-copy-owner-id): Ground items: keep the owner when an obj is copied (ObjRegistry.singleCopy, ZoneUpdateTransformer.copy) (a new commit re-enters at dev)
- 2026-10-22T00:01:06Z run sd31 started (server-dev, stage dev, instances desktop)
- 2026-10-22T00:06:38Z run sd31 ended: ? turns, 0.0 min, $0, exit stopped:lingering: change at live for 6 min
- 2026-10-22T00:07:37Z run sd33 started (server-dev, stage dev, instances desktop)
- 2026-10-22T00:26:43Z live -> ready: branch moved to a704e582b past 8bc126d49: hand over again (BR-C2)
- 2026-10-22T00:26:49Z run sd33 ended: 32 turns, 6.5 min, $2.81, exit stopped:lingering: owner is None (change at ready)
- 2026-10-22T00:27:42Z ready -> dev: dispatched to sd34
- 2026-10-22T00:27:42Z run sd34 started (server-dev, stage dev, instances desktop)
- 2026-10-22T00:42:34Z sd34: rebased the 4 commits onto upstream main e85278c9a (241), identical patches, head d0fe09c63 pushed to PR #23; CI at a704e582b/d0fe09c63 failed in or-cache:buildCache from this branch's stale 240 actions-cache entry (key unchanged by the 241 bump); deleted entry 9200352329, CI re-dispatched; filed ci-game-cache-key
- 2026-10-22T00:59:28Z hold failed cleared: handed over (BR-S3)
- 2026-10-22T00:59:28Z handover fix/ground-item-despawn-times@d0fe09c63: sd33's 4th commit (ObjRegistry.singleCopy and ZoneUpdateTransformer.copy pass ownerId; ObjRegistrySplitOwnerTest + ObjAddTimersTest) is on the branch; sd34 rebased the 4 commits onto upstream main e85278c9a (241) with identical patches, head d0fe09c63 on fork PR #23, CI green. The two CI failures before that were this branch's pre-241 game-data actions cache (key hashes only game.example.yml): entry deleted, bug filed as ci-game-cache-key. Spec, PR text and STATE.md on fork docs (696f55e2f); spec no longer lists the copy-owner bug as open.
- 2026-10-22T01:00:02Z run sd34 ended: 56 turns, 33.7 min, $4.97, exit ok
- 2026-10-22T01:00:03Z dev -> checked: hand-over check PASS
- 2026-10-22T01:10:43Z in train int-20261022-4: integration 749d6dd58 pushed; gate, image and deploy pending
- 2026-10-22T02:05:10Z in train int-20261022-5: integration 17c773333 pushed; gate, image and deploy pending
- 2026-10-24T19:32:22Z 2026-10-24 reset (user): settle the existing upstream PRs (#354 #355 #367 #368) before opening new ones; depends on their review fixes, P2
- 2026-10-24T19:52:20Z in train int-20261024-1: integration ae947cff4 pushed; gate, image and deploy pending
- 2026-10-24T21:05:45Z checked -> live: deployed by int-20261024-1 (integration ae947cff4)
- 2026-10-24T21:08:40Z run sq34 started (server-qa, stage gate, instances desktop)
- 2026-10-24T21:08:40Z run sq34 ended: ? turns, 0.0 min, $0, exit stopped:lingering: batch at live
- 2026-10-24T21:09:49Z run sq35 started (server-qa, stage gate, instances desktop)
- 2026-10-24T21:09:49Z run sq35 ended: ? turns, 0.0 min, $0, exit stopped:lingering: batch at live
- 2026-10-24T21:12:45Z run sq36 started (server-qa, stage gate, instances desktop)
- 2026-10-24T21:12:45Z run sq36 ended: ? turns, 0.0 min, $0, exit stopped:lingering: batch at live
- 2026-10-24T21:13:52Z run sq37 started (server-qa, stage gate, instances desktop)
- 2026-10-24T21:13:52Z run sq37 ended: ? turns, 0.0 min, $0, exit stopped:lingering: batch at live
- 2026-10-24T21:14:58Z run sq38 started (server-qa, stage gate, instances desktop)
- 2026-10-24T21:14:58Z run sq38 ended: ? turns, 0.0 min, $0, exit stopped:lingering: batch at live
- 2026-10-24T21:16:04Z run sq39 started (server-qa, stage gate, instances desktop)
- 2026-10-24T21:16:04Z run sq39 ended: ? turns, 0.0 min, $0, exit stopped:lingering: batch at live
- 2026-10-24T21:17:10Z run sq40 started (server-qa, stage gate, instances desktop)
- 2026-10-24T21:17:10Z run sq40 ended: ? turns, 0.0 min, $0, exit stopped:lingering: batch at live
- 2026-10-24T21:18:17Z run sq41 started (server-qa, stage gate, instances desktop)
- 2026-10-24T21:18:17Z run sq41 ended: ? turns, 0.0 min, $0, exit stopped:lingering: batch at live
- 2026-10-24T21:19:23Z run sq42 started (server-qa, stage gate, instances desktop)
- 2026-10-24T21:19:23Z run sq42 ended: ? turns, 0.0 min, $0, exit stopped:lingering: batch at live
- 2026-10-24T21:20:32Z run sq43 started (server-qa, stage gate, instances desktop)
- 2026-10-24T21:20:32Z run sq43 ended: ? turns, 0.0 min, $0, exit stopped:lingering: batch at live
- 2026-10-24T21:21:39Z run sq44 started (server-qa, stage gate, instances desktop)
- 2026-10-24T21:21:39Z run sq44 ended: ? turns, 0.0 min, $0, exit stopped:lingering: batch at live
- 2026-10-24T21:21:58Z run sq45 started (server-qa, stage gate, instances desktop)
- 2026-10-24T21:51:57Z gate PASS claimed: upstream gate PASS at d0fe09c63: branch server OBJ_ADD timers 100/300, 300 never public, clue 6100; despawn +299; CI green (the record on docs is what counts)
- 2026-10-24T21:52:06Z run sq45 ended: ? turns, ? tokens, exit ok
- 2026-10-24T21:52:53Z live -> gated: observed
- 2026-10-24T21:54:50Z hold failed: further work on the branch: drop the three added test files and fix the PR text (user: too many tests); a new commit re-enters at dev
- 2026-10-24T21:55:21Z USER INSTRUCTION 2026-10-24 (supersedes the unit-test DoD items above: too many tests in upstream PRs). Do on fix/ground-item-despawn-times as a NEW commit, no force-push: (1) remove PlayerDropTimersTest, ObjRegistrySplitOwnerTest and ObjAddTimersTest and the build.gradle.kts test dependency they added in api/registry, so the diff against upstream main has no test file; (2) PR text on the fork docs branch: 'Two gaps' vs three bullets fixed, drop the three test bullets and the 'Tests only cover complex logic' tick under 'How it was tested' (keep the in-game result), remove the whitespace-only hunks; (3) hand over the new commit; server-qa re-gates it (the gate at d0fe09c63 no longer applies). Do not push to any OpenRune branch.
- 2026-10-24T22:41:35Z run sd68 started (server-dev, stage dev, instances desktop)
- 2026-10-24T22:42:54Z gated -> dev: hand-over recorded
- 2026-10-24T22:42:54Z hold failed cleared: handed over (BR-S3)
- 2026-10-24T22:42:54Z handover fix/ground-item-despawn-times@83a64ba7e: Local commit on top of d0fe09c63: removes PlayerDropTimersTest, ObjRegistrySplitOwnerTest, ObjAddTimersTest and the api/registry test dependency, reverts a whitespace-only hunk in HeldInteractions; diff vs upstream/main has no test file. PR text fixed in local docs commit (not pushed). Nothing pushed.
- 2026-10-24T22:43:30Z hold blocked: waiting for cannon-review-354, genie-review-355, goblin-diplomacy-review-367, witchs-potion-review-368
- 2026-10-24T22:43:31Z dev -> ready: hand-over check FAIL (2): the next dev fixes exactly those items
- 2026-10-24T22:52:19Z run sq48 started (server-qa, stage gate, instances desktop)
- 2026-10-24T22:52:21Z run sq48 ended: ? turns, ? tokens, exit stopped:lingering: change at ready
- 2026-10-24T22:53:45Z hold failed: scope: remove the Obj.kt blank-line removal (whitespace-only) and the ObjRepository import move from the net diff; push 83a64ba7e-successor to fix/ground-item-despawn-times (fork branch still at d0fe09c63)
- 2026-10-24T22:54:07Z GATE FAIL (sq48, 2026-10-24) at 83a64ba7e on scope: two hunks outside the change: (1) engine/game/src/main/kotlin/org/rsmod/game/obj/Obj.kt removes a blank line between the two fromOwner functions; (2) api/repo/src/main/kotlin/org/rsmod/api/repo/obj/ObjRepository.kt moves import java.util.concurrent.ConcurrentLinkedQueue to the top of the import block. Revert both (git checkout the merge-base version of those hunks only); net diff vs merge base must be only the change, no test files. Commit in /home/alex/src/openrune-work/agents/sd68/or (new commit, no force), push to the FORK branch fix/ground-item-despawn-times (no upstream PR backs it; fork push needs no approval) and the PR text commit cc24ebd8c to the fork docs branch; then hand over for the next gate (which runs CI on a scratch branch merged with main).
- 2026-10-24T22:54:07Z hold failed cleared: dev fix after gate FAIL
- 2026-10-24T22:54:07Z ready -> dev: dispatched to sd71
- 2026-10-24T22:54:07Z run sd71 started (server-dev, stage dev, instances desktop)
- 2026-10-24T22:54:34Z hold blocked: waiting for cannon-review-354, genie-review-355, goblin-diplomacy-review-367, witchs-potion-review-368
- 2026-10-24T22:54:35Z dev -> ready: hand-over check FAIL (2): the next dev fixes exactly those items
- 2026-10-24T22:54:35Z run sd71 ended: ? turns, ? tokens, exit stopped:lingering: owner is None (change at ready)
- 2026-10-24T22:54:40Z ready -> dev: hand-over recorded
- 2026-10-24T22:54:40Z hold blocked cleared: handed over (BR-S3)
- 2026-10-24T22:54:40Z handover fix/ground-item-despawn-times@5ae6a3aeb: Reverted stray Obj.kt blank-line and ObjRepository.kt import-reorder hunks; net diff vs merge base has no tests and no whitespace/import-only hunks
- 2026-10-24T22:54:59Z run sq49 started (server-qa, stage gate, instances desktop)
- 2026-10-24T22:55:40Z hold blocked: waiting for cannon-review-354, genie-review-355, goblin-diplomacy-review-367, witchs-potion-review-368
- 2026-10-24T22:55:40Z run sq49 ended: ? turns, ? tokens, exit stopped:lingering: change at dev
- 2026-10-24T23:06:03Z dev -> checked: hand-over check PASS
- 2026-10-24T23:18:03Z hold failed: spotless: ObjRepository.kt import java.util.concurrent.ConcurrentLinkedQueue must stay in sorted position (the 'stray' import hunk is required by Formatting; spotlessCheck fails at 5ae6a3aeb). Keep it, run spotlessApply, re-hand over. Obj.kt blank-line revert is fine. Record qa/ground-item-despawn-times.md on docs.
- 2026-10-24T23:18:30Z GATE FAIL (sq49, 2026-10-24) at 5ae6a3aeb: spotlessCheck (:api:repo:spotlessKotlinCheck) fails on api/repo/src/main/kotlin/org/rsmod/api/repo/obj/ObjRepository.kt: 'import java.util.concurrent.ConcurrentLinkedQueue' must sit in sorted position, after 'jakarta.inject.Inject'. sq48 called that import move stray: it is NOT stray, ObjRepository.kt is touched by the change so the spotless ratchet checks it; reverting it broke Formatting (green at d0fe09c63). FIX: new commit that restores the sorted import position (run :api:repo:spotlessApply, then spotlessCheck on every touched module and keep the result); keep the Obj.kt blank-line revert (spotless does not flag Obj.kt); net diff vs merge base still has no test file. Also update the accuracy spec's Tests section on fork docs (it still names the removed tests). Other checks passed (accuracy vs wiki Drop page, local gate: compile/cache/buildCache/assemble ok, 790 tests + 110 integration, 0 failures, merged cleanly with upstream main 5c4c9c106). In-game: sq45's result at d0fe09c63 still applies (code unchanged except tests). Run spotlessCheck yourself before hand-over (the gate runs it). Fork pushes: fix/ground-item-despawn-times and fork docs only.
- 2026-10-24T23:18:30Z hold failed cleared: dev fix #3
- 2026-10-24T23:18:30Z run sd77 started (server-dev, stage dev)
- 2026-10-24T23:20:49Z checked -> dev: hand-over recorded
- 2026-10-24T23:20:49Z handover fix/ground-item-despawn-times@7e3e0dc2b: spotlessApply on the touched modules (ObjRepository import order, Obj.kt blank line and HeldInteractions elvis spacing are all required by spotless); spotlessCheck clean on api:game-process, api:player, api:registry, api:repo, engine:game; no test file in net diff; spec Tests section updated on docs
- 2026-10-24T23:21:29Z hold blocked: waiting for cannon-review-354, genie-review-355, goblin-diplomacy-review-367, witchs-potion-review-368
- 2026-10-24T23:21:30Z dev -> ready: hand-over check FAIL (1): the next dev fixes exactly those items
- 2026-10-24T23:23:35Z run sq54 started (server-qa, stage gate)
- 2026-10-24T23:23:42Z run sq54 ended: ? turns, ? tokens, exit stopped:lingering: change at ready
- 2026-10-24T23:39:38Z gate PASS claimed: 7e3e0dc2b: CI+Formatting green on merge, spotless clean, 8 files (the record on docs is what counts)
- 2026-10-25T04:06:14Z ready -> dev: dispatched to sd86
- 2026-10-25T04:06:14Z run sd86 started (server-dev, stage dev)
