#!/usr/bin/env python3
"""Sign the tester in on your own Agent_Phone emulator and reach the game, with no screen image.

  ANDROID_SERIAL=emulator-<port> python3 -I ~/osrs-harness/bench/emulator_login.py

Each step reads the screen as text and acts on what it reads: the app's game state from logcat (osrsrl-host
`GameStateChanged`), the focused window (`dumpsys window`) and the Android views' labels (`uiautomator dump`).
Android views (the full-screen tip, Chrome's first run, the privacy dialog) are tapped by label; the game's own login
screens are canvas, so they are tapped at the Agent_Phone landscape coordinates below, sign-in (LOCAL_AUTH) only, never
Google or Jagex account screens. Sign-in happens once per boot: the auth redirect back to the app leaves
/data/local/tmp/osrs-signed-in, gone with the read-only emulator. A dead app (a Play services update kills it on a fresh
boot) is relaunched, only after the installed APK is the repack. Exit 0 in game; 2 on a screen it does not know, with
the screen's labels printed.
"""
import os
import re
import subprocess
import sys
import time

ADB = os.environ.get("ADB", "/mnt/c/Users/Alex/AppData/Local/Android/Sdk/platform-tools/adb.exe")
SERIAL = os.environ.get("ANDROID_SERIAL") or sys.exit("set ANDROID_SERIAL to your emulator")
PKG = "com.jagex.oldscape.android"
MARK = "/data/local/tmp/osrs-signed-in"
LABELS = ("Got it", "Stay signed out", "Close", "Accept", "No thanks")   # Android views, tapped by label
SIGN_IN, ACCEPT, PLAY_NOW, TRY_AGAIN = (1200, 617), (1032, 645), (1197, 540), (1197, 620)   # canvas, landscape
NODE = re.compile(r'<node [^>]*?text="([^"]*)"[^>]*?content-desc="([^"]*)"[^>]*?bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"')


def adb(*a):
    for _ in range(5):   # adb.exe from WSL drops a call now and then (UtilAcceptVsock)
        r = subprocess.run([ADB, "-s", SERIAL, *a], capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout.replace("\r", "")
        time.sleep(1)
    return ""


def states():
    return re.findall(r"GameStateChanged (\w+)", adb("logcat", "-d", "-s", "osrsrl-host:I"))


def state():
    return (states() or [None])[-1]


def focus():
    m = re.search(r"mCurrentFocus=\S+ \S+ (\S+)\}", adb("shell", "dumpsys", "window"))
    return m.group(1) if m else ""


def labels():
    adb("shell", "uiautomator", "dump", "/sdcard/ui.xml")
    out = []
    for t, d, x0, y0, x1, y1 in NODE.findall(adb("exec-out", "cat", "/sdcard/ui.xml")):
        if t or d:
            out.append((t or d, ((int(x0) + int(x1)) // 2, (int(y0) + int(y1)) // 2)))
    return out


def tap(xy):
    print("tap", *xy, flush=True)
    adb("shell", "input", "tap", str(xy[0]), str(xy[1]))
    time.sleep(3)


def until(pred, polls=20):
    """Polls a fact until it holds; the count only bounds a tap that drew no reaction."""
    for _ in range(polls):
        v = pred()
        if v:
            return v
        time.sleep(2)
    return None


def launch():
    apk = adb("shell", "pm", "path", PKG).strip().replace("package:", "")
    if not apk or adb("shell", f"unzip -l {apk} | grep -c libosrsrl").strip() != "1":
        sys.exit("the installed app is not the repack: not launching it")
    adb("logcat", "-c")
    adb("shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    until(lambda: state() == "LOGIN_SCREEN", polls=90)


def signed_in():
    if "com.jagex.mobilesdk" in adb("logcat", "-d", "-s", "ActivityTaskManager:I"):
        adb("shell", "touch", MARK)
    return adb("shell", f"ls {MARK} 2>/dev/null").strip() == MARK


def main():
    failed = False
    for _ in range(60):
        if not adb("shell", "pidof", PKG).strip():
            launch()
            continue
        st, f = state(), focus()
        if st == "LOGGED_IN":
            print("LOGGED_IN")
            return 0
        found = labels()
        hit = next((xy for name, xy in found if name.strip() in LABELS), None)
        if hit:
            tap(hit)
            continue
        if f.startswith(PKG + "/com.jagex.android.MainActivity") and st == "LOGIN_SCREEN" and not found:
            if not signed_in():
                tap(SIGN_IN)
                if until(lambda: not focus().startswith(PKG + "/com.jagex.android.MainActivity") or labels(), polls=5) is None:
                    tap(ACCEPT)   # the terms, drawn on the canvas
                continue
            if failed:
                tap(TRY_AGAIN)   # "account still logged in": Try again; a blank spot on the Play Now screen
            n = len(states())
            tap(PLAY_NOW)
            st = until(lambda: next((s for s in states()[n:] if s in ("LOGGED_IN", "LOGIN_SCREEN")), None), polls=30)
            failed = st != "LOGGED_IN"
            continue
        if f.startswith("com.android.chrome") or (st in ("LOGGING_IN", "LOADING", "CONNECTION_LOST", "UNKNOWN", "STARTING", None) and f.startswith(PKG)):
            time.sleep(2)
            continue
        print(f"unknown screen: state {st}, focus {f}, labels {[n for n, _ in found]}")
        return 2
    print(f"not in game after 60 steps: state {state()}, focus {focus()}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
