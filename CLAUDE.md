# osrs-harness

The harness that moves changes to their live targets for two products: the client (AlexPerrin/osrs-plugins-reverse:
RuneLite plugins in the official OSRS Android app, APK releases) and the test server (the OpenRune fork
AlexPerrin/OpenRune-Server, contributed upstream to OpenRune/OpenRune-Server). It is neither product's code: the
client repo holds client code and releases only; server code and server tooling belong to the fork.

**New session: read docs/PROBLEM.md (the problem, constraints, workflow and rules, BR-*), then docs/ARCHITECTURE.md (how it is
built), docs/HANDOFF.md (current state) and, before repeating anything, docs/ISSUES.md (incidents).**
Run from the client checkout (`HD_CLIENT_ROOT`, default `~/osrs-plugins-reverse`), where agents work, evidence lives
(`re/evidence/<slug>/`) and the client builds; the client repo keeps thin shims at `tools/harness/hd.py`
and `tools/hooks/*.py` that exec this repo.

```
hd.py            the command line (python3 ~/osrs-harness/hd.py ...; `hd` in the docs)
hd/              the daemon (store, events, policy, stages, observe, check, locks (leases.py), agents, batches, ship, heal, tick,
                 daemon, kpi, metrics) and the console's side (actions, drive)
hooks/           the Claude Code hooks the role files and the client repo's .claude wiring exec
harness/         policy.yaml and changes/ (committed); state/ (git-ignored)
.claude/         agents/ (role files) and skills/ (drive = the console loop; the track rules; the QA procedures)
docs/            PROBLEM.md (rules), ARCHITECTURE.md (mechanism), HANDOFF.md (current state), ISSUES.md (incidents)
train/           image.sh deploy.sh Dockerfile.integration integrate.py: the train's steps
tests/           python3 -m unittest discover -s tests
```

Agents are spawned from the console session only (`hd drive`, skill `drive`); the user's OK for OpenRune upstream
actions and client releases is given in chat, and the commands run only after it.

## Iteration protocol
Every iteration starts by reading docs/PROBLEM.md and ends by updating it. Code, tests, policy keys and docs that trace
to no PROBLEM.md rule are dead logic: prune them in the same iteration and list what was pruned in the hand-over
report, never in the docs. docs/ARCHITECTURE.md states the mechanism only; no rule lives in both files.

## Rules
- The user's OK only for OpenRune upstream actions and client releases.
- Commits pathspec-only, authored as Alex Perrin <44126061+AlexPerrin@users.noreply.github.com>, ending with the
  Claude co-author line.
- Harness changes go through a harness-dev run or this console session, with a test per rule touched; definition-of-done
  items are ticked with `hd dod`.
- Decide on observable facts, never on time estimates; prefer one simple mechanism over stacked rules.
- Docs state current truth only and are the most concise source: no revision justification, history or dated
  rationale. Incidents and root causes live in docs/ISSUES.md alone (dated, short, newest first). Docs live in docs/;
  CLAUDE.md is the only root doc. The harness stays contained in this repo.
- The console never enters a worktree (EnterWorktree) while agents run.
- Times for the user are US Eastern.
- Hooks and `ask` rules live in the committed `.claude/settings.json`, never the personal `settings.local.json`; allow
  rules name scripts, not whole interpreters.
- Guards stay on: agents without the role hooks can push upstream.
