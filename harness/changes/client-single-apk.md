---
slug: client-single-apk
track: client
title: 'One installable, distributable APK: merge the repacked base and arm64 split into a single signed universal APK'
prio: P0
role: client-dev
stage: dev
hold: null
deps: []
branch: client/client-single-apk
commit: null
local_only: false
owner: cd53
booked:
  dev: '|da39a3ee5e6b'
created: '2026-10-25T02:50:15Z'
updated: '2026-10-25T02:50:15Z'
---
## Change
One installable, distributable APK: merge the repacked base and arm64 split into a single signed universal APK

## Definition of done
- [ ] tools/repack.sh (or a new step it calls) produces ONE APK (re/out/osrs-runelite.apk or a similar single name) from the repacked base.apk and the arm64 split: the split's native libraries (incl. the hook library and the patched game library) are folded into the base, the manifest's split-required flags (android:isSplitRequired and the com.android.vending.splits.required meta-data) are removed, the result is aligned and signed with the same debug key; the split pair stays buildable but is no longer the release artifact
- [ ] The single APK installs with one command (adb install <apk>) on an emulator or an own BlueStacks instance that does not have the original game, starts, loads the hooks and the host (sign-in against the test server, the default plugins), with evidence (logcat extract and a data-tool dump); record what architecture(s) it supports (arm64 only, as the split was) and the install failure modes if any
- [ ] The release flow attaches the single APK: tools/release-dev.sh (or its successor) and the release notes template name it; sha256 recorded; THIRD_PARTY_NOTICES.md still attached; docs and the client skills/role files updated where they say split APKs; no push, no tag, no release (the console handles them)

## Log
- 2026-10-25T02:50:15Z created (ready)
- 2026-10-25T02:50:15Z USER 2026-10-24: 'bundle into one installable, distributable .APK instead of split'. Background: release gate rel-20261024-1 PASSED at d78a893 on base.apk + split.apk (record /home/alex/osrs-plugins-reverse/re/evidence/rel-20261024-1/client-record.md); the v0.1.2 GitHub release was NOT created (also because the client repo master is 4 commits ahead of origin/main). tools/repack.sh header: 'Rebuilds the official OSRS split APKs with libosrsrl.so injected ... signed with re/debug.keystore'; steps: 3 extract game lib from split_config.arm64_v8a.apk, 4 add hook library to the ABI split, 5 align + sign with one key. The original app is a split install (base + split_config.arm64_v8a + others in the main checkout root). BlueStacks is open and belongs to the user: start your OWN BlueStacks instance or an Android Studio emulator (the emulator has a GLES version limitation per the user), never touch the open instance. After the build, the release gate must re-run on this exact artifact.
- 2026-10-25T02:50:15Z ready -> dev: dispatched to cd53
- 2026-10-25T02:50:15Z run cd53 started (client-dev, stage dev)
