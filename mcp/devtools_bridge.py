#!/usr/bin/env python3
"""MCP stdio front for the devtools bridges, so a session connects whether or not a client is running.

  mcp/devtools_bridge.py <name> <backend> [args...]

`initialize` is answered here; `tools/list` and every other request run `<backend> --call <method> <params>` one at a
time (the desktop and Android bridges both take it), so a client started after the session is used on its next call.
A live tools list is cached in ~/.cache/osrs-devtools/tools-<name>.json; without a live client the cache, else
mcp/devtools-snapshot.json, answers it. A call with no client returns the backend's error, not a dead server.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = json.load(open(os.path.join(HERE, "devtools-snapshot.json")))


def reply(msg_id, **body):
    print(json.dumps({"jsonrpc": "2.0", "id": msg_id, **body}, separators=(",", ":")), flush=True)


def backend(cmd, method, params):
    """The backend's JSON-RPC reply to one request, or None when it printed none."""
    p = subprocess.run([*cmd, "--call", method, json.dumps(params)], capture_output=True, text=True, timeout=240)
    for line in reversed(p.stdout.splitlines()):
        if line.startswith("{"):
            return json.loads(line)
    sys.stderr.write(p.stderr[-400:])
    return {"error": {"code": -32000, "message": (p.stderr.strip() or "no reply from the client bridge")[-300:]}}


def tools(name, cmd):
    cache = os.path.expanduser(f"~/.cache/osrs-devtools/tools-{name}.json")
    live = backend(cmd, "tools/list", {})
    if "result" in live:
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        with open(cache, "w") as f:
            json.dump(live["result"], f)
        return live["result"]
    try:
        return json.load(open(cache))
    except (OSError, ValueError):
        return {"tools": SNAPSHOT["tools"]}


def handle(name, cmd, line):
    try:
        msg = json.loads(line)
    except ValueError:
        return
    if "id" not in msg:   # notifications need no answer
        return
    method, params = msg.get("method"), msg.get("params") or {}
    if method == "initialize":
        reply(msg["id"], result={**SNAPSHOT["initialize"], "protocolVersion": params.get("protocolVersion")
                                 or SNAPSHOT["initialize"]["protocolVersion"]})
    elif method == "tools/list":
        reply(msg["id"], result=tools(name, cmd))
    elif method == "ping":
        reply(msg["id"], result={})
    else:
        r = backend(cmd, method, params)
        reply(msg["id"], **({"result": r["result"]} if "result" in r else {"error": r.get("error")}))


def main():
    name, cmd = sys.argv[1], sys.argv[2:]
    for line in sys.stdin:
        if line.strip():
            handle(name, cmd, line)


if __name__ == "__main__":
    main()
