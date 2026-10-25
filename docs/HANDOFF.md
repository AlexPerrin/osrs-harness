# HANDOFF

The brief for a fresh console session. Read CLAUDE.md, docs/PROBLEM.md, docs/PRD.md, docs/ARCHITECTURE.md, then
docs/ISSUES.md, the open ledger for v8. Live state is what `hd` prints; none of it is kept here.

## Start prompt
Start the session in ~/osrs-harness on branch `main`. Read CLAUDE.md and docs/HANDOFF.md, then the memory files named
under Standing rules. Run `python3 hd.py` and follow skill `drive`: spawn each listed run with the Agent tool, the
brief file's text as the prompt and the role as the agent type; show cards and questions; record the user's yes with
`hd approve` and answers with `hd answer`. Nothing is pushed upstream or released without the user's yes in chat.
A quick fix lands at once; a root cause or a rewrite too large for the run is one entry in docs/ISSUES.md for v8.

## What is live
v7 development is complete (2026-10-25). The pass runs from the systemd user timer `hd-tick.timer` every minute and
after every agent hand-back. The backlog is one change per open upstream PR (#354, #355, #367, #408) plus the P0
changes the pass files for maintainer findings. The goal `client-api` has no measurement and no client change yet; the
orchestrator's first run defines the client backlog, starting with the probe `tools/api-probe.sh`.

## Open decisions for the user
- Eleven `fin/*` fork branches hold finished, test-server-live work never contributed (diaries, doric, fairy-rings,
  farming, grand-exchange, jewellery, op-overrides, plank-sack, quest-test-fixture, rune-pouch, vampyre-slayer): the
  source of the rebuilt backlog, one change per feature, after the open PRs settle.
- The client API probe (`tools/api-probe.sh`, the measure of goal `client-api`) does not exist yet.
- `harness/state.v6/` (the v6 records) is kept until a server change completed a full v7 pass; then delete it.

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
- Hooks are read at session start: after a change to `.claude/settings.json`, restart the console. The hook program
  itself (`hooks/hook.py`) is read on every event, so its edits apply at once.
- A run ends when its agent calls SubagentHandback; a stop without one is a pause (background build). An agent that
  dies without a hand-back stays `running` in the list: end it by deleting `harness/state/runs/<name>.json`.
- The auto-mode classifier denies the console `kill` and deleting pushes even where the guard allows them; the user
  runs those with the `!` prefix.
- `systemctl --user` needs `XDG_RUNTIME_DIR=/run/user/1000` in a non-login shell (WSL); linger is enabled.
- Upstream merges often: every merge voids every gate (bound to base), so all open changes re-gate on fresh scratch
  merges; the fork CI load is one run per open change per upstream merge.
- WSL to Windows interop (adb.exe, desktop bridge) times out intermittently: retry. The devtools MCP servers often do
  not connect; `tools/devtools_mcp.py --call` and the desktop bridge script work.
- BlueStacks must be started on Windows after a reboot or WSL restart (`HD-Player.exe --instance Pie64`).
- The guard denies the console `bash -n train/train.sh` too (the train scripts are the pass's): check shell syntax by
  reading, or in a test.
