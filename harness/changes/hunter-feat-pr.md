---
slug: hunter-feat-pr
track: server
kind: change
title: 'One upstream feat: PR for the completed hunter work'
priority: P1
created: '2026-10-25T02:32:09Z'
branch: feat/hunter
---
## Change
One upstream feat: PR for the completed hunter work

## Definition of done
- [x] A single branch (fork feat/hunter or content/hunter, off CURRENT upstream main, no stacking) whose net diff against upstream main is ONLY the completed hunter work: the module, traps, rumours, bird houses, butterflies, herbiboar, implings and kebbit tracking as far as they are complete and verified on the test server; no unrelated files, no generated .data files, no test files, no added comments (AGENTS.md read live), gamevals via the gameval conflict check, spotlessCheck clean
- [x] PR text in docs/pr-texts (title 'feat: ...' accurate and short; body = upstream's pull_request_template.md checklist VERBATIM and in order, all items present, ticks only when true, explanations as plain notes with no checkboxes, no revision history, a plain scope list of what is in and what is not, data sources, guesses and gaps); accuracy specs for the parts included exist (accuracy/hunter*.md on fork docs) and the PR text says what was verified in game
- [ ] The branch is on the fork, fast-forwardable, builds and its touched modules' tests and spotless pass locally (targeted); the QA aggregate (hd gate-ci scratch merge, CI and Formatting, scope, style, text, in game on a branch server with an own client for the main hunter activities) is recorded; then the approval card for a NEW PR; hd contribute opens it as a draft and moves it out of draft after green CI
