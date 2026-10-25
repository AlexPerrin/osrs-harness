---
slug: sidecar-ge-digest
track: client
title: 'Sidecar: serve the GE digest (404 now, client retries every 10 s)'
prio: P3
role: client-dev
stage: ready
hold:
  kind: decision
  reason: 'held (user 2026-10-24): settle open PRs first; client changes wait for BlueStacks; unhold when ready'
  since: '2026-10-25T00:39:45Z'
deps: []
branch: null
commit: null
local_only: false
owner: null
network: true
created: '2026-10-20T03:34:37Z'
updated: '2026-10-25T00:39:45Z'
---
## Change
Sidecar: serve the GE digest (404 now, client retries every 10 s)

## Definition of done
- [ ] the sidecar (10.0.2.2:8080) answers GET /m=itemdb_oldschool/g=oldscape/digest.csv with 200 and a CSV (from the server's GE data, or an empty valid CSV if none), and the client fetches it once per login instead of every ~10 s (logcat/sidecar log as evidence)
- [ ] docs/client-state.md and docs/app-telemetry.md: drop 'No GE digest fetch captured yet'; add the dated Network QA entry from re/evidence/netqa-ge-digest/notes.txt
- [ ] no request leaves for Jagex hosts (network: re-run the DNS/socket check after the change)

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: sidecar-ge-digest
- 2026-10-22T02:08:34Z triage: not on the user's plugin list
- 2026-10-25T00:39:45Z hold decision: held (user 2026-10-24): settle open PRs first; client changes wait for BlueStacks; unhold when ready
