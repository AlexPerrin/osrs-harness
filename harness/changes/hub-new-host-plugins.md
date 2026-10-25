---
slug: hub-new-host-plugins
track: client
kind: change
title: 'The user''s hub plugins that contact a new host: WikiSync, AFK Marks Canifis,
  Quest Voiceover'
priority: P2
created: '2026-10-22T02:08:34Z'
network: true
---
## Change
Three of the user's plugins need outbound hosts the app does not contact today: WikiSync (sync.runescape.wiki uploads), AFK Marks Canifis (an NTP socket), Quest Voiceover (voice files from github.com, sqlite-jdbc). Privacy rule: any new outbound host is the user's decision (HANDOFF 7).

## Definition of done
- [ ] each plugin approved by the user built with netcheck (its host listed in docs/app-telemetry.md) or recorded as excluded with the reason
- [ ] Network QA on the build (new hosts expected)
