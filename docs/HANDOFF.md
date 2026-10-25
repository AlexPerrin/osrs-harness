# HANDOFF

The brief for a fresh console session. Read CLAUDE.md, docs/PROBLEM.md, docs/PRD.md, docs/ARCHITECTURE.md, then
docs/ISSUES.md before repeating anything. Live state is what `hd` prints; none of it is kept here.

## Start prompt
Start the session in ~/osrs-harness on branch `main`. Read CLAUDE.md and docs/HANDOFF.md, then the memory files named
under Standing rules. Run `python3 hd.py` and follow skill `drive`. Nothing is pushed upstream or released without the
user's yes in chat.

## What is live
The v7 harness of docs/ARCHITECTURE.md, cut over on 2026-10-25: the pass runs from the systemd user timer
`hd-tick.timer` (every minute) and after every agent run; `harness/state/` holds only v7 records. The v6 state is kept
aside in `harness/state.v6/` (git-ignored) until the first server change has gone through a full pass; then delete it.
The backlog was cleared on 2026-10-25 to one change per open upstream PR (#354, #355, #367, #408); the rest is rebuilt
from scratch by the user and the orchestrator, and the pass files a P0 change for each new maintainer finding. The kept
changes were migrated from v6: handed-over commits are the `dev/<slug>` and `client/<slug>` refs, the
review-stage PRs carry gate, verdict and approval records at their PR head. Upstream main moved since, so the gate of
every handed-over server change reruns on a fresh scratch merge.

## Open decisions for the user
- The six `fin/*` and `acc/*` fork branches not named by a change: drop or convert.
- Hunter #408: the review-fix work continues as the v7 change `hunter-feat-pr`.
- The client API probe (`tools/api-probe.sh`, the measure of goal `client-api`) does not exist yet; the orchestrator's
  first change builds it.

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
- `systemctl --user` needs `XDG_RUNTIME_DIR=/run/user/1000` in a non-login shell (WSL); linger is enabled.
- WSL to Windows interop (adb.exe, desktop bridge) times out intermittently: retry. The devtools MCP servers often do
  not connect; `tools/devtools_mcp.py --call` and the desktop bridge script work.
- BlueStacks must be started on Windows after a reboot or WSL restart (`HD-Player.exe --instance Pie64`).
- Editing `.claude/settings.json` drops the session out of auto mode; hooks are read at session start.
- The guard denies the console `bash -n train/train.sh` too (the train scripts are the pass's): check shell syntax by
  reading, or in a test.
