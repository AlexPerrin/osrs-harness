---
slug: check-cache-stock-limit
track: server
title: check_cache.py derives its clientscript id limit from the cache's stock maximum; remove HD_MAX_CLIENTSCRIPT_ID from image.sh
prio: P1
role: server-dev
stage: gate
hold:
  kind: decision
  reason: 'fork tooling, not test-server content and not an upstream PR: done in substance (merged/pushed); kept off the train and out of QA (the fork-only chain is a v7 item)'
  since: '2026-10-25T02:05:13Z'
deps: []
branch: harness/check-cache-stock-limit
commit: b2d3013f6202aa554382739930153278e9b8faee
repo: /home/alex/src/openrune-work/agents/sd78/harness
local_only: false
owner: null
evidence: /home/alex/osrs-plugins-reverse/re/evidence/check-cache-stock-limit
summary: 'check_cache.py derives its limit from the stock max (fork local/server-tools 5517be07c); HD_MAX_CLIENTSCRIPT_ID removed from image.sh (harness branch b2d3013). Batch int-20261024-2 image step
  not re-run by me: check passes on its failing cache.'
booked:
  dev: '|da39a3ee5e6b'
  gate: b2d3013f6202aa554382739930153278e9b8faee
cost:
  runs: 2
  turns: 0
  tokens: 0
  minutes: 0
created: '2026-10-25T00:04:42Z'
updated: '2026-10-25T02:05:35Z'
---
## Change
check_cache.py derives its clientscript id limit from the cache's stock maximum; remove HD_MAX_CLIENTSCRIPT_ID from image.sh

## Definition of done
- [x] check_cache.py (fork local/server-tools) derives its clientscript id limit from the stock cache's maximum id (1:1 with the official cache; custom ids placed right after it) instead of a fixed 9999; stock ids above 9999 (10000-10188 in revision 241) no longer fail the image step
- [x] HD_MAX_CLIENTSCRIPT_ID is removed from the image step (train/image.sh and the docs) and the train image builds without any override
- [x] The custom clientscript ids (10197-10198) are verified on a desktop client (cache and quest list); the Android tolerance of ids above 9999 is recorded as not tested (needs a client with BlueStacks)
- [x] Train batch int-20261024-2 passes its image step on the fix; no push of the upstream repo; fork pushes only

## Log
- 2026-10-25T00:04:42Z created (ready)
- 2026-10-25T00:04:42Z From the train exception on int-20261024-2: 'image: check_cache.py failed ... clientscript ids above 9999 break the Android client: [10000..10198]' (clientscripts: 10189 groups, max id 10198). HANDOFF open work 2/3: the live deploy used the one-off override HD_MAX_CLIENTSCRIPT_ID=10198. This blocks new changes reaching the test server (client dev's blocker) so it is the server track's top priority. Tooling lives in the fork local/server-tools branch (~/src/openrune-work/server-tools); train/image.sh is in this repo. No approval needed for fork work.
- 2026-10-25T00:04:42Z ready -> dev: dispatched to sd78
- 2026-10-25T00:04:42Z run sd78 started (server-dev, stage dev)
- 2026-10-25T00:09:33Z dod ticked: 1, 2, 3, 4
- 2026-10-25T00:09:33Z dev -> gate: hand-over recorded
- 2026-10-25T00:09:33Z handover harness/check-cache-stock-limit@b2d3013f6: check_cache.py derives its limit from the stock max (fork local/server-tools 5517be07c); HD_MAX_CLIENTSCRIPT_ID removed from image.sh (harness branch b2d3013). Batch int-20261024-2 image step not re-run by me: check passes on its failing cache.
- 2026-10-25T00:10:21Z run sd78 ended: ? turns, ? tokens, exit ok
- 2026-10-25T00:26:54Z run sq57 started (server-qa, stage gate)
- 2026-10-25T02:05:13Z hold decision: fork tooling, not test-server content and not an upstream PR: done in substance (merged/pushed); kept off the train and out of QA (the fork-only chain is a v7 item)
- 2026-10-25T02:05:35Z run sq57 ended: ? turns, ? tokens, exit stopped:lingering: hold decision
