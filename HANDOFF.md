# HANDOFF: start here

**Harness v4 (2026-10-24, built on branch worktree-agent-a0d68621b85fcc35e / merged by the console).** v4 is v3 minus the
approval queue, the dashboard and headless agents: read docs/ARCHITECTURE.md and docs/harness-v4.md. Start the next session
in ~/osrs-harness so the role agent types load with the fixed hook paths.

## State
- Daemon: restart it after the merge (`hd stop && hd start --interval 60`; there is no dashboard process).
- How to run: `python3 ~/osrs-harness/hd.py start --interval 60` (the tick loop), and in the console session run the
  loop of `.claude/skills/drive/SKILL.md`: `hd drive`, spawn each listed agent with the Agent tool (subagent_type =
  role; isolation worktree only for client-dev, client-qa, harness-dev; NEVER EnterWorktree in the console), `hd run-link
  <name> <agent-id>`, on completion `hd run-end <name> --tokens N --turns N`; upstream actions and releases are shown to
  the user in chat (AskUserQuestion) and their commands run only after a yes. Pace with /loop or ScheduleWakeup. The
  session must stay alive for dispatch. Never start with HD_MAX_CLIENTSCRIPT_ID set (see below).
- Old records in harness/state/approvals/ are ignored now; the not-ready release approval for v0.1.1 reappears in
  `hd actions` only once a release batch is `gated` (set the tag with `hd release-request v0.1.1`).
- Live test server: integration ae947cff4 on upstream main 5c4c9c106, image osrs-openrune:integration-ae947cf,
  rollback osrs-openrune:rollback-e27ff4d. Deployed with the one-off override HD_MAX_CLIENTSCRIPT_ID=10198.
- Upstream: #406 (stile, ours, open; head 68ddd1b6c = test dropped, body updated), #354 cannon (changes requested),
  #355 genie (draft, findings), #367 goblin (finding), #368 witch's potion (conflicting). Merged: #362 #366 #370 #372 #373 #388.
- Review-fix changes (P0, ready, not started): cannon-review-354, genie-review-355, goblin-diplomacy-review-367,
  witchs-potion-review-368. Client dev dispatch is OFF (policy tracks.client.dev_slots 0) until BlueStacks is up and
  server-dev is settled.
- stile-approach was handed over again at 68ddd1b6c; its check FAILS only on "no CI run at 68ddd1b6c": GitHub answers
  422 "Actions has been disabled for this repository" for the fork. Fork CI cannot run until the user fixes that on
  github.com. This blocks every green-CI hand-over check.

## Layout (repos are isolated; see memory project-repo-isolation-layout)
Fork clone ~/src/OpenRune-Server; work dir ~/src/openrune-work (integration, qa, images, agents/<name>/or, server-tools =
fork branch local/server-tools); role files and skills in ~/osrs-harness/.claude; the client repo is client-only
(its removal commit d78a893 is local, not pushed). Evidence dirs still live in the client checkout re/evidence/.
Not done: `.claude/settings.json` hook wiring in this repo (add it for the console session when the user says so).

## Open work, in the user's order
1. Re-dispatch the four review fixes with the guarded role types (server-dev); push to PR heads only after the user's OK.
2. Option 3: verify custom clientscript ids (10197-10198) with stock ids above 9999 (10000-10188 in 241.4). Server side: the
   desktop RuneLite instances (desktop/desktop2) can confirm the cache and quest list; the Android tolerance is a BlueStacks
   client test, only when the user starts BlueStacks.
3. Option 1: make check_cache.py derive its limit from the cache's stock maximum (1:1 with the official cache; custom ids
   right after it) and remove HD_MAX_CLIENTSCRIPT_ID from image.sh.
4. Prune timed mechanisms (user: "actions are atomic, not timed"): image/deploy/gate timeouts, train debounce, lease
   minutes/heartbeats, budget minutes. Replace with observed-fact checks. Also dead hook rules for ship.sh/integrate.py.
5. Gate for ground-item-despawn-times and 11-dense-clientscript-ids; unstack Hunter; spec-missing holds on old branches.
6. Stale text: docs/ (except harness-v4.md, docs/ARCHITECTURE.md) and the older handoff below describe v2/v3; the v5 candidate list is in docs/harness-v4.md.

## Rules that bit this session
- Guards matter: agents without the role hooks can push upstream; keep them on. Nothing goes to OpenRune without the user's OK.
- No "separately / its own PR" to maintainers; a PR is ready only when reported defects are fixed in it. No stacking.
- Time is never a mechanism; decide on observed facts.
- Times for the user are US Eastern.

---
# Older handoff (harness v3 build session, 2026-10-20/21; STALE: mentions approvals, the dashboard and headless agents, all removed in v4)


**2026-10-21 9:45 PM EDT: the harness moved to its own repo, AlexPerrin/osrs-harness (~/osrs-harness).** Commands below
run from the client checkout through its shims (`python3 tools/harness/hd.py` there execs `~/osrs-harness/hd.py`), or
directly here. The change store is `~/osrs-harness/harness/changes/`; state is `~/osrs-harness/harness/state/`.

Updated 2026-10-20 8:45 PM EDT by the v3 build session. **Harness v3 (`harnessd`, "hd") is built and
tested; it is not started yet.** Read docs/harness-v3.md (what exists), then this file. Times for the user are
always US Eastern; never report UTC to them.

## 0. v3 in one minute
- The store is `harness/changes/<slug>.md` (117 changes, migrated from v2's tasks by `hd migrate --apply`; v2's
  `harness/tasks/` is kept as history and is no longer read). State that is observed, not remembered, lives in
  the git-ignored `harness/state/` (events.jsonl, leases, runs, batches, approvals, live.json).
- First commands:
```
python3 tools/harness/hd.py status                 # progress, approvals, every change with why it waits
python3 tools/harness/hd.py tick --dry-run         # what one tick would do (reads git, gh, docker; writes nothing)
python3 tools/harness/hd.py lease status           # the leases (device, desktop, desktop2, integration, live-server, ghidra)
python3 tools/harness/hd.py events --limit 30      # the event log, local time
python3 -m unittest discover -s tools/harness/tests   # 169 tests, must pass
```
- **Console mode** (policy `agents.spawn_mode: console`): the daemon decides each dispatch and emits an `agent request`
  event with the brief's path (harness/state/runs/<name>.log); the console session spawns it with the Agent tool
  (subagent_type = the role; isolation worktree for client-dev, client-qa, harness-dev), runs `hd run-link <name>
  <agent-id>`, and on completion `hd run-end <name> --tokens N --turns N`; a `stop-request` event means TaskStop
  that agent. Headless (`claude -p`) is `spawn_mode: headless`. The session must stay alive for dispatch.
- Agents are watched in Claude Code Agent Monitor (http://127.0.0.1:4820/, `cd ~/tools/Claude-Code-Agent-Monitor
  && npm start`); the page on 7790 is the project tracker. docs/harness-v3.md "Watching agents".
- To run it: `hd serve --detach` (the tracker page, its own process, http://127.0.0.1:7790/; never restarted with
  the loop) and `hd start --interval 60` (the tick loop: trains, deploys, agents, approvals); `hd stop`,
  `hd serve-stop`, `hd daemon-status`, `hd digest`. A code change needs only `hd stop && hd start`. The first real start is the user's call (it spawns paid agents and takes
  the instances).
- What the first real ticks will do (from the dry run at 8:40 PM EDT): move `57-gameframe-fullscreen-map`,
  `sheep-shearer` and `edgeville-general-store-stock` to `published` (open upstream PRs); return `cannon`,
  `genie` and `goblin-diplomacy-unstacked` to `checked` (the live server runs `fin/*`, not these branches; each
  carries a `decision` hold: fold into the PR branch, the user's OK per PR); dispatch one client-dev
  (`hub-ground-items-despawn`), two server-devs (`ground-item-despawn-times` further work, then by priority) and
  one server-qa (upstream gates for live branches without a record), within the slots and free leases.
- Open: the acc/* and fin/* convergence decisions (one `decision` card each on the dashboard), the spec-missing
  `failed` holds on five live content branches (a dev writes the spec before the gate), the notification channel
  (the digest is written to harness/state/digest.md), milestone dates for the forecast.

## 1. The project in five lines
- RuneLite plugins running inside the official OSRS **Android app** (native/ hooks + host/ Java plugin host), in this
  repo (AlexPerrin/osrs-plugins-reverse, `master` -> `origin main`).
- A test server: **OpenRune** (OpenRune/OpenRune-Server upstream), developed on the fork **AlexPerrin/OpenRune-Server**
  (local clones under `re/upstream-pr/or` and `re/agents/<name>/or`). The fork's `integration` branch is what the live
  test server runs.
- Progress, as the user defines it: **client = RuneLite compatibility on mobile** (`tools/progress.py`);
  **server = parity with the official OSRS server**, 100% = an identical copy (not measured yet: task
  `server-parity-metric`).
- Work runs through **harness v3** (`tools/harness/hd.py`, docs/harness-v3.md): a change store, a daemon that
  observes, advances, dispatches, heals and logs, leases, trains, approvals and a dashboard. v2's files
  (`tools/harness/orchestrate.py`, `task.py`, `harness/tasks/`) are history.
- Your job: start the daemon when the user says so, act on decisions and exceptions, relay the user's approvals
  (the dashboard or `hd approve`), and keep building against docs/harness-v3-prd.md.

## 2. First commands (v2 era; v3's are in section 0)
```
git pull --ff-only origin main
python3 tools/harness/hd.py status
python3 -m unittest discover -s tools/harness/tests   # 169 tests, must pass
git -C re/upstream-pr/or fetch -q origin main && git -C re/upstream-pr/or log --oneline -1 origin/main
```
If upstream main moved past 829b9477d, a re-pin is due (the user's rule: keep the test server on current upstream).

## 3. Read, in this order
1. `docs/harness-v3-prd.md`: **the PRD** (the model in its simplest terms, every business rule, the dashboard:
   progress, status, approvals; the daemon pivot; acceptance criteria). v3 is built and accepted against it.
2. `docs/harness-v3-problem.md`: the problem definition for v3 (the goal per track, first principles, the
   lifecycle of a change as a state machine with tools and dependencies, the driver tick, the invariants to test).
3. `docs/harness-v3-handoff.md`: the full handoff (v2 KPIs and verdict, takeaways, findings, stretch goals and
   KPIs, the change model, breaking changes, state at hand-off). Section 8 is the state.
4. `docs/integration-pipeline.md`: the approved train design; phases 0-1 done, 2-5 to build.
5. `docs/harness.md` and `docs/workflow.md`: v2 as built.
6. `re/evidence/harness-v2-review/` (`kpi.md`, `session-a450a085.md`, `sessions-earlier.md`): evidence behind the
   handoff.
7. `docs/v2-shipped.md`: what v2 delivered. `CLAUDE.md`: project rules. Memory is auto-loaded.

## 4. State right now
- **Live test server**: integration `e27ff4d08` on upstream main `829b9477d`, image `osrs-openrune:integration-e27ff4d`
  (= `:241`), live since 2:46 AM EDT 10-20. Rollback: `osrs-openrune:rollback-e5b18a8`.
- **Nothing running**: no agents, no locks, no grants, no stray containers. BlueStacks is running and idle (keep it
  running: user). The device and both desktops are free.
- **Upstream PRs**: ready for review #354 (cannon), #362, #366, #367, #372, #373; in review #370. Drafts: #355
  (Genie: gate FAIL, fix task below), #368 (Witch's Potion: gate task ready). 17 of ours merged.
- **Top of the ready queue** (`orchestrate.py next`):
  - P1 `hub-ground-items-despawn`, `hub-clue-steps-tier`: client checks on the device, unblocked by the last deploy.
  - P1 `fix-genie-gate-findings`: two accuracy fixes on `acc/genie` (leave on the next call tick after Talk-to,
    lamp XP equal to its message), then re-gate (`gate-acc-genie`), then #355 leaves draft.
  - P2 `integration-phase-2` (image.sh), `server-parity-metric`, `despawn-copy-owner-id`, `gate-witchs-potion`,
    `fix-bankside-view-op-refresh`; client `client-gpu-plugin-feasibility`, `client-117hd-feasibility`.
- **Known debt** (handoff section 7a): each feature lives on 3-4 fork branches (`fin/*`, `acc/*`, `content/*`, ...);
  the live server runs `fin/*` while upstream PRs use `content/*`. v3 converges to one branch per change.

## 5. Priorities (the user's, in order)
1. **Runs overnight without the user** (driver runs the loop; only upstream actions and client releases wait).
2. **A live dashboard** (product progress tiles, KPIs from an event log, one row per change).
3. **Self-healing** (stale state, idle locks, lingering agents, failed deploys repaired automatically).
Suggested order of work: event log first (`events.jsonl`, so v3 can be measured), then pipeline phases 2-3 (image,
deploy) and the driver tick, then the change model and leases, then the dashboard on top of the event log.

## 6. Rules you must follow (also in memory and CLAUDE.md)
- **Approvals**: ask only for OpenRune upstream actions (push to a PR branch, open/edit/comment/ready/close) and
  client releases. Fork pushes, fork PRs, integration, docs, deploys (standing approval), own-repo pushes go ahead.
  A prompt anywhere else is a hook bug: fix the hook, with a test.
- **Before anything that may prompt**: one plain-words line saying what it does and that it will prompt; run it alone.
- **gh CLI** subcommands, not `gh api`; exception: `gh pr edit` fails on OpenRune with gh 2.45 (retired projects
  field): use `gh api -X PATCH` for edits and say so, or upgrade gh.
- **Deploy**: boot-checked image, all three instances held, rollback tag first, `compose up -d --no-deps openrune`,
  never `--build`; tell the user. The login key comes only from the live image by `COPY --from`; never print or copy it.
- **Agents**: exit once handed over/blocked/failed; you stop any that linger. Locks only while in use; per-agent
  scratch dirs; no screenshots unless the user asks. Only you deploy, grant, reclaim and push integration.
- **Upstream**: no stacked PRs, one change per PR, match the official game (RSProx recordings beat the wiki),
  accuracy divergences listed as caveats, attribution lines on commits and PR texts.
- **Never**: contact Jagex/RuneScape servers, read or modify the user's own RuneLite (`C:\\Users\\Alex\\.runelite`),
  `::empty` the tester account, stop processes you didn't start.
- Commits: pathspec-only, authored as Alex Perrin <44126061+AlexPerrin@users.noreply.github.com>, ending with the
  Co-Authored-By line for your model.

## 7. Open user decisions
- Client: allow WikiSync, AFK Marks Canifis, Quest Voiceover (each contacts a new host)? Add client setters for
  Animation Smoothing and Camera?
- v3: which breaking changes (handoff 7c) to make first, and when; the user handed all nine to v3.

## 8. Gotchas
- Lock times print in local time (EDT); branch servers from `qa.sh start` use fixed names unless renamed per agent.
- The auto-mode classifier blocks harness self-edits outside the allowed paths; editing settings drops the session
  out of auto mode (everything prompts until the user re-enables it). Plan settings changes up front.
- WSL to Windows interop (adb.exe, desktop bridge) times out intermittently (`UtilAcceptVsock accept4 failed 110`):
  retry. The devtools MCP servers often don't connect; `tools/devtools_mcp.py --call` and the desktop bridge script work.
- A long-running orchestrator compacts; keep state on disk (task store, this file, the handoff) and restart early.
