#!/usr/bin/env python3
"""Git helpers for the integration train (hd/batches.py): the clones and worktrees, integration.txt sections and
integration.lock pins, and the lease push of `integration`. The v2 queue and its command line are gone: hd's batches
run the train.

Environment (tests): HD_SERVER_HOME, INTEGRATION_DIR, INTEGRATION_CLONE, INTEGRATION_TOOLS_WT, INTEGRATION_REMOTE (fork)."""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hd import fork_clone, server_work  # noqa: E402
AUTHOR = "Alex Perrin <44126061+AlexPerrin@users.noreply.github.com>"
TRAILER = "Co-Authored-By: Claude <noreply@anthropic.com>"
TOOLS_BRANCH = "local/integration-tools"
SECTIONS = ("# Upstream fixes", "# Content", "# Local only")


def state_dir():
    return os.environ.get("INTEGRATION_DIR") or os.path.join(server_work(), "integration")


def clone():
    return fork_clone()


def tools_wt():
    return os.environ.get("INTEGRATION_TOOLS_WT") or os.path.join(server_work(), "integration-tools")


def build_wt():
    return os.path.join(state_dir(), "build")


def remote():
    return os.environ.get("INTEGRATION_REMOTE") or "fork"


def git(cwd, *args, check=True):
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise GitError(f"git {' '.join(args)} (in {cwd}): {(r.stderr or r.stdout).strip()}")
    return r


class GitError(RuntimeError):
    pass


def read_text(path):
    with open(path) as f:
        return f.read()


def rev(cwd, ref):
    return git(cwd, "rev-parse", "-q", "--verify", f"{ref}^{{commit}}", check=False).stdout.strip()


def section_for(branch):
    return "# Local only" if branch.startswith("local/") else "# Upstream fixes" if branch.startswith("fix/") else "# Content"


def add_to_list(text, branch):
    """integration.txt with `branch` at the end of its section (fix/* under "# Upstream fixes", content/* and fin/*
    under "# Content", local/* under "# Local only"); unchanged when it is already listed."""
    lines = text.splitlines()
    if branch in (l.strip() for l in lines):
        return text
    section = section_for(branch)
    start = next((i for i, l in enumerate(lines) if l.startswith(section)), None)
    if start is None:
        lines.append(branch)
    else:
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("#")), len(lines))
        while end > start + 1 and not lines[end - 1].strip():
            end -= 1
        lines.insert(end, branch)
    return "\n".join(lines) + "\n"


def listed(text):
    return [l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]


def parse_pins(text):
    pins = {}
    for l in text.splitlines():
        w = l.split()
        if len(w) >= 2 and not w[0].startswith("#"):
            pins[w[0]] = w[1]
    return pins


def set_pin(text, branch, sha):
    lines, done = text.splitlines(), False
    for i, l in enumerate(lines):
        w = l.split()
        if len(w) >= 2 and w[0] == branch:
            lines[i], done = f"{branch} {sha}", True
    if not done:
        lines.append(f"{branch} {sha}")
    return "\n".join(lines) + "\n"


def tail(text, n=15):
    return "\n".join(text.strip().splitlines()[-n:])


def rebuild(script, cwd, log):
    """Run build-integration.sh against the remote in the rebuild worktree; (rc, output)."""
    r = subprocess.run(["sh", script, remote()], cwd=cwd, capture_output=True, text=True)
    out = r.stdout + ("\n" + r.stderr if r.stderr else "")
    with open(log, "w") as f:
        f.write(out)
    return r.returncode, out


def push_integration(cwd, lease):
    return git(cwd, "push", "-q", f"--force-with-lease=integration:{lease}", remote(), "HEAD:refs/heads/integration",
               check=False)
