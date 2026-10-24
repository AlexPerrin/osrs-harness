# Harness v4: v3 minus approvals, dashboard and headless agents

Supersedes docs/harness-v3.md where they differ (v3's lifecycle, tick, train, leases and hand-over check are unchanged).
The technical description is docs/ARCHITECTURE.md; the rules are still docs/harness-v3-prd.md (BR-*).

## What v4 is
The daemon (`hd start --interval 60`) observes, advances, trains, deploys, heals and books agent runs. The console
session is its only pair of hands: it spawns agents with the Agent tool and performs upstream actions and releases
after the user's yes in chat. `hd drive` is the console's one work list; `.claude/skills/drive/SKILL.md` is the loop.

## What was removed
- `hd/approvals.py`, `hd/dashboard.py`, the HTTP server and its detached process; the CLI commands `approvals`,
  `approve`, `deny`, `serve`, `serve-stop`, `tail`; the tick's approvals step; approval records and events
  (`approval`), the digest's approval lines, policy `approvals:`.
- Headless agents: `claude -p`, `spawn_mode`, `permission_mode`, `model`, `budget_usd`, `budget_minutes`,
  `linger_grace_minutes`, `agents.poll`, `over_budget`, stream-json result parsing, workspace/worktree creation by the
  daemon (the console's Agent tool makes the worktree: `isolation: worktree` for client-dev, client-qa, harness-dev),
  HD_SPAWN, HD_WORKTREE. Every run is a console run.

## What was added
- `hd/actions.py` and `hd actions [--json]`: from observed state, what a gated server change needs upstream (open-pr,
  ready-pr, update-pr = push then comment) or a gated release batch needs (tag-release, or choose-tag), each with its
  exact commands and the text files they read (`harness/state/actions/<id>.<part>.md`). Nothing is recorded: no
  pending/approved/denied/stale/failed; an action leaves the list when GitHub shows it done. A release batch becomes
  `published` when `gh release view <tag>` shows its release (the tick's gates step).
- `hd/drive.py` and `hd drive [--json]`: spawn requests (runs without an `agent_id`), stop requests (stopped runs with an
  `agent_id` and no `stop_done`; the console marks them with `hd run-stopped`), actions, decisions (`decision` holds),
  exceptions (a train at `exception` whose integrator ended, `exception` holds, `failed` holds no dev run will pick up).
- `hd status` is text from the store (changes with why they wait, open batches, leases, runs, daemon); `--json` too.
- A batch carries the release `tag` from `harness/state/release.request` (`hd release-request vX.Y.Z`).
- The release command is one `gh release create <tag> --target <commit> ...` (the old pair, local `git tag` then
  `gh release create`, needed the tag pushed first).
- Tests use a test policy (`hd_helpers.write_test_policy`: client 1 dev slot, server 2, harness 1, 3 agents) so the live
  values in harness/policy.yaml never change a test.

## Run it
```
python3 ~/osrs-harness/hd.py start --interval 60      # the tick loop; restart freely: hd stop && hd start
python3 ~/osrs-harness/hd.py drive                    # the console's list (the console session runs this in a loop)
python3 ~/osrs-harness/hd.py status | actions | agents | events | digest | lease status | batches
python3 -m unittest discover -s tests
```
A console command after the user's yes still passes the every-session hooks: publish_gate.py (a QA PASS record at the
commit before `gh pr create`) and github_scope.py (upstream writes prompt the user once more). The role hooks
(deny_publish.py) are loaded by the agents' role files, never by the console, and keep every agent from publishing.

## Next iteration (v5 candidates, seen while building v4; none done)
- Prune the remaining timed mechanisms: train debounce, gate/image/deploy-ready timeouts, lease minutes and heartbeats
  (policy `batches:` and `leases:`), `leases.grant` minutes; replace with observed facts.
- Wire `slot_stop.py` and `task_stop.py` into every dev/QA role file (only harness-dev and integrator have task_stop;
  nobody has slot_stop), so every agent must hand over before it ends.
- `.claude/settings.json` for the console session (publish_gate, github_scope) is still not wired in this repo.
- `hooks/session_state.sh` still calls the removed v2 `orchestrate.py`; `integrate.py`'s trailer says "Claude Fable 5.1".
- A `decision` hold has no structured question/options; `hd drive` shows the hold reason only. A small `hd ask`
  (question + options as the hold reason) would let agents pose choices the console can ask with AskUserQuestion.
- The run record has no usage the console does not report: `hd run-end` tokens come from the Agent tool's result; add it
  to the skill's checklist or have a SubagentStop hook call `hd run-end` so it cannot be forgotten.
- Many `failed` holds are "spec missing" on live branches: a dev must write the spec; consider one change per spec.
- Evidence dirs still live in the client checkout (`re/evidence/<slug>`), while the harness lives in its own repo.
- `kpi.py` still reads `usd` (always empty now); replace with tokens.
- Old `harness/state/approvals/` records on disk are ignored (e.g. the release approval for v0.1.1); they can be deleted.
- docs/ other than harness-v4.md and docs/ARCHITECTURE.md describe v2/v3; retire or archive them.
