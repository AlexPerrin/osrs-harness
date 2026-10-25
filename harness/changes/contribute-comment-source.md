---
slug: contribute-comment-source
track: harness
title: hd contribute posts the prepared status comment (pr-texts/<slug>.comment), never the raw hand-over summary
prio: P1
role: harness-dev
stage: dev
hold: null
deps: []
branch: null
commit: null
local_only: false
owner: hd28
booked:
  dev: '|da39a3ee5e6b'
created: '2026-10-25T02:37:09Z'
updated: '2026-10-25T02:38:38Z'
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
