# Root causes

One short entry per issue, newest first: symptom, root cause, evidence, fix, how to recognise it again.

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
