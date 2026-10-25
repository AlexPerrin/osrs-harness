---
slug: cannon
track: server
title: 'Cannon (#354): PR text and spec header wording for the upstream gate'
prio: P1
role: server-dev
stage: review
hold: null
deps: []
branch: acc/cannon
commit: bc243d141fc27d5128d29d8266cf51e89a4f6c08
local_only: false
owner: null
evidence: /home/alex/osrs-plugins-reverse/re/evidence/fix-acc-cannon-text
spec: cannon
summary: 'Text only, fork docs 4c75a5850: PR text checklist and spec header now say none of the RSProx recordings we have (rsprox.net database) shows a player cannon; RESULTS_PENDING filled from CI 39350604565;
  in-game paragraph cites sq24''s run at bc243d141; boots box ticked; fork PR #20 body updated. sq24''s record 60f5e23ea was not on fork docs: cherry-picked as 3b27fffce and pushed. acc/cannon unchanged
  at bc243d141.'
live_commit: bc243d141fc27d5128d29d8266cf51e89a4f6c08
booked: null
batch: int-20261025-6
created: '2026-10-20T05:16:26Z'
updated: '2026-10-25T03:52:45Z'
upstream_pr: 354
review_seen: '2026-10-25T00:02:54Z'
---
## Change
Cannon (#354): PR text and spec header wording for the upstream gate

## Definition of done
- [x] pr-texts/cannon.upstream.body (and .title if needed) and the spec header of the cannon accuracy spec on the fork's docs branch say 'none of the RSProx recordings we have (rsprox.net database) shows a player cannon' instead of 'we have no dumps of the official game'; rest of the text re-read against acc/cannon bc243d141 (pr-text-review)
- [x] no code change; acc/cannon stays at bc243d141 with its green CI

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: fix-acc-cannon-text, gate-acc-cannon
- 2026-10-21T00:25:19Z hold decision: branch acc/cannon is not one-change-one-branch (BR-C1): fold into content/cannon (changes the upstream PR head: your OK per PR), then point integration at it
- 2026-10-22T00:00:47Z live -> checked: drift: integration pin is absent, not bc243d141 (next train)
- 2026-10-24T19:32:22Z 2026-10-24 reset: review fixes are cannon-review-354 (on the PR head content/cannon)
- 2026-10-25T00:02:45Z gate -> review: observed
- 2026-10-25T00:08:33Z hold decision cleared: obsolete: #354/#367 heads updated and in review (user OK 2026-10-24)
- 2026-10-25T00:15:15Z in train int-20261025-1: integration 7c62b8341 pushed; gate, image and deploy pending
- 2026-10-25T00:54:44Z in train int-20261025-1: integration e5d0a43ba pushed; gate, image and deploy pending
- 2026-10-25T01:09:44Z in train int-20261025-2: integration 5dccf9d0b pushed; gate, image and deploy pending
- 2026-10-25T03:52:45Z in train int-20261025-6: integration ed23f075c pushed; gate, image and deploy pending
