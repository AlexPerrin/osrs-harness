"""Metrics are derived, never typed (BR-H5): the client numbers from tools/progress.py --dry-run, the server parity
from tools/harness/server_parity.py when it exists; each a `metric` event {name, value, total, pct}. The tick
recounts on a fact: a client change went live, a deploy or a re-pin happened, or none was ever recorded; `hd recount`
does it now. HD_NO_RECOUNT=1 skips (tests)."""
import os
import re
import subprocess

from . import ROOT, events

LINE = re.compile(r"^(\S.*?)\s{2,}(\d+)/(\d+)\s+([\d.]+)%", re.M)


def last_recount():
    evs = events.read(kinds=["metric"], limit=1)
    return evs[-1]["ts"] if evs else None


def why(actions):
    """The fact that makes a recount due, from this tick's actions, or None."""
    if os.environ.get("HD_NO_RECOUNT"):
        return None
    for a in actions:
        if a.endswith("-> live") and not a.startswith(("int-", "rel-")):
            return "client live"
        if a.startswith("re-pin") or ": live (" in a:
            return "server deploy or re-pin"
    return None if last_recount() else "first recount"


def recount(why="scheduled"):
    out = []
    try:
        r = subprocess.run(["python3", os.path.join(ROOT, "tools", "progress.py"), "--dry-run"], capture_output=True,
                           text=True, timeout=300, cwd=ROOT)
        for name, v, t, pct in LINE.findall(r.stdout):
            events.emit("metric", name=name.strip(), value=int(v), total=int(t), pct=float(pct), why=why)
            out.append(name.strip())
    except (OSError, subprocess.TimeoutExpired) as e:
        events.emit("error", step="recount", error=repr(e))
    tool = os.path.join(ROOT, "tools", "harness", "server_parity.py")
    if os.path.exists(tool):
        try:
            r = subprocess.run(["python3", tool, "--json"], capture_output=True, text=True, timeout=900, cwd=ROOT)
            import json
            for name, d in (json.loads(r.stdout or "{}") or {}).items():
                events.emit("metric", name=name, value=d.get("value"), total=d.get("total"), pct=d.get("pct"), why=why)
                out.append(name)
        except Exception as e:   # the parity tool is optional
            events.emit("error", step="recount-parity", error=repr(e))
    return out
