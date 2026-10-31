# osrs-harness

The harness that moves changes to their live targets for two products: the client (AlexPerrin/osrs-plugins-reverse:
RuneLite plugins in the official OSRS Android app, APK releases) and the test server (the OpenRune fork
AlexPerrin/OpenRune-Server, contributed upstream to OpenRune/OpenRune-Server). It is neither product's code.

**New session: read docs/PROBLEM.md (first principles), docs/PRD.md (the constraints, R1–R7), docs/ARCHITECTURE.md (how it
is built), docs/HANDOFF.md (current state) and, before repeating anything, docs/ISSUES.md (the open issues, kept for v8).**
Every session and agent runs from this repo (hooks, agents, skills and MCP servers are wired in `.claude/` and `.mcp.json`).

```
hd.py, hd/        the nine commands (cli), store, facts, steps (the one mechanism), server, tick, dashboard (the page)
gates/            the script gate of each track
hooks/            hook.py (one program: run start, run stop, the guard) and its shell parser
train/            train.sh, image.sh, deploy.sh, Dockerfile.integration: the one long process
bench/            client instance tools: the emulator restore check, desktop RuneLite start and login, the headless launcher
mcp/              the osrs-mcp launcher and the devtools front (connects with no client running) named by .mcp.json
harness/          goals/ and changes/ (committed definitions); state/ and evidence/ at the root are git-ignored
hd.yaml           repos, paths, tracks, roles, the agent count
.claude/          agents/ (role files) and skills/ (drive = the console loop; the track rules; the QA procedures)
docs/             PROBLEM.md, PRD.md, ARCHITECTURE.md, HANDOFF.md, ISSUES.md (the open ledger for the next rebuild)
tests/            python3 -m unittest discover -s tests
```

Agents are spawned from the console session only (skill `drive`). A write to OpenRune and a client release happen only
after the user's yes in chat, recorded with `hd approve` and done by the pass.

## Iteration protocol
docs/PROBLEM.md, docs/PRD.md and docs/ARCHITECTURE.md are the only source of truth. Every iteration reads them first,
reduces the work surface (fewer concepts, steps, special cases, files, knobs), and updates them last, each fact in the
one document that owns it. Code, tests, config keys and docs traceable to no requirement are removed; the hand-over
summary lists what was pruned, the docs never do.

## Rules
- The user's OK only for OpenRune upstream actions and client releases.
- Commits pathspec-only, authored as Alex Perrin <44126061+AlexPerrin@users.noreply.github.com>, ending with the
  Claude co-author line only (no Claude-Session line).
- Harness changes go through a harness-dev run or this console session, with a test per requirement touched.
- Decide on observable facts, never on time estimates; one simple mechanism over stacked rules.
- Docs state current truth only: no revision justification, history or dated rationale. A quick fix lands at once
  and is not logged; a root cause or a rewrite too large for the run goes to docs/ISSUES.md alone (short, newest
  first), cleared at each hand-off. Docs live in docs/; CLAUDE.md and README.md are the only root docs.
- The console never enters a worktree (EnterWorktree) while agents run.
- Times for the user are US Eastern.
- Hooks live in the committed `.claude/settings.json`, never the personal `settings.local.json`.
- Guards stay on: an agent without the hook can push upstream.

## Shared rules (every role, both products)
- **Evidence** goes in `~/osrs-harness/evidence/<slug>/`, never a session scratchpad.
- **Testing tools over screenshots**: client, desktop and server state is read through the MCP data tools (`osrs-devtools-mobile`,
  `osrs-devtools-desktop`, `osrs-mcp`; `server-probe` for logs and packets) and text reads first. A screenshot costs
  much context: it is the fallback only when no data tool or text read answers, or evidence of how something is drawn.
- **Accuracy**: server behaviour must match the official server; divergences are caveats or fixes.
- **Privacy**: no client ever contacts Jagex or RuneScape servers. Every APK goes through the telemetry patch
  (`tools/repack.sh` in the client repo). Never put the user's email or personal identifiers in HTTP requests.
- **The user's own RuneLite** (C:\Users\Alex\.runelite) is never read or modified.
- **Tester account**: never ::empty it, keep its GE offer (lobster), drop only items you spawned.
- **Processes**: only stop processes you started.
- **Builds** go through the fork's `tools/buildq.sh`; client host builds are `host/build.sh` + `ninja -C re/build` +
  `OPENRUNE=1 LOCAL_AUTH=1 tools/repack.sh` (a plain repack keeps Jagex's servers; the guard refuses it).
- **Denied actions**: don't work around them; report them.
