---
slug: sheep-shearer-thing-runaway
track: server
kind: change
title: 'Sheep Shearer: The Thing runs away when sheared'
priority: P3
created: '2026-10-20T01:42:40Z'
branch: fix/sheep-shearer-thing-runaway
---
## Change
Implement the penguin (The Thing) running away on shear per the OSRS Wiki, lifting the caveat in #366's PR text.

## Definition of done
- [ ] Shearing The Thing makes it run away as on the wiki (message, movement, no wool), with the RSProx recording as evidence where it covers it
- [ ] accuracy/sheep-shearer-thing-runaway.md on the fork's docs branch (wiki/cache baseline per rule, RSProx comparison recorded)
- [ ] fork PR open with green CI at the handed-over commit
- [ ] one change only, branch off upstream main (no stacking)
