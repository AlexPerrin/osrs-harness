# Problem

The problem definition: the business context, the goals of each track and each track's process in plain language.
docs/PRD.md states the requirements a solution must meet; docs/ARCHITECTURE.md is the solution.

## Business context

The user maintains two products and wants changes to reach their live targets with no person watching.

| Product | What it is | Success measure | Where a change is live |
|---|---|---|---|
| Client | RuneLite plugins running in the official OSRS Android app, shipped as APK releases (repo AlexPerrin/osrs-plugins-reverse) | share of the RuneLite API covered, core plugins, the user's plugins, hub plugins, packets | `master`; a tagged APK release |
| Server | an identical copy of the OSRS server: the OpenRune fork (AlexPerrin/OpenRune-Server), contributed upstream to OpenRune/OpenRune-Server | parity of the integration tree and of upstream `main` with the game | the test server; upstream `main` |

The harness (this repo) is the third track: it is neither product's code. It moves changes of both products, and its own,
to their live targets.

The user's priorities, in order: it runs unattended, it shows its status, it heals itself. Only an action on the public
upstream repository and a client release wait for the user; both are answered in chat.

What the world looks like:

- Upstream is public and maintained by other people who review in their own time and may report a defect at any point.
  The fork, local commits and this repo are the user's own.
- GitHub, CI, docker and git are the truth; the harness keeps only a cache of what they show.
- Work is done by fresh AI agents that are fallible; something other than their word verifies what they claim.
- One integration clone, one live server and one Ghidra project writer exist; everything else (builds, clients) can run
  in parallel within the machine's budget.
- No client contacts Jagex, and the user's own RuneLite and the tester account are never touched.
- Only Python 3.12 standard library and PyYAML are available.

## Goals

**Client.** RuneLite plugins work in the official Android app. Each plugin change is built, checked on a real client and
merged into `master`; releases are cut from `master` after a network and privacy check, with the user's yes.

**Server.** (1) Unblock client work: the test server runs a server change as soon as it is checked, whatever upstream
thinks of it. (2) Contribute upstream: every change reaches OpenRune as a clean, single-purpose, verified contribution
that maintainers can merge, and review feedback is settled before new work is opened.

**Harness.** The harness improves itself quickly and safely: each iteration makes it simpler, more efficient and more
streamlined, without the user having to watch a deploy.

## Process of each track

All three tracks share one shape: a change is **ready**, a developer works on it, an independent check follows, and it
is **done** when its live target carries it. A change is the unit of work, check and approval; it has a branch, one
commit handed over, a definition of done and optionally other changes it waits on. One priority order serves every
track within one machine budget; nothing waits on a lock for something that can run in parallel.

**Client.**
1. A developer builds the plugin or feature in the Android app, ticks the definition of done and hands over a commit
   with build and device evidence.
2. The change is merged into `master`. That is live.
3. When enough client changes are live, or the user asks, a release is prepared: an independent check of `master` at one
   commit, network and privacy included. The user is shown the result and says yes; then the tag and the APK release are
   published.
4. A client change that needs server behaviour files the server change itself and waits for it.

**Server.**
1. A developer builds a feature or a fix on a branch off current upstream `main`, checked against official game
   behaviour, in the fork, and hands over a commit.
2. Two outputs follow independently. The test server: all handed-over changes are combined, built into an image, checked
   and deployed, so client work is unblocked at once. The upstream contribution: an independent check of the exact
   commit (accuracy, CI on the fork merged with current upstream `main`, scope, upstream style, PR text, in game) is put
   on one record and shown to the user as an approval card.
3. The user reads the card in chat and approves the commit. One approval covers one unbroken sequence: push to the
   upstream PR branch, wait for green CI, comment, move out of draft. If CI does not go green the sequence stops and
   reports.
4. A pull request is the bucket of the conversation with maintainers: its thread, draft or ready state, head commit
   and the changes on it. A change is the single action between us and them. Once a change is marked ready, we wait:
   the PR is merged, or a maintainer finding arrives and becomes a new change that runs the whole process again. A
   reported defect is fixed in the same PR before it leaves draft; it is never promised for later.
5. Server work that unblocks client work comes first; settling open PRs comes before opening new ones. Changes that stay
   on the test server never go upstream.

**Harness.**
1. A harness developer works in its own worktree, with a test for each rule it touches, and hands over a commit.
2. The harness merges it into `main` and deploys it without the user; a major rebuild is deployed only after the user's
   yes. The result is reported.
3. The three documents (this one, the PRD and the architecture) are what each iteration starts from and ends by
   updating; whatever is not needed by a requirement is removed.

## The user's day

The user returns to a digest of what moved overnight and a list of approvals: upstream contributions and releases, each
with the exact commands, the full text to be posted and the check record. Anything else (stuck locks, lingering agents,
dead servers, failed deploys) was repaired without them. Agents that cannot go on ask a question that appears in the
same list.
