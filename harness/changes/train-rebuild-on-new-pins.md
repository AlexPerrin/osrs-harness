---
slug: train-rebuild-on-new-pins
track: harness
title: hd resume rebuilds the integration when the tools branch moved past the batch's pins (a gate-failure resolution that changes integration.txt or pins must take effect)
prio: P0
role: harness-dev
stage: live
hold: null
deps: []
branch: harness/train-rebuild-on-new-pins
commit: 1d3d4e8ed0ba3d531f9dd616ee7e3634a9459c03
local_only: false
owner: null
evidence: /home/alex/osrs-plugins-reverse/re/evidence/train-rebuild-on-new-pins
summary: resume re-runs the train from pinning when the tools branch head differs from the batch's tools commit (drops unlisted entries), else restarts the gate; 2 tests; 263 pass; nothing pruned
live_commit: 1d3d4e8ed0ba3d531f9dd616ee7e3634a9459c03
booked:
  dev: '|da39a3ee5e6b'
cost:
  runs: 1
  turns: 0
  tokens: 0
  minutes: 0
created: '2026-10-25T00:43:25Z'
updated: '2026-10-25T00:46:12Z'
---
## Change
hd resume rebuilds the integration when the tools branch moved past the batch's pins (a gate-failure resolution that changes integration.txt or pins must take effect)

## Definition of done
- [x] batches.resume: when the batch's recorded tools commit differs from the tools branch head (the integrator's resolution changed integration.txt, pins or the rr-cache), resume re-runs the train from pinning/rebuilding (new integration clone and commit) instead of restarting the gate on the old clone; when nothing moved, a gate failure still restarts the gate
- [x] A test covers both cases (tools moved: rebuild; tools unmoved: gate restart) and the entries the integrator removed from integration.txt leave the batch (BR-B4)
- [x] ISSUES.md gets a short dated entry (symptom: resolved gate failure re-gated on the old tree); ARCHITECTURE.md train section states the resume rule in one sentence; full suite passes; no push, no daemon restart (the console restarts)

## Log
- 2026-10-25T00:43:25Z created (ready)
- 2026-10-25T00:43:25Z From batch int-20261025-1: the gate failed on a stale test from fin/goblin-diplomacy; ig20 resolved it by adding fork branch local/drop-stale-goblin-test (96f4e49be) to integration.txt/lock on local/integration-tools (d080c6c49). After hd resolve the daemon put the batch back to gating on the OLD clone qa/integration-7c62b8341 (tools e6cf9dc), so the fix never reaches the tree. Fix hd/batches.py resume (and the path the daemon uses after resolve) so a moved tools branch triggers a rebuild. Harness fix, autonomous; the console merges and restarts. Work in a worktree: git reset --hard main first.
- 2026-10-25T00:43:25Z ready -> dev: dispatched to hd20
- 2026-10-25T00:43:25Z run hd20 started (harness-dev, stage dev)
- 2026-10-25T00:45:04Z dod ticked: 1, 2, 3
- 2026-10-25T00:45:09Z dev -> gate: hand-over recorded
- 2026-10-25T00:45:09Z handover harness/train-rebuild-on-new-pins@1d3d4e8ed: resume re-runs the train from pinning when the tools branch head differs from the batch's tools commit (drops unlisted entries), else restarts the gate; 2 tests; 263 pass; nothing pruned
- 2026-10-25T00:45:33Z ship: merged into main 6efb7d3
- 2026-10-25T00:45:46Z run hd20 ended: ? turns, ? tokens, exit ok
- 2026-10-25T00:46:12Z gate -> live: observed
