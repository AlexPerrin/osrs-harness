---
slug: client-public-readme
track: client
title: Public README for the client repo (shareable on media) and a demo video plan
prio: P1
role: client-dev
stage: gate
hold: null
deps: []
branch: client/client-public-readme
commit: bdf9b3b5b958b824c4bb6ad215e09fb44aee5182
local_only: false
owner: null
evidence: /home/alex/osrs-plugins-reverse/re/evidence/client-public-readme
summary: Public README rewritten (10 sections, numbers from the generated progress block and plugin-host.md counts, observations cited, legal and safety, install true of the current build); demo video plan
  (9 shots) and capture.sh in the evidence dir; no clips recorded, docs/media not created (no real assets exist), no placeholder links; no dead links
booked:
  dev: '|da39a3ee5e6b'
cost:
  runs: 1
  turns: 0
  tokens: 0
  minutes: 0
created: '2026-10-25T03:05:20Z'
updated: '2026-10-25T03:13:18Z'
---
## Change
Public README for the client repo (shareable on media) and a demo video plan

## Definition of done
- [x] README.md in the client repo (osrs-plugins-reverse) is rewritten for a public audience: one-paragraph pitch, what works today with the current measured numbers (run hd status for the progress tiles: RuneLite API coverage, plugins running on Android, Plugin Hub plugins, mobile packets mapped; never invent a number), a short how-it-works (the native hook library libosrsrl.so plus the Java plugin host host.jar with a subset of the RuneLite client running inside the official OSRS Android app), screenshot/GIF/video placeholders that resolve to real files in docs/media, requirements and install (single APK once client-single-apk lands; connects to an OpenRune-compatible TEST server, 10.0.2.2:43594 on the emulator, never Jagex's live servers), a plain 'what this is not' section, project status and roadmap, building from source, contributing, licences and credits (LICENSE is ISC; THIRD_PARTY_NOTICES.md; RuneLite BSD-2; the Plugin Hub plugins' own licences)
- [x] A legal and safety section stated accurately and plainly: not affiliated with or endorsed by Jagex or RuneLite; Old School RuneScape and RuneScape are trademarks of Jagex Ltd; the release artifact contains Jagex's app content which this project's licence does not cover (the notices file says so); use on Jagex's official servers is not what this is for and may break their rules, with the account risk stated honestly; no claim the project is safe, approved or ban-proof; no claim that is not true of the code (check native/, host/, tools/ before each technical statement)
- [x] docs/media/ holds the real assets that exist (no broken links): and a demo video PLAN in the evidence dir (storyboard with 6-10 shots of RuneLite features and plugins running on Android: Ground Items despawn timers, Clue Steps, the plugin panel/menu, the host's plugin list, an installed Plugin Hub plugin, the login to the test server; for each shot: what to show, which plugin or feature, the exact steps and the data to read to prove it works, the target length 60-90 seconds) plus a capture script using adb screenrecord or scrcpy against the agent's OWN device or emulator; record raw clips only if an own instance is available and say what was recorded; clips go to the evidence dir, not into the repo
- [x] No claim in the README that the demo or any feature works unless it was observed (cite the evidence dir for the observation); the README is checked once for dead links; the rest of the repo is not changed; no push, no release (the console handles it)

## Log
- 2026-10-25T03:05:20Z created (ready)
- 2026-10-25T03:05:20Z USER 2026-10-24: 'Prepare the client GitHub repo README for a public release. Something that can be shared on media. Consider a demo video of runelite features and plugins.' Constraints: the repo is client-only (osrs-plugins-reverse); the client is RuneLite plugins inside the official OSRS Android app; the release APK includes Jagex's app content (see THIRD_PARTY_NOTICES.md 'Not covered: Jagex's Old School RuneScape app') and connects to the OpenRune TEST server; the console flags the distribution/legal model to the user separately, so write the Install and Legal sections as true of the CURRENT build and flag in your report anything that depends on a decision (bring-your-own-APK patcher vs shipping the repacked APK). Public wording must be factual, short and sober: no hype beyond what was observed; every number from hd status or the evidence. BlueStacks is open and belongs to the user: never touch it; use your own emulator or instance.
- 2026-10-25T03:05:20Z ready -> dev: dispatched to cd54
- 2026-10-25T03:05:20Z run cd54 started (client-dev, stage dev)
- 2026-10-25T03:12:25Z dod ticked: 1, 2, 3, 4
- 2026-10-25T03:12:26Z dev -> gate: hand-over recorded
- 2026-10-25T03:12:26Z handover client/client-public-readme@bdf9b3b5b: Public README rewritten (10 sections, numbers from the generated progress block and plugin-host.md counts, observations cited, legal and safety, install true of the current build); demo video plan (9 shots) and capture.sh in the evidence dir; no clips recorded, docs/media not created (no real assets exist), no placeholder links; no dead links
- 2026-10-25T03:12:57Z run cd54 ended: ? turns, ? tokens, exit ok
- 2026-10-25T03:13:18Z ship: merged into master 32b4573, pushed
