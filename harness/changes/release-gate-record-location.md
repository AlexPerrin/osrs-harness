---
slug: release-gate-record-location
track: harness
title: 'publish_gate: client release record accepted from the harness evidence dir and --target honoured'
prio: P0
role: harness-dev
stage: ready
hold:
  kind: decision
  reason: 'needs you: a dev run was already booked for exactly this head (none) and these findings; booking another would repeat it'
  since: '2026-10-25T02:50:23Z'
deps: []
branch: null
commit: null
local_only: false
owner: null
booked:
  dev: '|da39a3ee5e6b'
cost:
  runs: 1
  turns: 0
  tokens: 0
  minutes: 0
created: '2026-10-25T02:46:32Z'
updated: '2026-10-25T02:50:23Z'
---
## Change
publish_gate: client release record accepted from the harness evidence dir and --target honoured

## Definition of done
- [x] hooks/publish_gate.py release_gate: (1) the commit being released also comes from  (and ) of gh release create, not only the positional sha, falling back to the tag's commit then HEAD; (2) the record is found at <client repo>/qa/client-<version>.md (as before) OR in the harness evidence tree as a client-record.md (re/evidence/*/client-record.md under HD_CLIENT_ROOT today) whose '- Commit:' header names the released commit and whose verdict is PASS; a missing record, a FAIL verdict or a commit mismatch still denies
- [x] Tests for: --target honoured; record in the evidence tree accepted; wrong commit denied; FAIL denied; missing denied; the old qa/ path still works; docs one line (PRD/ARCHITECTURE hooks table only if wording changed); full suite passes; no push, no daemon restart

## Log
- 2026-10-25T02:46:32Z created (ready)
- 2026-10-25T02:46:32Z USER 2026-10-24: option 2 (fix the guard and release). The v0.1.2 release was denied by publish_gate: 'no release record qa/client-0.1.2.md; client-qa runs the release gate on a0a63ca4c first'. Causes: the regex takes the target only as a positional sha (I used --target d78a893...), and the record is looked up only in the client repo qa/ which is client-only now; cq4 wrote /home/alex/osrs-plugins-reverse/re/evidence/rel-20261024-1/client-record.md ('- Commit: `d78a8935f4...`', '## Verdict: **PASS**'). Keep the guard strict otherwise. Existing tests for publish_gate: find them under tests/ (test_live.py etc.). Work in a worktree: git reset --hard main first. The console merges and then runs the release.
- 2026-10-25T02:46:32Z ready -> dev: dispatched to hd29
- 2026-10-25T02:46:32Z run hd29 started (harness-dev, stage dev)
- 2026-10-25T02:48:31Z dod ticked: 1, 2
- 2026-10-25T02:48:43Z run hd29 ended: ? turns, ? tokens, exit ok
- 2026-10-25T02:49:25Z dev -> ready: run hd29 ended without a hand-over
- 2026-10-25T02:50:23Z hold decision: needs you: a dev run was already booked for exactly this head (none) and these findings; booking another would repeat it
