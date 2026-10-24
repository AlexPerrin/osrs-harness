---
slug: hunter-split-ship
track: server
title: 'Hunter: split the 7 fin/hunter-* branches and ship each'
prio: P2
role: server-dev
stage: ready
hold:
  kind: blocked
  reason: waiting for cannon-review-354, genie-review-355, goblin-diplomacy-review-367, witchs-potion-review-368
  since: '2026-10-24T19:46:29Z'
deps:
- cannon-review-354
- genie-review-355
- goblin-diplomacy-review-367
- witchs-potion-review-368
branch: null
commit: null
local_only: false
owner: null
instances:
- desktop
cost:
  runs: 1
  turns: 10
  minutes: 1.9
  usd: 15.47
created: '2026-10-20T01:42:41Z'
updated: '2026-10-24T19:46:29Z'
---
## Change
7 fin/hunter-* branches (local only, re/upstream-pr/dev-hunter): linearise rumours (the older linear rumours are archived as refs/archive/sd22/fin-hunter-rumours dcf92ca13 in re/upstream-pr/or), gate each, write texts; integration still uses fin/hunter.

## Definition of done
- [ ] 7 branches each off upstream main alone, pushed to the fork, with PR text
- [ ] integration.txt uses the split branches instead of fin/hunter
- [ ] internal gate PASS per branch
- [ ] accuracy/hunter-split-ship.md on the fork's docs branch (wiki/cache baseline per rule, RSProx comparison recorded)
- [ ] fork PR open with green CI at the handed-over commit
- [ ] one change only, branch off upstream main (no stacking)

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: hunter-split-ship
- 2026-10-22T00:01:06Z ready -> dev: dispatched to sd32
- 2026-10-22T00:01:06Z run sd32 started (server-dev, stage dev, instances desktop)
- 2026-10-22T00:08:50Z 7 branches content/hunter-{module,traps,bird-houses,butterflies,herbiboar,implings,rumours} rebuilt off upstream main e85278c9a (rumours linear: module>traps>herbiboar>butterflies>rumours; herbiboar dbrows on 63874-63891 as in fin/hunter a4a74b5a9), gameval --check clean on all 7, pushed to the fork, CI dispatched. Upstream check: no hunter content upstream (#63 open, #196/#229 closed unreviewed; a-thoren on #353 wants one PR per row). Note: a Bash hook denied reading tools/harness/integrate.py (pattern match), not worked around.
- 2026-10-22T00:15:20Z spec committed: accuracy/hunter-split-ship.md (RSProx 1106/350: trap timings compared, failing->broken fixed to 1 tick on content/hunter-traps 1cd2300ed, rumours rebuilt fddf38117); 7 PR texts in pr-texts/hunter-*.upstream.body
- 2026-10-22T02:16:31Z branch fix/<slug> (grooming)
- 2026-10-22T02:16:54Z no single branch: the hand-over names the split content/hunter-* branches (grooming)
- 2026-10-22T02:28:58Z run sd32 ended: 10 turns, 1.9 min, $15.47, exit ok
- 2026-10-22T02:28:58Z dev -> ready: run sd32 ended without a hand-over
- 2026-10-24T19:32:22Z 2026-10-24 reset (user): settle the existing upstream PRs (#354 #355 #367 #368) before opening new ones; depends on their review fixes, P2
- 2026-10-24T19:46:29Z hold blocked: waiting for cannon-review-354, genie-review-355, goblin-diplomacy-review-367, witchs-potion-review-368
