---
slug: client-readme-single-apk
track: client
title: README install and legal sections for the single-APK release that packages Jagex's app
prio: P1
role: client-dev
stage: dev
hold: null
deps: []
branch: client/client-readme-single-apk
commit: null
local_only: false
owner: cd55
booked:
  dev: '|da39a3ee5e6b'
created: '2026-10-25T03:15:39Z'
updated: '2026-10-25T03:15:39Z'
---
## Change
README install and legal sections for the single-APK release that packages Jagex's app

## Definition of done
- [ ] On top of branch client/client-public-readme (bdf9b3b): the Install section describes the current distribution truthfully: the release has ONE APK (osrs-runelite.apk or the tag-named file) with its sha256 and THIRD_PARTY_NOTICES.md, installed with one adb install or by sideloading, arm64 only, replaces the official app (same package, different key: uninstall the official app first, data is lost), connects to an OpenRune-compatible TEST server; the Legal and safety section states plainly that the APK contains Jagex's Old School RuneScape app content which this project's ISC licence does not cover, that the project is not affiliated with or endorsed by Jagex or RuneLite, that the trademarks are Jagex's, that using it on Jagex's live servers is not its purpose and may break their rules and risk an account, and makes no claim of safety, approval or ban-proofing; the APK alone loads no plugins: say how plugins get on the device (files/plugins) and what the release ships
- [ ] The release download link points at releases/latest (no invented file name); the README mentions the demo video only as 'coming' (no placeholder links); the LICENSE title-line edit is left alone; README only; 41 relative links stay valid (check-links); no push, no release

## Log
- 2026-10-25T03:15:39Z created (ready)
- 2026-10-25T03:15:39Z USER 2026-10-24: 'continue with a single apk that packages jagex app'. Distribution = the repacked single APK (contains Jagex's app content). The risk was flagged once; it is the user's decision. Update the README on top of client/client-public-readme (bdf9b3b, worktree /home/alex/osrs-plugins-reverse/.claude/worktrees/cd54 may still exist; make a new worktree from that branch if not). Facts from cd54's report: the APK alone loads no plugins (the host reads plugin jars from files/plugins on the device; no release attaches jars); Braze/OneTrust/Google/FCM are active; the Hiscore plugin contacts Jagex's public hiscores when used; v0.1.0 (published 2026-10-19) has the base and split APKs; v0.1.1 has no assets; the new release v0.1.2 will carry the single APK (gate cq5 running at master 2e7a849). Do not claim anything the evidence under /home/alex/osrs-plugins-reverse/re/evidence/ does not show.
- 2026-10-25T03:15:39Z ready -> dev: dispatched to cd55
- 2026-10-25T03:15:39Z run cd55 started (client-dev, stage dev)
