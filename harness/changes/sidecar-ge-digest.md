---
slug: sidecar-ge-digest
track: client
kind: change
title: 'Sidecar: serve the GE digest (404 now, client retries every 10 s)'
priority: P3
created: '2026-10-20T03:34:37Z'
network: true
---
## Change
Sidecar: serve the GE digest (404 now, client retries every 10 s)

## Definition of done
- [ ] the sidecar (10.0.2.2:8080) answers GET /m=itemdb_oldschool/g=oldscape/digest.csv with 200 and a CSV (from the server's GE data, or an empty valid CSV if none), and the client fetches it once per login instead of every ~10 s (logcat/sidecar log as evidence)
- [ ] docs/client-state.md and docs/app-telemetry.md: drop 'No GE digest fetch captured yet'; add the dated Network QA entry from re/evidence/netqa-ge-digest/notes.txt
- [ ] no request leaves for Jagex hosts (network: re-run the DNS/socket check after the change)
