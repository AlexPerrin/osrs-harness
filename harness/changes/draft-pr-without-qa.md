---
slug: draft-pr-without-qa
track: harness
title: 'publish_gate: an upstream draft PR may open without a QA record (the user''s unverified-draft decision); non-draft and contribute keep the record requirement'
prio: P0
role: harness-dev
stage: ready
hold:
  kind: decision
  reason: 'needs you: a dev run was already booked for exactly this head (none) and these findings; booking another would repeat it'
  since: '2026-10-25T02:59:27Z'
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
created: '2026-10-25T02:56:16Z'
updated: '2026-10-25T02:59:27Z'
---
## Change
publish_gate: an upstream draft PR may open without a QA record (the user's unverified-draft decision); non-draft and contribute keep the record requirement

## Definition of done
- [x] hooks/publish_gate.py: an upstream gh pr create that carries the --draft flag and an explicit --head AlexPerrin:<branch> whose branch exists is allowed without a QA record at the commit; a non-draft upstream PR creation, hd contribute (including moving a PR out of draft) and the client release gate keep every existing check unchanged
- [x] Tests: draft with head allowed; draft without --head denied; non-draft without record denied; non-draft with record allowed; the contribute and release cases unchanged; docs one line where the hooks wording changes (PRD/ARCHITECTURE), one dated line in docs/ISSUES.md; full suite passes; no push, no daemon restart

## Log
- 2026-10-25T02:56:16Z created (ready)
- 2026-10-25T02:56:16Z USER 2026-10-24: 'We can open it unverified as draft.' publish_gate denied the draft open of fork branch feat/hunter (fbfdb9eac): 'no change has a QA record at it (hunter-feat-pr: QA record missing)'. Relevant code: hooks/publish_gate.py main() lines ~94-113 (direct_pr_deny from hd/tracks/server/hooks.py). Implement exactly the DoD: a draft upstream PR creation skips the record check only; keep the explicit --head requirement. Work in a worktree: git reset --hard main first. The console merges and then opens the draft.
- 2026-10-25T02:56:16Z ready -> dev: dispatched to hd30
- 2026-10-25T02:56:16Z run hd30 started (harness-dev, stage dev)
- 2026-10-25T02:57:46Z dod ticked: 1, 2
- 2026-10-25T02:57:57Z run hd30 ended: ? turns, ? tokens, exit ok
- 2026-10-25T02:58:25Z dev -> ready: run hd30 ended without a hand-over
- 2026-10-25T02:59:27Z hold decision: needs you: a dev run was already booked for exactly this head (none) and these findings; booking another would repeat it
