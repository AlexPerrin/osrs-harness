# Root causes

One short entry per issue, newest first: symptom, root cause, evidence, fix, how to recognise it again.

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
