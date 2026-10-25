---
name: server-track
description: "Server track rules: fork branches, one-change-per-PR upstream rules, gameval ids, the dev's check, the reviewer's checks, the integrator's cases. Use as server-dev, server-qa or integrator, and before any upstream PR text."
---
# Server track

Test server: the fork AlexPerrin/OpenRune-Server (fork of OpenRune/OpenRune-Server). A change reaches the live test
server (`integration`) as soon as its gate passes and, independently, upstream as a PR after the user's yes.

## Branches on the fork
- `main` mirrors upstream `main`.
- `dev/<slug>`: the dev's ref, the only one a dev pushes; the change's head is its tip.
- `content/<slug>`, `fix/<slug>`: the public PR branches; moved only by the pass after the user's approval.
- `local/*`: test-only pieces that never go upstream (Android protocol, LOCAL_AUTH, test commands, deploy files).
- `integration` (default branch): `main` + every pinned branch in `integration.txt` at its pin in `integration.lock`,
  both on `local/integration-tools`, built by `scripts/build-integration.sh`; never hand-edited.
- `docs`: STATE.md (what is live, gotchas; rewritten, never appended), QA.md and older specs. `gate/<slug>`: the
  gate's scratch merges (fork CI only).

## Changes for upstream
- **One change per PR**: one quest, feature or fix. A fix found on the way is its own change. A large feature is split
  along its seams before coding, in the spec (shared base first); dependencies are `Depends:` in spec and PR text.
- **Off current `main`, independent, never stacked.** Contains no commit of another open PR; shared code is its own
  change that merges first.
- **Check upstream first** (`gh pr list -R OpenRune/OpenRune-Server --search <topic>`); if upstream has it, build on
  theirs or drop ours.
- **A PR is ready only when every reported defect is fixed in it**; nothing is promised for a later PR.
- **Updates**: a new commit on the PR branch (merge `main` in; never force-push), as a change of its own through gate,
  review and the user's approval; an update is a comment, the description is never replaced. A maintainer finding is
  filed by the pass as a P0 change on the same branch and PR.
- **Upstream conventions** (AGENTS.md, CONTRIBUTING, `.github/pull_request_template.md` on upstream `main`; re-read
  them each time): the default is no test in an upstream PR (only a rule with several cases or a reviewer's request,
  justified in the PR text); no new KDoc or explanatory comments; nothing public for a test; server toggles in the
  config with a default; commit subjects `feat:`/`fix:`. The PR text uses the template's sections plus problem, data
  sources, caveats, release note, `Depends:`; the checklist items as checkboxes verbatim, notes as plain text; in-game
  verification without cheats where possible, state in varbits/varps, gameval symbols not raw ids, wiki deviations in
  upstream's `docs/quirks.md`. The accuracy check (skill `accuracy-check`) is the wiki check: when it passes, tick
  "Matches the OSRS wiki" and add every deviation it records to `docs/quirks.md` in the same PR; a PR is never
  marked for review with that item unticked or a Not done list. Upstream texts (title, description, comments) never
  link a fork PR (`github.com/AlexPerrin/OpenRune-Server/pull/N`, `AlexPerrin/OpenRune-Server#N`, "fork PR #N"): it
  renders as a big red Closed. Naming the fork itself is fine. The pass will not post a text with such a link. Never open a PR, issue or
  comment on the fork: a fork PR that names an upstream PR puts a Closed "mentioned this pull request" entry on that
  PR's timeline for good. Branches and CI runs on the fork are fine.

## Gameval ids
Write each new gameval as `name = -1`, run `python3 tools/scripts/fix_gameval_conflicts.py` on the branch (needs
`.data/gamevals-binary/max-ids.toml` from `freshCache`), commit what it assigns. Names carry the feature; saves are
keyed by name. On a clash in the integration tree, the id goes to the branch later in `integration.txt`.

## The dev's check (server-dev)
1. Spec `accuracy.md` in the evidence dir first (skill `accuracy-check`). A decision you cannot take (the PR split, an
   upstream overlap, a conflicting source): `hd ask <slug> "..."`. For a blocker the client's repro is part of the spec.
2. Build off `origin/main` (upstream) in your clone; commit; tests only as above.
3. Verify: skill `build-test` (the touched modules' tests and `spotlessCheck`), behaviour against the spec, `ab-test`
   on desktop RuneLite where it renders.
4. Self-check the diff against upstream AGENTS.md and CONTRIBUTING; write `pr-title.txt`, `pr-body.md`,
   `pr-comment.md` (skill `pr-text-review`) in the evidence dir.
5. Push `dev/<slug>`, then `hd handover <slug> <sha>`.

## The gate (script, no agent)
Spec and PR texts present; the scratch merge head + upstream `main` pushed to `gate/<slug>`; fork CI and Formatting
green there (the full suite); the diff scanned for added tests and comments (listed for the reviewer).

## The reviewer's checks (server-qa)
accuracy (spec and sources re-read through `osrs-mcp`, RSProx comparison) · scope (one change, nothing unrelated, no
open upstream PR for the same content, `Depends:` stated, `fix_gameval_conflicts.py --check` clean) · style (no added
comments, no unjustified test, nothing public for a test, `feat:`/`fix:`) · text (template sections, every claim true
of the commit, caveats cover every gap; `pr-text-review`) · in game (the branch's own server on spare ports, your own
desktop RuneLite with `osrs-devtools-desktop`; every player-facing claim; a blocker's repro passes). Then
`hd verdict <slug> <sha> PASS|FAIL [findings]`, every finding at once.

## Integrator (the train failed)
Work in `~/src/openrune-work/integration/tree` and `~/src/openrune-work/integration-tools` (`local/integration-tools`).
- **Unrecorded merge conflict**: resolve in the stopped build as both branches intend (their specs and PR texts),
  `git add`, `git commit`, copy the new `.git/rr-cache` entries into `scripts/integration-rr-cache/` on the tools
  branch, commit and push it. The next train replays it.
- **Superseded branch** (same fix twice, one upstream): drop it from `integration.txt` and `integration.lock`, commit,
  push; `hd ask` on its change.
- **Gameval clash**: `fix_gameval_conflicts.py` in the build; a fix that belongs on a branch with an open upstream PR
  is the dev's: `hd ask` on that change.
- **Gate or boot failure**: read `<clone>.logs/summary`, the failing step's log or the boot log; drop the branch at fault
  and `hd ask` on its change with the cause; fix nothing on content branches.
