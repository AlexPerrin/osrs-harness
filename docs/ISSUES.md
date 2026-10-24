# Root causes

One short entry per issue, newest first: symptom, root cause, evidence, fix, how to recognise it again.

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
