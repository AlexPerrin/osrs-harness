# HANDOFF

Start the session in ~/osrs-harness so the role agent types load with their hook paths. Read CLAUDE.md, docs/PRD.md,
docs/ARCHITECTURE.md. Live state is what `hd status`, `hd drive` and `hd actions` print; none of it is kept here.

## Run
- The daemon: `python3 ~/osrs-harness/hd.py start --interval 60` (`hd stop && hd start` after a code change). There is
  no other process.
- The console session runs the loop of `.claude/skills/drive/SKILL.md` and must stay alive for dispatch; pace it with
  /loop or ScheduleWakeup.
- Do not start the daemon with `HD_MAX_CLIENTSCRIPT_ID` set (open work 2).

## Layout
Fork clone `~/src/OpenRune-Server`; work dir `~/src/openrune-work` (integration build, qa clones, images, agents'
clones `agents/<name>/or`, `server-tools` = fork branch `local/server-tools`); role files and skills in
`~/osrs-harness/.claude`; the client repo holds client code only. Evidence dirs live in the client checkout
`re/evidence/<slug>/`.

## Open work
1. Verify custom clientscript ids (10197-10198) against stock ids above 9999 (10000-10188 in 241.4): the desktop
   RuneLite instances can confirm the cache and quest list; Android tolerance needs a BlueStacks client test.
2. `check_cache.py` derives its limit from the cache's stock maximum (custom ids right after it); then
   `HD_MAX_CLIENTSCRIPT_ID` leaves `image.sh`.
3. Prune the remaining timed mechanisms (train debounce, gate/image/deploy-ready timeouts, lease minutes and
   heartbeats in policy `batches:` and `leases:`, `leases.grant` minutes); replace with observed facts. Also dead hook
   rules for ship.sh and integrate.py.
4. Wire `slot_stop.py` and `task_stop.py` into every dev/QA role file (only harness-dev and integrator have
   `task_stop`; nobody has `slot_stop`), so every agent hands over before it ends.
5. `.claude/settings.json` hook wiring for the console session (publish_gate, github_scope) in this repo.
6. A `decision` hold has no structured question and options; an `hd ask` (question + options as the hold reason)
   would let agents pose choices the console asks with AskUserQuestion.
7. `hd run-end` tokens come from the Agent tool's result and can be forgotten: a SubagentStop hook calling it, or a
   checklist item.
8. Many `failed` holds are "spec missing" on live branches: one change per spec.
9. `kpi.py` reads `usd` (always empty): replace with tokens.

## Gotchas
- WSL to Windows interop (adb.exe, desktop bridge) times out intermittently (`UtilAcceptVsock accept4 failed 110`):
  retry. The devtools MCP servers often do not connect; `tools/devtools_mcp.py --call` and the desktop bridge script work.
- BlueStacks must be started on Windows after a reboot or WSL restart (`HD-Player.exe --instance Pie64`); client dev
  runs need it.
- Plan settings changes up front: editing settings drops the session out of auto mode, and the auto-mode classifier
  blocks harness self-edits outside the allowed paths.
