# ISSUES

The open ledger of the v7 run, cleared at the hand-off on 2026-10-25. A quick fix lands at once and is not logged (git
history has it). What lands here is what a quick fix does not settle: a root cause in the design, or a rewrite too large
for the run. Each entry is what happens, why, and what v8 should do; newest first. The v8 iteration reads this with
docs/PROBLEM.md, docs/PRD.md and docs/ARCHITECTURE.md and questions all four.

## Open

- **A run's lifecycle is read from hook events.** The start event races the agent's transcript and a stop is a pause as
  often as an end; v7 patches this by binding at the first command and ending on the hand-back call. Root cause: the
  run is a fact of the agent's transcript (first line the brief, hand-back the end), not of events. v8: derive it from
  the transcript alone; drop the start and stop events.
- **Every upstream merge re-gates every open change.** The gate is bound to `base`, upstream merges several times a day,
  so each merge costs one scratch merge and one fork CI run per open change and keeps the PRs at "gate pending" for
  hours. v8: gate on the merge GitHub already computes for the PR (mergeable state, upstream CI on the PR head); keep the
  scratch merge only for changes without a PR.
- **The train stops at the first unrecorded conflict.** The integrator resolves one conflict per run; a rebuild with
  several stale pinned branches needs one run each. v8: the rebuild reports every conflict at once, or a stale pinned
  branch leaves integration by a fact (its change is gone) instead of being resolved.
- **Findings are anchored on the approval record's timestamp.** The anchor has nothing to do with the maintainer and the
  migration got it wrong once. v8: anchor on our own last comment or push on the PR.
- **Throughput is bounded by the console.** Agents are spawned by hand with the Agent tool, so listed spawns wait for the
  user's presence, and a paused agent holds one of three slots. v8: measure how long spawns wait; decide whether the
  pass may spawn.
- **The guard judges command text.** A local `git remote set-url` naming upstream was denied while the pass's own
  `gh pr ready` runs outside the guard. v8: judge by effect only (the remote resolved at push time, the repo named to
  gh).
- **The brief's first line is a protocol between three programs** (steps writes it, the Agent prompt carries it, the
  hook parses it back). v8: the spawner writes the run record; nothing is parsed out of a prompt.
- **Repairs find orphans by the v7 run name.** Artefacts of earlier versions (v6 clones, state) are invisible to them
  and were removed by hand. v8: name every artefact after its change and remove it when the change is done.
- **`events.jsonl` grows without bound** and nothing reads it but people. v8: drop it, or make `hd` read it.
