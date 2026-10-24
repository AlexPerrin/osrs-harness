---
name: test-instances
description: "Rules for the test instances and data tools: taking an instance (device, desktop), the restore check, the MCP servers (osrs-mcp, osrs-devtools, osrs-devtools-desktop), capacity. Use before any device or desktop client work, and before looking up game data."
---
# Test instances and data tools

## Instances
- Your change's `instances` are granted to you; take one only when you start using it and free it right after
  (`hd lease take|release <instance> <your-name>`; desktop RuneLite: `LOCK_NAME=desktop`,
  `tools/multiclient/desktop.sh`, profile under `C:\osrs-test` only). One you were not granted: `hd log <slug> "..."`
  what you need and go on with the rest.
- Device slots: `tools/device-restore-check.sh pre /tmp/osrs-slot/<your-name>` first; at the end of the slot (once,
  not per change) `check` on that dir until all OK, then free. Set the devtools up at the start of every slot
  (`device-test` step 3).
- Remove test jars BY NAME in a plain `adb -s 127.0.0.1:5555 shell rm <dir>/hub-x.jar ...` call of their own: no
  loops, no `bash -c`, no wildcards. Back up with `adb exec-out cat`.
- Sign-in is LOCAL_AUTH only: look first, tap only "Sign in with Email / Username".
- The tester account is never `::empty`d; keep its GE offer, drop only items you spawned.
- A server dev never touches the Android device. Server restarts reserve every instance.

## MCP servers
Agents inherit the session's MCP tools; load them with ToolSearch (e.g.
`select:mcp__osrs-mcp__wiki_page,mcp__osrs-mcp__gameval_search`). Game state comes from the data tools, never
screenshots unless the user asks.

| Server | Gives | Rules | Used by |
|---|---|---|---|
| `osrs-mcp` | `wiki_search`, `wiki_page`, `wiki_npc_spawns`, `gameval_search`, `cache_search`, `*_reload` (read-only; no server keys, no live-server control; `tools/osrs-mcp/run.sh`) | No lock. Gamevals and cache are the tree it was built from (`openrune/src`), not upstream `main`; ids are assigned by upstream's tool (skill `server-track`), not looked up here | all roles: accuracy baseline, ids |
| `osrs-devtools` | OpenRune-Developer-Tools in the Android plugin host: client state, chat, NPC/object/item actions, vars, dialogue, walking (`tools/devtools-mcp.sh`) | Only while holding the device lock. Needs `devtools.jar` in plugins/ and `setprop debug.osrsrl.devtools 1` plus a restart; remove both at the end of the slot. `get_chat_history` under-reports repeats: confirm with a screenshot | client roles |
| `osrs-devtools-desktop` | The same tools in the isolated desktop RuneLite (`tools/multiclient/desktop-devtools-mcp.sh`) | Only while holding the desktop lock; start the client first (`tools/multiclient/desktop.sh start`) | all roles |

## Capacity
Several BlueStacks instances (about 2-3 GB each) and desktop clients (about 1 GB each); each dev/QA pair has its own
instance and desktop client (own profile and port, `LOCK_NAME=<instance>`). Builds go through `tools/buildq.sh`
(classes gate 2 slots, dev 2, measure 1; a ticket starts only while memory covers it); QA gates run in one 5 GB
container via `qa.sh gate`, dev builds in the dev's warm container `qa-dev-<owner>` via `qa.sh dev`. Fork CI runs
upstream-bound gates on GitHub's runners, so they use no local slot. Each container has its own Gradle home and shares
compiled outputs through the build-cache node (`tools/gradle-cache.sh`); tests are never cached.
