---
slug: cannon-review-354
track: server
title: 'Cannon #354: address maintainer review'
prio: P0
role: server-dev
stage: dev
hold: null
deps: []
branch: fix/cannon-drop-tests
commit: 0df5c63a009b75fffb33f8ead897b432f55fcead
local_only: false
owner: sd80
evidence: /home/alex/osrs-plugins-reverse/re/evidence/cannon-review-354
network: true
summary: 'Drop #354''s tests: new commit on 60cffedfb on fork staging fix/cannon-drop-tests; PR text and accuracy/cannon.md updated on docs'
booked:
  dev: 0df5c63a009b75fffb33f8ead897b432f55fcead|da39a3ee5e6b
cost:
  runs: 9
  turns: 0
  minutes: 0
  usd: 0
  tokens: 0
created: '2026-10-24T19:31:52Z'
updated: '2026-10-25T00:37:54Z'
---
## Change
Upstream #354 is CHANGES_REQUESTED (Mark7625 2026-10-22 07:57, eaglepurerocketgrape 11:42). Head content/cannon 9c08b42ca. Supersedes the BR-C1 fold decision on `cannon`: the fix goes on the PR head itself.

## Definition of done
- [x] Mark7625 inline: replace the `while` loop in DwarfMulticannon.kt (no while functions)
- [x] eaglepurerocketgrape P1: replaceLostCannon (Nulodion.kt 235-250) returns only the parts matching the saved assembly stage (varp.dropcannon), not CANNON_SET.take(4); test reclaim after partial assembly and after a full cannon
- [x] fork CI green; update pushed onto the #354 head content/cannon as a merge/new commit, no force-push, after the user's OK
- [x] reply on #354 listing each fix (after the user's OK)

## Log
- 2026-10-24T19:31:52Z created (ready)
- 2026-10-24T20:09:15Z ready -> dev: dispatched to sd40
- 2026-10-24T20:09:15Z run sd40 started (server-dev, stage dev, instances desktop)
- 2026-10-24T21:10:05Z run sd40 ended: ? turns, 0.0 min, $0, exit cancelled
- 2026-10-24T21:12:45Z dev -> ready: run sd40 ended without a hand-over
- 2026-10-24T21:17:10Z ready -> dev: dispatched to sd44
- 2026-10-24T21:17:10Z run sd44 started (server-dev, stage dev, instances desktop)
- 2026-10-24T21:36:09Z hold decision: code done, not verifiable: commit a2202478b on fork branch fix/cannon-review-354 (fork PR #33; clone ~/src/openrune-work/agents/sd44/or, based on #354 head 9c08b42ca): buildStages while -> repeat; replaceLostCannon returns CANNON_SET.take(4).take(varp.dropcannon) (+ free-space check by stage) with a partial-assembly test. Fork Actions disabled (no CI run), and local qa gate/dev fail in :or-cache:freshCache on cs2 SYNTAX_ERROR in [proc,cr_quests_ui_create_entry].cs2:195 (env cs2 sources, not this change), so modules cannot compile/test. Needs Actions fixed or cache env fixed, then push to content/cannon after user OK + #354 reply.
- 2026-10-24T21:36:09Z dev -> ready: agent could not finish
- 2026-10-24T21:36:20Z run sd44 ended: ? turns, 0.0 min, $0, exit ok
- 2026-10-24T22:47:57Z run sq46 started (server-qa, stage gate, instances desktop)
- 2026-10-24T22:48:36Z run sq46 ended: ? turns, ? tokens, exit stopped:lingering: change at ready
- 2026-10-24T23:10:06Z hold failed: PR #354 body stale vs the review fix: Nulodion now returns parts by saved stage and checks that many free slots; update Summary, Caveats (the 'gives all four parts' line), accuracy spec D2 and the NulodionCannonSaleTest line. Code, CI, scope, in-game reclaim at stages 1-4 all pass.
- 2026-10-24T23:10:30Z GATE FAIL (sq46, 2026-10-24) at 60cffedfb, PR TEXT ONLY (code passes; CI green at the head; in game OK: stages build in order, reclaim at stages 1/2/3/full returns exactly the first k parts, varp resets, no duplicates). Record: /home/alex/src/openrune-work/server-tools/upstream/qa/cannon-review-354.md (local commit fb499e9a6). FIX the PR text (pr-texts/cannon upstream body on the fork docs branch) and accuracy/cannon.md: (1) Summary says Nulodion gives 'the four parts' and refuses with fewer than 4 free slots: it now gives the first k parts for the saved varp.dropcannon stage and needs k free slots; (2) Caveats say 'Nulodion gives all four parts even when only part of the cannon was set up': now false; the wiki (Transcript:Nulodion, Dwarf multicannon) says nothing about part-built cannons, so state the stage-based return as a divergence/guess in Caveats; (3) accuracy/cannon.md row D2 ('gives four parts even for a part-built cannon') same update; (4) the NulodionCannonSaleTest line 'replaced with four parts' is true only for a full cannon: qualify it. Fork docs pushes need no approval; do NOT touch the upstream PR body (an upstream action: the console asks the user). Hand over the new text; QA re-gates the text.
- 2026-10-24T23:10:30Z hold failed cleared: dev: PR text fix after gate FAIL
- 2026-10-24T23:10:30Z ready -> dev: dispatched to sd73
- 2026-10-24T23:10:30Z run sd73 started (server-dev, stage dev)
- 2026-10-24T23:11:29Z handover content/cannon@60cffedfb: Text-only gate fix: PR text and accuracy/cannon.md state Nulodion returns the first k parts for the saved stage (docs e86532f97); wiki silent, divergence in Caveats; test line qualified. Left: user OK to update upstream #354 body and reply
- 2026-10-24T23:11:41Z run sd73 ended: ? turns, ? tokens, exit ok
- 2026-10-24T23:11:41Z run sq52 started (server-qa, stage gate)
- 2026-10-24T23:12:40Z dev -> ready: hand-over check FAIL (1): the next dev fixes exactly those items
- 2026-10-24T23:12:40Z hold failed: PR text: remove history text ('This push replaces the first version...', 'current main (829b9477d)', 'The first version's mcannon_decay timer is gone'); say 'a full cannon's replacement' in the tests paragraph. Everything else verified true at 60cffedfb
- 2026-10-24T23:12:58Z GATE FAIL #2 (sq52, 2026-10-24), PR TEXT ONLY (code at 60cffedfb accepted; claims vs code all true; no stale 'four parts'; template sections present). Fix pr-texts/cannon.upstream.body (docs e86532f97): (1) HISTORY TEXT, remove: 'This push replaces the first version with a rewrite checked against the OSRS Wiki, on current main (829b9477d).' and 'The first version's mcannon_decay timer is gone; the break and decay timers are loc durations now.' and any other 'first version / replaces / now / no longer / was' revision wording; the text states what the PR does, not how it changed (user rule: no revision justification); also drop 'current main (829b9477d)' (stale; upstream main moved on). (2) the tests paragraph ends '...the decay and Nulodion's replacement are covered by the integration tests': say 'a full cannon's replacement' (partial reclaim is not covered by a test). BEFORE hand-over re-read the WHOLE text and spec once for any remaining history, stale sha or overstated claim, so QA does not fail a third time. Fork docs push (no approval); do not touch the upstream PR.
- 2026-10-24T23:12:58Z hold failed cleared: dev: PR text fix #2
- 2026-10-24T23:12:58Z ready -> dev: dispatched to sd74
- 2026-10-24T23:12:58Z run sd74 started (server-dev, stage dev)
- 2026-10-24T23:13:46Z dev -> ready: hand-over check FAIL (1): the next dev fixes exactly those items
- 2026-10-24T23:13:46Z run sd74 ended: ? turns, ? tokens, exit stopped:lingering: owner is None (change at ready)
- 2026-10-24T23:16:06Z ready -> dev: dispatched to sd75
- 2026-10-24T23:16:06Z run sd75 started (server-dev, stage dev)
- 2026-10-24T23:17:05Z dev -> ready: hand-over check FAIL (1): the next dev fixes exactly those items
- 2026-10-24T23:17:05Z run sd75 ended: ? turns, ? tokens, exit stopped:lingering: owner is None (change at ready)
- 2026-10-24T23:17:05Z ready -> dev: hand-over recorded
- 2026-10-24T23:17:05Z handover content/cannon@60cffedfb: Text-only gate fix #2: PR text and accuracy/cannon.md state what the PR does with no revision history or stale sha; tests line says a full cannon's replacement (docs 6241778db). Left: user OK to update upstream #354 body and reply
- 2026-10-24T23:17:17Z run sq53 started (server-qa, stage gate)
- 2026-10-24T23:18:11Z dev -> ready: hand-over check FAIL (1): the next dev fixes exactly those items
- 2026-10-24T23:18:11Z run sq53 ended: ? turns, ? tokens, exit stopped:lingering: change at ready
- 2026-10-24T23:18:13Z USER DECISION 2026-10-24: drop #354's tests (DwarfMulticannonTest and the NulodionCannonSaleTest file, i.e. every test file the PR adds against upstream main) and the test-only build dependencies they need; the PR keeps the code only. Work: a NEW local commit on top of 60cffedfb (no force-push) in a clone of fork content/cannon (e.g. /home/alex/src/openrune-work/agents/sd44/or); update the PR text (the tests section and any test line in Caveats, tick lines) and accuracy/cannon.md so they state what the PR does and that no tests are included (in-game verification only) with no revision/history wording; read upstream AGENTS.md and CONTRIBUTING and self-check the whole net diff; push the commit to a FORK scratch/staging branch only (e.g. fix/cannon-drop-tests, no approval needed), NOT content/cannon (that is the upstream PR head: the user's approval after the QA gate PASS). Then QA gates it: scope (no test files), CI on a fork scratch branch merged with upstream main, text true; in game is not needed (only tests removed). sq53's text re-gate was cancelled as moot.
- 2026-10-24T23:18:13Z ready -> dev: dispatched to sd76
- 2026-10-24T23:18:13Z run sd76 started (server-dev, stage dev)
- 2026-10-24T23:19:17Z dev -> ready: hand-over check FAIL (1): the next dev fixes exactly those items
- 2026-10-24T23:19:17Z run sd76 ended: ? turns, ? tokens, exit stopped:lingering: owner is None (change at ready)
- 2026-10-24T23:21:39Z ready -> dev: hand-over recorded
- 2026-10-24T23:21:39Z handover fix/cannon-drop-tests@0df5c63a0: Drop #354's tests: new commit on 60cffedfb on fork staging fix/cannon-drop-tests; PR text and accuracy/cannon.md updated on docs
- 2026-10-24T23:22:36Z dev -> ready: hand-over check FAIL (2): the next dev fixes exactly those items
- 2026-10-24T23:23:35Z run sq55 started (server-qa, stage gate)
- 2026-10-24T23:23:42Z run sq55 ended: ? turns, ? tokens, exit stopped:lingering: change at ready
- 2026-10-24T23:39:46Z gate PASS claimed: CI 40142538549 and Formatting 40142539998 green on scratch merge; 4-file scope, no tests, spotless ok, logic unchanged from 60cffedfb (the record on docs is what counts)
- 2026-10-25T00:09:34Z dod ticked: 3, 4
- 2026-10-25T00:37:54Z ready -> dev: dispatched to sd80
- 2026-10-25T00:37:54Z run sd80 started (server-dev, stage dev)
