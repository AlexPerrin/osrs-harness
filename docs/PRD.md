# Harness PRD

The process in its simplest terms and every business rule the harness enforces (cited as BR-*). docs/ARCHITECTURE.md
is how it is built; each module's docstring is its spec.

## 1. Product statement

A daemon moves changes to their live targets for two products without a human or a chat session on the path. The
user's priorities, in order: it runs overnight, it shows its status, it heals itself. Only an upstream action and a
client release wait for the user.

| Product | Goal | Metric | Live target |
|---|---|---|---|
| Client | RuneLite on mobile | RuneLite API %, core plugins, the user's plugins, hub plugins, packets (client repo `tools/progress.py`) | `master`; a tagged release |
| Server | an identical copy of the OSRS server, contributed upstream | server parity % of the integration tree and of upstream `main` | the live test server; upstream `main` |

## 2. The model in its simplest terms

```
CHANGE    = { slug, track, branch, commit, stage, hold?, deps[], dod[], evidence, cost }
STAGE     : backlog -> ready -> dev -> checked -> live -> gated -> published -> merged
HOLD      : blocked(deps) | decision(user) | failed(fix needed) | exception(integrator)
RULE      : a change advances to the next stage when that stage's precondition is OBSERVED true;
            the actor is a script, unless the step needs judgement (agent) or crosses the boundary (user)
BATCH     = train   (server: every checked change -> one integration commit -> image -> live)
          | release (client: a set of live changes -> gate -> tag)
LEASE     = resource + holder + purpose + attached process
EVENT     = every change to any of the above, appended once, UTC
DRIVER    = loop { observe -> advance -> dispatch -> heal -> log }
```

1. **A change is the only unit of work.** Specs, gates, fixes and review rounds are stages or new commits of one
   change. Harness work and cleanups are changes on the `harness` track (`ready -> dev -> checked -> live`).
2. **Stages are the same for both tracks; preconditions differ** (section 4). A client change stops at `live`;
   releases carry the client's `gated -> published` as a batch.
3. **Truth is observed, never remembered.** Every precondition is a fact the daemon can read (a ref at a sha, a CI
   conclusion, a PR state, an image record, a lease row). The store is a cache of those facts.
4. **Only two actions need the user**: an upstream action on OpenRune (open, update, ready, comment) and a client
   release (tag, GitHub release). The user's yes is given in chat; nothing else prompts.
5. **Agents are stage executors.** One change, one stage, an exit. Everything repeatable is a script.
6. **Resources are leases**, and a tool that touches a resource checks the lease.
7. **The event log is the product's memory.** The KPIs and every post-mortem read it; nothing is rewritten.

## 3. Business rules: changes

- **BR-C1 Identity.** A change is named by its slug; its branch is `content/<slug>`, `fix/<slug>`, `local/<slug>`
  (server), `client/<slug>` (client) or `harness/<slug>` (harness); its spec is `accuracy/<slug>.md`, its gate record
  `qa/<slug>.md`, its PR text `pr-texts/<slug>.*`, all on the fork's `docs` branch. No second branch for the same
  change (no prefixes or suffixes besides these).
- **BR-C2 One change, one commit pointer.** `commit` is the commit the dev handed over. A new commit on the
  branch (fix, review round, merge from `main`) re-enters the change at `dev` with the hand-over's evidence due
  again, and voids every stage after `checked`.
- **BR-C3 Definition of done before ready.** A change leaves `backlog` only with a definition of done; a server
  change's DoD always contains the spec, the fork PR with green CI, one change only, off current `main`.
- **BR-C4 Dependencies are edges.** `deps[]` names other changes. A change is `ready` only when every dep is
  `live` or later. A client change that needs the server files the server change itself and adds the edge.
- **BR-C5 Priority.** P1 before P2; a server change that unblocks a client change inherits the client's priority;
  age breaks ties.
- **BR-C6 Scope.** One quest, feature or fix per change; a fix found on the way is its own change; a large feature
  is split in the spec before coding; no change contains a commit of another open upstream PR (no stacking).
- **BR-C7 Local-only.** `local/*` changes end at `live`; they are never gated or published.
- **BR-C8 Merged means dropped.** When upstream `main` contains the change's commit, the next re-pin removes the
  branch from integration and the change is `merged`.

## 4. Business rules: stages and their preconditions

The precondition is what the daemon must observe before the stage counts as reached. "Script" means the daemon.

| Stage | Reached when (server) | Reached when (client) | Actor |
|---|---|---|---|
| backlog | filed | filed | user, console, or a dev filing a blocker |
| ready | DoD present; every dep live or later; no hold | same | script |
| dev | an agent owns it (run record) | same | script books the run; the console spawns it |
| checked | branch at `commit` on the fork; spec on `docs`; fork PR open; CI `success` at exactly `commit`; DoD all ticked; evidence dir non-empty | branch at `commit`; commit not on `master`; repack log with 7 `telemetry:` lines; device evidence (logcat or data-tool dump); `netqa` record when the change touches networking; docs-only changes need none of the build evidence | script (the hand-over check) after the agent's claim |
| live | integration pin = `commit` **and** the live server runs the image built from that integration commit (`live.json`) | `master` contains `commit` | script: train (server), merge (client) |
| gated | QA record `## Upstream gate: **PASS**` at `commit`, written while the live server ran `commit`; CI green at `commit`; one change; on current `main`; gameval check clean; PR text reviewed | (release batch) `qa/client-X.Y.Z.md` with `## Verdict: **PASS**` at the `master` commit, Network QA included | agent `server-qa` / `client-qa` |
| published | the OpenRune PR is open, not draft, head = `commit` | the tag exists and the GitHub release is published | **user says yes; the console executes** |
| merged | upstream `main` contains `commit` | n/a (published is terminal) | observed |

The harness track's `live` is: this repo's `main` contains `commit`.

- **BR-S1 Gate only what is live.** `gated` is unreachable unless `live` was reached at the same `commit`.
- **BR-S2 A stage is never set by hand.** The daemon sets stages from observations; an operator can add a hold
  or a note, not a stage.
- **BR-S3 A failed gate is a hold, not a stage.** `failed` holds the change with the record's required changes;
  the fix is a new commit (BR-C2); the hold clears on the next hand-over.
- **BR-S4 Maintainer review is a hold.** A review comment on the upstream PR puts the change on `failed` with the
  comment as the required change; a push to that PR branch is an upstream action and needs the user's yes (BR-A2).
- **BR-S5 A check failure returns the change to `ready`** with the failing items; the next agent fixes exactly those.

## 5. Business rules: batches

- **BR-B1 Train.** The daemon starts a train when a checked server change has waited the policy debounce, or on demand. A train: pins
  every checked change at its `commit`, rebuilds `integration` in recorded order with recorded conflict resolutions,
  pushes with a lease, runs the gate, builds the image (keys only by `COPY --from` the live image; key hash must
  match; private boot check), records the image.
- **BR-B2 One train at a time.** One integration lock. Changes checked during a train join the next one.
- **BR-B3 Deploy.** A gated image deploys when all instances are leased by the daemon (BR-R4 drain). Rollback tag
  first; `compose up -d --no-deps`, never `--build`; wait for "Server ready in"; auto-rollback on timeout. On
  success every included change becomes `live`, dependents unblock, the metric recounts.
- **BR-B4 Exceptions go to an agent.** An unrecorded conflict, a gameval clash, a gate failure or a boot failure
  puts the train on `exception`; an `integrator` agent, briefed from the train and the stop output, records a
  resolution or drops one change (with a note); it never pushes `integration` or deploys.
- **BR-B5 Re-pin.** When upstream `main` moves, the daemon files a re-pin: fork `main` fast-forwards, merged
  branches drop, a train runs. The test server is always on current upstream.
- **BR-B6 Release.** A release batch is created by a rule (N live client changes, or a user request); it gates
  `master` at a commit with `client-qa`, then needs the user's yes to tag and publish with the APK attached.

## 6. Business rules: the user's yes

- **BR-A1 Only two kinds.** `upstream` (open, update, mark ready, comment on an OpenRune PR; a push to a branch
  that backs an open OpenRune PR) and `release` (tag + GitHub release). A `decision` hold carries a question when an
  agent cannot proceed; the console asks it in chat.
- **BR-A2 Only when gated.** No upstream action or release is offered before its gate passed at the same commit.
- **BR-A3 Explained.** Every action is shown with the exact command(s) that will run, the full text that will be
  posted (PR body, comment), the gate record, the diff range and the caveats. The user never approves a summary.
- **BR-A4 Executed once, after the yes.** The console runs the commands after a yes, never before. A no or silence
  changes nothing: the action stays listed until the world moves.
- **BR-A5 Stale detection.** If GitHub already shows the action done (PR open, ready, head = commit), it leaves the
  list; the user is not asked.
- **BR-A6 Never blocks the loop.** Everything that does not depend on the user keeps moving.
- **BR-A7 Notification.** A decision, a `failed` hold, a deadlock, a deploy and a rollback each notify once; many at
  once are one digest.
- **BR-A8 Append, never edit.** An existing OpenRune PR description is never replaced; updates are comments, except
  when the shown text says the description is replaced and the user said yes to that text.

## 7. Business rules: resources, agents, policy

**Leases**
- **BR-R1** Every instance (`device`, `desktop`, `desktop2`, more rows later), build slot, the integration lock,
  the Ghidra writer and the live server are leases with: holder, purpose, attached process or container, heartbeat,
  expiry, UTC times.
- **BR-R2** A lease is granted at dispatch for the change's stage and taken only while in use; a lease whose attached
  process or container is gone is reclaimed, with that evidence in the event.
- **BR-R3** The tools that drive a resource (the devtools bridge, `desktop.sh`, `qa.sh`, deploy) refuse without
  the lease; a branch server or client is named by its holder.
- **BR-R4 Drain.** A pending deploy stops new grants on the instances, waits for current holders up to a cap,
  reclaims past it, deploys, then re-grants. A waiter never starves the deploy it waits for.
- **BR-R5 Capacity.** Client slots = Android instances; server slots = 2; one QA per track; build slots by class
  (gate, dev, measure) with the memory guard.

**Agents**
- **BR-G1** One change, one stage, a fresh context, a brief generated from the change; roles: `client-dev`,
  `client-qa`, `server-dev`, `server-qa`, `integrator`, `harness-dev`.
- **BR-G2** An agent ends when its stage is reached or its hold is set; the daemon stops any agent still alive one
  tick later. Cost (tokens, turns, exit reason) is recorded on the change.
- **BR-G3** Agents read game state through data tools, not screenshots; keep leases only while in use; use their
  own scratch dir; hand read-heavy lookups to read-only subtasks; report denials, never work around them.
- **BR-G4** A rule change reaches running agents by a new run: the brief and role file are read at spawn.

**Policy (one versioned file; hooks, briefs and the daemon read it; a test per rule)**
- **BR-P1** Agents never push to OpenRune, deploy, grant, write progress or edit records they did not make.
  `server-dev` may push the fork and open fork PRs; `server-qa` may push the fork's `docs`; QA roles write only
  records. Targets are resolved (remote URL, repo, branch, instance), never matched as words.
- **BR-P2** Only the daemon deploys, grants, merges, trains and re-pins; only the console runs upstream actions.
- **BR-P3** Every denial (hook or classifier) is an event with the rule that fired.
- **BR-P4** Harness changes go through an allow-listed path agreed with the user (worktree, tests, merge).

**Accuracy and privacy**
- **BR-X1** Behaviour matches the official game: RSProx recordings over wiki over cache; every divergence is a
  caveat in the spec and the PR text.
- **BR-X2** No client contacts Jagex; every APK passes the telemetry patch (7 assertions); netcheck/NetScan on
  plugins; Network QA whenever traffic changes; any new outbound host halts the change.
- **BR-X3** The user's own RuneLite is never read; the tester account is never emptied; only processes the
  harness started are stopped.

## 8. Business rules: reconciliation, healing, measurement

- **BR-H1 Observe first.** Each tick reads: fork and OpenRune refs and PR states, CI conclusions, `live.json`,
  docker images and containers, leases, running agents, upstream `main` tip. Any difference from the store is
  repaired in the store and logged as `drift`.
- **BR-H2 Heal.** Idle leases: reclaimed. Agents alive past their stage: stopped. Dead branch servers and stale
  containers: removed. A failed deploy: rolled back. Each is an event; the user is told only in the digest.
- **BR-H3 Deadlock.** A cycle or an idle hold that stops a waiter is detected within one tick and resolved by
  BR-R2/BR-R4; detect and recover times are events.
- **BR-H4 Events.** `events.jsonl`, append-only, UTC: every stage change, hold, batch step, lease event, agent start
  and end (cost), denial, drift, deploy, re-pin, metric recount. The store can be rebuilt from the log.
- **BR-H5 Metrics are derived, never typed.** Client metrics from `tools/progress.py` on each client `live`;
  server parity from the parity tool on each deploy and each re-pin (integration and upstream `main`).

## 9. Status

`hd status` (changes with why each waits, batches, leases, runs, daemon), `hd drive` (the console's work list), `hd kpi`
and the digest read the store and `events.jsonl`; they keep no state of their own. Times shown in the user's zone
(US Eastern), stored in UTC. Harness KPIs (from events): unattended hours, lead time ready -> live, first-pass check
rate, gate first-pass rate, stall minutes, interventions per day, denials per hour, tokens per change by role.

## 10. Architecture

- **`harnessd`**: one long-running process in WSL that owns the store and runs the tick (observe, advance, dispatch,
  heal, log), trains, images, deploys and re-pins.
- **The console session** (Claude Code, with the user in chat) spawns the agents the daemon books and runs the upstream
  actions after the user's yes; it does not run the loop.
- **Store**: one file per change (YAML front matter + DoD + log), `batches/`, `leases/`, `runs/`, `events.jsonl`,
  `policy.yaml`. Human-readable, git-ignored except `policy.yaml` and the changes.
- **Tests**: a test per business rule above, run on every harness change; replay fixtures for a train, a deploy, a
  reconcile, a deadlock.

## 11. Acceptance criteria

1. A night (8 h) with no user message in which the daemon dispatched, checked, trained, deployed, unblocked and
   re-pinned, and the user returned to a digest and a list of upstream actions.
2. Each of these is injected and repaired without the user: an idle lease, a lingering agent, a dead branch server,
   a drifted stage, a failed deploy.
3. No prompt reached the user for anything but an upstream action or a release.

## 12. Open decisions for the user

1. Milestone dates for the forecast (the user's 25 plugins; v0.2.0; a parity %).
2. The notification channel for the digest.
