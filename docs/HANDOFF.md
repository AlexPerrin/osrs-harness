# HANDOFF

The brief for a fresh console session. Read CLAUDE.md, docs/PROBLEM.md, docs/PRD.md, docs/ARCHITECTURE.md, then
docs/ISSUES.md before repeating anything. Live state is what `hd status`, `hd drive`, `hd actions`, `hd batches` and
`hd agents` print; none of it is kept here.

## Start prompt
Start the session in ~/osrs-harness (the role agent types load with their hook paths). Read CLAUDE.md and docs/HANDOFF.md,
then the memory files named under Standing rules. Run `hd status` and `hd drive`; follow skill `drive` while the
daemon runs. The first work is v7 (section Open work): a major revision to the least complex, most efficient solution
that meets docs/PRD.md. Nothing is deployed, pushed or contributed without the user's chat OK.

## What is live
Harness v6 part A: the three-track core (client, harness, server behind `hd/tracks/`), derived stages from observed facts,
holds, capacity classes, priority, trains and release batches, the approval cards and the console driver (ARCHITECTURE
sections 2 to 11). `hd lint` and `python3 -m unittest discover -s tests` verify it. The client's latest release is the
single merged APK v0.1.2 (`gh release list -R AlexPerrin/osrs-plugins-reverse`).

## Run
- The daemon: `python3 ~/osrs-harness/hd.py start --interval 60`; `hd stop && hd start` after a code change. There is no
  other process.
- The console runs `.claude/skills/drive/SKILL.md` (spawn, link, end, ask, run, repeat) and must stay alive for
  dispatch; pace it with /loop or ScheduleWakeup. The console never enters a worktree while agents run.
- Approvals: the fork is free; each upstream action needs the user's OK per change in chat, then one atomic
  `hd contribute <slug> --approved <sha>` (push, CI, comment, ready); a client release needs the user's OK. A PR is the
  bucket of the maintainer conversation, a change the single action on it.

## Layout
Fork clone `~/src/OpenRune-Server`; work dir `~/src/openrune-work` (integration build, qa clones, images, agents'
clones `agents/<name>/or`, `server-tools` = fork branch `local/server-tools`); role files and skills in
`~/osrs-harness/.claude`; the client repo `~/osrs-plugins-reverse` holds client code, releases and evidence dirs
`re/evidence/<slug>/`.

## Held decisions (need the user's answer; `hd status` shows the hold reasons)
- Upstream: PR #408 (draft Hunter) has an unticked gate, see Open work v7; `hunter-feat-pr` is at `contribute` with a QA
  FAIL record. Review-fix changes on #354, #355, #367, #368, #406, #407 wait on the maintainers.
- 12 `fin/*` and `acc/*` branches (`hd status`: "is not one-change-one-branch") need converting into `content/*`
  branches; each conversion that opens an upstream PR needs the user's OK per PR.
- New feature dispatch is held (user 2026-10-24): settle open PRs first.
- Client decisions: the Animation Smoothing and Camera host setters, the hub plugins that contact a new host (WikiSync,
  AFK and others), the WorldEntity API (`hd status`: `host-*`, `hub-new-host-plugins`).
- Harness decisions: `draft-pr-without-qa` and `release-gate-record-location` (a dev run is already booked for the same
  commit).
- Many P3 `failed` holds are "spec missing" on live branches: one accuracy spec per change.

## Open work, in order
1. **v7: a major revision.** Judged by reducing to the least complex, most efficient solution that meets docs/PRD.md:
   fewer concepts, steps, special cases, files and knobs; iterate quickly; the docs hold only the source of truth. Rebuild
   over patch; deployment of the revision is gated by the user. Inputs, each with where to look:
   - v6 part B (`harness/changes/v6-driver-and-tracks.md`): driver cards with plan and queue lists; a SubagentStop hook
     calling `hd run-end` (tokens are forgotten otherwise; `.claude/settings.json`, `hooks/`); track modules in their own
     repos with pinned modules; harness contained in this repo (`harness-self-contained`); pruning.
   - Timed knobs left in `hd/observe.py`, `hd/heal.py`, `hd/metrics.py`, `hd/batches.py` (subprocess timeouts),
     `HD_POLL_SECONDS`, `stall_minutes` in `hd/kpi.py`; `kpi.py` reads `usd` (always empty): use tokens.
   - A `decision` hold has no structured question and options (`hd ask`; `hd/store.py`, `hd/drive.py`).
   - A hand-contributed change must be re-handed over on the PR head branch name to reach review
     (`hd/tracks/server/__init__.py`).
   - `hd gate-ci` and the integrator: the OpenRS2 cache download (archive.openrs2.org HTTP 500) failed the Hunter gate and
     `freshCache` (`hd/tracks/server/gateci.py`, ISSUES 2026-10-25); the integrator reset the tools branch (`train/`,
     `.claude/agents/integrator.md`).
   - Fork tooling: `qa.sh` full-gate mode and idle stop, the stale shared cs2 volume, the review step in `contribute.py`
     (no reviewers possible), the cross-repo module update path, the harness doc in the tooling branch not versioned with
     pins, a QA agent pushing `gate/<slug>` under the role hook, the local clone `origin` being the shared clone (scratch
     merges merged the wrong main once).
   - Client: unregistered change `client-contributing-file` (branch `client/client-contributing-file` af26042 pushed, not
     merged).
   - Dead hook rules for `ship.sh` and `integrate.py` (`hooks/deny_publish.py`).
2. **Hunter #408** (QA FAIL findings, `hd actions`): raw item and npc ids in `ImplingLootTables.kt` to gamevals symbols;
   wiki deviations into `docs/quirks.md`; in-game verification of bird houses, Herbiboar, butterflies and implings; rerun
   fork CI (run 40158597103) and `hd gate-ci hunter-feat-pr` when the cache host is back.
3. **Train int-20261025-6** (`hd batches`; step `gating` when this was written: genie-review-355, hunter-feat-pr,
   witchs-potion-review-368, cannon): the daemon advances it; an `exception` books an integrator.
4. **Unregistered change** `client-contributing-file`: register it with `hd new` or drop the branch.
5. Verify custom clientscript ids (10197-10198) against stock ids above 9999 (10000-10196 in 241.4): desktop RuneLite
   confirms the cache and quest list; Android tolerance needs a BlueStacks client test.
6. The `fin/*` and `acc/*` convergence into `content/*` (Held decisions).

## Standing rules
The user's rules are the memory files in `/home/alex/.claude/projects/-home-alex-osrs-harness/memory/` (index
`MEMORY.md`); read the ones named:
- Docs and process: `feedback_three_source_docs.md`, `feedback_docs_roles.md`, `feedback_harness_self_contained.md`,
  `feedback_redesign_over_patch.md`, `feedback_no_quick_fixes.md`, `feedback_atomic_not_timed.md`,
  `feedback_targeted_tests.md`.
- Upstream: `feedback_approvals_in_chat.md`, `feedback_gate_before_upstream.md`, `feedback_ready_procedure.md`,
  `feedback_ready_means_mergeable.md`, `feedback_upstream_pr_no_deferral.md`, `feedback_settle_existing_prs_first.md`,
  `feedback_upstream_rules_revisable.md`, `feedback_fewer_tests_upstream.md`, `feedback_pr_body_checkboxes.md`,
  `project_pr_contribution_model.md`, `project_fork_staging.md`, `project_planning_and_approval_queue.md`.
- Layout and clients: `project_repo_isolation_layout.md`, `project_no_device_locking.md`.
- Client releases: `project_client_versioning.md`, `project_single_apk.md`.
- Cutover: `project_v6_cutover.md`, `project_v6_decisions.md`.

## Gotchas
- WSL to Windows interop (adb.exe, desktop bridge) times out intermittently (`UtilAcceptVsock accept4 failed 110`):
  retry. The devtools MCP servers often do not connect; `tools/devtools_mcp.py --call` and the desktop bridge script work.
- BlueStacks must be started on Windows after a reboot or WSL restart (`HD-Player.exe --instance Pie64`); client dev
  runs need it.
- Plan settings changes up front: editing settings drops the session out of auto mode, and the auto-mode classifier
  blocks harness self-edits outside the allowed paths.
