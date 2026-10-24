---
slug: drop-instance-locks
track: harness
title: 'Remove instance leases and device locking: each agent opens its own client'
prio: P2
role: harness-dev
stage: live
hold: null
deps: []
branch: harness/drop-instance-locks
commit: 09d72309e21f588a091d5380caf7415a9027f5f1
local_only: false
owner: null
instances: []
evidence: /home/alex/osrs-plugins-reverse/re/evidence/drop-instance-locks
summary: Instance leases deleted (grant/revoke/drain/heartbeat/deadlock rule, instances/qa_instances/leases policy keys, device-lock.sh, train/instances.tsv); dispatch waits on slots only; locks kept only
  for integration, live-server, ghidra; roles, skills, PRD and ARCHITECTURE updated; 164 tests OK. Do not merge or deploy until the console gates it with the user.
live_commit: 09d72309e21f588a091d5380caf7415a9027f5f1
cost:
  runs: 1
  turns: 0
  tokens: 0
  minutes: 0
created: '2026-10-24T22:43:11Z'
updated: '2026-10-24T22:59:58Z'
---
## Change
Remove instance leases and device locking: each agent opens its own client

## Definition of done
- [x] Instance leases for device/desktop/desktop2 are removed: hd/leases.py, 'hd lease', the grant/take/revoke events, lease waits in dispatch and heal, the 'instances' and 'qa_instances' policy keys, instances in briefs and role files; dispatch waits only on a free slot
- [x] device-lock.sh and train/instances.tsv are removed or reduced to what a per-agent client start still needs; the client repo's shims that exec device-lock.sh are listed for the user (no client repo edit without the user's OK)
- [x] Leases that still guard a single shared resource (integration clone/push, live-server deploy, ghidra project) are kept only if a real shared resource needs them, each justified in ARCHITECTURE.md as mechanism
- [x] Role files and skills tell agents to start their own client (own port, own account state) and to stop it when done; no lock steps
- [x] Tests per rule touched, full suite passes; docs state current truth only; incident notes in docs/ISSUES.md; no push, no daemon restart

## Log
- 2026-10-24T22:43:11Z created (ready)
- 2026-10-24T22:43:11Z hold decision: major harness build: needs the user's OK (removes the lease subsystem for client instances); approve = unhold
- 2026-10-24T22:44:25Z USER 2026-10-24: rebuilds are cheap; prefer core redesign over patching; no approval before building, gate at deployment (merge into main and daemon restart: ask the user then). Redesign, do not patch: delete the instance-lease subsystem and rebuild dispatch on slots only. If main moved (docs trim hd13 merges first), merge main into your branch before reporting.
- 2026-10-24T22:44:25Z hold decision cleared: user: build it, gate at deployment
- 2026-10-24T22:44:25Z ready -> dev: dispatched to hd14
- 2026-10-24T22:44:25Z run hd14 started (harness-dev, stage dev, instances none)
- 2026-10-24T22:52:48Z dod ticked: 1, 2, 3, 4, 5
- 2026-10-24T22:53:15Z handover harness/drop-instance-locks@09d72309e: Instance leases deleted (grant/revoke/drain/heartbeat/deadlock rule, instances/qa_instances/leases policy keys, device-lock.sh, train/instances.tsv); dispatch waits on slots only; locks kept only for integration, live-server, ghidra; roles, skills, PRD and ARCHITECTURE updated; 164 tests OK. Do not merge or deploy until the console gates it with the user.
- 2026-10-24T22:53:49Z run hd14 ended: ? turns, ? tokens, exit ok
- 2026-10-24T22:53:56Z hold decision: significant build: deployment (merge into main + daemon restart) is the user's gate; branch harness/drop-instance-locks @09d72309e, 164 tests pass; approve = unhold
- 2026-10-24T22:54:34Z dev -> checked: hand-over check PASS
- 2026-10-24T22:59:34Z hold decision cleared: feature, not a major revision: autonomous deployment (user 2026-10-24)
- 2026-10-24T22:59:58Z checked -> live: observed
