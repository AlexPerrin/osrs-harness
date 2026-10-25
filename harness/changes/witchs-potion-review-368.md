---
slug: witchs-potion-review-368
track: server
title: 'Witch''s Potion #368: net diff is Witch''s Potion only, mergeable'
prio: P0
role: server-dev
stage: review
hold: null
deps: []
branch: content/witchs-potion
commit: 74048def774aabf7f96544f765819f9d1fb3d827
repo: /home/alex/src/openrune-work/agents/sd43/or
local_only: false
owner: null
evidence: /home/alex/osrs-plugins-reverse/re/evidence/witchs-potion-review-368
network: true
summary: 'Five QA fixes: comment removed (fixed tip 569393171 on fork fix/witchs-potion-clean), merge commit with fix: subject, template-verbatim bodies without history, fresh status comment, quest tests
  and spotless pass'
booked:
  gate: 74048def774aabf7f96544f765819f9d1fb3d827
batch: int-20261025-5
cost:
  runs: 5
  turns: 0
  minutes: 0
  usd: 0
  tokens: 0
created: '2026-10-24T19:31:52Z'
updated: '2026-10-25T03:25:42Z'
review_seen: '2026-10-25T02:34:27Z'
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
- 2026-10-25T01:39:49Z QA aggregate FAIL at d782b5798 (6 finding(s)): 6 findings: added comment; PR text checklist not verbatim and revision wording; stale live #368 body and update comment; history/merge subject. CI+format green, in game PASS
- 2026-10-25T01:40:20Z gate -> contribute: observed
- 2026-10-25T01:43:25Z QA AGGREGATE (sq60, 2026-10-24) at the merge commit d782b5798 (rebuilt c407c2272f54 on #368 head 18afab0a7): behaviour PASS (CI 40148714790 + Formatting 40148804289 green on gate/witchs-potion-review-368, scope = exactly 6 files, fix_gameval_conflicts clean at 65447, in game end to end on a fresh account: offer/decline/accept, partial and full hand-in, cauldron, 1 QP, Magic XP, the rat tail drops at stage 1 and not after the quest). FINDINGS TO FIX (user: apply now): (1) style: an added comment above WitchsPotionRatTail in WitchsPotion.kt ('A kill hook, not a quest-gated drop...'): remove it (AGENTS.md: comments less is more); (2) text: the PR text checklist is not the template's verbatim (lines 2, 3, 5 have explanations; two unticked with justification inside the line): rebuild both bodies with /home/alex/.claude/jobs/24c56aeb/tmp/normalise.py and the template /home/alex/.claude/jobs/24c56aeb/tmp/template.md, explanations as plain notes with no checkboxes; (3) the PR text and the .comment contain revision history ('63718 and 65449 in earlier versions', 'the earlier version's dialogue tests... as with #366', the 'impossible to finish' rationale; the comment file is entirely change history) and stale facts (main 829b9477d, the id 65449 / clash with #366, f69c8ed4c): rewrite so the body states what the PR does (current main, id 65447, no stacked content) with no history; write a fresh short status comment file for the contribution (what changed in this push, what is verified) with the hidden marker not needed (hd contribute adds it); (4) the live #368 body is still the old stacked text: provide the replacement body as pr-texts/witchs-potion.upstream.body (the console posts it with the user's approval); (5) commit subjects must be feat:/fix: for the tip and the merge commit (the merge subject must claim only what is true); rebuild the contribution merge commit (tree = the fixed tip, parents = #368 head 18afab0a7 and the fixed tip; fast-forward, no force-push) in /home/alex/src/openrune-work/agents/sd43/or and point local content/witchs-potion at it; (6) observation only: RATS/INGREDIENTS are Kotlin lists (AGENTS.md discourages game data in Kotlin): keep them, the PR text discloses the rat list. Run only the quest module's tests and spotlessCheck (the full suite is the fork CI). Fork pushes need no approval; NEVER push content/witchs-potion or anything upstream; never edit the live #368 body or comment.
- 2026-10-25T01:43:26Z run sd83 started (server-dev, stage dev)
- 2026-10-25T01:52:12Z contribute -> gate: hand-over recorded
- 2026-10-25T01:52:12Z handover content/witchs-potion@74048def7: Five QA fixes: comment removed (fixed tip 569393171 on fork fix/witchs-potion-clean), merge commit with fix: subject, template-verbatim bodies without history, fresh status comment, quest tests and spotless pass
- 2026-10-25T01:52:25Z run sd83 ended: ? turns, ? tokens, exit ok
- 2026-10-25T01:52:25Z run sq63 started (server-qa, stage gate)
- 2026-10-25T02:04:01Z run sq63 ended: ? turns, ? tokens, exit ok
- 2026-10-25T02:04:11Z hold decision: needs you: a gate run was already booked for exactly this head (74048def7) and these findings; booking another would repeat it
- 2026-10-25T02:08:06Z hold decision cleared: re-run the aggregate (user 2026-10-24: re-run both)
- 2026-10-25T02:08:06Z run sq65 started (server-qa, stage gate)
- 2026-10-25T02:20:06Z QA aggregate PASS at 74048def7 (0 finding(s)): no findings: comment removed, bodies template-verbatim, CI 40152325198 + Formatting green, quest tests 219 pass
- 2026-10-25T02:20:26Z gate -> contribute: observed
- 2026-10-25T02:20:28Z run sq65 ended: ? turns, ? tokens, exit stopped:lingering: change at contribute
- 2026-10-25T02:34:24Z contribute -> review: observed
- 2026-10-25T03:25:42Z in train int-20261025-5: integration 442b396d2 pushed; gate, image and deploy pending
