---
slug: harness-track-check-v5
track: harness
title: 'v5: harness-track check and live_target for this repo (main, not the client''s master); hd command to tick a DoD item'
prio: P1
role: harness-dev
stage: live
hold: null
deps: []
branch: main
commit: b3c38d9fef627d572cfccfe91770aba59e2c981d
local_only: false
owner: null
instances: []
evidence: /home/alex/osrs-harness/docs/evidence/handover-upstream-ci
summary: Merged into main at b3c38d9 by the console (c23ee97 ship follow-up included).
live_commit: b3c38d9fef627d572cfccfe91770aba59e2c981d
cost:
  runs: 2
  turns: 0
  tokens: 0
  minutes: 0
created: '2026-10-24T22:29:11Z'
updated: '2026-10-24T22:41:14Z'
---
## Change
v5: harness-track check and live_target for this repo (main, not the client's master); hd command to tick a DoD item

## Definition of done
- [x] The harness-track hand-over check and the live detection work for this repo: branch main (or a harness/ branch merged into main), no read of the client repo's master; policy tracks.harness.live_target is main of this repo; a harness change whose commit is on main is observed live
- [x] New command hd dod <slug> <n>... ticks definition-of-done items on a change (the only sanctioned way for an agent to tick, since agents cannot edit change files); tested
- [x] handover-upstream-ci (on a decision hold, merged at 14ac15c/5ce5d75) can be handed over with the new check in a dry run and passes; do not alter its stage by hand
- [x] Tests per rule touched, full suite passes; ARCHITECTURE.md (docs/) describes the harness-track lifecycle in a few lines; the cause goes in docs/ISSUES.md; no root files; no push, no merge, no daemon restart

## Log
- 2026-10-24T22:29:11Z created (ready)
- 2026-10-24T22:29:11Z ready -> dev: dispatched to hd10
- 2026-10-24T22:29:11Z run hd10 started (harness-dev, stage dev, instances none)
- 2026-10-24T22:32:55Z dod ticked: 1, 2, 3, 4
- 2026-10-24T22:32:58Z handover harness/harness-track-check-v5@484c6ac06: Harness track reads this repo's main (policy live_target main; check, stages, ship, observer repo 'harness'); hd dod; handover-upstream-ci passes a dry run on a scratch store; 164 tests pass
- 2026-10-24T22:33:17Z run hd10 ended: ? turns, ? tokens, exit ok
- 2026-10-24T22:33:44Z dev -> ready: hand-over check FAIL (2): the next dev fixes exactly those items
- 2026-10-24T22:33:44Z ready -> dev: dispatched to hd11
- 2026-10-24T22:33:44Z run hd11 started (harness-dev, stage dev, instances none)
- 2026-10-24T22:34:50Z dev -> ready: hand-over check FAIL (2): the next dev fixes exactly those items
- 2026-10-24T22:34:50Z run hd11 ended: ? turns, ? tokens, exit stopped:lingering: owner is None (change at ready)
- 2026-10-24T22:36:03Z ready -> dev: hand-over recorded
- 2026-10-24T22:36:03Z handover harness/harness-track-check-v5@c23ee9777: Adds: harness ship guard follows current layout; model-neutral trailer in ship.py and train/integrate.py; harness merge stays automatic and local; 167 tests pass
- 2026-10-24T22:37:06Z dev -> ready: hand-over check FAIL (2): the next dev fixes exactly those items
- 2026-10-24T22:37:08Z ready -> dev: hand-over recorded
- 2026-10-24T22:37:08Z handover harness/harness-track-check-v5@b3c38d9fe: Docs trimmed to mechanism only; 167 tests pass
- 2026-10-24T22:38:12Z dev -> ready: hand-over check FAIL (2): the next dev fixes exactly those items
- 2026-10-24T22:40:38Z ready -> dev: hand-over recorded
- 2026-10-24T22:40:38Z handover main@b3c38d9fe: Merged into main at b3c38d9 by the console (c23ee97 ship follow-up included).
- 2026-10-24T22:40:52Z dev -> checked: hand-over check PASS
- 2026-10-24T22:40:52Z ship: already on main
- 2026-10-24T22:41:14Z checked -> live: observed
