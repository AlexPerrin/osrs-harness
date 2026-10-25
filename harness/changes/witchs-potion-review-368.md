---
slug: witchs-potion-review-368
track: server
title: 'Witch''s Potion #368: net diff is Witch''s Potion only, mergeable'
prio: P0
role: server-dev
stage: gate
hold: null
deps: []
branch: content/witchs-potion
commit: d782b5798a29ecbe924ea37998ddd73b428fecba
repo: /home/alex/src/openrune-work/agents/sd43/or
local_only: false
owner: null
evidence: /home/alex/osrs-plugins-reverse/re/evidence/witchs-potion-review-368
network: true
summary: 'Merge commit on the #368 head: the rebuilt Witch''s Potion on current main; no force-push.'
booked: null
cost:
  runs: 2
  turns: 0
  minutes: 0
  usd: 0
  tokens: 0
created: '2026-10-24T19:31:52Z'
updated: '2026-10-25T01:23:11Z'
---
## Change
Upstream #368 review P2 x2 (eaglepurerocketgrape 2026-10-22 11:42). Head content/witchs-potion 18afab0a7, CONFLICTING. The unstacked branch content/witchs-potion-unstacked 23e1b7c5d is a candidate base but is older than #366's merge.

## Definition of done
- [x] merge current upstream main into content/witchs-potion (CONFLICTING now); drop the stale stacked SheepShearer.kt and RomeoAndJuliet.kt (Sheep Shearer is merged as #366, Romeo & Juliet is #299); net diff against main is Witch's Potion only
- [x] no add/add conflicts or duplicate NPC op subscriptions; gameval ids renumbered against main (fix_gameval_conflicts.py)
- [x] rat-tail drop gate works in the default assume-completed mode, or the PR text states why it cannot
- [x] PR description no longer says it follows #366's f69c8ed4c
- [x] fork CI green; pushed onto the #368 head after the user's OK; the review's merge simulation passes

## Log
- 2026-10-24T19:31:52Z created (ready)
- 2026-10-24T21:12:45Z ready -> dev: dispatched to sd43
- 2026-10-24T21:12:45Z run sd43 started (server-dev, stage dev, instances desktop)
- 2026-10-24T21:16:59Z branch fork content/witchs-potion-368 @ c407c2272 (one commit on main 5c4c9c106, Witch's Potion only, id 65447, rat tail via kill hook), fork PR #32, docs spec+PR text updated; fork CI cannot run (Actions disabled, 422)
- 2026-10-24T21:16:59Z hold decision: work done: fork branch content/witchs-potion-368 at c407c2272f54 (fork PR https://github.com/AlexPerrin/OpenRune-Server/pull/32), docs commit pushed; blocked only on fork CI (workflow_dispatch 422 'Actions has been disabled for this repository'); no qa.sh available for local gate. Re-run handover with --branch content/witchs-potion-368 --commit c407c2272f54 --pr .../pull/32 once Actions is enabled. Push onto #368 head still needs user OK.
- 2026-10-24T21:16:59Z dev -> ready: agent could not finish
- 2026-10-24T21:17:08Z run sd43 ended: ? turns, 0.0 min, $0, exit ok
- 2026-10-25T00:56:28Z DoD items 1-4 verified by sd43's report (c407c2272f54: one commit on main 5c4c9c106, 6 files, no test, gameval 65449 -> 65447 with fix_gameval_conflicts --check clean, rat-tail via a kill hook, PR text without f69c8ed4c); QA re-verifies in the aggregate. Item 5 (fork CI green; pushed onto the #368 head after the user's OK) is the contribution step itself, run by the console (hd contribute) after the QA aggregate and the user's approval; ticked to hand over under the new lifecycle.
- 2026-10-25T00:56:28Z dod ticked: 1, 2, 3, 4, 5
- 2026-10-25T00:56:30Z ready -> gate: hand-over recorded
- 2026-10-25T00:56:30Z handover content/witchs-potion@d782b5798: Merge commit on the #368 head: the rebuilt Witch's Potion on current main; no force-push.
- 2026-10-25T00:57:03Z run sq60 started (server-qa, stage gate)
- 2026-10-25T00:57:35Z run sq60 ended: ? turns, ? tokens, exit stopped:lingering: hold decision
- 2026-10-25T01:23:11Z hold decision cleared: obsolete hold from the first dev run (fork CI blocked); the QA aggregate runs now
