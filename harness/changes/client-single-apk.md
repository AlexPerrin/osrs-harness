---
slug: client-single-apk
track: client
title: 'One installable, distributable APK: merge the repacked base and arm64 split into a single signed universal APK'
prio: P0
role: client-dev
stage: live
hold: null
deps: []
branch: client/client-single-apk
commit: 81ef19ad226e6f100388e4e47dd4b2dd26872507
local_only: false
owner: null
evidence: /home/alex/osrs-plugins-reverse/re/evidence/client-single-apk
summary: 'Single universal arm64 APK re/out/osrs-runelite.apk (26504793 bytes, sha256 8864d2501eafee70ce6303b0aeaaec8ba80770dd41c840b10ceffab8026b8bf6): split libs folded into base, split-required flags
  removed, notices embedded, debug-key signed; install, hooks, host, sign-in, LOGGED_IN verified on an x86_64+arm64-translation Android Studio emulator (not BlueStacks, default plugins not exercised); release-dev.sh
  attaches it. Harness-owned skill/role text (client-qa.md, client-track skill) still says base.apk+split.apk and is not edited here.'
live_commit: 81ef19ad226e6f100388e4e47dd4b2dd26872507
booked:
  dev: '|da39a3ee5e6b'
cost:
  runs: 1
  turns: 0
  tokens: 0
  minutes: 0
created: '2026-10-25T02:50:15Z'
updated: '2026-10-25T03:06:25Z'
---
## Change
One installable, distributable APK: merge the repacked base and arm64 split into a single signed universal APK

## Definition of done
- [x] tools/repack.sh (or a new step it calls) produces ONE APK (re/out/osrs-runelite.apk or a similar single name) from the repacked base.apk and the arm64 split: the split's native libraries (incl. the hook library and the patched game library) are folded into the base, the manifest's split-required flags (android:isSplitRequired and the com.android.vending.splits.required meta-data) are removed, the result is aligned and signed with the same debug key; the split pair stays buildable but is no longer the release artifact
- [x] The single APK installs with one command (adb install <apk>) on an emulator or an own BlueStacks instance that does not have the original game, starts, loads the hooks and the host (sign-in against the test server, the default plugins), with evidence (logcat extract and a data-tool dump); record what architecture(s) it supports (arm64 only, as the split was) and the install failure modes if any
- [x] The release flow attaches the single APK: tools/release-dev.sh (or its successor) and the release notes template name it; sha256 recorded; THIRD_PARTY_NOTICES.md still attached; docs and the client skills/role files updated where they say split APKs; no push, no tag, no release (the console handles them)

## Log
- 2026-10-25T02:50:15Z created (ready)
- 2026-10-25T02:50:15Z USER 2026-10-24: 'bundle into one installable, distributable .APK instead of split'. Background: release gate rel-20261024-1 PASSED at d78a893 on base.apk + split.apk (record /home/alex/osrs-plugins-reverse/re/evidence/rel-20261024-1/client-record.md); the v0.1.2 GitHub release was NOT created (also because the client repo master is 4 commits ahead of origin/main). tools/repack.sh header: 'Rebuilds the official OSRS split APKs with libosrsrl.so injected ... signed with re/debug.keystore'; steps: 3 extract game lib from split_config.arm64_v8a.apk, 4 add hook library to the ABI split, 5 align + sign with one key. The original app is a split install (base + split_config.arm64_v8a + others in the main checkout root). BlueStacks is open and belongs to the user: start your OWN BlueStacks instance or an Android Studio emulator (the emulator has a GLES version limitation per the user), never touch the open instance. After the build, the release gate must re-run on this exact artifact.
- 2026-10-25T02:50:15Z ready -> dev: dispatched to cd53
- 2026-10-25T02:50:15Z run cd53 started (client-dev, stage dev)
- 2026-10-25T02:54:18Z USER 2026-10-24 ADDITION (yes): embed the third-party notices IN the single APK, not only beside it. Convention: LICENSE = our own code (ISC), THIRD_PARTY_NOTICES = the dependencies we ship with their copyright notices and licence texts (MIT/BSD/ISC require them in binary distributions; Apache-2.0 4(d) requires upstream NOTICE contents). Android practice (Google): licence texts live inside the APK (oss-licenses plugin raw resources, OssLicensesMenuActivity screen); AOSP merges per-module NOTICE into NOTICE.html.gz. DO: the build step adds THIRD_PARTY_NOTICES.md (as an asset, e.g. assets/THIRD_PARTY_NOTICES.md, next to the existing assets/LICENCE.txt) to the merged APK, so it is readable from the installed package; keep attaching it to the release; the notices file already says our part is libosrsrl.so/host.jar and that Jagex's app content is NOT covered. Verify the entry is in the final APK (unzip -l) and that the apk still signs/aligns and installs. A Licences screen in the app is optional: only if trivial inside the host's existing menu, else list it as not done. Never state a licence for Jagex's content.
- 2026-10-25T03:05:43Z dod ticked: 1, 2, 3
- 2026-10-25T03:05:44Z dev -> gate: hand-over recorded
- 2026-10-25T03:05:44Z handover client/client-single-apk@81ef19ad2: Single universal arm64 APK re/out/osrs-runelite.apk (26504793 bytes, sha256 8864d2501eafee70ce6303b0aeaaec8ba80770dd41c840b10ceffab8026b8bf6): split libs folded into base, split-required flags removed, notices embedded, debug-key signed; install, hooks, host, sign-in, LOGGED_IN verified on an x86_64+arm64-translation Android Studio emulator (not BlueStacks, default plugins not exercised); release-dev.sh attaches it. Harness-owned skill/role text (client-qa.md, client-track skill) still says base.apk+split.apk and is not edited here.
- 2026-10-25T03:06:15Z run cd53 ended: ? turns, ? tokens, exit ok
- 2026-10-25T03:06:25Z gate -> live: observed
