# osrs-harness

The harness that moves changes to their live targets for two products: the client (AlexPerrin/osrs-plugins-reverse:
RuneLite plugins in the official OSRS Android app, APK releases) and the test server (the OpenRune fork
AlexPerrin/OpenRune-Server, contributed upstream to OpenRune/OpenRune-Server). It is neither product's code: the
client repo holds client code and releases only; server code and server tooling belong to the fork.

**New session: read docs/PROBLEM.md (the problem), docs/PRD.md (the requirements, BR-*), docs/ARCHITECTURE.md (how it is
built), docs/HANDOFF.md (current state) and, before repeating anything, docs/ISSUES.md (incidents).**
Every session and agent runs from this repo (hooks, agents, skills and MCP servers are wired in `.claude/` and `.mcp.json`
here). The client checkout (`HD_CLIENT_ROOT`, default `~/osrs-plugins-reverse`) is where agents' worktrees, evidence
(`re/evidence/<slug>/`) and the client builds live; it holds client code and releases only.

```
hd.py            the command line (python3 ~/osrs-harness/hd.py ...; `hd` in the docs)
hd/              the daemon (store, events, policy, stages, observe, check, locks (leases.py), agents, batches, ship, heal, tick,
                 daemon, kpi, metrics) and the console's side (actions, drive); hd/tracks/ holds each track
                 (client, harness, server) behind one interface: the core only orchestrates between them
hooks/           the Claude Code hooks (wired in .claude/settings.json and the role files)
mcp/             MCP launchers (osrs-mcp); osrs-devtools and the desktop bridge launch from the client repo's tools/ (.mcp.json)
harness/         policy.yaml and changes/ (committed); state/ (git-ignored)
.claude/         agents/ (role files) and skills/ (drive = the console loop; the track rules; the QA procedures)
docs/            PROBLEM.md (goals, process), PRD.md (requirements), ARCHITECTURE.md (implementation), HANDOFF.md (current state), ISSUES.md (incidents)
train/           image.sh deploy.sh Dockerfile.integration integrate.py: the train's steps
tests/           python3 -m unittest discover -s tests
```

Agents are spawned from the console session only (`hd drive`, skill `drive`); the user's OK for OpenRune upstream
actions and client releases is given in chat, and the commands run only after it.

## Iteration protocol
docs/PROBLEM.md (goals, process), docs/PRD.md (requirements) and docs/ARCHITECTURE.md (implementation) are the only
source of truth. Every iteration reads them first, reduces the work surface (fewer concepts, steps, special cases,
files, knobs; the least complex solution that meets the PRD), and updates them last, each fact in the one document that
owns it. Code, tests, policy keys and docs traceable to no requirement are removed; the hand-over report lists what was
pruned, the docs never do.

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

## Shared rules (every role, both products)
- **Evidence** goes in `re/evidence/<slug>/` in the client main checkout, never a session scratchpad.
- **Testing tools over screenshots**: client, desktop and server state is read through the MCP data tools (`osrs-devtools`,
  `osrs-devtools-desktop`, `osrs-mcp`; `server-probe` for logs and packets). A screenshot is evidence only for how
  something is drawn, and agents take none unless the user asks.
- **Accuracy**: server behaviour must match the official server; divergences are caveats or fixes.
- **Privacy**: no client ever contacts Jagex or RuneScape servers. Every APK goes through the telemetry patch
  (`tools/repack.sh` in the client repo). Never put the user's email or personal identifiers in HTTP requests; use a
  generic User-Agent.
- **The user's own RuneLite** (C:\Users\Alex\.runelite) is never read or modified.
- **Tester account**: never ::empty it, keep its GE offer (lobster), drop only items you spawned.
- **Processes**: only stop processes you started.
- **Builds** go through the fork's `tools/buildq.sh`; client host builds are `host/build.sh` + `ninja -C re/build` + repack.
- **Denied actions**: don't work around them; report them to the orchestrator.
