# osrs-harness

The harness that moves changes to their live targets for two products: the client (AlexPerrin/osrs-plugins-reverse:
RuneLite plugins in the official OSRS Android app, APK releases) and the test server (the OpenRune fork
AlexPerrin/OpenRune-Server, contributed upstream to OpenRune/OpenRune-Server). It is neither product's code: the
client repo holds client code and releases only; server code and server tooling belong to the fork.

**New session: read docs/HANDOFF.md first.** The design: docs/harness-v3-prd.md (the rules, BR-*), docs/ARCHITECTURE.md and
docs/harness-v4.md (what is built: harness v4). Run from the client checkout (`HD_CLIENT_ROOT`, default `~/osrs-plugins-reverse`), where agents work,
evidence lives (`re/evidence/<slug>/`) and the client builds; the client repo keeps thin shims at `tools/harness/hd.py`,
`tools/hooks/*.py` and `tools/device-lock.sh` that exec this repo, so role files, skills and the committed hook wiring
there keep working.

```
hd.py            the command line (python3 ~/osrs-harness/hd.py ...; `hd` in the docs)
hd/              the daemon: store, events, policy, stages, observe, check, leases, agents, batches, ship, heal, tick,
                 daemon, kpi, metrics; and the console's side: actions (what needs the user's OK), drive (its work list)
hooks/           the Claude Code hooks the role files and the client repo's .claude wiring exec (deny_publish,
                 task_stop, slot_stop, ...)
harness/         policy.yaml and changes/ (committed); state/ (git-ignored: events.jsonl, leases, runs, batches,
                 actions, images, deploys, live.json, daemon.json)
.claude/         agents/ (role files) and skills/ (drive = the console loop, accuracy-check, ...)
device-lock.sh   instance leases (the client's tools/device-lock.sh shim execs it at this path)
docs/            ARCHITECTURE.md (components, data model, lifecycle, console loop, train, leases, hooks; Mermaid UML),
                 HANDOFF.md (current state), ISSUES.md (what went wrong and why: one dated entry per issue, newest
                 first: symptom, root cause, evidence, fix, how to recognise), harness-v4.md, evidence/harness-v4/
train/           image.sh deploy.sh Dockerfile.integration instances.tsv: the train's image and deploy steps, the lease rows;
                 integrate.py: git helpers for the train (clones, integration.txt pins, the lease push); the v2 queue, task.py, ship.sh,
                 handover-check.sh and progress_report.py are removed (git history keeps them)
tests/           python3 -m unittest discover -s tests
```

v4 is minimal: no approval records, no dashboard, no headless agents. Agents are spawned from the console session only
(`hd drive`, skill `drive`); the user's OK for OpenRune upstream actions and client releases is given in chat, and the
commands run only after it.

Rules that hold here as in the client repo: the user's OK only for OpenRune upstream actions and client releases; commits
pathspec-only, authored as Alex Perrin <44126061+AlexPerrin@users.noreply.github.com>, ending with the Claude
co-author line; harness changes go through a harness-dev run or this console session, with a test per rule touched;
decide on observable facts, never on time estimates; prefer one simple mechanism over stacked rules.
