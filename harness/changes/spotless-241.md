---
slug: spotless-241
track: server
title: Spotless formatting of PrayerRepository.kt after upstream 241 Latest Support (local-only)
prio: P1
role: server-dev
stage: checked
hold: null
deps: []
branch: local/spotless-241
commit: e6afed4620d1bfecc2cf522a98e3ff00a3477d73
local_only: true
owner: null
instances: []
evidence: re/evidence/spotless-241
summary: one-space spotless fix of PrayerRepository.kt (upstream main f28349cd4 violates spotlessCheck; upstream CI does not run it); local-only until upstream reformats
batch: int-20261022-5
created: '2026-10-22T00:16:41Z'
updated: '2026-10-22T02:08:34Z'
---
## Change
Upstream main f28349cd4 leaves one line of content/interfaces/prayer-tab PrayerRepository.kt unformatted; our integration gate (spotlessCheck) fails on it while upstream CI does not run spotless on main. A one-space fix carried as a local-only branch until upstream reformats.

## Definition of done
- [x] the formatted line only, one commit off current upstream main
- [x] fork CI green at the commit

## Log
- 2026-10-22T00:16:41Z created (ready)
- 2026-10-22T00:18:13Z ready -> dev: hand-over recorded
- 2026-10-22T00:18:13Z handover local/spotless-241@e6afed462: one-space spotless fix of PrayerRepository.kt (upstream main f28349cd4 violates spotlessCheck; upstream CI does not run it); local-only until upstream reformats
- 2026-10-22T00:31:28Z dev -> checked: hand-over check PASS
- 2026-10-22T00:41:46Z in train int-20261022-3: integration a5e4d23f4 pushed; gate, image and deploy pending
- 2026-10-22T01:10:43Z in train int-20261022-4: integration 749d6dd58 pushed; gate, image and deploy pending
- 2026-10-22T02:05:10Z in train int-20261022-5: integration 17c773333 pushed; gate, image and deploy pending
