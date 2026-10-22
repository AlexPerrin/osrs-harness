---
slug: hub-new-host-plugins
track: client
title: 'The user''s hub plugins that contact a new host: WikiSync, AFK Marks Canifis, Quest Voiceover'
prio: P2
role: client-dev
stage: ready
hold:
  kind: decision
  reason: 'your open decision (HANDOFF 7): allow WikiSync (sync.runescape.wiki), AFK Marks Canifis (NTP), Quest Voiceover (github.com fetches)? Name the ones to allow in the note.'
  since: '2026-10-22T02:08:34Z'
deps: []
branch: null
commit: null
local_only: false
owner: null
instances: []
network: true
created: '2026-10-22T02:08:34Z'
updated: '2026-10-22T02:08:34Z'
---
## Change
Three of the user's plugins need outbound hosts the app does not contact today: WikiSync (sync.runescape.wiki uploads), AFK Marks Canifis (an NTP socket), Quest Voiceover (voice files from github.com, sqlite-jdbc). Privacy rule: any new outbound host is the user's decision (HANDOFF 7).

## Definition of done
- [ ] each plugin approved by the user built with netcheck (its host listed in docs/app-telemetry.md) or recorded as excluded with the reason
- [ ] Network QA on the build (new hosts expected)

## Log
- 2026-10-22T02:08:34Z created (ready)
- 2026-10-22T02:08:34Z hold decision: your open decision (HANDOFF 7): allow WikiSync (sync.runescape.wiki), AFK Marks Canifis (NTP), Quest Voiceover (github.com fetches)? Name the ones to allow in the note.
