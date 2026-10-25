# ISSUES

The open ledger of the v7 run, cleared at the hand-off on 2026-10-25. A quick fix lands at once and is not logged (git
history has it). What lands here is what a quick fix does not settle: a root cause in the design, or a rewrite too large
for the run. Each entry is what happens, why, and what v8 should do; newest first. The v8 iteration reads this with
docs/PROBLEM.md, docs/PRD.md and docs/ARCHITECTURE.md and questions all four.

## Open

- **Stale pinned branches stay in integration until a person drops them.** The v6-era entries of `integration.txt`
  (`fix/*`, `content/*`, `local/*`) belong to no v7 change, so nothing removes them when they rot against upstream main;
  each rot is an integrator run. v8: every pinned branch belongs to a change or to the fork's permanent local list, and a
  branch leaves integration by a fact (its change is gone), not by a resolution.
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
