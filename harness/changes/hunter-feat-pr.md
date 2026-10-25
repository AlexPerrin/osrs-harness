---
slug: hunter-feat-pr
track: server
kind: change
title: 'Hunter #408: the entire Hunter skill'
priority: P1
created: '2026-10-25T02:32:09Z'
branch: feat/hunter
---
## Change
Upstream #408 (draft) is the entire Hunter skill (the user, 2026-10-25: "Scope is entire Hunter Skill"): every Hunter
technique and activity on the OSRS wiki's Hunter page, matching the wiki, nothing left out. Today it carries bird
snares and box traps, bird houses, Herbiboar, butterflies, implings and Hunters' Rumours; still to add: Razor-backed
and other kebbit tracking, deadfalls, net traps, falconry, drift net fishing, pitfalls, and every item of the PR text's
Not done list. Net diff against upstream main is the hunter work only: no unrelated files, no generated .data files,
no test files, no added comments (AGENTS.md read live), gamevals through the gameval conflict check, spotlessCheck
clean. Title: "feat: Hunter skill".

## Definition of done
- the gate passes (accuracy specs in the evidence dir, fork CI and Formatting green on the scratch merge)
- the review passes: scope, upstream style, PR text (pull_request_template.md verbatim, ticks only when true, a plain
  scope list of what is in and what is not, data sources, guesses and gaps), the main hunter activities in game on a
  branch server
- mergeable as it stands (the user, 2026-10-25: "Hunter is not complete. It's missing a checklist item Matches the OSRS
  wiki and there's a list of 'not done'"): every template checklist item ticked and true, no Not done list; each Not
  done item is implemented to match the official game (the user: "dont include any quirks in our changes. If it
  differs from official OSRS, fix it"); no docs/quirks.md entries; no technique is taken out of scope
- after the user's yes: #408 leaves draft once upstream CI is green
