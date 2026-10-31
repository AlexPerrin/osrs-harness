---
slug: harness-dupe-check
track: harness
kind: change
title: 'Dupe check: AGENTS.md''s dupe tests for item-moving flows, a skill for dev
  and QA, and a gate check'
priority: P1
deps: []
created: '2026-10-31T18:22:50Z'
---
## Change
The user, 2026-10-31: tests + skill + gate. Upstream AGENTS.md (since #304; read it live on upstream main, section 'Unit tests — where they earn their keep') requires a unit test proving no item can be duplicated or lost for every flow that moves items in or out of an inventory, bank, shop, trade, equipment slot or ground stack, covering: full inventory / no space mid-transaction (the whole action rolls back); stack overflow at Int.MAX_VALUE; repeated or same-tick clicks and the source item vanishing between the check and the take; every obj's total count before and after matching what the action is meant to do. The template item 'Tests only cover complex logic and anything that moves items (no dupes)' points at it.

- A skill `dupe-check` (.claude/skills/dupe-check/SKILL.md): how a server dev finds the item-moving flows in its diff and writes the dupe tests upstream's way (look at how upstream main's existing tests build players and inventories), and how server-qa checks each flow's four paths (the tests, plus a short in-game try on the branch server).
- The no-tests default (skill server-track, role files, the memory rule) gets this exception: item-moving flows need dupe tests; other tests stay as they are.
- The server gate (gates/server.py) fails a change whose net diff moves items without a dupe test in the same module: a simple, observable rule (for example, the diff adds calls of the fork's item-moving API in main sources, and no test source under that module is added or changed); its scan output names the flows for the reviewer. Find the API names in the fork (api/ inventory/bank/obj code), do not guess them.
- A test per requirement touched (tests/), docs/ARCHITECTURE.md updated.

## Definition of done
- the skill, the rule exception and the gate check are in, with tests; python3 -m unittest discover -s tests passes
- the gate check run against the open server dev heads (hunter-feat-pr, server-friends-chat-clan-channels, goblin-diplomacy-review-367-fftgsrq) reports which flows lack dupe tests, in the hand-over
