---
name: server-track
description: "Server track rules: fork branches, one-change-per-PR upstream rules, gameval ids, the dev's check, QA's aggregate and its record, the contribution, the integrator's cases. Use as server-dev, server-qa or integrator, and before any upstream PR text."
---
# Server track

Test server: the fork AlexPerrin/OpenRune-Server (fork of OpenRune/OpenRune-Server). Our changes reach the live test
server (`integration`) and, independently, upstream as PRs.

## Branches on the fork
- `main` mirrors upstream `main`; only a fast-forward sync moves it.
- `content/<slug>`, `fix/<slug>`: one self-contained feature or fix each, off `main`; these are what get PR'd.
- `local/*`: test-only pieces that never go upstream (Android protocol, LOCAL_AUTH, test commands, deploy files),
  small and separate by topic.
- `integration` (default branch): `main` + every `content/*`/`fix/*` handed over and not merged upstream + every
  `local/*`, in the recorded order (`integration.txt`, pins in `integration.lock`). Built by
  `scripts/build-integration.sh`, never hand-edited; the live server builds from a pinned commit.
- `docs`: STATE.md (what is live, gotchas; rewritten, never appended; about 150 lines), QA.md and older specs.
  Our docs never go upstream. Gate branches `gate/<slug>` are QA's scratch merges (fork CI only).

## Changes for upstream
- **One change per PR**: one quest, feature or fix. A fix found on the way is its own `fix/<slug>`. A large feature is
  split along its seams before coding, in the spec (shared base first). Named by slug, never by number;
  dependencies are written as `Depends:` in the spec and PR text.
- **Off current `main`, independent, never stacked.** Builds and tests alone and contains no commit of another open
  PR. Shared code is its own small change; a change that needs it waits until that has merged and rebases.
- **Check upstream first**: open PRs, issues and recent `main` for the same content
  (`gh pr list -R OpenRune/OpenRune-Server --search <topic>`); if upstream has it, build on theirs or drop ours.
  Content that overlaps another open PR goes up as a draft that references it.
- **A PR is ready only when every reported defect is fixed in it**; nothing is promised to a maintainer as a separate
  or later PR.
- **Updates**: a new commit goes onto the existing PR branch (merge `main` in; never force-push) as a change of its
  own that went through QA's aggregate and the user's approval of that commit; an update is a comment, the
  description is never replaced (BR-A8). A maintainer finding is filed once as a review-fix change on the same branch.
- **Upstream conventions** (AGENTS.md, CONTRIBUTING, `.github/pull_request_template.md` on upstream `main`): tests
  only for real logic that moves items or state (a rule with several cases, a regression a reviewer asked for), never
  for a handler, packet, shop, simple op or wiki string. **The default is no test in an upstream PR**; files used to
  check your own work stay out of the commit; each new test is justified in the PR text. No new KDoc or explanatory
  comments; nothing made public just for a test; server toggles go in the server config with a default. Commit
  subjects `feat:`/`fix:`. Every PR text uses the template's sections (Summary, Type of change, How it was tested,
  Checklist, notes) plus problem, data sources, caveats, release note, `Depends:`, and ends with the Claude Code
  line. The checklist asks for: in-game verification end to end without cheats where possible, state in
  varbits/varps not attrs, gamevals symbols not raw ids, wiki deviations in upstream's `docs/quirks.md` (part of the
  change), rsprox checks (tick only when the accuracy check's RSProx comparison found a recording and was done).

## Gameval ids
- Write each new gameval as `name = -1`, run `python3 tools/scripts/fix_gameval_conflicts.py` on the branch (needs
  `.data/gamevals-binary/max-ids.toml` from `freshCache`), commit what it assigns. Names carry the feature
  (`sheep_shearer_*`); saves are keyed by name and code uses names. Renaming a gameval or moving a varbit's bits needs
  a data migration; renumbering does not.
- After `build-integration.sh`, run it with `--check` on the integration tree; on a clash between two of our
  branches, apply the reported id to the one that is later in `integration.txt`. Upstream's CI cannot push to a fork
  PR: apply its reported reassignment on the branch.

## Lifecycle of a server change
dev (local commit, hand-over) -> QA aggregate -> the user's approval card -> `hd contribute` -> review -> merged. The
test server runs the change through the integration train as soon as the fork has its commit; that and the upstream
flow are independent. The only gate is the user's approval of the upstream action.

## The dev's check (server-dev; nothing runs before the hand-over but the dev's own checks)
The dev owns accuracy and the build:
1. Spec `accuracy.md` in the evidence dir first (skill `accuracy-check`: upstream overlap, each mechanic's source,
   behaviour, caveats, guesses, tests, PR split and `Depends:`). Stop only for a decision the dev cannot take (the PR
   split, an upstream overlap, a conflicting source): `hd fail <slug> "decision needed: ..."`. For a blocker the
   client's repro is part of the spec.
2. Build on `content/<slug>` or `fix/<slug>` off `upstream/main`, in the dev's clone; commit locally. Tests only as
   above. Push the branch to the fork when the test server should run it.
3. Verify: skill `build-test` (`qa.sh dev <name> <clone>` in the warm container: the touched modules' tests and
   `spotlessCheck` on them, not the full suite), behaviour against the spec,
   `ab-test` on desktop RuneLite where it renders.
4. Self-check the diff against upstream AGENTS.md and CONTRIBUTING (no added comments, no tests unless justified) and
   write the PR text (`pr-title.txt`, `pr-body.md`, skill `pr-text-review`) in the evidence dir.
5. `hd handover ... --repo <clone>`: the check runs at once and refuses an incomplete hand-over.

A new commit voids QA's record and the approval; the branch stays in `integration` at the last pushed commit meanwhile.

## QA's aggregate (server-qa; reports, never blocks)
Independent check of the exact commit; the dev's runs are evidence, QA's count. Every check gets a PASS, FAIL or N/A line
and every finding is listed at once; the result goes on the user's approval card.
- **accuracy**: `accuracy-check` against the spec and sources re-read through `osrs-mcp`, including the RSProx comparison.
- **tests**: the `Tests` line: the modules whose tests QA ran (the touched ones plus `spotlessCheck` on them) and the
  fork CI run id covering the full suite; never a local full `qa.sh gate` unless the fork CI cannot run.
- **ci**: `hd gate-ci <slug>`: the commit merged with current upstream `main` in a scratch clone (read from the dev's
  clone, no push needed), pushed to the fork's `gate/<slug>`, CI dispatched there and observed.
- **format**: spotless on the scratch merge.
- **scope**: one change, nothing unrelated, none of our docs in the diff, no open upstream PR for the same content, on
  current `upstream/main`, `Depends:` stated, `fix_gameval_conflicts.py --check` clean.
- **style**: upstream AGENTS.md and CONTRIBUTING: no added comments, no test file the PR text does not justify
  (`hd gate-ci` scans the diff for both), nothing public for a test, commit subjects `feat:`/`fix:`.
- **text**: template sections, every claim true of the commit, caveats cover every gap (`pr-text-review`); `reverse`
  (`-readOnly`) when the branch claims client protocol.
- **ingame**: the branch's own server on spare ports, your own desktop RuneLite driven with `osrs-devtools-desktop`;
  every player-facing claim of the PR text; a blocker's repro passes. Stop and remove your containers after; never touch
  `osrs-openrune`, `osrs-openrune-http`, `osrs-openrune-http-desktop`.

## The QA record
`re/evidence/<slug>/gate.md`, beginning exactly (`hd gate` and the hooks parse it):
```
# Gate: <branch>
- Branch: `<branch>`
- Commit: `<full sha>`
- Tests: <modules whose tests ran>; CI run <id covering the full suite>
## Gate: **PASS**     (or **FAIL**; PASS only with no failed check and no finding)
## Checks
- accuracy|ci|format|scope|style|text|ingame: PASS|FAIL|N/A <reason or evidence link>   (one line each)
## Findings
- <each finding>     (or `- none`)
```
`hd gate <slug> PASS|FAIL "note"` checks it against the commit and, for PASS, the green CI result in `gate-ci.json`. A
new commit voids the record: re-check, never edit a verdict. A finding holds nothing; if the user wants it fixed the
console puts a `failed` hold on the change and a dev run is booked with the findings (no run for a head and finding set
already booked: BR-S9).

## The contribution
After the user's yes on the approval card, bound to the commit sha, the console runs `hd contribute <slug> --approved
<sha>`: push to the PR branch (fast-forward or the dev's merge commit; never force), open the PR as a draft when none
exists, wait for green upstream CI at that commit, comment, move out of draft, request review. It resumes at the first
unobserved step and stops before the comment when CI is not green.

## Integrator (a train at `exception`)
Work in the build worktree `~/src/openrune-work/integration/build` and in `~/src/openrune-work/integration-tools`
(branch `local/integration-tools`).
- **Unrecorded merge conflict**: resolve in the stopped worktree as the two branches intend (their specs and PR
  texts say what each does), `git add`, `git commit`, copy the new `.git/rr-cache` entries into
  `scripts/integration-rr-cache/` on `local/integration-tools`, commit there and push that branch to the fork. That is
  the recorded resolution the next train replays.
- **Superseded branch** (same fix twice, one upstream): drop it from `integration.txt` and `integration.lock`, commit,
  push, and name the change that loses its pin (its PR is the user's decision).
- **Gameval clash**: run `fix_gameval_conflicts.py` in the build worktree; if the fix belongs on a branch with an
  open upstream PR, stop and say so.
- **Gate failure**: read `<clone>.logs/summary` and the failing step's log; if one branch's tests fail, report which
  change and why (the daemon holds it `failed`); fix nothing on content branches.
- **Boot failure**: read the boot log, report the cause.
- A decision (which of two branches wins, a push to a PR branch, a fix on a content branch):
  `hd resolve <batch> --decision "<finding and options>"`; the train waits for the user.

## Live server
Built from a pinned `integration` commit; the daemon deploys boot-checked images with a rollback tag once the daemon holds the live-server lock. Live ids are the ids on the branches.
