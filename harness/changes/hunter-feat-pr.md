---
slug: hunter-feat-pr
track: server
kind: change
title: 'Hunter #408: one feat PR for the completed hunter work'
priority: P1
created: '2026-10-25T02:32:09Z'
branch: feat/hunter
---
## Change
Upstream #408 (draft) carries the completed hunter work as one feat: the module, traps, rumours, bird houses, butterflies,
herbiboar, implings and kebbit tracking, as far as complete and verified on the test server. Net diff against upstream
main is the hunter work only: no unrelated files, no generated .data files, no test files, no added comments (AGENTS.md
read live), gamevals through the gameval conflict check, spotlessCheck clean.

## Definition of done
- the gate passes (accuracy specs in the evidence dir, fork CI and Formatting green on the scratch merge)
- the review passes: scope, upstream style, PR text (pull_request_template.md verbatim, ticks only when true, a plain
  scope list of what is in and what is not, data sources, guesses and gaps), the main hunter activities in game on a
  branch server
- after the user's yes: #408 leaves draft once upstream CI is green
