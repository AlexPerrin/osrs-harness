#!/usr/bin/env python3
"""SubagentStart hook (R6): the run record for an agent the console spawned, bound to its change.

The brief's first line names the change: "Harness change `<slug>` ...". It is the first user message of the
subagent's transcript (`<projects>/<session>/subagents/agent-<id>.jsonl`, on disk at spawn); when that file is not
there yet, the Agent tool call in the parent transcript carries the same prompt. The console pid is the hook's
ancestor whose command is `claude`; a run is alive while that pid is (R7). An agent whose prompt names no change
and whose type is not a harness role gets no record. Never blocks; never raises.
"""
import json
import os
import re
import sys

HD_HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HD_HOME)
from hd import records  # noqa: E402

SLUG = re.compile(r"Harness change `([a-z0-9][a-z0-9.-]*)`")


def console_pid(pid=None):
    """The pid of the `claude` process above this hook, or None."""
    pid = pid or os.getppid()
    while pid and pid > 1:
        try:
            with open(f"/proc/{pid}/comm") as f:
                if f.read().strip() == "claude":
                    return pid
            with open(f"/proc/{pid}/status") as f:
                pid = int(re.search(r"^PPid:\s*(\d+)", f.read(), re.M).group(1))
        except (OSError, AttributeError, ValueError):
            return None
    return None


def agent_transcript(data):
    p = data.get("agent_transcript_path")
    if p:
        return p
    t, sid, aid = data.get("transcript_path"), data.get("session_id"), data.get("agent_id")
    if t and sid and aid:
        return os.path.join(os.path.dirname(t), sid, "subagents", f"agent-{aid}.jsonl")
    return None


def _text(content):
    if isinstance(content, str):
        return content
    return "\n".join(b.get("text", "") for b in content or [] if isinstance(b, dict) and b.get("type") == "text")


def first_prompt(path):
    """The first user message of a transcript, or ''."""
    try:
        with open(path, errors="replace") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if e.get("type") == "user":
                    return _text((e.get("message") or {}).get("content"))
    except OSError:
        pass
    return ""


def slug_of(text):
    m = SLUG.search(text or "")
    return m.group(1) if m else None


def slug_from_parent(data):
    """Fallback: the latest Agent tool call of this agent type in the parent transcript whose prompt names a change."""
    found = None
    try:
        with open(data.get("transcript_path") or "", errors="replace") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if e.get("type") != "assistant":
                    continue
                for b in (e.get("message") or {}).get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Agent":
                        inp = b.get("input") or {}
                        if inp.get("subagent_type") == data.get("agent_type") and slug_of(inp.get("prompt")):
                            found = slug_of(inp.get("prompt"))
    except OSError:
        pass
    return found


def main():
    data = json.load(sys.stdin)
    aid, role = data.get("agent_id"), data.get("agent_type")
    if not aid:
        return
    transcript = agent_transcript(data)
    slug = slug_of(first_prompt(transcript)) or slug_from_parent(data)
    if not slug and role not in (records.config().get("roles") or {}):
        return
    rec = {"agent_id": aid, "role": role, "change": slug, "console_pid": console_pid(),
           "session_id": data.get("session_id"), "transcript": transcript, "started": records.now(),
           "ended": None, "exit": None}
    records.save_run(rec)
    records.event("run", action="start", run=aid, role=role, change=slug, console_pid=rec["console_pid"])


if __name__ == "__main__":
    try:
        main()
    except Exception:   # a hook never breaks the session
        pass
