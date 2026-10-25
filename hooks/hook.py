#!/usr/bin/env python3
"""The one hook program (ARCHITECTURE 6), on two Claude Code events read from the input's `hook_event_name`:

  PreToolUse (Bash) binds the run first: an agent of a role with no run yet gets runs/<name>.json from its transcript's first
                    line (``Harness change `<slug>` run `<name>` head `<sha>` def `<hash>` step `<step>` ``), the agent id,
                    its role and the console pid with its start time. Without that line nothing is written. Then the guard.
  SubagentStop      when the agent handed back (a SubagentHandback call in its transcript): ends the run (`ended`,
                    `record`: the role's record exists and is newer than the start, `last`, the token usage) and runs
                    `hd tick`. Without the hand-back it is a pause for background work, or a transcript not yet flushed:
                    the pass ends the run when it sees the hand-back. A stop cannot be refused.
  The guard (R4):   deny by default for OpenRune: a `git` or `gh` command naming the upstream repo passes
                    only as a read; fork pushes and gh writes only to the role's refs (hd.yaml `roles`); forced pushes,
                    tags, releases, the train scripts and docker writes on the live stack denied to all; `hd approve`
                    only from the console. A write the parser cannot see is denied. Every denial is an event.
Never raises into the session.
"""
import fnmatch
import json
import os
import re
import subprocess
import sys

HD_HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HD_HOME)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shellparse as sp  # noqa: E402
from hd import store, tick  # noqa: E402
from hd.tick import _lines, handed_back  # noqa: E402

BRIEF = re.compile(r"Harness change `([a-z0-9][a-z0-9.-]*)` run `([a-z0-9][a-z0-9.-]*)`(?: head `([0-9a-f]*)`)?(?: def `(\w+)`)?(?: step `(\w+)`)?")
PUSH = re.compile(r"\bgit\b(\s+-\S+(\s+[^-\s]\S*)?)*\s+push\b")
GH_READ = re.compile(r"\bgh\s+(pr\s+(view|list|diff|checks|status)|run\s+(view|list|watch|download)|repo\s+view|search\s|"
                     r"issue\s+(view|list)|api\s(?![^|;&]*(-X\s*(POST|PATCH|PUT|DELETE)|--method|\s-[fF]\s|--field|--raw-field|--input)))")
GIT_READ = re.compile(r"\bgit\b(\s+-C\s+\S+)?\s+(fetch|ls-remote|clone|log|show|diff|remote\s+(-v|show|get-url|add|set-url))\b")
GH_WRITE = re.compile(r"\bgh\s+(pr|issue|release|gist|repo|label|workflow|run|api)\b")
REPO_ARG = re.compile(r"(?:^|\s)(?:-R|--repo)[=\s]+(\S+)|github\.com[:/]+([^/\s]+/[^/\s]+)")
LIVE = re.compile(r"osrs-openrune|(?<![\w.-])openrune(?![\w.-])")
COMPOSE_READ = {"ps", "logs", "config", "ls", "images", "top", "version"}
DOCKER_WRITES = {"tag", "rm", "rmi", "stop", "restart", "kill", "build"}
SCRIPTS = {"train.sh", "image.sh", "deploy.sh"}
INTERPRETERS = {"python3", "python", "bash", "sh", "env", "nohup", "timeout", "flock"}
RECORD = {"handover": "handover", "verdict": "verdict", "measure": "measure"}


# --- runs --------------------------------------------------------------------------------------------------------------

def console(pid=None):
    """(pid, start) of the `claude` process above this hook, or (None, None)."""
    pid = pid or os.getppid()
    while pid and pid > 1:
        try:
            with open(f"/proc/{pid}/comm") as f:
                if f.read().strip() == "claude":
                    with open(f"/proc/{pid}/stat") as s:
                        return pid, s.read().rsplit(")", 1)[1].split()[19]
            with open(f"/proc/{pid}/status") as f:
                pid = int(re.search(r"^PPid:\s*(\d+)", f.read(), re.M).group(1))
        except (OSError, AttributeError, ValueError, IndexError):
            return None, None
    return None, None


def transcript_of(data):
    p = data.get("agent_transcript_path")
    if p:
        return p
    t, sid, aid = data.get("transcript_path"), data.get("session_id"), data.get("agent_id")
    return os.path.join(os.path.dirname(t), sid, "subagents", f"agent-{aid}.jsonl") if t and sid and aid else None


def _text(content):
    if isinstance(content, str):
        return content
    return "\n".join(b.get("text", "") for b in content or [] if isinstance(b, dict) and b.get("type") == "text")


def first_prompt(path):
    for e in _lines(path):
        if e.get("type") == "user":
            return _text((e.get("message") or {}).get("content"))
    return ""


def _bind(data):
    m = BRIEF.search(first_prompt(transcript_of(data)))
    return m.groups() if m else None


def start(data):
    b = _bind(data)
    if not b:
        return
    slug, name, head, dh, step = b
    pid, st = console()
    rec = {"name": name, "agent_id": data.get("agent_id"), "role": data.get("agent_type"), "change": slug, "head": head or None,
           "def_hash": dh, "step": step, "transcript": transcript_of(data), "console_pid": pid, "console_start": st,
           "started": store.now(), "ended": None}
    store.save_run(rec)
    store.event("run", action="start", run=name, role=rec["role"], change=slug, agent=data.get("agent_id"))


def stop(data):
    """The agent handed back: end its run and run a pass. Without the hand-back in the transcript this stop is a pause
    (background work), or the transcript is not flushed yet: the pass ends the run when it sees the hand-back."""
    aid = data.get("agent_id")
    run = next((r for r in store.runs() if r.get("agent_id") == aid), None)
    path = data.get("agent_transcript_path") or transcript_of(data)
    if not handed_back(path):
        store.event("run", action="pause", run=(run or {}).get("name"), agent=aid)
        return
    if run is None:
        b = _bind(data)
        if not b:
            return
        slug, name, head, dh, step = b
        run = {"name": name, "agent_id": aid, "role": data.get("agent_type"), "change": slug, "head": head or None,
               "def_hash": dh, "step": step, "transcript": path, "console_pid": None, "console_start": None,
               "started": store.now(), "ended": None}   # first seen now: a record it may have written earlier is not credited
    if not run.get("ended"):
        tick.end_run(run, last=(data.get("last_assistant_message") or "")[-500:])
    subprocess.run([sys.executable, os.path.join(HD_HOME, "hd.py"), "tick"], capture_output=True, timeout=600)


# --- the guard ----------------------------------------------------------------------------------------------------------

def _exe(w):
    i = 0
    while i < len(w) and (os.path.basename(w[i]) in INTERPRETERS or (i > 0 and w[i].startswith("-"))
                          or (os.path.basename(w[0]) == "env" and "=" in w[i])):
        i += 1
    return os.path.basename(w[i]) if i < len(w) else ""


def _hd_sub(w):
    i = 0
    while i < len(w) and os.path.basename(w[i]) in INTERPRETERS:
        i += 1
    return w[i + 1] if i + 1 < len(w) and os.path.basename(w[i]) == "hd.py" else None


class Guard:
    def __init__(self, cfg, role, slug, run=subprocess.run):
        self.cfg, self.role, self.slug, self.run = cfg, role, slug, run
        self.repos = {k: sp.norm_repo(v) for k, v in (cfg.get("repos") or {}).items()}
        self.ours = {v for k, v in self.repos.items() if k != "upstream"}
        self.refs = (cfg.get("roles") or {}).get(role, {}).get("push") or {}

    def _key(self, repo):
        return next((k for k, v in self.repos.items() if v == repo), None)

    def upstream(self, seg):
        if not sp.UPSTREAM_NAME.search(seg):
            return None
        if GH_READ.search(seg) and not PUSH.search(seg):
            return None
        if GIT_READ.search(seg) and not PUSH.search(seg) and not GH_WRITE.search(seg):
            return None
        return "it names OpenRune upstream and is not a read"

    def push(self, seg, w, cwd):
        p = sp.parse_push(w, cwd) if w else None
        if p is None:
            return "a push the guard cannot see"
        if not p["remote"]:
            return "a bare `git push`: the target cannot be told"
        url = sp.push_url(p, self.run)
        if url and "://" not in url and not re.match(r"^[\w.-]+@[\w.-]+:", url):
            return None   # a local path: nothing leaves the machine
        repo = sp.norm_repo(url)
        if repo not in self.ours:
            return f"remote {p['remote']} is {url or 'unknown'}, not one of our repos"
        if self.role == "console":
            return None   # our repos are the user's: the console is free on them
        if sp.forced(p) and not all(sp.dest(r).startswith("gate/") for r in p["refspecs"] or [""]):
            return "a forced or deleting push"
        pats = [a.replace("<slug>", self.slug or "<no-change>") for a in self.refs.get(self._key(repo)) or []]
        for r in p["refspecs"] or ["HEAD"]:
            if not any(fnmatch.fnmatchcase(sp.dest(r), pat) for pat in pats):
                return f"ref {sp.dest(r)} on {repo}: {self.role} may push only {', '.join(pats) or 'nothing'}"
        return None

    def gh(self, seg):
        if GH_READ.search(seg):
            return None
        if re.search(r"\bgh\s+release\s+create\b", seg):
            return "a release: the pass publishes after the user's yes"
        m = REPO_ARG.search(seg)
        repo = sp.norm_repo(m.group(1) or m.group(2)) if m else ""
        if repo not in self.ours:
            return f"the repo {repo or 'is not named'}: name one of ours with -R"
        if self._key(repo) == "fork" and re.search(r"\bgh\s+(pr\s+(create|comment|edit|review)|issue\s+(create|comment))\b", seg):
            return "no PRs, issues or comments on the fork: a fork PR that names an upstream PR shows on its timeline as a Closed mention"
        if self.role != "console" and self._key(repo) not in self.refs:
            return f"{self.role} may not write to {repo}"
        return None

    def live(self, w):
        exe = _exe(w)
        if exe in SCRIPTS:
            return f"{exe} is the pass's"
        if exe == "docker" and len(w) > 1:
            if w[1] == "compose":
                sub = next((x for x in w[2:] if not x.startswith("-")), None)
                if sub not in COMPOSE_READ and (any(LIVE.search(a) for a in w[1:]) or any(a.endswith("switch.env") for a in w)):
                    return "a compose write on the live stack"
                return None
            args = w[2:] if w[1] in ("image", "container") else w[1:]
            if args and args[0] in DOCKER_WRITES and any("osrs-openrune" in a for a in args[1:]):
                return "a docker write on the live stack"
        if exe == "git" and "tag" in w[1:] and not any(x in w for x in ("-l", "--list")):
            return "a tag: the pass publishes after the user's yes"
        return None

    def decide(self, cmd, cwd):
        for seg in sp.resolved_segments(cmd):
            w = sp.words(seg)
            if not w:
                continue
            if os.path.basename(w[0]) in ("bash", "sh", "zsh") and "-c" in w and w.index("-c") + 1 < len(w):
                why = self.decide(w[w.index("-c") + 1], cwd)
                if why:
                    return why
                continue
            nd = sp.cd_target(w, cwd)
            why = self.upstream(seg) or self.live(w)
            if not why and PUSH.search(seg):
                why = self.push(seg, w, cwd)
            if not why and GH_WRITE.search(seg):
                why = self.gh(seg)
            if not why and _hd_sub(w) == "approve" and self.role != "console":
                why = "`hd approve` records the user's yes: the console alone runs it"
            if why:
                return why
            cwd = nd or cwd
        if sp.hidden_writes(cmd):
            return "a push or gh call inside a substitution: the target cannot be told"
        return None


def guard(data):
    if data.get("tool_name") not in (None, "Bash"):
        return
    cmd = (data.get("tool_input") or {}).get("command") or ""
    role = data.get("agent_type") or "console"
    run = next((r for r in store.runs() if r.get("agent_id") == data.get("agent_id")), None) if data.get("agent_id") else None
    if run is None and data.get("agent_id") and data.get("agent_type") in (store.config().get("roles") or {}):
        start(data)   # the start event can come before the agent's transcript exists: bind at its first command instead
        run = next((r for r in store.runs() if r.get("agent_id") == data.get("agent_id")), None)
    why = Guard(store.config(), role, (run or {}).get("change")).decide(cmd, data.get("cwd") or os.getcwd())
    if why:
        store.event("denial", role=role, run=(run or {}).get("name"), rule=why[:160], command=cmd[:200])
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": f"{why}. Report it; do not work around it."}}))


def main(event=None):
    raw = sys.stdin.read()
    try:
        data = json.loads(raw or "{}")
        event = event or data.get("hook_event_name")
        {"SubagentStart": start, "SubagentStop": stop, "PreToolUse": guard}[event](data)
    except Exception as e:   # fail closed on the writes the guard exists for, open elsewhere
        cmd = ""
        try:
            cmd = (json.loads(raw).get("tool_input") or {}).get("command", "")
        except Exception:
            pass
        if PUSH.search(cmd) or GH_WRITE.search(cmd):
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                     "permissionDecisionReason": f"guard error: {e!r}"}}))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
