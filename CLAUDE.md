# osrs-harness

The harness that moves changes to their live targets for two products: the client (AlexPerrin/osrs-plugins-reverse:
RuneLite plugins in the official OSRS Android app, APK releases) and the test server (the OpenRune fork
AlexPerrin/OpenRune-Server, contributed upstream to OpenRune/OpenRune-Server). It is neither product's code: the
client repo holds client code and releases only; server code and server tooling belong to the fork.

**New session: read HANDOFF.md first.** The design: docs/harness-v3-prd.md (the rules, BR-*), docs/harness-v3.md
(what is built). Run from the client checkout (`HD_CLIENT_ROOT`, default `~/osrs-plugins-reverse`), where agents work,
evidence lives (`re/evidence/<slug>/`) and the client builds; the client repo keeps thin shims at `tools/harness/hd.py`,
`tools/hooks/*.py` and `tools/device-lock.sh` that exec this repo, so role files, skills and the committed hook wiring
there keep working.

```
hd.py            the command line (python3 ~/osrs-harness/hd.py ...; `hd` in the docs)
hd/              the daemon: store, events, policy, stages, observe, check, leases, agents, batches, ship, approvals,
                 heal, tick, daemon, dashboard, kpi, metrics
hooks/           the Claude Code hooks the client repo's .claude wiring execs (deny_publish, task_stop, slot_stop, ...)
harness/         policy.yaml and changes/ (committed); state/ (git-ignored: events.jsonl, leases, runs, batches,
                 approvals, images, deploys, live.json, daemon.json, server.json)
image.sh deploy.sh Dockerfile.integration   the train's image and deploy steps
integrate.py   git helpers for the train (clones, integration.txt pins, the lease push); the v2 queue, task.py, ship.sh,
                 handover-check.sh and progress_report.py are removed (git history keeps them)
tests/           python3 -m unittest discover -s tests
```

Rules that hold here as in the client repo: approvals only for OpenRune upstream actions and client releases; commits
pathspec-only, authored as Alex Perrin <44126061+AlexPerrin@users.noreply.github.com>, ending with the Claude
co-author line; harness changes go through a harness-dev run or this console session, with a test per rule touched;
decide on observable facts, never on time estimates; prefer one simple mechanism over stacked rules.
