# Requirements

What a solution to docs/PROBLEM.md must satisfy. Each requirement has a stable id (BR-*) that code and tests cite, is
testable, and traces to a goal. docs/ARCHITECTURE.md names the mechanism that meets each.

Goals referenced: **Unattended** (runs without the user), **Status** (shows what is happening), **Heals** (repairs
itself), **Client**, **Server-unblock** (the test server runs a change at once), **Server-upstream** (clean verified
contributions), **Harness** (safe, simple self-improvement), **Privacy** (nothing leaks, nothing of the user's is touched).

## Changes (all tracks)

| Id | Requirement | Goal |
|---|---|---|
| BR-C1 | A change is named by its slug; its branch is `content/<slug>`, `fix/<slug>`, `local/<slug>` (server), `client/<slug>` or `harness/<slug>`. No second branch for the same change. | Unattended |
| BR-C2 | `commit` is the commit the dev handed over. A new commit on the branch (fix, review round, merge from `main`) re-enters the change at dev, the hand-over's evidence is due again, and every later fact (gate, approval) is void. | Server-upstream |
| BR-C3 | A change leaves `backlog` only with a definition of done; a server change's contains the spec, one change only, off current `main`. | Unattended |
| BR-C4 | `deps[]` names other changes; a change is `ready` only when every dep is done for its purpose. A client change that needs the server files the server change itself and adds the edge. | Server-unblock |
| BR-C5 | One order for every track, recomputed from facts each tick: a change a track says settles open work (a review fix on an open PR) while policy `settle_first` is true; then effective priority (the highest of the change and of every unfinished change that lists it as a dep while it is not live, transitive); then age. | Server-unblock |
| BR-C6 | One quest, feature or fix per change; a fix found on the way is its own change; no change contains a commit of another open upstream PR (no stacking). An upstream diff carries no test file unless a rule has several cases or a reviewer asked. | Server-upstream |
| BR-C7 | A change with a `local/*` branch or `local_only` ends at the test server; it is never gated or published. | Server-upstream |
| BR-C8 | When upstream `main` contains the change's commit, the next re-pin removes the branch from integration and the change is `merged`. | Server-upstream |

## Stages, holds, failure (all tracks)

| Id | Requirement | Goal |
|---|---|---|
| BR-S2 | Stages are set from observed facts (a ref at a sha, a CI conclusion, a PR state, an image record, a lock row); an operator adds a hold or a note, never a stage. A hold is `decision`, `failed` or `exception`; nothing clears one automatically: `hd unhold` does, a hand-over or a moved commit also clears `failed`. A change waiting on a dep is not held; the wait is derived each tick. | Unattended |
| BR-S3 | A fix is asked for with a `failed` hold carrying the findings; the fix is a new commit (BR-C2); the hold clears on the next hand-over. | Server-upstream |
| BR-S5 | A failed hand-over returns the change to `ready` with the failing items; a failing check never re-dispatches a dev without new facts. | Unattended |
| BR-S9 | A dev or verifier is booked only if the head SHA or the finding set differs from the last booked run; otherwise a durable `decision` hold appears in the user's list. | Unattended |
| BR-S10 | No timeout, debounce, grace period, heartbeat or `*_minutes` / `*_seconds` knob: an action ends on an observed fact and fails only on a fact meaning its result cannot arrive (the step's process or container exited without its record, the run concluded). A queued server change starts a train at once. | Unattended |

## Client track

| Id | Requirement | Goal |
|---|---|---|
| BR-S8 | Client done = commit on `master` with the repack log (7 `telemetry:` lines), device evidence (logcat or data-tool dump) and a `netqa` record when networking changes; a docs-only change needs no build evidence. | Client, Privacy |
| BR-B6 | A release batch is created by a rule (N client changes on `master`) or a user request; it gates `master` at one commit with `client-qa` (Network QA included), then needs the user's yes to tag and publish with the APK attached. | Client |
| BR-X2 | Every APK passes the telemetry patch (7 assertions); netcheck/NetScan on plugins; Network QA whenever traffic changes; any new outbound host halts the change. | Privacy |
| BR-R4 | A client instance (BlueStacks, desktop RuneLite) is not locked: every agent starts its own with its own profile, port and account state, stops it when done and never touches an instance already open (the user's own BlueStacks). | Client |

## Server track

| Id | Requirement | Goal |
|---|---|---|
| BR-S4 | A maintainer finding on the upstream PR is filed once, keyed by its comment or review id, as a review-fix change carrying the finding; moving the PR to draft and any push to its branch are upstream actions (BR-A1). | Server-upstream |
| BR-S6 | A PR leaves draft only when reported defects are fixed in its head, CI is green at that commit, the gate passed there, the PR text is true and no deferral wording ("its own PR", "later") is in it. | Server-upstream |
| BR-S7 | The gate checks the exact commit merged with current upstream `main` in a scratch clone: accuracy against the spec, CI and Formatting on a fork scratch branch (a green fork run satisfies its upstream twin; each check runs once), one change, upstream AGENTS.md and CONTRIBUTING, PR text, gameval ids, in game on its own client. Fork actions are part of the gate and need no approval. Dev and QA run locally only the tests of the touched modules plus spotlessCheck on them; the full suite is the fork CI run, and the record's `Tests` line names both. A red fork check, Formatting included, means not ready for upstream. | Server-upstream |
| BR-B1 | The daemon starts a train when a server change is queued, or on demand: pins every queued change at its `commit`, rebuilds `integration` in recorded order with recorded conflict resolutions, pushes with a lease, runs the gate, builds the image (keys only by `COPY --from` the live image; key hash must match; private boot check), records the image. | Server-unblock |
| BR-B2 | One train at a time; changes queued during a train join the next. | Server-unblock |
| BR-B3 | A gated image deploys when the daemon holds the `live-server` lock. Rollback tag first; `compose up -d --no-deps`, never `--build`; wait for "Server ready in"; roll back when the container exits. On success every included change is on the test server, dependents unblock, the metric recounts. | Server-unblock |
| BR-B4 | An unrecorded conflict, a gameval clash, a gate failure or a boot failure puts the train on `exception`; an `integrator`, briefed from the stop output, records a resolution or drops one change with a note; it never pushes `integration` or deploys. | Server-unblock, Unattended |
| BR-B5 | When upstream `main` moves, fork `main` fast-forwards, merged branches drop, a train runs: the test server is always on current upstream. | Server-unblock |
| BR-X1 | Behaviour matches the official game: RSProx recordings over wiki over cache; every divergence is a caveat in the spec and the PR text. | Server-upstream |

## The user's yes (upstream and releases)

| Id | Requirement | Goal |
|---|---|---|
| BR-A1 | Only two kinds of action need the user: `upstream` (open, update, mark ready, move to draft, comment on an OpenRune PR; a push to a branch backing an open OpenRune PR) and `release` (tag and GitHub release). A `decision` hold carries a question when an agent cannot proceed; the console asks it in chat. Fork actions, local commits and harness merges need none. | Unattended |
| BR-A2 | No upstream action or release is offered before its gate passed at the same commit. A QA finding blocks nothing by itself; the user's approval is the only gate to an upstream action. | Server-upstream |
| BR-A3 | The user sees the exact commands, the full text to be posted, the gate record, the diff range, the caveats and a concise context (branch, commit, net diff, what QA verified, risk, recommendation); never a summary. | Server-upstream |
| BR-A4 | The console runs the commands after a yes, never before. A no or silence changes nothing; the action stays listed until the world moves. One yes covers that commit's contribution only, as one atomic sequence with no further asks: push (fast-forward or merge commit, never force), green CI at that commit, comment, out of draft; if CI does not go green it stops before the comment and reports. After the push only the required upstream twins are confirmed. | Server-upstream |
| BR-A5 | If GitHub already shows the action done, it leaves the list. | Status |
| BR-A6 | Everything not depending on the user keeps moving. | Unattended |
| BR-A7 | A decision, a `failed` hold, a deploy and a rollback each notify once; many at once are one digest. | Status |
| BR-A8 | An existing OpenRune PR description is never replaced; updates are comments, except when the shown text says the description is replaced and the user said yes to that text. | Server-upstream |

## Resources and capacity

| Id | Requirement | Goal |
|---|---|---|
| BR-R1 | Only a resource that exists once is a lock: `integration`, `live-server`, `ghidra`. A lock has a holder, a purpose, an attached process or container and a UTC time. | Unattended |
| BR-R2 | A lock is taken only while in use; one whose holder's run ended or whose process or container is gone is reclaimed with that evidence in the event. | Heals |
| BR-R3 | Tools that drive a locked resource (deploy, the integration push) refuse without it. | Server-unblock |
| BR-R5 | One machine budget as data (policy `capacity`): the classes `agent`, `build`, `client` (2), `device` (2) and `image`. A role and a train step declare the classes they use; dispatch books a run only while every class it uses has a free slot, counted from runs not ended and batches at a step that uses one. | Unattended |

## Agents and permissions

| Id | Requirement | Goal |
|---|---|---|
| BR-G1 | One change, one stage, a fresh context, a brief generated from the change; roles `client-dev`, `client-qa`, `server-dev`, `server-qa`, `integrator`, `harness-dev`. | Unattended |
| BR-G2 | An agent ends when its stage is reached or its hold is set; the daemon stops one still alive on a later tick. Cost (tokens, turns, exit reason) is recorded on the change. | Status, Heals |
| BR-G3 | Agents read game state through data tools, not screenshots; use their own scratch dir; hand read-heavy lookups to read-only subtasks; report denials, never work around them. | Privacy |
| BR-G4 | Rules reach agents by a new run: the brief and role file are read at spawn. | Unattended |
| BR-P1 | Agents never push to OpenRune, deploy, grant, write progress or edit records they did not make. `server-dev` may push the fork and open fork PRs; `server-qa` may push the fork's `docs` and gate scratch branches; QA roles write only records. Targets are resolved (remote URL, repo, branch, instance), never matched as words. | Server-upstream |
| BR-P2 | Only the daemon deploys, grants, merges, trains and re-pins; only the console runs upstream actions. | Server-upstream |
| BR-P3 | Denials are events with the rule that fired. | Status |
| BR-X3 | Only processes the harness started are stopped. | Privacy |

## Harness track

| Id | Requirement | Goal |
|---|---|---|
| BR-P4 | Harness changes go through an allow-listed path: a worktree, a test per rule touched, merge by the daemon, autonomous; a major rebuild deploys (merge and daemon restart) only after the user's yes. | Harness |
| BR-H7 | The daemon keeps this repo tidy without approval: it commits the change store (pathspec-only) when only store files differ, removes clean agent worktrees and local branches merged into `main` while no agent runs, keeps `.claude/worktrees` ignored, and lists the holds nothing will clear (a hold on a finished change, a dep naming no change). | Harness, Heals |
| BR-I1 | Iteration: every iteration starts from PROBLEM, PRD and ARCHITECTURE and ends by updating them; code, tests, policy keys and docs not traceable to a requirement here are removed; each iteration reduces complexity. | Harness |

## Observation, healing, measurement

| Id | Requirement | Goal |
|---|---|---|
| BR-H1 | Each tick reads fork and OpenRune refs and PR states, CI conclusions, `live.json`, docker, locks, running agents and the upstream `main` tip; any difference from the store is repaired and logged as `drift`. | Heals |
| BR-H2 | Idle locks are reclaimed, agents alive past their stage stopped, dead branch servers and stale containers removed, a failed deploy rolled back; each is an event, the user hears of it in the digest only. | Heals |
| BR-H8 | A running `qa-dev-<name>` container whose run ended, has no run record, or whose change left its stage is stopped; one whose run is alive never. | Heals |
| BR-H9 | A run that ends with a linked agent id is listed under Stop in `hd drive` until `hd run-stopped` records the stop. | Heals |
| BR-H3 | A lock held without use is detected within one tick; detect and recover are events. | Heals |
| BR-H4 | `events.jsonl` is append-only, UTC, and records every stage change, hold, batch step, lock event, agent start and end (cost), denial, drift, deploy, re-pin and metric recount; the store can be rebuilt from it. | Status |
| BR-H5 | Metrics are derived, never typed: client metrics on each client `master` merge; server parity on each deploy and re-pin. | Status |
| BR-H6 | Status, the console's work list, KPIs and the digest read the store and the log and keep no state of their own. Times are shown in US Eastern, stored in UTC. KPIs: unattended hours, lead time, first-pass rates of hand-over and gate, interventions per day, denials per hour, tokens per change by role. | Status |

## Acceptance

1. A night with no user message in which the daemon dispatched, trained, deployed, unblocked and re-pinned, and the user
   returned to a digest and a list of approvals.
2. An idle lock, a lingering agent, a dead branch server, a drifted stage and a failed deploy are each injected and
   repaired without the user.
3. No prompt reached the user for anything but an upstream action or a release.
