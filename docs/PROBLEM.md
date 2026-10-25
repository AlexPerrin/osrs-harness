# Problem

The source of truth for what the harness is for and the rules it holds. docs/ARCHITECTURE.md is how it is built;
module docstrings are the spec of each mechanism. Rules carry stable ids (BR-*) that code and tests cite.

## 1. Problem

Move changes to their live targets for two products with no human or chat session on the loop. Only an upstream
action and a client release wait for the user.

| Product | Goal | Metric | Live target |
|---|---|---|---|
| Client | RuneLite plugins in the official OSRS Android app | RuneLite API %, core plugins, the user's plugins, hub plugins, packets | `master`; a tagged APK release |
| Server | an identical copy of the OSRS server, contributed upstream | server parity % of the integration tree and of upstream `main` | the test server; upstream `main` |

Priorities, in order: it runs unattended, it shows its status, it heals itself.

## 2. Constraints

- Upstream (OpenRune/OpenRune-Server) is public and maintained by others; the fork, local commits and this repo are
  ours.
- No client contacts Jagex; the user's own RuneLite and the tester account are never touched.
- One integration clone, one live server and one Ghidra project writer exist.
- Harness code, state, evidence and docs live in this repo; the client repo holds client code and releases only, the
  fork holds server code and server tooling.
- Python 3.12 stdlib and PyYAML only.
- Decisions rest on observed facts: no timeouts, debounces, grace periods, heartbeats or estimates.

## 3. Assumptions

- GitHub, CI, docker and git are the observable truth; the store is a cache of them.
- Upstream maintainers review in their own time and may report defects at any point.
- Agents are fresh, fallible executors of one stage; a hook or the daemon verifies what they claim.
- The user answers in chat; the console session is alive to spawn agents and run approved actions.

## 4. Workflow

The core orchestrates between three tracks (client, server, harness): changes, deps and blockers, one priority order,
one capacity budget, dispatch, holds, run bookkeeping, the console's list. It knows nothing of GitHub, CI or PRs: each
track owns its product's workflow behind one interface and its own policy section (`tracks.<name>`).

One lifecycle for every track: **ready -> dev -> gate -> done**; a track defines what its gate checks and what done means.

- **Dev.** One agent, one change, one stage. It commits locally, ticks the definition of done and hands over.
- **Gate.** An independent agent aggregates every check of the exact handed-over commit onto one record: PASS or FAIL
  per check, every finding, evidence links. A finding blocks nothing by itself; the user's approval of the change is the
  only gate to an upstream action (BR-A2).
- **Done.** Per track: client = `master` contains the commit, then a release gated and approved; server = the
  approved atomic contribution upstream, then merged; harness = this repo's `main` contains the commit.

**Priority and capacity.** One priority order for every track, recomputed from facts each tick: a change that settles
an open PR first, then the highest priority among a change and the changes waiting on it, then age. One machine
budget of capacity classes; dispatch waits for a free slot, never for a lock.

**Server.** Priority is unblocking client dev: a server change inherits the highest priority of the client changes
blocked on it. Two independent outputs per server change: (a) the test server runs it, via the integration train, no
upstream gate; (b) the gated upstream contribution, which never holds up the client.

**The PR and the change.** A PR is the bucket of maintainer interaction (thread, draft or ready, head commit, its
changes). A change is the atomic action between us and the maintainers and the unit of work, gate and approval. A
maintainer finding is filed once as one new change, keyed by its comment or review id; it runs the full process. A PR is
done when it is ready for review with no open items; merge is observed afterward. Once a change is marked ready we
wait for the maintainers: the PR is merged (observed) or a finding arrives as a follow-up change. Marking ready ends our
action, and a change in review books no agent.

**The contribution.** Once QA's record exists for the commit and fork CI is green, the change enters the approval
queue, which holds only upstream contributions: one card per item with the record's checks and findings. The user
approves the commit in chat with concise context (branch, commit, net diff, what QA verified, risk, recommendation).
The approval is bound to the commit SHA. One approval covers one atomic sequence with no further asks: push to the
upstream PR branch (fast-forward or merge commit, never force), wait for green CI at that commit, comment, move out of
draft. If CI does not go green the sequence stops before the comment and reports.

**CI equivalence.** Each check runs once, at the fork on the scratch branch merged with current upstream `main`; a
green fork run satisfies its upstream twin (policy `tracks.server.ci_equivalence`: the fork CI and Formatting workflows, the required
upstream checks, the advisory ones). After the push the contribution only confirms the required twins: it never re-runs
a check and never waits on an advisory one. A red fork check, Formatting included, means not ready for upstream.

**Harness.** Features and fixes are built in a worktree, merged by the daemon and deployed autonomously, then
reported. A major revision is deployed (merge and daemon restart) only after the user's yes.

**Iteration.** Read this file first; update it last; delete code, tests, policy keys and docs not traceable to a rule
here.

## 5. Business rules: changes

- **BR-C1 Identity.** A change is named by its slug; its branch is `content/<slug>`, `fix/<slug>`, `local/<slug>`
  (server), `client/<slug>` (client) or `harness/<slug>` (harness). No second branch for the same change.
- **BR-C2 One change, one commit pointer.** `commit` is the commit the dev handed over. A new commit on the branch
  (fix, review round, merge from `main`) re-enters the change at dev with the hand-over's evidence due again and
  voids every later fact (gate, approval).
- **BR-C3 Definition of done before ready.** A change leaves `backlog` only with a definition of done; a server
  change's contains the spec, one change only, off current `main`.
- **BR-C4 Dependencies are edges.** `deps[]` names other changes; a change is `ready` only when every dep is done
  for its purpose. A client change that needs the server files the server change itself and adds the edge.
- **BR-C5 Priority.** One order for every track, recomputed from facts each tick: a change a track says settles open
  work (a review fix on an open PR) while policy `settle_first` is true; then effective priority, the highest (P1
  before P2) of the change and of every unfinished change that lists it as a dep while it is not live (`hd block --by`,
  transitive); then age.
- **BR-C6 Scope.** One quest, feature or fix per change; a fix found on the way is its own change; no change
  contains a commit of another open upstream PR (no stacking). Upstream diffs carry no test file unless a rule has
  several cases or a reviewer asked.
- **BR-C7 Local-only.** Changes with a `local/*` branch or `local_only` end at the test server; they are never gated or published.
- **BR-C8 Merged means dropped.** When upstream `main` contains the change's commit the next re-pin removes the
  branch from integration and the change is `merged`.

## 6. Business rules: stages and holds

- **BR-S2 Stages are observed; holds are durable.** The daemon sets stages from facts (a ref at a sha, a CI
  conclusion, a PR state, an image record, a lock row); an operator adds a hold or a note, never a stage. A hold is
  `decision`, `failed` or `exception`; the reconciler never clears one: `hd unhold` does, a hand-over or a moved commit
  also clears `failed`. A change waiting on a dep is not held: the wait is derived from `deps` each tick (BR-C4).
- **BR-S3 A fix is asked for with a hold.** The user (or a failed train) puts the change on `failed` with the
  findings to fix; the fix is a new commit (BR-C2); the hold clears on the next hand-over.
- **BR-S4 Maintainer review.** A maintainer finding on the upstream PR is filed once, keyed by its comment or review
  id, as a review-fix change carrying the finding; moving the PR to draft and any push to its branch are upstream
  actions (BR-A1), each needing the user's yes.
- **BR-S9 No loops.** A dev is booked only if the head SHA or the finding set differs from the last booked run;
  otherwise a durable `decision` hold appears in the user's list.
- **BR-S10 Failure on facts.** No timeout, debounce, grace period, heartbeat or `*_minutes` / `*_seconds` knob: an
  action ends on an observed fact, and fails only on a fact meaning its result cannot arrive (the step's process or
  container exited without its record, the run concluded). A queued server change starts a train at once.
- **BR-S5 A failed hand-over returns the change to `ready`** with the failing items; the next agent fixes exactly
  those. A failing check never re-dispatches a dev without new facts.
- **BR-S6 Ready means mergeable.** A PR leaves draft only when reported defects are fixed in its head, CI is green at
  that commit, the gate passed there, the PR text is true and no deferral wording ("its own PR", "later") is in it.
- **BR-S7 Gate scope.** The gate checks the exact commit merged with current upstream `main` in a scratch clone:
  accuracy against the spec, CI and Formatting on a fork scratch branch, one change, upstream AGENTS.md and CONTRIBUTING, PR text,
  gameval ids, in game on its own client. Fork actions (scratch branches, fork PRs, docs branch, fork CI) are
  part of the gate and need no approval. Dev and QA run locally only the tests of the touched modules plus
  spotlessCheck on them; the full suite is the fork CI run, and the record's `Tests` line names both.
- **BR-S8 Client done.** Commit on `master`: repack log with 7 `telemetry:` lines, device evidence (logcat or
  data-tool dump), a `netqa` record when networking changes; docs-only changes need no build evidence.

## 7. Business rules: batches

- **BR-B1 Train.** The daemon starts a train when a server change is queued, or on demand: pins every queued
  change at its `commit`, rebuilds `integration` in recorded order with recorded conflict resolutions, pushes with a
  lease, runs the gate, builds the image (keys only by `COPY --from` the live image; key hash must match; private
  boot check), records the image.
- **BR-B2 One train at a time.** One integration lock; changes queued during a train join the next.
- **BR-B3 Deploy.** A gated image deploys when the daemon holds the `live-server` lock (BR-R3). Rollback tag first;
  `compose up -d --no-deps`, never `--build`; wait for "Server ready in"; roll back when the container exits. On
  success every included change is on the test server, dependents unblock, the metric recounts.
- **BR-B4 Exceptions go to an agent.** An unrecorded conflict, a gameval clash, a gate failure or a boot failure puts
  the train on `exception`; an `integrator`, briefed from the stop output, records a resolution or drops one change
  with a note; it never pushes `integration` or deploys.
- **BR-B5 Re-pin.** When upstream `main` moves, fork `main` fast-forwards, merged branches drop, a train runs. The
  test server is always on current upstream.
- **BR-B6 Release.** A release batch is created by a rule (N client changes on `master`, or a user request); it gates
  `master` at a commit with `client-qa` (Network QA included), then needs the user's yes to tag and publish with the
  APK attached.

## 8. Business rules: the user's yes

- **BR-A1 Only two kinds.** `upstream` (open, update, mark ready, move to draft, comment on an OpenRune PR; a push to a branch
  that backs an open OpenRune PR) and `release` (tag and GitHub release). A `decision` hold carries a question when an
  agent cannot proceed; the console asks it in chat. Fork actions, local commits and harness merges need none.
- **BR-A2 Only when gated.** No upstream action or release is offered before its gate passed at the same commit.
- **BR-A3 Explained.** The user sees the exact commands, the full text to be posted, the gate record, the diff range
  and the caveats; never a summary.
- **BR-A4 Executed once, after the yes.** The console runs the commands after a yes, never before. A no or silence
  changes nothing; the action stays listed until the world moves. One yes covers that commit's contribution only.
- **BR-A5 Stale detection.** If GitHub already shows the action done, it leaves the list.
- **BR-A6 Never blocks the loop.** Everything not depending on the user keeps moving.
- **BR-A7 Notification.** A decision, a `failed` hold, a deploy and a rollback each notify once; many at once are
  one digest.
- **BR-A8 Append, never edit.** An existing OpenRune PR description is never replaced; updates are comments, except
  when the shown text says the description is replaced and the user said yes to that text.

## 9. Business rules: resources, agents, policy

- **BR-R1 Locks.** Only a resource that exists once is a lock: `integration`, `live-server`, `ghidra`. A lock has a
  holder, a purpose, an attached process or container and a UTC time.
- **BR-R2 Reclaim.** A lock is taken only while in use; one whose holder's run ended or whose process or container is
  gone is reclaimed with that evidence in the event.
- **BR-R3 Lock-checked tools.** Tools that drive a locked resource (deploy, the integration push) refuse without it.
- **BR-R4 Own client.** A client instance (emulator, desktop RuneLite) is not locked: every agent starts its own with
  its own profile, port and account state and stops it when done.
- **BR-R5 Capacity.** One machine budget as data (policy `capacity`): the classes `agent`, `build`, `client` (desktop clients, 2), `device` (the Android app, 0 until BlueStacks is up; `client-dev` holds it) and
  `image`. A role and a train step declare the classes they use; dispatch books a run only while every class it uses
  has a free slot, counted from runs not ended and batches at a step that uses one.
- **BR-G1 Agents.** One change, one stage, a fresh context, a brief generated from the change; roles `client-dev`,
  `client-qa`, `server-dev`, `server-qa`, `integrator`, `harness-dev`.
- **BR-G2 Exit.** An agent ends when its stage is reached or its hold is set; the daemon stops one still alive on a
  later tick. Cost (tokens, turns, exit reason) is recorded on the change.
- **BR-G3 Conduct.** Agents read game state through data tools, not screenshots; use their own scratch dir; hand
  read-heavy lookups to read-only subtasks; report denials, never work around them.
- **BR-G4 Rules reach agents by a new run:** the brief and role file are read at spawn.
- **BR-P1 Agent writes.** Agents never push to OpenRune, deploy, grant, write progress or edit records they did not
  make. `server-dev` may push the fork and open fork PRs; `server-qa` may push the fork's `docs` and gate scratch
  branches; QA roles write only records. Targets are resolved (remote URL, repo, branch, instance), never matched as
  words.
- **BR-P2 Daemon and console.** Only the daemon deploys, grants, merges, trains and re-pins; only the console runs
  upstream actions.
- **BR-P3 Denials are events** with the rule that fired.
- **BR-P4 Harness changes** go through an allow-listed path agreed with the user: worktree, a test per rule touched,
  merge by the daemon.
- **BR-X1 Accuracy.** Behaviour matches the official game: RSProx recordings over wiki over cache; every divergence is
  a caveat in the spec and the PR text.
- **BR-X2 Privacy.** Every APK passes the telemetry patch (7 assertions); netcheck/NetScan on plugins; Network QA
  whenever traffic changes; any new outbound host halts the change.
- **BR-X3 Isolation.** Only processes the harness started are stopped.

## 10. Business rules: reconciliation, healing, measurement

- **BR-H1 Observe first.** Each tick reads fork and OpenRune refs and PR states, CI conclusions, `live.json`, docker,
  locks, running agents and the upstream `main` tip; any difference from the store is repaired and logged as `drift`.
- **BR-H2 Heal.** Idle locks are reclaimed, agents alive past their stage stopped, dead branch servers and stale
  containers removed, a failed deploy rolled back; each is an event, the user hears of it in the digest only.
- **BR-H3 Idle detection.** A lock held without use is detected within one tick; detect and recover are events.
- **BR-H4 Events.** `events.jsonl` is append-only, UTC, and records every stage change, hold, batch step, lock event,
  agent start and end (cost), denial, drift, deploy, re-pin and metric recount; the store can be rebuilt from it.
- **BR-H5 Metrics are derived, never typed.** Client metrics on each client `master` merge; server parity on each
  deploy and re-pin.
- **BR-H6 Status.** Status, the console's work list, KPIs and the digest read the store and the log and keep no state
  of their own. Times are shown in US Eastern, stored in UTC. KPIs: unattended hours, lead time, first-pass hand-over
  rate, gate first-pass rate, interventions per day, denials per hour, tokens per change by role.
- **BR-H7 Maintenance.** The daemon keeps this repo tidy as harness-internal work, no approval: it commits the change
  store (pathspec-only) when only store files differ, removes clean agent worktrees and local branches merged into
  `main` while no agent runs, keeps `.claude/worktrees` ignored, and lists the holds nothing will clear (a hold on a
  finished change, a dep naming no change).

## 11. Acceptance

1. A night with no user message in which the daemon dispatched, trained, deployed, unblocked and re-pinned, and the
   user returned to a digest and a list of approvals.
2. An idle lock, a lingering agent, a dead branch server, a drifted stage and a failed deploy are each injected and
   repaired without the user.
3. No prompt reached the user for anything but an upstream action or a release.
