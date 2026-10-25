---
name: client-track
description: "Client track rules: the dev's check, the release gate and its record, artifacts, networking and privacy limits. Use as client-dev or client-qa."
---
# Client track

RuneLite plugins in the official OSRS Android app (`native/`, `host/`, APK repack) in the client repo, tested against
the OpenRune test server. State: `docs/client-state.md` in the client repo (what is live, gotchas; rewritten, never
appended; about 150 lines). Reference: `docs/app-telemetry.md` (read in full before any build that touches
networking), `docs/plugin-host.md`, `docs/offsets.md` (ELF addresses; Ghidra = ELF + 0x100000).

## The dev's check (client-dev; no QA before `master`)
1. Analyse with `reverse` (Ghidra on `re/ghidra`, `-readOnly` unless the task updates the project) and, when the
   feature depends on what the server sends, `server-probe`. Ids and game data come from `osrs-mcp`.
2. Build on `client/<topic>` (small fixes may go to `master`). Host build: `host/build.sh`, `ninja -C re/build`,
   `tools/repack.sh`; every APK goes through the telemetry patch (7 `telemetry:` lines).
3. Verify the changed plugin or host path on the device (`device-test`, BlueStacks against the test server). Evidence
   is a logcat extract or a data-tool dump. Automatic, never re-verified by hand: `repack.sh`'s telemetry assertions,
   the hub netcheck and R1 NetScan at load, the release hook. Only when relevant: `network-qa` when the change adds or
   alters outbound traffic (new host, new fetch); `ab-test` when it claims parity with desktop drawing.
4. Blocked by the server: never work around it; file the blocker as a server change with the repro, the expected
   behaviour and its source, and `hd block`.
5. Hand over: copy the repack log (7 `telemetry:` lines) and the logcat extracts into `re/evidence/<slug>/` (main
   checkout), tick the DoD, `hd handover`. Dev builds (`tools/release-dev.sh`) stay automated.
6. Rewrite the affected lines of `docs/client-state.md` and commit (pathspec-only).

## The release gate (client-qa; the track's only QA step)
Full client QA on `master` at the exact commit, stopping at the first failure; the dev's runs are evidence, yours
count. A release is `vX.Y.Z` (semver; `-dev` suffix = GitHub pre-release), with the single universal APK `re/out/osrs-runelite.apk` attached.
- A device regression: core and pinned hub plugins, scripted through the devtools bridge where possible, the
  plugin-host table updated; `ab-test` where plugins draw.
- `network-qa` (every release); sign-in (LOCAL_AUTH); the privacy patches present in the build's `repack.sh` log.
- `reverse` for native claims (offsets, patched bytes, the telemetry rewrites' match counts and xrefs).
- `pr-text-review` on the release notes; the attached APK carries no secrets or personal data.
- **Artifacts**: your worktree is removed when you end. Copy the release build into `re/evidence/<batch-id>/` in the
  main checkout first: `re/out/osrs-runelite.apk`, `THIRD_PARTY_NOTICES.md`, the repack log; the record's files table
  lists those copies (sha256), since the release attaches them.
- **On the single APK**: one `adb install` on a device or emulator without the original game (an installed official
  copy gives `INSTALL_FAILED_UPDATE_INCOMPATIBLE`: uninstall first); hooks load, the host starts, sign-in against the
  test server; `THIRD_PARTY_NOTICES.md` is embedded as an asset (`unzip -l`) and equals the committed file;
  `apksigner verify` and `zipalign -c`; the privacy and network checks; arm64-v8a only.
- **Emulator quirks**: Chrome needs `pm grant com.android.chrome android.permission.ACCESS_LOCAL_NETWORK` for
  10.0.2.2; close the first-run OneTrust dialog with its X; a shell-pushed `files/plugins` dir needs `chmod 777`;
  after a force-stop the server holds the session for a while.
- **Record** `qa/client-<version>.md` (the publish hook reads it before a tag), beginning exactly:

```
# QA: <branch or version>
- Branch: `<branch>`
- Commit: `<full sha>`
## Verdict: **PASS**   (or **FAIL**)
```

A FAIL says precisely what must change. A new commit voids the record: re-check, never edit the verdict. Commit only
your records (pathspec-only), then `hd gate <slug> PASS|FAIL "note"`.

## Limits
Never connect anything to Jagex or RuneScape servers, ping their worlds or enable netwrite; a new outbound host:
stop and report at once. NET-RAW hub jars are dropped unless the user approves them. Never read or modify
`C:\Users\Alex\.runelite`. The server is not the client dev's: do not restart or edit it.
