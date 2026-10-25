---
slug: client-117hd-feasibility
track: client
kind: change
title: 'Stretch goal: 117 HD on the Android app (feasibility)'
priority: P2
created: '2026-10-20T04:39:08Z'
---
## Change
Stretch goal: 117 HD on the Android app (feasibility)

## Definition of done
- [ ] what 117 HD needs on its own terms (its renderer, GL version and features, shaders, scene and model hooks, texture/material data, memory), independent of RuneLite's GPU plugin
- [ ] the gap against the app's GL context (GLES via libnb) and the Android device, from the reverse/agent; reuse the GPU spike's rendering notes when they exist but don't wait for them
- [ ] a ranked plan for the smallest path to a 117 HD frame on the device (e.g. a GLES port of its shaders, reduced feature set), with blockers and a rough size; written to docs and linked from README
