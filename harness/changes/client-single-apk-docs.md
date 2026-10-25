---
slug: client-single-apk-docs
track: harness
title: client-qa role file and client-track skill describe the single universal APK
prio: P0
role: harness-dev
stage: live
hold: null
deps: []
branch: main
commit: 2b19e576a6e9ce1c120dc5ebc2595ce9ff9c6fca
local_only: false
owner: null
evidence: /home/alex/osrs-harness/docs
summary: 'Merged into main: single APK in the client-qa role file and the client-track skill.'
live_commit: 2b19e576a6e9ce1c120dc5ebc2595ce9ff9c6fca
booked:
  dev: '|da39a3ee5e6b'
cost:
  runs: 1
  turns: 0
  tokens: 0
  minutes: 0
created: '2026-10-25T03:08:17Z'
updated: '2026-10-25T03:12:07Z'
---
## Change
client-qa role file and client-track skill describe the single universal APK

## Definition of done
- [x] .claude/agents/client-qa.md and .claude/skills/client-track/SKILL.md (and any other .claude file or doc that says base.apk + split.apk for the release artifact) name the single artifact re/out/osrs-runelite.apk: the release gate copies it, THIRD_PARTY_NOTICES.md and the repack log into the evidence dir; the gate checks (a) one 'adb install' on a device or emulator WITHOUT the original game (an installed official copy gives INSTALL_FAILED_UPDATE_INCOMPATIBLE: uninstall first), (b) hooks load and the host starts, sign-in against the test server, (c) THIRD_PARTY_NOTICES.md is embedded as an asset (unzip -l) and equals the committed file, (d) apksigner verify and zipalign -c, (e) the existing privacy and network checks on the single APK, (f) arm64-v8a only; the artifact sha256 goes in the record
- [x] docs minimal and current truth (PRD/ARCHITECTURE only if a requirement changed); full suite passes; no push, no daemon restart

## Log
- 2026-10-25T03:08:17Z created (ready)
- 2026-10-25T03:08:17Z From cd53's report (client-single-apk handed over at 81ef19a, merged into client master 2ec736d): repack.sh now produces re/out/osrs-runelite.apk (one APK: the arm64 split's libs folded into the base, split-required flags removed, THIRD_PARTY_NOTICES.md embedded as assets/THIRD_PARTY_NOTICES.md, signed with re/debug.keystore); tools/release-dev.sh attaches it. Lines to fix: .claude/agents/client-qa.md line ~27 and .claude/skills/client-track/SKILL.md line ~36. Emulator quirks the gate should know (from docs/client-state.md in the client repo): Chrome needs 'pm grant com.android.chrome android.permission.ACCESS_LOCAL_NETWORK' for 10.0.2.2; the first-run OneTrust dialog is closed with its X; a shell-pushed files/plugins dir needs chmod 777; after a force-stop the server holds the session for a while. Harness fix, apply now. Work in a worktree: git reset --hard main first.
- 2026-10-25T03:08:17Z ready -> dev: dispatched to hd31
- 2026-10-25T03:08:17Z run hd31 started (harness-dev, stage dev)
- 2026-10-25T03:10:18Z dod ticked: 1, 2
- 2026-10-25T03:10:56Z run hd31 ended: ? turns, ? tokens, exit ok
- 2026-10-25T03:11:14Z dev -> gate: hand-over recorded
- 2026-10-25T03:11:14Z handover main@2b19e576a: Merged into main: single APK in the client-qa role file and the client-track skill.
- 2026-10-25T03:12:07Z gate -> live: observed
