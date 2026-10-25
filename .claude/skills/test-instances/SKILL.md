---
name: test-instances
description: "Rules for the test instances and data tools: starting your own client, the MCP servers (osrs-mcp, osrs-devtools, osrs-devtools-desktop), capacity. Use before any device or desktop client work, and before looking up game data."
---
# Your own client and data tools

## Your own client
- No instance is shared or locked: start your own client when you need one and stop it when you are done (before
  you hand over, gate or end). It has its own profile, devtools port and account state, named after you
  (desktop RuneLite: your own window, never a shared one: `export DESKTOP_INSTANCE=$(~/osrs-harness/bench/multiclient/desktop.sh free)` takes the first instance nobody uses, no lock; on a new instance run `~/osrs-harness/bench/multiclient/desktop-build.sh` once to stage it; your own login account; `DESKTOP_DEVTOOLS_PORT=<free port>`,
  `~/osrs-harness/bench/multiclient/desktop.sh start|stop`; Android: your own emulator. BlueStacks has one instance (Pie64, the user's) and no command-line way to add one,
  so start the Android Studio AVD read-only on a free even port: `env -u HOME emulator -avd Medium_Phone_API_37.0 -read-only -gpu swiftshader_indirect -port <5560..5598>` (from WSL: without `env -u HOME` it finds no AVD, without the GPU flag the game screen is black),
  `ANDROID_SERIAL=emulator-<port>`; read-only lets several agents run the same AVD at once). Never use another agent's client, profile or port,
  never touch an instance already open (the user's own BlueStacks), and never leave yours running.
- Set the devtools up when you start the client (`device-test` step 3) and remove the test jars and the
  `debug.osrsrl.devtools` property when you stop it.
- Remove test jars BY NAME in a plain `adb -s <your serial> shell rm <dir>/hub-x.jar ...` call of their own: no
  loops, no `bash -c`, no wildcards. Back up with `adb exec-out cat`.
- Sign-in is LOCAL_AUTH only: look first, tap only "Sign in with Email / Username".
- The tester account is never `::empty`d; keep its GE offer, drop only items you spawned.
- A server dev never touches the Android device. A live-server restart disconnects every client; log back in.

## MCP servers
Agents inherit the session's MCP tools; load them with ToolSearch (e.g.
`select:mcp__osrs-mcp__wiki_page,mcp__osrs-mcp__gameval_search`). Game state comes from the data tools, never
screenshots unless the user asks.

| Server | Gives | Rules | Used by |
|---|---|---|---|
| `osrs-mcp` | `wiki_search`, `wiki_page`, `wiki_npc_spawns`, `gameval_search`, `cache_search`, `*_reload` (read-only; no server keys, no live-server control; `mcp/osrs-mcp.sh`) | Gamevals and cache are the tree it was built from (`openrune/src`), not upstream `main`; ids are assigned by upstream's tool (skill `server-track`), not looked up here | all roles: accuracy baseline, ids |
| `osrs-devtools` | OpenRune-Developer-Tools in the Android plugin host: client state, chat, NPC/object/item actions, vars, dialogue, walking (`~/osrs-plugins-reverse/tools/devtools-mcp.sh`) | Needs `devtools.jar` in plugins/ and `setprop debug.osrsrl.devtools 1` plus a restart; remove both when you stop the client. `get_chat_history` under-reports repeats: confirm with a screenshot | client roles |
| `osrs-devtools-desktop` | The same tools in the isolated desktop RuneLite (`~/osrs-harness/bench/multiclient/desktop-devtools-mcp.sh`) | Start your own client first (`~/osrs-harness/bench/multiclient/desktop.sh start`) | all roles |

## Capacity
BlueStacks instances (about 2-3 GB each) and desktop clients (about 1 GB each): start only what you use. Builds go through `tools/buildq.sh`
(classes gate 2 slots, dev 2, measure 1; a ticket starts only while memory covers it); QA gates run in one 5 GB
container via `qa.sh gate`, dev builds in the dev's warm container `qa-dev-<owner>` via `qa.sh dev`. Fork CI runs
upstream-bound gates on GitHub's runners, so they use no local slot. Each container has its own Gradle home and shares
compiled outputs through the build-cache node (`tools/gradle-cache.sh`); tests are never cached.
