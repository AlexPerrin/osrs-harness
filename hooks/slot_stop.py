#!/usr/bin/env python3
"""SubagentStop / Stop hook for the stage executors (harness v3): the end-of-slot gate. An agent cannot finish
while it holds a shared-resource lock (BR-R2: locks only while in use).

  slot_stop.py <role>     the role is kept for the settings matcher; the agent's name comes from the transcript
                          ("Your name is `<name>`") or HD_AGENT.
"""
import json
import os
import re
import sys

HD_PY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hd.py")

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # the harness repo
try:
    from hd import leases   # noqa: E402
except Exception:
    leases = None


def block(reason):
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


def agent_name(data):
    path = data.get("agent_transcript_path") or data.get("transcript_path")
    try:
        with open(path, errors="replace") as f:
            for i, line in enumerate(f):
                if i > 80:
                    break
                m = re.search(r"Your name is `([a-z0-9_-]{1,20})`", line)
                if m:
                    return m.group(1)
    except (OSError, TypeError):
        pass
    return os.environ.get("HD_AGENT") or (sys.argv[1] if len(sys.argv) > 1 else None)


def main():
    data = json.load(sys.stdin)
    if data.get("stop_hook_active"):
        return
    name = agent_name(data)
    if not name:
        return
    if leases is None:
        return
    held = [r for r, st in leases.status_all().items() if st.get("holder") == name]
    if held:
        block("You still hold " + ", ".join(held) + ": release "
              + "; ".join(f"`python3 {HD_PY} lease release {r} {name}`" for r in held) + ".")


main()
