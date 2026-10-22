---
slug: hub-clue-steps-tier
track: client
title: Clue Steps hub plugin
prio: P2
role: client-dev
stage: live
hold: null
deps:
- treasure-trails
branch: client/hub-clue-steps-tier
commit: d66e4c3ee3238638d950e7b61d4a7b022d5f34cc
local_only: false
owner: null
instances:
- device
evidence: /home/alex/osrs-plugins-reverse/re/evidence/hub-clue-steps-tier
summary: 'Clue Steps hub plugin reads the step count from the live server''s tiered Check message on the device: easy clue 2677, Check -> ''You have completed N steps on this easy clue scroll.'', plugin
  stores clueSteps.rsprofile.default.clueEasy = N (0; 3 via the say probe then 0 by a real Check, chat path isolated; 2 after ::varp trail_easy_steps_done 2). No plugin, host or native change: branch d66e4c3
  = master 3aca471 + plugin-host row and client-state rewrite. Built (host/build.sh + ninja + repack, 7 telemetry lines), evidence re/evidence/hub-clue-steps-tier/ (data-tool dump, host logcat extract,
  device capture, repack.log, README). Slot restored (restore check all OK, lease released).'
live_commit: d66e4c3ee3238638d950e7b61d4a7b022d5f34cc
cost:
  runs: 1
  turns: 0
  minutes: 0.0
  usd: 0
created: '2026-10-20T01:42:43Z'
updated: '2026-10-22T02:08:34Z'
---
## Change
Clue Steps hub plugin reads the steps/tier message on the device once the server includes the tier (docs/client-state.md Next tasks 1).

## Definition of done
- [x] Clue Steps shows the step count for a clue after Check on the device
- [x] built (host/build.sh + ninja + repack); changed path tried on the device with a screenshot or logcat in re/evidence/hub-clue-steps-tier/

## Log
- 2026-10-21T00:25:19Z migrated from v2 tasks: hub-clue-steps-tier
- 2026-10-22T01:33:23Z ready -> dev: dispatched to cd49
- 2026-10-22T01:33:23Z run cd49 started (client-dev, stage dev, instances device)
- 2026-10-22T01:52:51Z handover client/hub-clue-steps-tier@d66e4c3ee: Clue Steps hub plugin reads the step count from the live server's tiered Check message on the device: easy clue 2677, Check -> 'You have completed N steps on this easy clue scroll.', plugin stores clueSteps.rsprofile.default.clueEasy = N (0; 3 via the say probe then 0 by a real Check, chat path isolated; 2 after ::varp trail_easy_steps_done 2). No plugin, host or native change: branch d66e4c3 = master 3aca471 + plugin-host row and client-state rewrite. Built (host/build.sh + ninja + repack, 7 telemetry lines), evidence re/evidence/hub-clue-steps-tier/ (data-tool dump, host logcat extract, device capture, repack.log, README). Slot restored (restore check all OK, lease released).
- 2026-10-22T01:53:46Z dev -> checked: hand-over check PASS
- 2026-10-22T01:53:48Z ship: merged into master dfade26, pushed
- 2026-10-22T01:53:48Z run cd49 ended: ? turns, 0.0 min, $0, exit stopped:lingering: owner is None (change at checked)
- 2026-10-22T01:54:37Z checked -> live: observed
