---
slug: contribute-comment-source
track: harness
title: hd contribute posts the prepared status comment (pr-texts/<slug>.comment), never the raw hand-over summary
prio: P1
role: harness-dev
stage: live
hold: null
deps: []
branch: main
commit: 58c48ec794726bb4c0e95922600580fc16f24e53
local_only: false
owner: null
evidence: /home/alex/osrs-harness/docs
summary: 'Merged into main: the comment source order and the short fallback.'
live_commit: 58c48ec794726bb4c0e95922600580fc16f24e53
booked:
  dev: '|da39a3ee5e6b'
cost:
  runs: 1
  turns: 0
  tokens: 0
  minutes: 0
created: '2026-10-25T02:37:09Z'
updated: '2026-10-25T02:40:23Z'
---
## Change
hd contribute posts the prepared status comment (pr-texts/<slug>.comment), never the raw hand-over summary

## Definition of done
- [x] texts() in hd/tracks/server/contribute.py reads the status comment from the evidence dir pr-comment.md, else fork docs pr-texts/<slug>.comment (and the existing .update.md name), else a short generated text with no sha prefix, never the raw hand-over summary; the dev and QA role files and the server-track skill name the file
- [x] Test: summary present and no prepared file gives the short generated text, prepared file wins; docs one line (PRD/ARCHITECTURE only if a requirement changed); full suite passes; no push, no daemon restart

## Log
- 2026-10-25T02:37:09Z created (ready)
- 2026-10-25T02:37:09Z From the #368 and #406 contributions: the posted comments were the hand-over summaries ('Five QA fixes... fork fix/witchs-potion-clean ... template-verbatim bodies') because the prepared files were named pr-texts/<slug>.comment while the code reads pr-comment.md or pr-texts/<slug>.update.md. USER 2026-10-24: fix both comments (done by hand) and apply fixes now. Work in a worktree: git reset --hard main first.
- 2026-10-25T02:37:09Z ready -> dev: dispatched to hd28
- 2026-10-25T02:37:09Z run hd28 started (harness-dev, stage dev)
- 2026-10-25T02:38:38Z dod ticked: 1, 2
- 2026-10-25T02:39:33Z run hd28 ended: ? turns, ? tokens, exit ok
- 2026-10-25T02:39:51Z dev -> gate: hand-over recorded
- 2026-10-25T02:39:51Z handover main@58c48ec79: Merged into main: the comment source order and the short fallback.
- 2026-10-25T02:40:23Z gate -> live: observed
