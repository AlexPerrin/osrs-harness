---
slug: harness-no-screenshots
track: harness
kind: change
title: 'Agents read client state through the data tools, not screenshots'
priority: P0
deps: []
created: '2026-10-26T03:20:00Z'
---
## Change
The user, 2026-10-25: "Still taking screenshots". The shared rule (CLAUDE.md, test-instances) says client state is read through the data tools and agents take no screenshots unless the user asks, yet every recent client run read 17-85 screenshots (`adb exec-out screencap` saved as scratchpad/<run>/s*.png, then Read): client-api-probe-reach-1 85, client-api-host-gaps-reach-1 38, client-api-projectile-2 37, client-devtools-menu-actions-2 19, and others. Find from those transcripts what each screenshot was for (likely: the Android home screen and app launch, the login screen before the plugin host is up, the terms of service, dialogs or the Play services update, placing taps), give each need a data-tool or text way (e.g. `uiautomator dump`, `dumpsys activity`, logcat, osrs-devtools reads, a scripted login), and make the rule hold: the guard refuses a screen capture (adb screencap, screenrecord, Windows screen copy) and a Read of an image an agent made, unless the change definition says the user asked for one.

## Definition of done
- Each screenshot use found in the recent client transcripts has a non-image way, written into the test-instances/device-test skills (and a script under bench/ where one is needed, e.g. the emulator login).
- The guard refuses a screen capture command and a Read of a .png/.jpg under a scratchpad or evidence dir for every role, with a test; a change whose definition names "screenshot" as the user's request is let through, with a test.
- One client run (or a dry run of the login path on your own Agent_Phone emulator) logs in and reaches the game with no image read.
