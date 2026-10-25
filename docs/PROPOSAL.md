# Harness v7 — build proposal

The design is in the three source docs on this branch: docs/PROBLEM.md (context, goals, process), docs/PRD.md (R1–R32,
acceptance), docs/ARCHITECTURE.md (the solution). This file is what the docs do not carry: the decisions taken, what v7
removes, the build order, the risks to verify first, and the cutover. It is deleted when v7 is live.

## Decisions taken (user, 2026-10-25)

| Decision | Effect |
|---|---|
| Agents are spawned with the Agent tool from the console; never OS subprocesses | the console is the only spawner and nothing else depends on it |
| Committed definition separate from state | `harness/changes/*.md` holds the definition only; `harness/state/` is never committed; the harness commits nothing but harness merges |
| The ticker is a systemd user timer | no daemon, no restart after a code change, the OS supervises; `loginctl enable-linger alex` once |
| The dev's fork ref is `dev/<slug>`; the public branch moves only by an approved publish | an agent push to a PR head is impossible by construction |
| Evidence lives in this repo (`evidence/<slug>/`, git-ignored) | the client repo holds code and releases only |
| Releases are created on request | no release rule; `hd` shows how many client changes are live since the last tag |
| Priority then age; review fixes filed at P0 | no priority inheritance, no settle-first flag |
| Maintainer findings are filed by the tick as definitions | one change per finding, keyed by id, committed by the user later |
| The tick pushes harness `main` after each merge | origin never lags |

## What v7 removes

| v6 | v7 |
|---|---|
| stored `stage`, `hold`, `owner`, `commit`, `repo`, `booked`, `cost`, `live_commit`, `batch`, `## Log` in the change file | derived on read, or a record owned by one actor |
| `hd run-link`, `run-end`, `run-stopped`, TaskStop by the console; lingering runs; `counters.json` | two hooks write run start and end; alive = console pid alive |
| booking, no-loop keys, finding sets, three hold kinds, `stalled`, `waiting`, `stale`, `view/` cache, digest | `derive.candidates`, one hold with text |
| `hd contribute` run by the console with a sleep-poll | `hd approve` records; `publish.py` runs detached |
| harnessd (`hd start`/`stop`, `daemon.json`, 63 restarts), `batches.lock`, two tickers | `hd tick` under a systemd timer, `flock` |
| 10 train steps as a state machine in the core, `queue.json`, `repin.json`, `includes` and `entries` | one `train.py` process with step results in its record |
| release batches | a change of kind `release` |
| 20-method track interface; `target.py`; `migrate_stage`; retired keys | 9 functions per track |
| 6 hooks, two shell parsers, two write tables, dead rules for deleted scripts | `guard.py`, `run_start.py`, `run_stop.py` |
| `kpi.py` (`usd`, `deadlocks`, `trend`), `metrics.py`, `maintain.py`, `capacity.py`, `priority.py`, `leases.py` heartbeats | `hd cost`; capacity and locks inside `derive` and `records` |
| 14 `hd` commands with no caller; `hd version` "4.0" | 15 commands, each with a caller |
| 7 172 lines, 4 463 of tests, 68-line policy | ≤ 2 500, ≤ 1 500, ≤ 40 |

## Build order (branch `v7`)

1. **Hooks, verified live.** `run_start.py`, `run_stop.py`, `guard.py`, `.claude/settings.json`; a real Agent-tool spawn
   from this console proves: the start hook binds the run to its change from the prompt; the stop hook blocks without a
   record and records usage from the transcript; a killed console ends its runs on the next tick. Acceptance 2 rests on
   this, so it goes first.
2. **Core.** `defs`, `records`, `observe`, `derive`, `tick`, `brief`, `cli`; the client and harness tracks; the `drive`
   skill; `hd-tick.timer`; tests per requirement. One harness change dispatched, handed over, merged and pushed by the
   tick end to end.
3. **Server track.** `dev/<slug>`, `hd verdict` and its checks, cards, `publish.py`, `train.py` wrapping the reviewed
   `image.sh` and `deploy.sh`, review-fix filing, re-pin.
4. **Heal and alerts**, fault injection (acceptance 2), the purge, `HANDOFF.md` and `ISSUES.md` reset, this file deleted.
5. **Cutover** (the user's yes): stop v6 (`hd stop`; kill pids 217615 and 791045), `loginctl enable-linger alex`, enable
   the timer, start the console with the `drive` skill, merge `v7` → `main`.

## Risks to verify in step 1

- `SubagentStart` fires before the subagent transcript exists; the start hook therefore reads the Agent tool's prompt from
  the parent transcript (`transcript_path`). If the prompt is not yet on disk at that moment, the fallback is binding at
  `SubagentStop` from the subagent transcript's first user message, and `derive.alive` counts an unbound start as alive
  for its console pid.
- Whether `SubagentStop` fires when the console is killed. Not required: the console pid check covers it.
- The console pid from a hook: the hook's ancestor whose command is `claude`; verified with `/proc/<pid>/status`.

## Purge (step 4)

Code: all of v6 `hd/`, `hooks/`, `tests/`, `harness/policy.yaml`, `harness/retired/`, `docs/evidence/`, `bench/`
except what `test-instances` names. Kept after review: `train/image.sh`, `train/deploy.sh`,
`train/Dockerfile.integration`, the git helpers of `train/integrate.py` folded into `train.py`; skills trimmed of harness
mechanics; role files without hooks.

State: `harness/state/` emptied; `live.json` kept; the rest is rebuilt from facts.

Definitions: the 142 v6 files → open ones stripped to the v7 schema; done ones deleted; the `fin/*` and `acc/*`
leftovers become one question each on the first `hd` list.

Machine: pids 217615 (v3 page server) and 791045 (`deploy.sh int-t-1`); the `harness/handoff-v6` worktree and
`worktree-agent-*` branch; `origin/progress-2026-10-24`; `~/src/openrune-work/{agents,qa,dev-hunter,image-*}` except
the live image dir; docker volumes of ended agents and `upstream-pr-gradle`, the six old image generations, the build
cache; client repo `re/harness/`, `re-evidence/`, `re/ghidra-old`, the six merged agent worktrees; `~/.claude/agent-dashboard`.
The `osrs-openrune-http(-desktop)` containers are recreated from `server-tools/docker-compose.yml`. Nothing live is
touched: the live server and its data volume, the rollback image, the fork clone, `server-tools`, `integration-tools`,
the gradle cache node, the client's `re/evidence` (copied into `evidence/`), `re/ghidra`.
