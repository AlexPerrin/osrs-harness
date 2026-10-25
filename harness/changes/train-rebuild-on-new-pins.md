---
slug: train-rebuild-on-new-pins
track: harness
title: hd resume rebuilds the integration when the tools branch moved past the batch's pins (a gate-failure resolution that changes integration.txt or pins must take effect)
prio: P0
role: harness-dev
stage: dev
hold: null
deps: []
branch: null
commit: null
local_only: false
owner: hd20
booked:
  dev: '|da39a3ee5e6b'
created: '2026-10-25T00:43:25Z'
updated: '2026-10-25T00:43:25Z'
---
## Change
hd resume rebuilds the integration when the tools branch moved past the batch's pins (a gate-failure resolution that changes integration.txt or pins must take effect)

## Definition of done
- [ ] batches.resume: when the batch's recorded tools commit differs from the tools branch head (the integrator's resolution changed integration.txt, pins or the rr-cache), resume re-runs the train from pinning/rebuilding (new integration clone and commit) instead of restarting the gate on the old clone; when nothing moved, a gate failure still restarts the gate
- [ ] A test covers both cases (tools moved: rebuild; tools unmoved: gate restart) and the entries the integrator removed from integration.txt leave the batch (BR-B4)
- [ ] ISSUES.md gets a short dated entry (symptom: resolved gate failure re-gated on the old tree); ARCHITECTURE.md train section states the resume rule in one sentence; full suite passes; no push, no daemon restart (the console restarts)

## Log
- 2026-10-25T00:43:25Z created (ready)
- 2026-10-25T00:43:25Z From batch int-20261025-1: the gate failed on a stale test from fin/goblin-diplomacy; ig20 resolved it by adding fork branch local/drop-stale-goblin-test (96f4e49be) to integration.txt/lock on local/integration-tools (d080c6c49). After hd resolve the daemon put the batch back to gating on the OLD clone qa/integration-7c62b8341 (tools e6cf9dc), so the fix never reaches the tree. Fix hd/batches.py resume (and the path the daemon uses after resolve) so a moved tools branch triggers a rebuild. Harness fix, autonomous; the console merges and restarts. Work in a worktree: git reset --hard main first.
- 2026-10-25T00:43:25Z ready -> dev: dispatched to hd20
- 2026-10-25T00:43:25Z run hd20 started (harness-dev, stage dev)
