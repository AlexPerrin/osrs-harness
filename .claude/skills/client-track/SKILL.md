---
name: client-track
description: "Client track rules: the dev's check, the release gate, artifacts, networking and privacy limits. Use as client-dev or client-qa."
---
# Client track

RuneLite plugins in the official OSRS Android app (`native/`, `host/`, APK repack) in the client repo, tested against
the OpenRune test server. State: `docs/client-state.md` in the client repo (what is live, gotchas; rewritten, never
appended). Reference: `docs/app-telemetry.md` (read in full before any build that touches networking),
`docs/plugin-host.md`, `docs/offsets.md` (ELF addresses; Ghidra = ELF + 0x100000). Evidence dir:
`~/osrs-harness/evidence/<slug>/`.

## The dev's check (client-dev)
1. Analyse with `reverse` (Ghidra on `re/ghidra`, `-readOnly` unless the task updates the project; Ghidra's own project
   lock serialises writers) and, when the feature depends on what the server sends, `server-probe`. Ids and game data
   from `osrs-mcp`.
2. Build on `client/<slug>`. Host build: `host/build.sh`, `ninja -C re/build`, `tools/repack.sh`; every APK goes through
   the telemetry patch (7 `telemetry:` lines).
3. Verify the changed plugin or host path on the device (`device-test`, BlueStacks against the test server). Evidence
   is a logcat extract or a data-tool dump. Only when relevant: `network-qa` when the change adds or alters outbound
   traffic (then `network: true` in the definition and `netqa*.md` in the evidence); `ab-test` when it claims parity
   with desktop drawing.
4. Blocked by the server: never work around it; file the blocker as a server change with the repro and the expected
   behaviour, as a dep of yours.
5. Hand over: the repack log and the device evidence in the evidence dir, `docs/client-state.md` rewritten, the branch
   pushed to `origin/client/<slug>`, `hd handover <slug> <sha>`. The gate checks the evidence and the pass merges.

## The release gate (client-qa)
Full client QA on the client's live tip (`origin/main`) at the exact commit; every finding at once. A release is
`vX.Y.Z` (semver; `-dev` suffix = pre-release) with the single universal APK attached.
- A device regression: core and pinned hub plugins, scripted through the devtools bridge where possible; `ab-test`
  where plugins draw.
- `network-qa` (every release); sign-in (LOCAL_AUTH); the privacy patches present in the build's `repack.sh` log.
- `reverse` for native claims (offsets, patched bytes, the telemetry rewrites' match counts and xrefs).
- `pr-text-review` on the release notes; the APK carries no secrets or personal data.
- **Artifacts**: your worktree is removed when you end. Copy the release build into the evidence dir first:
  `osrs-runelite.apk`, `THIRD_PARTY_NOTICES.md`, the repack log; the pass attaches them to the release.
- **On the single APK**: one `adb install` on a device without the original game (an installed official copy gives
  `INSTALL_FAILED_UPDATE_INCOMPATIBLE`: uninstall first); hooks load, the host starts, sign-in against the test server;
  `THIRD_PARTY_NOTICES.md` embedded as an asset and equal to the committed file; `apksigner verify` and `zipalign -c`;
  arm64-v8a only.
- **Emulator quirks**: Chrome needs `pm grant com.android.chrome android.permission.ACCESS_LOCAL_NETWORK` for
  10.0.2.2; close the first-run OneTrust dialog with its X; a shell-pushed `files/plugins` dir needs `chmod 777`;
  after a force-stop the server holds the session for a while.
- Then `hd verdict <slug> <sha> PASS|FAIL [findings]`. A new commit voids the verdict.

## Limits
Never connect anything to Jagex or RuneScape servers, ping their worlds or enable netwrite; a new outbound host: stop
and report at once. NET-RAW hub jars are dropped unless the user approves them. Never read or modify
`C:\Users\Alex\.runelite`. The server is not the client dev's: do not restart or edit it.
