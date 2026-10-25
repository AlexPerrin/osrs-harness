---
slug: members-general-stores
track: server
kind: change
title: 'Members'' general stores: handlers verified from RSProx'
priority: P2
created: '2026-10-20T03:00:41Z'
branch: fix/members-general-stores
---
## Change
Members' general stores: handlers verified from RSProx

## Definition of done
- [ ] transcribe the ~19 candidate RSProx recordings (keeper npc + interface 300) and confirm each keeper -> inv
- [ ] add a handler for every store a recording confirms; resolve Port Phasmatys (233 vs 235) and Quartermaster (159 vs 160) or leave them out
- [ ] unconfirmed stores listed as caveats or left out; league-only recordings marked
- [ ] one PR off upstream main, independent of #371 (no stacking)
- [ ] accuracy spec + green fork CI + Trade checked in game
