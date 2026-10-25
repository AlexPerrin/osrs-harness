# Root causes

One short entry per issue, newest first: symptom, root cause, evidence, fix, how to recognise it again.

## 2026-10-25 First agents under v7 (all fixed the same day)

- **Agents ran unbound.** The SubagentStart event fired before the agent's transcript existed (or not at all under the
  session's stale hook config), so no run was recorded and a dev could push nothing. Fix: the guard binds an unbound
  role at its first command. Recognise: `hd` lists a spawn for a change whose agent is already running.
- **A stop ended a paused agent.** SubagentStop fires when an agent waits on background work; the run was ended, a new
  one dispatched, and repairs deleted the agent's clone mid-work. Fix: a stop ends the run only when the transcript holds
  a SubagentHandback call. Recognise: a `run end` event followed by commands from the same agent id.
- **Pins cleared a failed train.** The pass's own pin commits moved the tools branch, which read as "resolved", so the
  train restarted into the same conflict and no integrator was listed. Fix: pin-only movement keeps the failure.
- **Three integrators for one train.** Every queued change listed its own integrator. Fix: one integrator at a time.
- **A hand-over followed by a gate failure stalled.** The no-loop rule compared head and definition only, so the gate
  fix at the same head looked like a repeat and became a question. Fix: the step is part of the input.
- **Image pruning raced the train** (found by audit, not live): a tick between image build and deploy would remove the
  new image. Fix: no pruning while the train is alive.

## 2026-10-25 First v7 pass on the live system (all fixed the same day)

- **A squash-merged PR never counted as done.** `done` checked ancestry only; #368 and #406 stayed at `gate`. Fix: the
  PR's merged state counts too. Recognise: a merged PR whose change still lists a step.
- **The gate failed every migrated change on PR texts.** The gate required `pr-title.txt`, `pr-body.md`, `pr-comment.md`;
  v6 evidence rarely had them, so ten changes went back to a dev to add a file. Fix: the gate checks the accuracy spec and
  CI; `pr` and `comment` check the text they post and become the dev's step when it is missing; a comment is not owed
  when nobody else has commented or ours names the head.
- **The gate script crashed with `ok` unbound** after that edit removed its initialisation. Fix: `ok, pending = True, False`.
- **Migrated approvals were dated at the migration**, so a maintainer comment made before it was not a finding. Fix: the
  three approvals dated at the v6 push; the finding on #355 was then filed.
- **A pending gate rewrote its record every pass** (one record event per minute). Fix: saved only when it changed.
- **Refusals printed an empty sha** for a change whose ref does not exist. Fix: "nothing".

## 2026-10-25 Audit of the v6 code: open defects (v7 inputs)

Found by reading the code; none reproduced live. Fixed ones say so.

- **Contribution publishes an unapproved commit.** `hd/tracks/server/contribute.py` `run` checks `refusal(ch, approved)`
  once; each pass reloads the change, so a hand-over during the CI wait makes the next pass push, comment and ready the
  new commit. Fixed: `run` calls `refusal` on every pass (test: `ContributeTest`). Recognise: a PR head commit with no QA
  record or approval.
- **Lost change-file updates.** The tick works on `Ctx.idx` (loaded at tick start) and `hd handover`, `dod`, `log` do
  load, edit, save on the whole file; only `batches.lock` locks. A handover's commit or a `dod` tick can vanish, or
  `heal._dead_runs` can send a handed-over change back to `ready`. Fix: one `flock` around reload-edit-save.
  Recognise: a hand-over event with no commit on the change.
- **Hooks are best-effort.** `hooks/deny_publish.py` matches text: `git "push"`, `git p''ush`, `gh workflow run` and
  `gh secret set` on upstream are allowed, and commands inside scripts are invisible. Fix: agent sessions get no
  upstream-write credential; add the missing `gh` verbs. Recognise: a `denial`-free upstream write by an agent.
- **Broken change files disappear.** `store.all_changes` skips a file with bad YAML or no front matter without an event.
  Fix: emit an `error` event and count them in `hd status`. Recognise: a change absent from `hd status`.
- **Reused pids look alive.** `pid_alive` (`os.kill(pid, 0)`) backs leases and batch health; after a WSL restart a
  recycled pid keeps a lock or batch "in use". Fix: record the process start time with the pid.
- **A failed fetch counts as fresh.** `Observer.fetch` sets `_fetched` first and ignores return codes, so stale refs
  derive stages. Fix: a failed fetch makes ref facts unknown for the tick.
- **`heal` removes starting containers.** `_containers` runs `docker rm -f` on every `qa-or-*` / `hd-boot-*` whose status
  does not start with "up" (`Restarting`, `Paused`, `Created`). Fix: remove only `exited` and `dead`.
- **Minor.** `train/deploy.sh` and `image.sh` default `STATE` to the client checkout (the daemon passes `HD_STATE_DIR`);
  `daemon._server_json` is unused; `.claude/worktrees/agent-ada2833…` is a finished worktree; `tests/test_hooks.py:312`
  leaves files open; the co-author line is hard-coded in `hd/ship.py` and `train/integrate.py`.

## 2026-10-25 The OpenRS2 cache download failed the Hunter gate

- **Symptom.** Fork CI run 40158597103 for `hunter-feat-pr` failed in "Generate cache and gameval sources" twice, and the
  local `freshCache` failed the same way: archive.openrs2.org `disk.zip` returned HTTP 500; the suite never ran.
- **Root cause.** The cache host was down; the gate keeps no copy of the cache.
- **Fix.** None: rerun `hd gate-ci hunter-feat-pr` when the host answers (v7 input).
- **Recognise.** "Generate cache and gameval sources" failing with an HTTP 5xx while Formatting is green.

## 2026-10-25 The integrator reset the server tools branch

- **Symptom.** `local/server-tools` moved to an unintended commit during an integrator run.
- **Root cause.** The integrator's reset ran on the shared tools clone, whose head the train pins as the tools commit.
- **Fix.** The branch was restored by hand; nothing prevents it yet (v7 input).
- **Recognise.** A batch's `tools` commit that is not on `local/server-tools`.

## 2026-10-25 A client change was pushed with no change file

- **Symptom.** Branch `client/client-contributing-file` (af26042, "move Contributing section to CONTRIBUTING.md") is on
  the client origin, unmerged, and no change names it.
- **Root cause.** The branch was made outside the change store, so no track observes it.
- **Fix.** None yet: register the change or drop the branch (v7 input).
- **Recognise.** A `client/*` branch on origin that no `harness/changes/*.md` names.

## 2026-10-24 The contribution comment was the hand-over summary

- **Symptom.** The comments on two upstream PRs were the dev's hand-over summary.
- **Root cause.** `texts()` read `pr-comment.md` or `pr-texts/<slug>.update.md`; the prepared files were named
  `pr-texts/<slug>.comment`, so the fallback (the summary after "Ready for review at <sha>") was posted.
- **Fix.** `texts()` also reads `.comment`; with no file it posts "Updated to <sha>."; role files and skill name
  `pr-comment.md`. Test: `tests/test_hd_track_server_flow.py` (`ContributeTest`).
- **Recognise.** A PR comment that reads like a hand-over summary.

## 2026-10-24 Finished agents and qa-dev containers outlived their runs

- **Symptom.** An agent waiting on its own background work stayed live over an hour after its run ended; a
  `qa-dev-<name>` container ran for hours.
- **Root cause.** The harness tracked run records, not agent or container liveness: heal handled only `qa-or-*` and
  `hd-boot-*`, and `hd drive` listed only daemon-stopped runs under Stop.
- **Fix.** Heal stops a running `qa-dev-<name>` container whose run ended, has no record or whose change left its
  stage; every run that ends with a linked agent id is a Stop item until `hd run-stopped`.
- **Recognise.** A `qa-dev-*` container in `docker ps` with no running run record.

## 2026-10-25 Cutover defects found while handing contributions over

- **Symptom.** Records written by QA were not found (the dev had recorded `re/evidence/<branch-name>`); a train listed one
  change twice; an imaging or deploy failure after the integrator's fix rebuilt on the old clone; a `local/` branch
  without `local_only` got a QA run; a hand-contributed change needed its DoD contribution items ticked before
  hand-over; `hd gate-ci` never ran the Formatting workflow; `hd drive` kept stop requests of agents that had ended; QA
  desktop clients and client-dev shared one `client` class.
- **Root cause.** The evidence path followed the recorded value, the queue deduplicated by branch only, `resume`
  rebuilt only for a gating failure, fork-only was read from the flag alone, and the capacity class mixed Android and
  desktop clients.
- **Fix.** The evidence dir is the slug dir (the recorded dir is copied); queue and `includes` keep one entry per change;
  `resume` rebuilds on a moved tools branch for gating, imaging and deploying; `Change.fork_only` also reads the
  `local/` branch; contribution DoD items do not block hand-over; `gate-ci` dispatches and waits for the Formatting
  workflow and `hd gate` needs it green; class `device` (0) for client-dev; stop requests clear on run-end or a recorded
  hand-back.
- **Platform limit.** GitHub refuses a review request by the fork's author on the upstream PR (404), so the reviewer
  step and `tracks.server.reviewers` are removed; the CODEOWNERS request on ready stands.
- **Recognise.** `gate.md` in a dir other than `re/evidence/<slug>/`; a `queue`/`includes` slug twice; a batch at
  `exception` after imaging whose `tools` is not the tools branch head.

## 2026-10-25 A resolved gate failure was re-gated on the old tree

- **Symptom.** The integrator fixed a gate failure by changing `integration.txt` and the pins; after `hd resolve` the
  batch gated the old integration clone and the fix never reached the tree.
- **Root cause.** `batches.resume` restarted the gate for every gate failure.
- **Fix.** When the batch's tools commit differs from the tools branch head, resume re-runs the train from pinning.
- **Recognise.** A resumed batch whose `tools` commit is not the fork's tools branch head.

## 2026-10-24 The gate ran after the upstream push and reported one failure at a time

- **Symptom.** A PR was already public when QA found a head regression; the next round found style comments (goblin);
  the fix commit needed another push and another round. A gate run on a change that was not yet live was stopped as
  lingering; QA could not push its CI scratch branch (the role hook denied every push).
- **Root cause.** The lifecycle put the gate after the test-server deploy and the upstream publication, QA stopped at the
  first failing check, a dev's own check paper-stamped the hand-over (`checked`), and the upstream workflow lived in the
  core beside client and harness code.
- **Fix.** dev -> QA aggregate -> the user's approval card -> `hd contribute`; `hd handover` refuses an incomplete hand-over;
  QA records every check and finding for the exact commit before anything is pushed (`hd gate-ci` runs the scratch merge
  and fork CI; server-qa may push `gate/*`); the contribution is one resumable sequence bound to the commit sha; the
  server's upstream workflow is the server track module behind the track interface (`hd/tracks/`).
- **Recognise.** A PR head newer than the last QA record; a `gate` run stopped as lingering while its change waited for
  a train; two QA rounds on one commit with different findings.

## 2026-10-24 Instance leases made every agent wait for a shared client

- **Symptom.** Dispatch stalled while an agent held `device` or `desktop`; a pending deploy drained instances and
  agents waited on each other; many lease, grant and drain steps sat between a ready change and a run.
- **Root cause.** Client instances were modelled as shared resources, so a lock, a grant, a drain and a deadlock rule
  existed for something each agent can simply start for itself.
- **Fix.** Instance leases, grants, drain, the deadlock rule, `device-lock.sh` and `train/instances.tsv` are deleted;
  dispatch waits on slots only; each agent starts its own client and stops it when done. Locks remain only for
  `integration`, `live-server` and `ghidra`.
- **Recognise.** A ready change stalled with a free slot; a `lease` event with action grant or drain in old logs.

## 2026-10-24 The console's EnterWorktree broke the subagents' Bash

- **Symptom.** Agents spawned while the console session sat in a worktree could not run Bash commands.
- **Root cause.** EnterWorktree moves the whole session's working directory, subagents included.
- **Fix.** The console never enters a worktree while agents run (CLAUDE.md, skill `drive`); the Agent tool's
  `isolation: worktree` makes the agents' worktrees.
- **Recognise.** Bash errors in every agent right after the console called EnterWorktree.

## 2026-10-24 A fresh worktree was created from origin/main

- **Symptom.** A harness-dev worktree lacked the commits already on local main.
- **Root cause.** Worktrees are created from `origin/main`, not from the local `main`, which is never pushed.
- **Fix.** The harness-dev role file starts with a hard reset of the worktree to `main`.
- **Recognise.** The log of a fresh worktree is behind main; files the brief names are missing.

## 2026-10-24 New change files were invisible to worktrees

- **Symptom.** A harness-dev agent could not tick its definition of done: the change file was not in its worktree.
- **Root cause.** New files in `harness/changes/` are untracked in the main checkout, so a worktree has no copy.
- **Fix.** `hd dod <slug> <n>...` ticks items on the store (`HD_HARNESS_DIR=~/osrs-harness/harness` from a worktree).
- **Recognise.** `harness/changes/<slug>.md` missing in a worktree.

## 2026-10-24 Harness check failed once main already held the commit

- **Symptom.** The harness-track check failed a `harness/<slug>` change after the console had merged it by hand,
  before the daemon's check ran.
- **Root cause.** The check required main not to contain the commit.
- **Fix.** The change was handed over on `main`; a change handed over on main passes while main contains the commit
  (`hd/check.py`, `tests/test_hd_harness_track.py`).
- **Recognise.** A harness change failing the check with its commit already on main.

## 2026-10-24 Harness hand-over check read the client repo's master

- **Symptom.** `hd check handover-upstream-ci` (handed over with `--repo ~/osrs-harness --branch main`) failed with
  "no local branch main" and "could not read master"; each FAIL re-dispatched a dev.
- **Root cause.** The harness moved out of the client repo, but `check`, `stages.observed` and `ship` still read the
  client repo's `master` for the harness track (policy `tracks.harness.live_target: master`).
- **Fix.** `policy.live_target(track)`, `stages.repo_of(track)` (harness = `HD_HOME`, observer repo `harness`); policy
  target `main`; a change handed over on main itself needs only main to contain the commit; `ship` merges harness
  changes into main of this repo, no push. `hd dod` added so agents can tick the definition of done.
  Tests: `tests/test_hd_harness_track.py`.
- **Recognise.** A harness change failing on "no local branch" / "could not read master" with the commit on main.

## 2026-10-24 Upstream PR lookup by branch found nothing

- **Symptom.** With the CI fix in, `hd check stile-approach` still read "CI pending" although upstream #406 was green.
- **Root cause.** `Observer.upstream_pr(branch)` ran `gh pr list --head owner:branch`; gh's `--head` takes a bare branch
  name and returns nothing for `owner:branch`. The check also ignored the `upstream_pr` number recorded on the change.
- **Evidence.** `gh pr view 406 -R OpenRune/OpenRune-Server` showed all checks green at 68ddd1b6c while the lookup gave `{}`.
- **Fix.** The check uses the recorded number first; the branch lookup passes the bare branch and filters on
  `headRepositoryOwner.login` == the fork owner. Advisory checks (spotless) are neither required nor failing.
  Tests: `tests/test_hd_ci_check.py` (`LookupTest`, `RecordedNumberTest`, `RollupTest`).
- **Recognise.** A change with a recorded `upstream_pr` whose check says "CI pending" while the PR is green.

## 2026-10-24 Hand-over check failed on fork CI and re-dispatched devs every tick

- **Symptom.** `fix/stile-approach` and `genie-review-355` failed the hand-over check on "no CI run" / a red fork run;
  each FAIL returned the change to `ready`, so the daemon booked a new dev run each time (sd47..sd58).
- **Root cause.** The check read the fork's `gh workflow run ci.yml --ref <branch>` result. A dispatch runs the bare
  branch tip, which is behind upstream main (30 commits, among them f28349cd4 "241 Latest Support", which changed the
  cache/game-data pipeline), so its cs2 build fails with SYNTAX_ERROR whatever the change is. Upstream PR CI runs on the
  merge ref with main and passes. Missing CI was also a FAIL, so a branch with no PR yet looped as well.
- **Evidence.** Upstream #354 at 60cffedfb and #406 at 68ddd1b6c (stile-approach) are green; the fork runs at the same
  tips fail in the cs2 build; `hd` events show the check FAIL then `agent request` pairs for the two slugs.
- **Fix.** `hd/check.py` `_ci_item`: CI is the upstream PR's checks at the exact commit (`observe.upstream_ci`: build and
  gameval-conflicts green); a passing fork run is accepted; otherwise the item is pending ("CI pending: runs when the PR
  opens or the head moves"), which waits and never returns the change to ready. Tests: `tests/test_hd_ci_check.py`.
- **Recognise it.** A `check` event FAIL whose items name CI, followed by a new `agent request` for the same slug; a fork
  run failing in the cs2/cache build while the upstream PR is green.

## 2026-10-21 Cleanup changes could not merge: unrelated tests re-pinned

- **Symptom.** Two cleanup changes (deleting refs, cleaning containers) failed to merge.
- **Root cause.** Each commit also re-pinned tests that failed for reasons the change did not cause.
- **Fix.** A harness commit holds only its change; an unrelated failing test is named in the hand-over summary and
  left (role file `harness-dev`). A side-effect change hands over a note that records it.
- **Recognise.** A harness commit touching tests outside its change.

## 2026-10-21 A gated release build was lost with its worktree

- **Symptom.** The release gate passed, but its build no longer existed when the release needed the APKs.
- **Root cause.** The QA agent built in its own worktree, which is removed when the run ends.
- **Fix.** `client-qa` copies `base.apk`, `split.apk`, `THIRD_PARTY_NOTICES.md` and the repack log into
  `re/evidence/<batch-id>/` before it ends; the record lists those copies by sha256 (skill `client-track`).
- **Recognise.** A release batch at `gated` whose evidence dir holds no APKs.

## 2026-10-20 An agent drove another agent's client

- **Symptom.** A helper script drove the wrong desktop client.
- **Root cause.** Every agent of a session shares the scratchpad; two agents wrote the same file name at its top level.
- **Fix.** Scripts and temp files go under `<scratchpad>/<your-name>/` (the brief's rules).
- **Recognise.** A script at the scratchpad's top level that another agent also wrote.

## 2026-10-24 The release gate denied a release with a PASS record
- **Symptom.** A client release with `--target <sha>` was denied: no `qa/client-0.1.2.md`.
- **Root cause.** The gate read the target only as a positional sha and looked for the record only in the client repo's `qa/`; client-qa writes `client-record.md` in the evidence tree.
- **Fix.** The gate takes `--target` and accepts a PASS record at the released commit from either place.
- **Recognise.** A release denied "no release record" while `re/evidence/*/client-record.md` says PASS.

## 2026-10-24 A draft upstream PR was denied for lack of a QA record
- **Symptom.** Opening fork branch feat/hunter as an upstream draft was denied: no QA record at the commit.
- **Root cause.** The gate required the record for every upstream PR creation; the user decides to open drafts unverified.
- **Fix.** A `--draft` creation with an existing explicit `--head AlexPerrin:<branch>` skips the record check; non-draft creation, `hd contribute` and releases keep theirs.
- **Recognise.** A draft denied "QA record missing" while the command carries `--draft` and `--head`.
