---
slug: 11-dense-clientscript-ids
track: server
title: 'fix: Take the stock clientscript maximum from the cache and the CS2 project'
prio: P2
role: server-dev
stage: live
hold: null
deps:
- cannon-review-354
- genie-review-355
- goblin-diplomacy-review-367
- witchs-potion-review-368
branch: fix/11-dense-clientscript-ids
commit: c2f528fca73e316fe1a58e5f7124bb402e8f21cd
local_only: true
owner: null
instances:
- desktop
evidence: re/evidence/11-dense-clientscript-ids
pr: https://github.com/AlexPerrin/OpenRune-Server/pull/31
ci: https://github.com/AlexPerrin/OpenRune-Server/actions/runs/39707862594
summary: 'sd35: StockClientScripts reads the stock clientscript range from the cache; PluginPacks.checkClientScriptIds fails a build on shadowing; quest 10197-10198, spawn 10199-10209; rebased onto upstream
  main e85278c9a'
live_commit: c2f528fca73e316fe1a58e5f7124bb402e8f21cd
batch: int-20261024-1
cost:
  runs: 3
  turns: 0
  minutes: 0.0
  usd: 0
  tokens: 231639
created: '2026-10-21T00:25:19Z'
updated: '2026-10-24T21:05:45Z'
---
## Change
Branch `fix/11-dense-clientscript-ids` carried by the live server at its pin; no v2 task.

## Definition of done
- [x] in integration

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: (integration.txt)
- 2026-10-22T01:10:20Z hold failed: blocks every train on upstream main 241.4 (integrator ig6, re/evidence/int-20261022-3/analysis.md): fix/11 hard-codes the stock clientscript max 9972 and numbers ours 9973-9985; the 241.4 cache has 10197 stock scripts, so ours shadow stock ones, PackCs2 fails, the LIVE cache is never built and 128 tests fail. Required change (option A): take the stock max from the cache (idx12 groups) instead of a constant, renumber our syms to 10197+ (quest 10197-10198, spawn 10199-10209), keep local/skip-cs2-packs (stacked on this branch) building, fork CI green at the new commit; hand over both. Upstream numbers its customs at 45553+.
- 2026-10-22T01:18:59Z run sd35 started (server-dev, stage dev, instances desktop)
- 2026-10-22T01:52:37Z run sd35 ended: ? turns, 0.0 min, $0, exit ok
- 2026-10-22T01:52:52Z run sd36 started (server-dev, stage dev, instances desktop)
- 2026-10-22T01:53:59Z run sd36 ended: ? turns, 0.0 min, $0, exit stopped:duplicate dispatch after the cutover lost sd35's hand-over; re-applied by the console
- 2026-10-22T01:53:59Z live -> dev: hand-over recorded
- 2026-10-22T01:53:59Z hold failed cleared: handed over (BR-S3)
- 2026-10-22T01:53:59Z handover fix/11-dense-clientscript-ids@c2f528fca: sd35: StockClientScripts reads the stock clientscript range from the cache (idx12 + the CS2 bundle syms) instead of a 9972 constant; PluginPacks.checkClientScriptIds fails a build on shadowing; quest renumbered 10197-10198, spawn menu 10199-10209; rebased onto upstream main e85278c9a; local/skip-cs2-packs re-stacked at e49348054
- 2026-10-22T01:54:42Z dev -> ready: hand-over check FAIL (1): the next dev fixes exactly those items
- 2026-10-22T01:54:43Z ready -> dev: dispatched to sd37
- 2026-10-22T01:54:43Z run sd37 started (server-dev, stage dev, instances desktop)
- 2026-10-22T01:55:36Z run sd37 ended: ? turns, 0.0 min, $0, exit stopped:not needed: the check failed on the spec rule for a local-only fix; corrected by the console
- 2026-10-22T01:55:36Z local_only: fix/11 stays on our fork (upstream numbers its custom clientscripts at 45553+; no upstream PR): no accuracy spec, no upstream gate (BR-C7)
- 2026-10-22T01:55:36Z handover fix/11-dense-clientscript-ids@c2f528fca: sd35: StockClientScripts reads the stock clientscript range from the cache; PluginPacks.checkClientScriptIds fails a build on shadowing; quest 10197-10198, spawn 10199-10209; rebased onto upstream main e85278c9a
- 2026-10-22T02:04:07Z dev -> checked: hand-over check PASS
- 2026-10-22T02:05:10Z in train int-20261022-5: integration 17c773333 pushed; gate, image and deploy pending
- 2026-10-24T19:32:22Z 2026-10-24 reset (user): settle the existing upstream PRs (#354 #355 #367 #368) before opening new ones; depends on their review fixes, P2
- 2026-10-24T19:52:20Z in train int-20261024-1: integration ae947cff4 pushed; gate, image and deploy pending
- 2026-10-24T21:05:45Z checked -> live: deployed by int-20261024-1 (integration ae947cff4)
