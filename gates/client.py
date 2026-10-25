#!/usr/bin/env python3
"""The client gate (ARCHITECTURE 4): gates/client.py <slug> <head> <base> <evidence>. Exit 0 ok, 1 fail; stdout lists
each check. The evidence dir holds the repack log with the telemetry patch's seven lines, device evidence (a logcat
extract, a data-tool dump or a devtools JSON), and a Network QA report when the definition says `network: true`."""
import fnmatch
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hd import store  # noqa: E402

TELEMETRY_LINES = 7
DEVICE = ("*logcat*.txt", "*.dump.*", "*devtools*.json")


def main(slug, head, base, ev):
    ch = next((c for c in store.changes() if c["slug"] == slug), {})
    files = sorted(os.listdir(ev)) if os.path.isdir(ev) else []
    ok = True
    logs = [f for f in files if re.match(r"repack.*\.log$|.*repack.*\.txt$", f)]
    if logs:
        with open(os.path.join(ev, logs[0]), errors="replace") as f:
            n = len(re.findall(r"^telemetry:", f.read(), re.M))
        ok &= n == TELEMETRY_LINES
        print(f"repack log {logs[0]}: {n} telemetry lines" + ("" if n == TELEMETRY_LINES else f", not {TELEMETRY_LINES}"))
    else:
        ok = False
        print("no repack log (repack*.log) in the evidence dir")
    hits = [f for p in DEVICE for f in files if fnmatch.fnmatch(f, p)]
    ok &= bool(hits)
    print("device evidence: " + (", ".join(hits[:3]) if hits else f"none ({', '.join(DEVICE)})"))
    if ch.get("network"):
        nq = [f for f in files if fnmatch.fnmatch(f, "netqa*.md")]
        ok &= bool(nq)
        print("network QA report: " + (nq[0] if nq else "missing (network: true)"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
