---
slug: rules-version-line
track: harness
title: QA record names the blob shas of upstream's AGENTS.md, CONTRIBUTING.md and PR template; hd contribute re-checks them
prio: P1
role: harness-dev
stage: ready
hold:
  kind: decision
  reason: 'cancelled by the user (2026-10-24: ''nvm continue as is''); not built'
  since: '2026-10-25T01:54:08Z'
deps: []
branch: null
commit: null
local_only: false
owner: null
booked:
  dev: '|da39a3ee5e6b'
created: '2026-10-25T01:53:59Z'
updated: '2026-10-25T01:54:12Z'
---
## Change
QA record names the blob shas of upstream's AGENTS.md, CONTRIBUTING.md and PR template; hd contribute re-checks them

## Definition of done
- [ ] gate.md has a header line 'Rules: AGENTS.md <sha>; CONTRIBUTING.md <sha>; pull_request_template.md <sha>' (the blob shas read live from upstream main); the validator in hd/tracks/server/qa.py requires it and hd gate refuses a record without it
- [ ] hd contribute compares the recorded shas with upstream main's current ones (observed with gh api) and stops before pushing when any differs, telling the console to re-run the style and text checks; the check lives in the server track module
- [ ] The PR text normaliser and template used by agents read the live template from upstream (a helper in the server track returns the live template text and the three blob shas), no cached copy is shipped or used; briefs and the server-qa and server-dev role files and the server-track skill say to read the live files
- [ ] Tests per rule touched; the full suite passes; docs concise current truth (PROBLEM.md BR-S7 one sentence, ARCHITECTURE.md mechanism); one dated entry in docs/ISSUES.md; no push, no daemon restart

## Log
- 2026-10-25T01:53:59Z created (ready)
- 2026-10-25T01:53:59Z USER 2026-10-24: 'AGENTS.md can be revised at any time.' Upstream's AGENTS.md changed 2026-10-09, the PR template 2026-10-19. Current blob shas: AGENTS.md e38e31fc54c6, .github/CONTRIBUTING.md ff362f760f92, .github/pull_request_template.md b7b9e8927f53. Harness fix, apply now (user: no deferral); server-track details stay in hd/tracks/server/. Work in a worktree: git reset --hard main first.
- 2026-10-25T01:53:59Z ready -> dev: dispatched to hd24
- 2026-10-25T01:53:59Z run hd24 started (harness-dev, stage dev)
- 2026-10-25T01:54:08Z hold decision: cancelled by the user (2026-10-24: 'nvm continue as is'); not built
- 2026-10-25T01:54:12Z dev -> ready: run hd24 ended without a hand-over
