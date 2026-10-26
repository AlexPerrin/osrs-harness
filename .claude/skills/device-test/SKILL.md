---
name: device-test
description: "Test on the Android emulator (Agent_Phone) against the OpenRune test server, from backup to handing the device back restored. Use for any check that needs the Android app."
---
# Device test (your own Agent_Phone emulator, its own adb port; app uid 10071)

1. **Instance.** Start your own emulator (the Agent_Phone AVD read-only on a free even port, command in skill `test-instances`), `export ANDROID_SERIAL=emulator-<port>`, then `adb uninstall com.jagex.oldscape.android` (a second guard; Agent_Phone holds no OSRS app) before installing the repack, stop on any install error, and launch only after `libosrsrl.so` is in the installed APK; stop it when done; never touch an instance already open; no lock. Client repo paths below are under `~/osrs-plugins-reverse` (docs, tools, re/).
2. **Backup.** `~/osrs-harness/bench/device-restore-check.sh pre /tmp/osrs-slot/<name>` before touching anything.
3. **Set up.** Push test jars to the plugins dir; for the `osrs-devtools` MCP push `devtools.jar`,
   `adb shell setprop debug.osrsrl.devtools 1` and restart the app (~/osrs-plugins-reverse/docs/plugin-host.md).
4. **Sign in.** `ANDROID_SERIAL=<serial> python3 -I ~/osrs-harness/bench/emulator_login.py` launches the repack (only
   after its check), signs in with "Sign in with Email / Username" (LOCAL_AUTH, never Google or Jagex screens), passes
   the tip, terms, Chrome and privacy dialogs, retries Play Now while the account is still logged in elsewhere, and
   exits 0 in game; exit 2 prints the screen it does not know as text. Run it again after any app restart.
5. **Test.** Drive it with `osrs-devtools` (load with ToolSearch, or `python3 -I tools/devtools_mcp.py --call
   tools/call '{"name":...}'` from the client repo when the MCP did not connect) and read state as text, each need
   by its text way:

   | Need | Text way |
   |---|---|
   | which screen or dialog, app up, host ready | logcat `-s osrsrl-host:I` (`host ready`, `GameStateChanged`), `dumpsys window` (`mCurrentFocus`), `uiautomator dump` then `exec-out cat` (Android views' labels and bounds) |
   | logged in, loading, connection lost | `get_client_state` (`gameState`), the `GameStateChanged` log |
   | where to tap in the game UI | act without coordinates (`widget_action`, `click_component`, `interact_npc`, `interact_object`, `item_action`, `click_menu_option`, `walk_to`), or take bounds from `get_widget`, `dump_interface`, `list_interfaces`, `get_widget_at` |
   | menus, dialogues, chat input | `get_npc_menu`, `get_dialogue`, `continue_dialogue`, `select_option`, `type_chat` (it landed: `get_var varcstr 335`) |
   | combat, effects, projectiles, items | `get_combat_history`, `get_effect_history`, `list_projectiles`, `get_projectile_history`, `list_npcs`, `get_inventory`, `list_ground_items` |
   | vars, XP, sounds, chat | `get_var`, `get_var_history`, `get_xp_history`, `get_sound_history`, `get_chat_history` |

   A screenshot costs far more context: it is the fallback only when no text way answers, i.e. how something is drawn
   (an overlay, a highlight) or a repeated chat line `get_chat_history` under-reports; crop it to the part in question.
   The native long-press menu is `input swipe x y x y 900`. `osrs-mcp` gives ids and game data.
6. **Restore.** Remove what you added BY NAME, each in a plain `adb -s $ANDROID_SERIAL shell rm <path>` call of its
   own (no wildcards, loops or `bash -c`); clear the debug props; log in at 3219,3222.
7. **Check.** `~/osrs-harness/bench/device-restore-check.sh check /tmp/osrs-slot/<name>` until every line is OK.

Tester account: never `::empty` it, keep its GE offer (lobster), drop only items you spawned. More gotchas:
~/osrs-plugins-reverse/docs/client-state.md "Gotchas".

## Report
What was tested on which build, the result per item, and evidence paths (logcat and devtools extracts).
