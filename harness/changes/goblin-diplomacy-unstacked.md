---
slug: goblin-diplomacy-unstacked
track: server
kind: change
title: 'Unstack #367 Goblin Diplomacy and #368 Witch''s Potion'
priority: P2
created: '2026-10-20T01:42:40Z'
branch: content/goblin-diplomacy-unstacked
pr: 367
---
## Change
#367 Goblin Diplomacy (draft since 2026-10-18, user) and #368 Witch's Potion are stacked on #366's old f69c8ed4c (old Sheep Shearer + R&J). Rebuild each off upstream main alone (the -829 branches 4f5e59627 / 4dc1ac9c7 are the candidates, internal PASS); any shared base (QuestTalkFixture) merges upstream first. Then replace #367/#368 with a non-force-push merge commit after the user's OK (sq24).

## Definition of done
- [x] content/goblin-diplomacy and content/witchs-potion each build off upstream main alone with no commit from #366
- [ ] QuestTalkFixture (or whatever shared base) merged upstream before either PR is updated
- [ ] #367 and #368 updated with a merge commit (no force-push) only after the user's OK
- [ ] accuracy/unstack-367-368.md on the fork's docs branch (wiki/cache baseline per rule, RSProx comparison recorded)
- [ ] fork PR open with green CI at the handed-over commit
- [x] one change only, branch off upstream main (no stacking)
