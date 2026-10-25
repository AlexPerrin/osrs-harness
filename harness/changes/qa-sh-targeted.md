---
slug: qa-sh-targeted
track: server
kind: change
title: 'Fork tooling (local/server-tools): qa.sh gate runs targeted module tests by
  default; the shared cs2 volume is refreshed when stale; dev clones get fork and
  upstream remotes'
priority: P1
created: '2026-10-25T01:31:10Z'
branch: local/server-tools
---
## Change
Fork tooling (local/server-tools): qa.sh gate runs targeted module tests by default; the shared cs2 volume is refreshed when stale; dev clones get fork and upstream remotes

## Definition of done
- [x] qa.sh gate/gate-run accepts the touched modules and runs only their test and integration tasks plus spotlessCheck on them by default; the full-suite mode stays behind an explicit flag; documented in the fork tools README
- [x] The shared cs2 volume used by qa.sh freshCache is detected as stale (cs2 SYNTAX_ERRORs on scripts outside the change, while fork CI on the same merge is green) and refreshed by one command, documented; the check is observed by fact (the freshCache failure shape), not by age
- [x] Agent clone setup (scripts under local/server-tools) names the remotes fork and upstream and never calls the shared local clone origin; spotless's origin/main ref is set to upstream/main in the setup
- [x] Fork pushes only (local/server-tools); no upstream push; handed over with hd handover (--repo the tools clone)
