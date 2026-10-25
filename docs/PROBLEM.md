# Problem

The problem definition: the business context, the goals of each track and each track's process in plain language.
docs/PRD.md states the requirements a solution must meet; docs/ARCHITECTURE.md is the solution.

## Business context

The user maintains two products and wants changes to reach their live targets with no person watching, overnight and
across days.

| Product | What it is | Where a change is live | Published as |
|---|---|---|---|
| Client | RuneLite plugins running in the official OSRS Android app (repo AlexPerrin/osrs-plugins-reverse) | `master` contains the commit | a tagged APK release |
| Server | a copy of the OSRS server identical to the official game: the OpenRune fork (AlexPerrin/OpenRune-Server), contributed upstream to OpenRune/OpenRune-Server | the test server runs an integration tree that contains the commit | a pull request merged upstream |

The harness (this repo) is the third track. It is neither product's code; it moves changes of both products, and its
own, to their live targets.

The user's priorities, in order: it runs unattended; it heals itself; it shows, from facts, what needs them and what is
running. Only an action on the public upstream repository and a client release wait for the user; both are answered in
chat.

What the world looks like:

- Work is done by Claude Code agents that the user spawns from a console session (the Agent tool) and can watch there.
  The console can vanish at any moment (usage limit, WSL restart, compaction, closed terminal) and its agents die with
  it; its absence may pause new spawns and nothing else.
- Agents are fallible; what git, GitHub, docker, the process table and a checked record show is the truth. Nothing is
  decided from elapsed time.
- Upstream is public and maintained by other people who review in their own time and may report a defect at any point;
  they want one change per PR, no stacking, no tests unless needed. The fork, local commits and this repo are the
  user's own and free.
- The fork's CI on a scratch merge with current upstream `main` is the same fact as upstream's PR CI.
- Things that exist once: the integration clone, the live server, the Ghidra project. A machine budget: builds, image
  builds, desktop clients, Android devices, agents.
- Python 3.12 standard library and PyYAML only. WSL2 with systemd; Docker Desktop and BlueStacks run on Windows and are
  started by hand.
- No client contacts Jagex; the user's own RuneLite and the tester account are never touched.

## Goals

**Client.** RuneLite plugins work in the official Android app. Each plugin change is built, checked on a real client and
merged into `master`; a release is cut from `master` after a network and privacy check, with the user's yes.

**Server.** (1) Unblock client work: the test server runs a server change as soon as it is checked, whatever upstream
thinks of it. (2) Contribute upstream: every change reaches OpenRune as a clean, single-purpose, verified contribution
that maintainers can merge; review findings are settled before new work is opened.

**Harness.** Each iteration makes it simpler and faster; a change to it is live on the next tick with no restart and no
one watching the deploy.

## Process of each track

All tracks share one shape. A change is **defined** (slug, track, title, priority, definition of done, optional deps on
other changes). It is **ready** when its deps are live. A dev agent builds it on the change's branch and hands over one
commit with evidence; an incomplete hand-over is refused. An independent check follows where the track needs one. The
change is **live** when its target contains the commit and **done** when live (client, harness, server-local) or merged
upstream (server). Everything an agent produces is a commit on a ref or a record on disk; what it says in chat counts
for nothing.

**Client.**
1. A developer builds the plugin or feature in the Android app and hands over a commit with the repack log and device
   evidence.
2. The harness merges it into `master`. That is live.
3. A release is a change of its own, made when the user asks: a QA agent gates `master` at one commit (install, hooks,
   network and privacy); the user reads the result and says yes in chat; the harness tags and publishes the APK.
4. A client change that needs server behaviour files the server change and waits for it.

**Server.**
1. A developer builds a feature or a fix on a branch off current upstream `main`, checked against official game
   behaviour, and hands over a commit on the fork.
2. Two things follow independently. The test server: every handed-over commit is combined, built, gated, imaged and
   deployed, so client work is unblocked at once. The upstream path: an independent check of the exact commit
   (accuracy, fork CI on the scratch merge, scope, upstream style, PR text, in game) is put on one record and shown to
   the user as a card.
3. The user approves the commit in chat. One approval covers one unbroken sequence, run by the harness: push the public
   branch, wait for green CI, comment, mark ready. If CI does not go green the sequence stops and the card says so.
4. A pull request is the conversation with the maintainers; a change is the single action on it. Once ready, we wait:
   the PR is merged, or a maintainer finding becomes a new change on the same PR that runs the whole process again. A
   reported defect is fixed on the same PR before it leaves draft; it is never promised for later.
5. Review fixes come before new PRs; server work that unblocks the client comes first. Changes that stay on the test
   server never go upstream.

**Harness.**
1. A harness developer works in a worktree, with a test per requirement touched, and hands over a commit.
2. The harness merges it into `main`, pushes, and the next tick runs the new code. A major revision is merged only after
   the user's yes.
3. This document, the PRD and the architecture are what each iteration starts from and ends by updating; whatever no
   requirement needs is removed.

## The user's day

The user opens the console and sees, from facts: the agents to spawn, the cards waiting for a yes (each with the exact
commands, the full text to be posted and the check record), the questions agents could not answer, the alerts only they
can fix (Docker engine down, BlueStacks absent), and what is running. Everything else — a dead console, a dead ticker,
a stuck lock, an orphan container or clone, a failed deploy — was repaired by a tick without them.
