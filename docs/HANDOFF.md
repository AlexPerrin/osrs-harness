# HANDOFF

The brief for a fresh console session. Read CLAUDE.md, docs/PROBLEM.md, docs/PRD.md, docs/ARCHITECTURE.md, then
docs/ISSUES.md before repeating anything. Live state is what `hd` prints; none of it is kept here.

## Start prompt
Start the session in ~/osrs-harness on branch `v7`. Read CLAUDE.md and docs/HANDOFF.md, then the memory files named
under Standing rules. Nothing is deployed, pushed upstream or released without the user's yes in chat.

## What is built (branch `v7`, not live)
The v7 harness of docs/ARCHITECTURE.md: `hd/`, `gates/`, `hooks/hook.py`, `train/train.sh`, `hd.yaml`, the seven role
files, the skills, one test class per requirement (`python3 -m unittest discover -s tests`). `main` is v6 and still
runs the live harness (`hd start`/`hd stop` there). `docs/PROPOSAL.md` is the approved build plan; delete it at cutover.

## Cutover (needs the user's yes; nothing in flight on v6 first)
1. Stop v6: `python3 ~/osrs-harness/hd.py stop` from a `main` checkout; no agent running.
2. Reset the state: move `harness/state/` aside (v6 records have another shape); `mkdir -p harness/state evidence`.
3. Definitions: `python3 harness/migrate-v6.py --apply` (deletes the done and v6-harness changes, keeps the open ones
   with the definition keys only), then `python3 harness/migrate-v6.py --cutover --apply` (dev refs `dev/<slug>` and
   `client/<slug>` at the handed-over commits, evidence copied to `evidence/<slug>/`, hand-over records; review-stage
   changes also gate, verdict and approval records at their PR head; backlog changes get a question). Commit the
   definitions; delete `harness/migrate-v6.py`.
4. The goal: `harness/goals/client-api.md` (target 100, `measure: tools/api-probe.sh`); the probe does not exist yet,
   so the orchestrator's first change builds it.
5. Delete `hooks/guard.py` (the shim for consoles started with the v6 settings) and restart the console so
   `.claude/settings.json` takes effect.
6. `loginctl enable-linger alex`; the two systemd units of ARCHITECTURE section 10; `systemctl --user enable --now
   hd-tick.timer`.
7. Merge `v7` into `main` (`git merge --no-ff v7`), push; `python3 hd.py` from the console; follow skill `drive`.
8. Fault injection per PRD acceptance 5 on the live system, one fault at a time, each repaired in one pass.

## Open decisions for the user
- The six `fin/*` and `acc/*` fork branches not named by a change: drop or convert.
- Hunter #408: the review-fix work continues as a v7 change (`hunter-feat-pr` carries its hand-over; the gate reruns CI).
- Client decisions carried as open changes: Animation Smoothing and Camera host setters, hub plugins that contact a new
  host, the WorldEntity API.

## Standing rules
The user's rules are the memory files in `/home/alex/.claude/projects/-home-alex-osrs-harness/memory/` (index
`MEMORY.md`); read the ones named:
- Docs and process: `feedback_three_source_docs.md`, `feedback_docs_roles.md`, `feedback_harness_self_contained.md`,
  `feedback_redesign_over_patch.md`, `feedback_no_quick_fixes.md`, `feedback_atomic_not_timed.md`,
  `feedback_targeted_tests.md`, `feedback_no_source_of_truth_in_rewrite.md`.
- Upstream: `feedback_approvals_in_chat.md`, `feedback_gate_before_upstream.md`, `feedback_ready_procedure.md`,
  `feedback_ready_means_mergeable.md`, `feedback_upstream_pr_no_deferral.md`, `feedback_settle_existing_prs_first.md`,
  `feedback_upstream_rules_revisable.md`, `feedback_fewer_tests_upstream.md`, `feedback_pr_body_checkboxes.md`,
  `project_pr_contribution_model.md`, `project_fork_staging.md`.
- Layout and clients: `project_repo_isolation_layout.md`, `project_no_device_locking.md`.
- Client releases: `project_client_versioning.md`, `project_single_apk.md`.
- v7: `project_v7_agents_via_agent_tool.md`, `project_v7_cutover.md`.

## Gotchas
- WSL to Windows interop (adb.exe, desktop bridge) times out intermittently: retry. The devtools MCP servers often do
  not connect; `tools/devtools_mcp.py --call` and the desktop bridge script work.
- BlueStacks must be started on Windows after a reboot or WSL restart (`HD-Player.exe --instance Pie64`).
- Editing `.claude/settings.json` drops the session out of auto mode; hooks are read at session start.
- The guard denies the console `bash -n train/train.sh` too (the train scripts are the pass's): check shell syntax by
  reading, or in a test.
