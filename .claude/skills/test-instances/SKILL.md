---
name: test-instances
description: "Rules for the test instances and data tools: starting your own client, the MCP servers (osrs-mcp, osrs-devtools-mobile, osrs-devtools-desktop), capacity. Use before any device or desktop client work, and before looking up game data."
---
# Your own client and data tools

## Your own client
- No instance is shared or locked: start your own client when you need one and stop it when you are done (before
  you hand over, gate or end). It has its own profile, devtools port and account state, named after you
  (desktop RuneLite: your own window, never a shared one: `export DESKTOP_INSTANCE=$(~/osrs-harness/bench/multiclient/desktop.sh free) DESKTOP_OWNER=<your run name>` takes the first instance nobody uses, no lock, and titles the window "OpenRune Test - <your run name>" so the user sees whose it is; if `desktop.sh start` then exits 1 (another agent started that instance first), run `free` again and start that one; the session's osrs-devtools-desktop MCP is fixed to instance `desktop` (port 7780): drive your own window through `DESKTOP_DEVTOOLS_PORT=<your port> bench/multiclient/desktop-devtools-mcp.sh --tool ...` instead; on a new instance run `~/osrs-harness/bench/multiclient/desktop-build.sh` once to stage it; your own login account; `DESKTOP_DEVTOOLS_PORT=<free port>`,
  `~/osrs-harness/bench/multiclient/desktop.sh start|stop`; Android: your own Android Studio emulator, started
  read-only on a free even port: `env -u HOME emulator -avd Agent_Phone -read-only -gpu swiftshader_indirect -port <5560..5598>` (from WSL: without `env -u HOME` it finds no AVD, without the GPU flag the game screen is black),
  `ANDROID_SERIAL=emulator-<port>`; read-only lets several agents run the same AVD at once). **Use `Agent_Phone` only, for every emulation (dev checks, QA, the release gate)**: it is the supported release-gate device, the Medium Phone profile on an x86_64 API 37 image with arm64 translation (the native library is arm64-v8a only: a 64-bit ARM phone or an emulator with ARM translation; no real phone is tested), made for agents with no OSRS app; `Medium_Phone` is the user's and carries the official, unpatched app (com.jagex.oldscape.android), never boot it. As a second guard, before any install, `adb uninstall com.jagex.oldscape.android`; install the repack and stop on any install error; before every launch, check the installed APK is the repack (`adb shell "unzip -l $(adb shell pm path com.jagex.oldscape.android | sed 's/package://') | grep -c libosrsrl"` is 1; it needs no root). Never launch the package otherwise: the official app contacts Jagex and Google. Never use another agent's client, profile or port (check the window title, "OpenRune Test - <run>", before driving one), keep every helper script and log under a scratchpad folder named after your run (the scratchpad's top level is shared by all agents: another agent's `dt.sh` there drove the wrong window),
  never touch an instance already open, and never leave yours running: start a client (desktop window or emulator) only right before you drive it, log in straight away, and stop it as soon as that check is done, not at the end of your run; a window idle at the login screen is a defect the user sees.
- Set the devtools up when you start the client (`device-test` step 3) and remove the test jars and the
  `debug.osrsrl.devtools` property when you stop it.
- Remove test jars BY NAME in a plain `adb -s <your serial> shell rm <dir>/hub-x.jar ...` call of their own: no
  loops, no `bash -c`, no wildcards. Back up with `adb exec-out cat`.
- Sign-in is LOCAL_AUTH only: look first, tap only "Sign in with Email / Username".
- The tester account is never `::empty`d; keep its GE offer, drop only items you spawned.
- A server dev never touches the Android device. A live-server restart disconnects every client; log back in.

## MCP servers
Agents inherit the session's MCP tools; load them with ToolSearch (e.g.
`select:mcp__osrs-mcp__wiki_page,mcp__osrs-mcp__gameval_search`). Game and screen state come from the data tools and
text reads first (logcat, `dumpsys`, `uiautomator dump`; each need and its tool: skill `device-test` step 5, the same
tools on desktop); a screenshot costs far more context and is the fallback only when none answers (how something is
drawn).

| Server | Gives | Rules | Used by |
|---|---|---|---|
| `osrs-mcp` | `wiki_search`, `wiki_page`, `wiki_npc_spawns`, `gameval_search`, `cache_search`, `*_reload` (read-only; no server keys, no live-server control; `mcp/osrs-mcp.sh`) | Gamevals and cache are the tree it was built from (`openrune/src`), not upstream `main`; ids are assigned by upstream's tool (skill `server-track`), not looked up here | all roles: accuracy baseline, ids |
| `osrs-devtools-mobile` | OpenRune-Developer-Tools in the Android plugin host: client state, chat, NPC/object/item actions, vars, dialogue, walking (`~/osrs-plugins-reverse/tools/devtools-mcp.sh`) | Needs `devtools.jar` in plugins/ and `setprop debug.osrsrl.devtools 1` plus a restart; remove both when you stop the client. `get_chat_history` under-reports repeats | client roles |
| `osrs-devtools-desktop` | The same tools in the isolated desktop RuneLite (`~/osrs-harness/bench/multiclient/desktop-devtools-mcp.sh`) | Start your own client first (`~/osrs-harness/bench/multiclient/desktop.sh start`) | all roles |

## Capacity
Emulators (about 2-3 GB each) and desktop clients (about 1 GB each): start only what you use. Builds go through `tools/buildq.sh`
(classes gate 2 slots, dev 2, measure 1; a ticket starts only while memory covers it); QA gates run in one 5 GB
container via `qa.sh gate`, dev builds in the dev's warm container `qa-dev-<owner>` via `qa.sh dev`. Fork CI runs
upstream-bound gates on GitHub's runners, so they use no local slot. Each container has its own Gradle home and shares
compiled outputs through the build-cache node (`tools/gradle-cache.sh`); tests are never cached.
