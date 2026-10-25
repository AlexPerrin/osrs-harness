---
slug: qa-sh-targeted
track: server
title: 'Fork tooling (local/server-tools): qa.sh gate runs targeted module tests by default; the shared cs2 volume is refreshed when stale; dev clones get fork and upstream remotes'
prio: P1
role: server-dev
stage: dev
hold: null
deps: []
branch: null
commit: null
local_only: false
owner: sd82
booked:
  dev: '|da39a3ee5e6b'
created: '2026-10-25T01:31:10Z'
updated: '2026-10-25T01:31:11Z'
---
## Change
Fork tooling (local/server-tools): qa.sh gate runs targeted module tests by default; the shared cs2 volume is refreshed when stale; dev clones get fork and upstream remotes

## Definition of done
- [ ] qa.sh gate/gate-run accepts the touched modules and runs only their test and integration tasks plus spotlessCheck on them by default; the full-suite mode stays behind an explicit flag; documented in the fork tools README
- [ ] The shared cs2 volume used by qa.sh freshCache is detected as stale (cs2 SYNTAX_ERRORs on scripts outside the change, while fork CI on the same merge is green) and refreshed by one command, documented; the check is observed by fact (the freshCache failure shape), not by age
- [ ] Agent clone setup (scripts under local/server-tools) names the remotes fork and upstream and never calls the shared local clone origin; spotless's origin/main ref is set to upstream/main in the setup
- [ ] Fork pushes only (local/server-tools); no upstream push; handed over with hd handover (--repo the tools clone)

## Log
- 2026-10-25T01:31:10Z created (ready)
- 2026-10-25T01:31:10Z USER 2026-10-24: apply quick fixes now. Items j, i from the cutover defect list (handoff-v6 log): qa.sh full gate runs ~790 unit + ~112 integration (too much; the full suite is the fork CI), the shared cs2 volume went stale (262 cs2 SYNTAX_ERRORs in freshCache that fork CI did not see), and dev clones named the shared local clone 'origin' (a scratch merge merged the wrong main once; spotless needs refs/remotes/origin/main = upstream/main). Tooling lives in the fork branch local/server-tools (~/src/openrune-work/server-tools); fork actions need no approval; never push to OpenRune.
- 2026-10-25T01:31:11Z ready -> dev: dispatched to sd82
- 2026-10-25T01:31:11Z run sd82 started (server-dev, stage dev)
