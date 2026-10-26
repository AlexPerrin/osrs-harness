#!/usr/bin/env python3
"""The client gate (ARCHITECTURE 4): gates/client.py <slug> <head> <base> <evidence>. Exit 0 ok, 1 fail; stdout lists
each check. The evidence dir holds the repack log with the telemetry patch's seven lines and the test-server patches, device evidence (a logcat
extract, a data-tool dump or a devtools JSON), and a Network QA report when the definition says `network: true`."""
import fnmatch
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hd import store  # noqa: E402

TELEMETRY_LINES = 7
SERVER_PATCHES = (("the RSA modulus", r"^patched RSA modulus"), ("jav_config", r"^patched /jav_config\.ws"),
                  ("the AppAuth endpoints", r"^patched \S*/net/openid/appauth/"))   # OPENRUNE=1 LOCAL_AUTH=1
DEVICE = ("*logcat*.txt", "*.dump.*", "*devtools*.json")


def main(slug, head, base, ev):
    ch = next((c for c in store.changes() if c["slug"] == slug), {})
    files = sorted(os.listdir(ev)) if os.path.isdir(ev) else []
    ok = True
    logs = [f for f in files if re.match(r"repack.*\.log$|.*repack.*\.txt$", f)]
    if logs:
        with open(os.path.join(ev, logs[0]), errors="replace") as f:
            text = f.read()
        n = len(re.findall(r"^telemetry:", text, re.M))
        ok &= n == TELEMETRY_LINES
        print(f"repack log {logs[0]}: {n} telemetry lines" + ("" if n == TELEMETRY_LINES else f", not {TELEMETRY_LINES}"))
        missing = [what for what, pat in SERVER_PATCHES if not re.search(pat, text, re.M)]
        ok &= not missing
        print("repack log: points at the test server" if not missing else
              f"repack log: missing {', '.join(missing)}: a build without them talks to Jagex (OPENRUNE=1 LOCAL_AUTH=1 tools/repack.sh)")
    else:
        ok = False
        print("no repack log (repack*.log) in the evidence dir")
    hits = [f for p in DEVICE for f in files if fnmatch.fnmatch(f, p)]
    ok &= bool(hits)
    print("device evidence: " + (", ".join(hits[:3]) if hits else f"none ({', '.join(DEVICE)})"))
    built = None
    if os.path.exists(os.path.join(ev, "api-probe.tsv")):
        with open(os.path.join(ev, "api-probe.tsv"), errors="replace") as f:
            m = re.search(r"^# build: \S*-g([0-9a-f]{7,})", f.read(4000), re.M)
        built = m and m.group(1)
    if built and not head.startswith(built):   # the report is evidence of the build it names: only docs may differ
        r = subprocess.run(["git", "-C", store.config()["paths"]["client"], "diff", "--name-only", built, head],
                           capture_output=True, text=True)
        code = [p for p in r.stdout.split() if not p.startswith("docs/")] if r.returncode == 0 else ["(cannot diff)"]
        ok &= not code
        print(f"probe report built at {built[:9]}: " + ("only docs differ from the head" if not code else
              f"the head differs in {', '.join(code[:5])}: rerun the probe at the head"))
    if ch.get("network"):
        nq = [f for f in files if fnmatch.fnmatch(f, "netqa*.md")]
        ok &= bool(nq)
        print("network QA report: " + (nq[0] if nq else "missing (network: true)"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
