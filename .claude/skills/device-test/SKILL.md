---
name: device-test
description: "Test on the Android emulator (Agent_Phone) against the OpenRune test server, from backup to handing the device back restored. Use for any check that needs the Android app."
---
# Device test (your own Agent_Phone emulator, its own adb port; app uid 10071)

1. **Instance.** Start your own emulator (the Agent_Phone AVD read-only on a free even port, command in skill `test-instances`), `export ANDROID_SERIAL=emulator-<port>`, then `adb uninstall com.jagex.oldscape.android` (a second guard; Agent_Phone holds no OSRS app) before installing the repack, stop on any install error, and launch only after `libosrsrl.so` is in the installed APK; stop it when done; never touch an instance already open; no lock. Client repo paths below are under `~/osrs-plugins-reverse` (docs, tools, re/).
2. **Backup.** `~/osrs-harness/bench/device-restore-check.sh pre /tmp/osrs-slot/<name>` before touching anything.
3. **Set up.** Push test jars to the plugins dir; for the `osrs-devtools` MCP push `devtools.jar`,
   `adb shell setprop debug.osrsrl.devtools 1` and restart the app (~/osrs-plugins-reverse/docs/plugin-host.md).
4. **Sign in.** Screenshot first; tap only "Sign in with Email / Username" (LOCAL_AUTH). After a force-stop the
   server may still hold the session: wait 30-60 s, "Try again" (958,668) only on that screen.
5. **Test.** Drive it with `osrs-devtools` (load with ToolSearch) and read state from its data tools: menus
   (`get_npc_menu`, `get_widget_at`), widgets (`get_widget`, `dump_interface`), vars (`get_var`), chat
   (`get_chat_history`), NPCs and items (`list_*`). Raw `adb shell input` and screenshots are the fallback for what
   the tools can't reach (the native long-press menu: `input swipe x y x y 900`) and for drawing claims; confirm
   repeated chat lines by screenshot (`get_chat_history` under-reports repeats). `osrs-mcp` gives ids and game data.
6. **Restore.** Remove what you added BY NAME, each in a plain `adb -s $ANDROID_SERIAL shell rm <path>` call of its
   own (no wildcards, loops or `bash -c`); clear the debug props; log in at 3219,3222.
7. **Check.** `~/osrs-harness/bench/device-restore-check.sh check /tmp/osrs-slot/<name>` until every line is OK.

Tester account: never `::empty` it, keep its GE offer (lobster), drop only items you spawned. More gotchas:
~/osrs-plugins-reverse/docs/client-state.md "Gotchas".

## Report
What was tested on which build, the result per item, and evidence paths (screenshots, logcat extracts).
