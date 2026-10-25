---
slug: hunter-split-ship
track: server
kind: change
title: 'Hunter: split the 7 fin/hunter-* branches and ship each'
priority: P2
deps:
- cannon-review-354
- genie-review-355
- goblin-diplomacy-review-367
- witchs-potion-review-368
created: '2026-10-20T01:42:41Z'
---
## Change
7 fin/hunter-* branches (local only, re/upstream-pr/dev-hunter): linearise rumours (the older linear rumours are archived as refs/archive/sd22/fin-hunter-rumours dcf92ca13 in re/upstream-pr/or), gate each, write texts; integration still uses fin/hunter.

## Definition of done
- [ ] 7 branches each off upstream main alone, pushed to the fork, with PR text
- [ ] integration.txt uses the split branches instead of fin/hunter
- [ ] internal gate PASS per branch
- [ ] accuracy/hunter-split-ship.md on the fork's docs branch (wiki/cache baseline per rule, RSProx comparison recorded)
- [ ] fork PR open with green CI at the handed-over commit
- [ ] one change only, branch off upstream main (no stacking)
