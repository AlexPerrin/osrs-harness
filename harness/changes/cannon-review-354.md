---
slug: cannon-review-354
track: server
kind: change
title: 'Cannon #354: address maintainer review'
priority: P0
created: '2026-10-24T19:31:52Z'
branch: content/cannon
network: true
---
## Change
Upstream #354 is CHANGES_REQUESTED (Mark7625 2026-10-22 07:57, eaglepurerocketgrape 11:42). Head content/cannon 9c08b42ca. Supersedes the BR-C1 fold decision on `cannon`: the fix goes on the PR head itself.

## Definition of done
- [x] Mark7625 inline: replace the `while` loop in DwarfMulticannon.kt (no while functions)
- [x] eaglepurerocketgrape P1: replaceLostCannon (Nulodion.kt 235-250) returns only the parts matching the saved assembly stage (varp.dropcannon), not CANNON_SET.take(4); test reclaim after partial assembly and after a full cannon
- [x] fork CI green; update pushed onto the #354 head content/cannon as a merge/new commit, no force-push, after the user's OK
- [x] reply on #354 listing each fix (after the user's OK)
