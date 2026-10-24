---
name: server-track
description: "Server track rules: fork branches, one-change-per-PR upstream rules, gameval ids, the dev's check and the upstream gate, the QA record format, the integrator's cases. Use as server-dev, server-qa or integrator, and before any upstream PR text."
---
# Server track

Test server: the fork AlexPerrin/OpenRune-Server (fork of OpenRune/OpenRune-Server). Our changes reach the live test
server first (`integration`), then upstream as PRs.

## Branches on the fork
- `main` mirrors upstream `main`; only a fast-forward sync moves it.
- `content/<slug>`, `fix/<slug>`: one self-contained feature or fix each, off `main`; these are what get PR'd.
- `local/*`: test-only pieces that never go upstream (Android protocol, LOCAL_AUTH, test commands, deploy files),
  small and separate by topic.
- `integration` (default branch): `main` + every `content/*`/`fix/*` handed over and not merged upstream + every
  `local/*`, in the recorded order (`integration.txt`, pins in `integration.lock`). Built by
  `scripts/build-integration.sh`, never hand-edited; the live server builds from a pinned commit.
- `docs`: STATE.md (what is live, gotchas; rewritten, never appended; about 150 lines), `accuracy/<slug>.md`,
  `qa/<slug>.md`, `pr-texts/<slug>.*`, QA.md. Our docs never go upstream.

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
- **Updates**: a new commit goes onto the existing PR branch (merge `main` in; never force-push), after the gate and
  with the user's yes; an update is a comment, the description is never replaced (BR-A8).
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

## The dev's check (server-dev; no QA before `integration`)
The dev owns accuracy and the build for the fork and live server:
1. Spec `accuracy/<slug>.md` on `docs` first (skill `accuracy-check`: upstream overlap, each mechanic's source,
   behaviour, caveats, guesses, tests, PR split and `Depends:`). Commit it, `hd log <slug> "spec committed"`, keep
   coding; the console may veto from the log. Stop only for a decision the dev cannot take (the PR split, an upstream
   overlap, a conflicting source): `hd fail <slug> "decision needed: ..."`. For a blocker the client's repro is part
   of the spec.
2. Build on `content/<slug>` or `fix/<slug>` off `upstream/main` with tests only as above.
3. Verify: skill `build-test` (dev builds in the warm container with `qa.sh dev <name> <clone>`), behaviour against
   the spec, `ab-test` on desktop RuneLite where it renders. Build evidence is the fork's GitHub Actions CI green at
   the commit, or `GATE_VOL=<name>-gate-gradle GATE_OWNER=<name> qa.sh gate <clone>` where CI does not apply.
4. PR text on `docs` (skill `pr-text-review`), fork PR opened, then `hd handover`.

A new commit voids the gate and needs the evidence again; the branch stays in `integration` at the last handed-over
commit meanwhile. A push to a branch that backs an open upstream PR changes that PR and asks the user.

## The upstream gate (server-qa; the track's only QA step)
Independent re-check at the exact commit, stopping at the first failure; the dev's runs are evidence, yours count.
- **Accuracy**: `accuracy-check` against the spec and sources re-read through `osrs-mcp` (not the spec's quotes),
  including the RSProx comparison.
- **In-game**: the branch's own server on spare ports, desktop RuneLite pointed at it under the desktop lock, driven
  with `osrs-devtools-desktop`; every player-facing claim of the PR text; a blocker's repro passes. Stop and remove
  your containers after; never touch `osrs-openrune`, `osrs-openrune-http`, `osrs-openrune-http-desktop`.
- **Build**: CI green at the exact commit (`qa.sh gate` on upstream `main` + the branch where CI does not apply),
  boot to "Server ready in".
- **Scope**: one change, nothing unrelated, none of our docs in the diff, no open upstream PR for the same content,
  on current `upstream/main`, `Depends:` stated, `fix_gameval_conflicts.py --check` clean.
- **Tests**: a test file the PR text does not justify is a FAIL item.
- **Text**: CONTRIBUTING, AGENTS.md, template sections present; `pr-text-review`; every claim true of the commit;
  caveats cover every gap the accuracy check found. `reverse` (`-readOnly`) when the branch claims client protocol.

On PASS the change waits for the user's yes per upstream item.

## The QA record
`qa/<slug>.md` on `docs`, beginning exactly (the publish hook parses it):
```
# QA: <branch>
- Branch: `<branch>`
- Commit: `<full sha>`
## Upstream gate: **PASS**     (or **FAIL**, or **PENDING**)
```
A FAIL says precisely what must change. A new commit voids the record: re-check, never edit a verdict. An
`## Internal gate: N/A (dev-checked)` line is optional; the hook reads only the upstream line.

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
Built from a pinned `integration` commit; the daemon deploys boot-checked images with a rollback tag when every
instance is free. Live ids are the ids on the branches.
