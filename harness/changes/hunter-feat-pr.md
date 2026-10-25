---
slug: hunter-feat-pr
track: server
title: 'One upstream feat: PR for the completed hunter work'
prio: P1
role: server-dev
stage: gate
hold: null
deps: []
branch: feat/hunter
commit: fbfdb9eac0c512510ce0c8808f31f15331d4ee20
repo: /home/alex/src/openrune-work/agents/sd85/or
local_only: false
owner: sd85
evidence: /home/alex/osrs-plugins-reverse/re/evidence/hunter-feat-pr
summary: 'One Hunter feat PR: traps, bird houses, Herbiboar, butterflies, implings, Hunters'' Rumours; one commit off upstream main, no tests or comments; compile, spotless, gameval check pass; not verified
  in game (draft); kebbit tracking out'
booked:
  dev: '|da39a3ee5e6b'
created: '2026-10-25T02:32:09Z'
updated: '2026-10-25T02:55:08Z'
---
## Change
One upstream feat: PR for the completed hunter work

## Definition of done
- [x] A single branch (fork feat/hunter or content/hunter, off CURRENT upstream main, no stacking) whose net diff against upstream main is ONLY the completed hunter work: the module, traps, rumours, bird houses, butterflies, herbiboar, implings and kebbit tracking as far as they are complete and verified on the test server; no unrelated files, no generated .data files, no test files, no added comments (AGENTS.md read live), gamevals via the gameval conflict check, spotlessCheck clean
- [x] PR text in docs/pr-texts (title 'feat: ...' accurate and short; body = upstream's pull_request_template.md checklist VERBATIM and in order, all items present, ticks only when true, explanations as plain notes with no checkboxes, no revision history, a plain scope list of what is in and what is not, data sources, guesses and gaps); accuracy specs for the parts included exist (accuracy/hunter*.md on fork docs) and the PR text says what was verified in game
- [ ] The branch is on the fork, fast-forwardable, builds and its touched modules' tests and spotless pass locally (targeted); the QA aggregate (hd gate-ci scratch merge, CI and Formatting, scope, style, text, in game on a branch server with an own client for the main hunter activities) is recorded; then the approval card for a NEW PR; hd contribute opens it as a draft and moves it out of draft after green CI

## Log
- 2026-10-25T02:32:09Z created (ready)
- 2026-10-25T02:32:09Z USER 2026-10-24: 'We have a lot of hunter work completed, we should draft a single upstream feat: PR.' Sources: fork branches content/hunter (6310b11ef), content/hunter-module (c189c1969), hunter-traps (92d435055), hunter-rumours (544881bfe), hunter-bird-houses (7967d0fc5), hunter-butterflies (53a52d555), hunter-herbiboar (63d44a4a2), hunter-implings (f89a2fd60), the live combined fin/hunter (a4a74b5a9), changes hunter, hunter-split-ship (the old plan: 7 split PRs with the linearised rumours; superseded by this user decision of ONE PR), hunter-kebbit-tracking; earlier closed upstream PRs #196 and #229 (hunter module with bird snares and box traps) for maintainers' prior feedback (read their review threads before writing the text). Spec/QA records under re/evidence and fork docs accuracy/. Rules: no stacking (one branch off current main), no tests in the diff, no added comments, template-verbatim body, live AGENTS.md/CONTRIBUTING, targeted tests locally, fork actions free, nothing upstream before the user's approval card.
- 2026-10-25T02:32:09Z ready -> dev: dispatched to sd85
- 2026-10-25T02:32:09Z run sd85 started (server-dev, stage dev)
- 2026-10-25T02:33:25Z USER 2026-10-24: 'We can open it unverified as draft.' The PR may be opened as a DRAFT before the QA aggregate and in-game verification; the body says plainly what is verified and what is not (ticks only when true). The move out of draft needs the full checks and the user's card. The console opens the draft directly after the hand-over, without the contribute command (which waits for CI and then readies).
- 2026-10-25T02:55:06Z dod ticked: 1, 2
- 2026-10-25T02:55:08Z dev -> gate: hand-over recorded
- 2026-10-25T02:55:08Z handover feat/hunter@fbfdb9eac: One Hunter feat PR: traps, bird houses, Herbiboar, butterflies, implings, Hunters' Rumours; one commit off upstream main, no tests or comments; compile, spotless, gameval check pass; not verified in game (draft); kebbit tracking out
