---
slug: host-animation-smoothing-setter
track: client
kind: change
title: 'Host: setAnimationInterpolationFilter for Animation Smoothing (the user''s
  built-in plugin)'
priority: P2
created: '2026-10-22T02:08:34Z'
---
## Change
The user runs Animation Smoothing in their own RuneLite; on Android it is not added because the host stubs setAnimationInterpolationFilter (re/evidence/hub-batch-next/user-plugins.md). HANDOFF 7 listed 'client setters for Animation Smoothing' as an open user decision.

## Definition of done
- [ ] setAnimationInterpolationFilter implemented in the host (AndroidClient) with the native side it needs
- [ ] Animation Smoothing switched on and running on the device (logcat or data-tool dump)
- [ ] built (host/build.sh + ninja + repack), repack log 7 telemetry lines
