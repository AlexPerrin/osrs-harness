# osrs-harness

The harness that moves changes to their live targets for two products: a RuneLite-plugin client for the official OSRS
Android app (AlexPerrin/osrs-plugins-reverse, APK releases) and an OpenRune test server (the fork
AlexPerrin/OpenRune-Server, contributed upstream to OpenRune/OpenRune-Server). It is neither product's code.

One mechanism: a change is a list of steps, each "done when this fact holds" plus an action by a script, an agent or
the user. One pass per minute reads the facts (git, GitHub, docker, processes), does the next script step of every
change, and names the agent or person every other step needs. Facts over claims; nothing is recorded that can be read.

```
python3 hd.py                 # the console's list: goals, spawns, cards, questions, running, changes
python3 hd.py tick --dry-run  # what the next pass would do, changing nothing
python3 -m unittest discover -s tests
```

Read `docs/PROBLEM.md` (first principles), `docs/PRD.md` (the constraints), `docs/ARCHITECTURE.md` (how it is built),
`docs/HANDOFF.md` (the current state) and `docs/ISSUES.md` (the open ledger). `CLAUDE.md` holds the rules every
session and agent runs under.
