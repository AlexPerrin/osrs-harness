---
slug: check-cache-stock-limit
track: server
kind: change
title: check_cache.py derives its clientscript id limit from the cache's stock maximum;
  remove HD_MAX_CLIENTSCRIPT_ID from image.sh
priority: P1
created: '2026-10-25T00:04:42Z'
branch: harness/check-cache-stock-limit
---
## Change
check_cache.py derives its clientscript id limit from the cache's stock maximum; remove HD_MAX_CLIENTSCRIPT_ID from image.sh

## Definition of done
- [x] check_cache.py (fork local/server-tools) derives its clientscript id limit from the stock cache's maximum id (1:1 with the official cache; custom ids placed right after it) instead of a fixed 9999; stock ids above 9999 (10000-10188 in revision 241) no longer fail the image step
- [x] HD_MAX_CLIENTSCRIPT_ID is removed from the image step (train/image.sh and the docs) and the train image builds without any override
- [x] The custom clientscript ids (10197-10198) are verified on a desktop client (cache and quest list); the Android tolerance of ids above 9999 is recorded as not tested (needs a client with BlueStacks)
- [x] Train batch int-20261024-2 passes its image step on the fix; no push of the upstream repo; fork pushes only
