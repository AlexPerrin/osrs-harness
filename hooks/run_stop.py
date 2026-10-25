#!/usr/bin/env python3
"""SubagentStop hook (R6, R8): an agent cannot stop while its change still needs the record this run owes; when it
stops, the run record gets its end, exit, last message and the token usage summed from the subagent transcript.

The record a role owes (hd.yaml `roles.<role>.record`): `handover` (devs), `verdict` (QA), `resolution` (the
integrator, on its train). A record written since the run started, or a hold this run asked (`hd ask`), settles it.
The first stop without it is blocked with the command to run; the second (`stop_hook_active`) is let through as exit
`no-record`, and a hold carrying the last message is put on the change so nothing re-dispatches it (R8). Then
`hd tick` runs so the state moves at once. Never raises.
"""
import json
import os
import subprocess
import sys

HD_HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HD_HOME)
from hd import records  # noqa: E402
from run_start import agent_transcript, console_pid, first_prompt, slug_of  # noqa: E402

HD = f"python3 {HD_HOME}/hd.py"
HOW = {
    "handover": "`{hd} handover <slug> --sha <sha> --evidence <dir> --summary \"...\"` (its check refuses an incomplete hand-over: fix what it prints and run it again)",
    "verdict": "write the record in the evidence dir, then `{hd} verdict <slug> PASS|FAIL --sha <sha>`",
    "resolution": "`{hd} resolve <train> \"<what you recorded or dropped>\"`",
}


def produced(run, slug, kind):
    """The record this run owes exists and is newer than the run."""
    if kind == "resolution":
        t = records.train(slug) or {}
        r = t.get("resolution") or {}
        return bool(r) and r.get("ts", "") >= run.get("started", "")
    r = records.record(slug, kind)
    return bool(r) and r.get("ts", "") >= run.get("started", "")


def asked(run, slug):
    h = records.record(slug, "hold")
    return bool(h) and h.get("by") == run.get("agent_id")


def usage(path):
    """Token usage summed over the assistant messages of a transcript, plus the number of turns."""
    out = {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0, "turns": 0}
    keys = {"input_tokens": "input", "output_tokens": "output", "cache_read_input_tokens": "cache_read",
            "cache_creation_input_tokens": "cache_creation"}
    try:
        with open(path or "", errors="replace") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if e.get("type") != "assistant":
                    continue
                u = (e.get("message") or {}).get("usage") or {}
                if not u:
                    continue
                out["turns"] += 1
                for k, name in keys.items():
                    v = u.get(k)
                    if isinstance(v, (int, float)):
                        out[name] += int(v)
    except OSError:
        pass
    return out


def block(reason):
    print(json.dumps({"decision": "block", "reason": reason}))


def main():
    data = json.load(sys.stdin)
    aid = data.get("agent_id")
    if not aid:
        return
    transcript = agent_transcript(data)
    run = records.run(aid)
    if run is None:   # the start hook did not see this agent
        slug = slug_of(first_prompt(transcript))
        if not slug:
            return
        run = {"agent_id": aid, "role": data.get("agent_type"), "change": slug, "console_pid": console_pid(),
               "session_id": data.get("session_id"), "transcript": transcript, "started": "", "ended": None,
               "exit": None}
    slug, role = run.get("change"), run.get("role")
    kind = ((records.config().get("roles") or {}).get(role) or {}).get("record")
    last = (data.get("last_assistant_message") or "")[-500:]
    exit_ = "ok"
    if slug and kind and not produced(run, slug, kind) and not asked(run, slug):
        if not data.get("stop_hook_active"):
            block(f"Change {slug}: your {kind} is not on disk. Finish with {HOW[kind].format(hd=HD)}; if you cannot, "
                  f"`{HD} ask {slug} \"<what you need>\"`. Then stop.")
            return
        exit_ = "no-record"
    run.update(ended=records.now(), exit=exit_, last=last, usage=usage(data.get("agent_transcript_path") or transcript))
    records.save_run(run)
    if exit_ == "no-record":
        records.save_record(slug, "hold", {"text": f"run {aid} ({role}) ended without its {kind}: {last[-300:]}",
                                           "by": aid, "kind": "no-record"})
    records.event("run", action="end", run=aid, role=role, change=slug, exit=exit_, **run["usage"])
    if os.path.exists(os.path.join(HD_HOME, "hd", "derive.py")):   # the v7 tick is in place
        subprocess.run([sys.executable, os.path.join(HD_HOME, "hd.py"), "tick"], capture_output=True, timeout=600)


if __name__ == "__main__":
    try:
        main()
    except Exception:   # a hook never breaks the session; an error here never blocks a stop
        pass
