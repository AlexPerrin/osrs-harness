---
slug: targeted-tests-procedure
track: harness
title: Dev and QA run only the touched modules' tests; the full suite is the fork CI on the scratch merge
prio: P2
role: harness-dev
stage: live
hold: null
deps: []
branch: main
commit: ade63be115d4c111d62b1803f802090b354d1caf
local_only: false
owner: null
evidence: /home/alex/osrs-harness/docs
summary: 'Merged into main: targeted tests rule and the gate.md Tests line.'
live_commit: ade63be115d4c111d62b1803f802090b354d1caf
booked:
  dev: '|da39a3ee5e6b'
cost:
  runs: 1
  turns: 0
  tokens: 0
  minutes: 0
created: '2026-10-25T01:26:53Z'
updated: '2026-10-25T01:29:20Z'
---
## Change
Dev and QA run only the touched modules' tests; the full suite is the fork CI on the scratch merge

## Definition of done
- [x] The server-dev and server-qa role files, the build-test and server-track skills say: dev tests and the QA aggregate run only the tests of the modules the change touches plus spotlessCheck on them; the full unit and integration suite is the fork CI run (hd gate-ci), never a local full qa.sh gate unless the fork CI cannot run
- [x] The QA record format (gate.md) has a 'tests' line listing which modules' tests ran and the CI run id that covers the full suite; hd gate validates the line is present
- [x] Docs concise, current truth, no justification; tests per rule touched, full suite passes; no push, no daemon restart

## Log
- 2026-10-25T01:26:53Z created (ready)
- 2026-10-25T01:26:53Z USER 2026-10-24: 790 unit + 112 integration is high for the scope of one feature; in the QA aggregate test only what is necessary during dev test and run the FULL CI only in the fork (scratch merge, hd gate-ci). The fork-tools qa.sh (fork branch local/server-tools) full-gate mode is out of scope here (list it for v7).
- 2026-10-25T01:26:53Z ready -> dev: dispatched to hd22
- 2026-10-25T01:26:53Z run hd22 started (harness-dev, stage dev)
- 2026-10-25T01:28:24Z dod ticked: 1, 2, 3
- 2026-10-25T01:28:40Z run hd22 ended: ? turns, ? tokens, exit ok
- 2026-10-25T01:28:56Z dev -> gate: hand-over recorded
- 2026-10-25T01:28:56Z handover main@ade63be11: Merged into main: targeted tests rule and the gate.md Tests line.
- 2026-10-25T01:29:20Z gate -> live: observed
