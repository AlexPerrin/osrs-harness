#!/usr/bin/env python3
"""PreToolUse (Bash) guard for every role and the console (R31). One table, in hd.yaml:

  repos                 the GitHub repos by key (client, fork, harness, upstream)
  roles.<role>.push     {repo key: [ref patterns]} an agent may push to; `<slug>` is its change's slug
  roles.<role>.gh       repo keys an agent may write to with gh

The role is the hook input's `agent_type`; without one the caller is the console. Denied to everyone: any write to
upstream (OpenRune), `gh release create` and `git tag` (the tick's publish does them), the train and publish scripts,
image builds, deploys and docker writes on the live stack (`osrs-openrune*`, the compose service `openrune`). The
console may push and write any repo of ours (hd.yaml `repos` other than upstream) and alone may run `hd approve`.
Targets are resolved: a push's remote URL from the repo it runs in (`git -C`, `cd`, the hook's cwd), a gh write's
repo from `-R/--repo` or a URL in the same simple command; words never decide. A push the parser cannot see
(inside `$(...)`, a script, a bare `git push`) is denied. A push to a local path never leaves the machine and is
allowed. Every denial is an event.
"""
import fnmatch
import json
import os
import re
import sys

HD_HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HD_HOME)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shellparse as sp  # noqa: E402
from hd import records  # noqa: E402

PUSH = re.compile(r"\bgit\b(\s+-\S+(\s+[^-\s]\S*)?)*\s+push\b")
GH_WRITE = re.compile(r"\bgh\s+(pr|issue|release|gist|repo|label|workflow|run)\s+"
                      r"(create|edit|comment|close|reopen|merge|ready|review|delete|fork|upload|sync|transfer|lock|"
                      r"unlock|rename|archive|delete-asset|run|rerun|cancel|enable|disable)\b")
GH_API_WRITE = re.compile(r"\bgh\s+api\b[^|;&]*(-X\s*(POST|PATCH|PUT|DELETE)|--method|\s-[fF]\s|--field|--raw-field|"
                          r"--input|\bgraphql\b)")
REPO_ARG = re.compile(r"(?:^|\s)(?:-R|--repo)[=\s]+(\S+)|github\.com[:/]+([^/\s]+/[^/\s]+)")
LIVE = re.compile(r"osrs-openrune|(?<![\w.-])openrune(?![\w.-])")
COMPOSE_READ = {"ps", "logs", "config", "ls", "images", "top", "version"}
DOCKER_WRITES = {"tag", "rm", "rmi", "stop", "restart", "kill", "build"}
SCRIPTS = {"train.py", "image.sh", "deploy.sh", "publish.py"}
INTERPRETERS = {"python3", "python", "bash", "sh", "env", "nohup", "timeout"}


def _exe(w):
    i = 0
    while i < len(w) and (os.path.basename(w[i]) in INTERPRETERS or (i > 0 and w[i].startswith("-"))
                          or (os.path.basename(w[0]) == "env" and "=" in w[i])):
        i += 1
    return os.path.basename(w[i]) if i < len(w) else ""


def _hd_sub(w):
    """The `hd` subcommand when the words run this repo's hd.py, else None."""
    i = 0
    while i < len(w) and os.path.basename(w[i]) in INTERPRETERS:
        i += 1
    if i < len(w) and os.path.basename(w[i]) == "hd.py" and i + 1 < len(w):
        return w[i + 1]
    return None


def walk(cmd, cwd):
    out = []
    for seg in sp.resolved_segments(cmd):
        w = sp.words(seg)
        if w:
            sp.note_worktree(w, cwd)
        out.append((seg, w, cwd))
        nd = sp.cd_target(w, cwd) if w else None
        if nd:
            cwd = nd
    return out


class Guard:
    def __init__(self, cfg, role, slug, run=None):
        import subprocess
        self.cfg, self.role, self.slug, self.run = cfg, role, slug, run or subprocess.run
        self.repos = {k: sp.norm_repo(v) for k, v in (cfg.get("repos") or {}).items()}
        self.ours = {v for k, v in self.repos.items() if k != "upstream"}
        self.rules = (cfg.get("roles") or {}).get(role) or {}

    def repo_key(self, repo):
        for k, v in self.repos.items():
            if v == repo:
                return k
        return None

    def push_problem(self, seg, w, cwd):
        p = sp.parse_push(w, cwd) if w else None
        if p is None:
            return "a push the guard cannot see (inside a substitution, a script or a subshell)"
        if sp.UPSTREAM_NAME.search(seg):
            return "it names OpenRune upstream"
        if not p["remote"]:
            return "a bare `git push`: the target cannot be told"
        url = sp.push_url(p, self.run)
        if url and "://" not in url and not re.match(r"^[\w.-]+@[\w.-]+:", url) and "/" in url and os.path.isabs(
                url if os.path.isabs(url) else os.path.join(p["dir"] or ".", url)):
            return None   # a local path: nothing leaves the machine
        repo = sp.norm_repo(url)
        if repo not in self.ours:
            return f"remote {p['remote']} in {p['dir']} is {url or 'unknown'}, not one of our repos"
        if self.role == "console":
            return None
        allowed = (self.rules.get("push") or {}).get(self.repo_key(repo)) or []
        pats = [a.replace("<slug>", self.slug or "<no-change>") for a in allowed]
        for r in p["refspecs"] or ["HEAD"]:
            d = sp.dest(r)
            if not any(fnmatch.fnmatchcase(d, pat) for pat in pats):
                return f"ref {d} on {repo}: {self.role} may push only {', '.join(pats) or 'nothing'}"
            if sp.forced(p) and not d.startswith("gate/"):
                return "a forced or deleting push"
        return None

    def gh_problem(self, seg):
        if sp.UPSTREAM_NAME.search(seg):
            return "it names OpenRune upstream"
        if re.search(r"\bgh\s+release\s+create\b", seg):
            return "a release: the tick publishes after the user's yes"
        m = REPO_ARG.search(seg)
        repo = sp.norm_repo(m.group(1) or m.group(2)) if m else ""
        if repo not in self.ours:
            return f"the repo {repo or 'is not named'}: name one of ours with -R"
        if self.role == "console":
            return None
        if self.repo_key(repo) not in (self.rules.get("gh") or []):
            return f"{self.role} may not write to {repo}"
        return None

    def live_problem(self, w, cwd):
        exe = _exe(w)
        if exe in SCRIPTS:
            return f"{exe} is the tick's"
        if exe == "docker" and len(w) > 1:
            if w[1] == "compose" or exe == "docker-compose":
                sub = next((x for x in w[2:] if not x.startswith("-")), None)
                if sub in COMPOSE_READ:
                    return None
                if any(LIVE.search(a) for a in w[1:]) or any(a.endswith("switch.env") for a in w):
                    return "a compose write on the live stack"
                return None
            args = w[2:] if w[1] in ("image", "container") else w[1:]
            if args and args[0] in DOCKER_WRITES and any("osrs-openrune" in a for a in args[1:]):
                return "a docker write on the live stack"
        if exe == "git" and "tag" in w[1:] and not any(x in w for x in ("-l", "--list")):
            return "a tag: the tick publishes after the user's yes"
        return None

    def decide(self, cmd, cwd):
        """The deny reason, or None."""
        for seg, w, c in walk(cmd, cwd):
            if not w:
                continue
            if os.path.basename(w[0]) in ("bash", "sh", "zsh") and "-c" in w and w.index("-c") + 1 < len(w):
                why = self.decide(w[w.index("-c") + 1], c)
                if why:
                    return why
                continue
            why = self.live_problem(w, c)
            if why:
                return why
            if PUSH.search(seg):
                why = self.push_problem(seg, w, c)
                if why:
                    return f"push denied: {why}"
            if GH_WRITE.search(seg) or GH_API_WRITE.search(seg):
                why = self.gh_problem(seg)
                if why:
                    return f"GitHub write denied: {why}"
            if re.search(r"(^|[\s/])fork\.sh\b", seg) and (sp.UPSTREAM_NAME.search(seg) or "fork" not in (self.rules.get("gh") or []) and self.role != "console"):
                return "fork.sh: not this role's"
            sub = _hd_sub(w)
            if sub == "approve" and self.role != "console":
                return "`hd approve` records the user's yes: the console alone runs it"
        if sp.hidden_writes(cmd):
            return "a push or gh call inside a substitution: the target cannot be told"
        return None


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") not in (None, "Bash"):
        return
    cmd = (data.get("tool_input") or {}).get("command") or ""
    cwd = data.get("cwd") or os.getcwd()
    role = data.get("agent_type") or "console"
    run = records.run(data.get("agent_id")) if data.get("agent_id") else None
    slug = (run or {}).get("change")
    why = Guard(records.config(), role, slug).decide(cmd, cwd)
    if why:
        records.event("denial", role=role, run=data.get("agent_id"), change=slug, rule=why[:160], command=cmd[:200])
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": f"{why}. Report it; do not work around it."}}))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:   # fail closed on the writes the guard exists for, open elsewhere
        try:
            cmd = (json.loads(sys.stdin.read() or "{}").get("tool_input") or {}).get("command", "")
        except Exception:
            cmd = ""
        if PUSH.search(cmd) or GH_WRITE.search(cmd) or GH_API_WRITE.search(cmd):
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                     "permissionDecisionReason": f"guard error: {e!r}"}}))
