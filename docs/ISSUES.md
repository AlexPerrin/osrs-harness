# ISSUES

The open ledger of the v7 run, cleared at the hand-off on 2026-10-25. A quick fix lands at once and is not logged (git
history has it). What lands here is what a quick fix does not settle: a root cause in the design, or a rewrite too large
for the run. Each entry is what happens, why, and what v8 should do; newest first. The v8 iteration reads this with
docs/PROBLEM.md, docs/PRD.md and docs/ARCHITECTURE.md and questions all four.

## Open

- **A client build reached Jagex's servers.** Run `client-devtools-menu-actions-3` repacked without `OPENRUNE=1
  LOCAL_AUTH=1`, so the APK kept Jagex's jav_config, RSA modulus and AppAuth endpoints; on the emulator it very likely
  fetched Jagex's jav_config and world list and opened account.jagex.com in Chrome (no sign-in). The brief's build line
  and the "7 telemetry lines" check pass a stock-server build too. The guard now refuses a plain repack and the client
  gate wants the test-server patch lines; v8: no APK is installable without those lines in its repack log, checked at
  install, not only at the gate.
- **A pass change goes live on upstream within a minute.** The timer runs `main`, so a commit that changes an upstream
  step acts on real PRs at the next tick: twice on 2026-10-25 a rule committed before its dry run put a PR in a wrong
  visible state (#355 drafted, #367 marked ready for a minute). Until v8 the console pauses the pass
  (`harness/state/paused`) and dry-runs against the live PRs before committing such a change. v8: a change to an
  upstream step is dry-run against the live PRs by the harness's own gate before it can be merged.
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
  and were removed by hand; client windows carry no owner at all, so one left by an ended run stays open until a
  person notices (desktop, 2026-10-25). v8: name every artefact after its change, clients included, and remove it when
  the change is done.
