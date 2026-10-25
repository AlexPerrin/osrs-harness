#!/usr/bin/env python3
"""The server gate (ARCHITECTURE 4): gates/server.py <slug> <head> <base> <evidence>. Exit 0 ok, 1 fail, 2 pending.

  1. the evidence dir holds the accuracy spec (accuracy*.md); the PR texts are the publish steps' concern
  2. the scratch merge <head> + upstream main (<base>) in state/gates/<slug>/or, pushed to the fork's gate/<slug>; the
     merge commit on the fork with those two parents is reused
  3. the net diff scanned: added test files and comment lines are printed for the reviewer
  4. the fork's CI and Formatting workflows at the scratch commit: dispatched when absent, pending while they run, ok
     when both are green
"""
import glob
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hd import store  # noqa: E402
from hd.facts import Facts, sh  # noqa: E402

WORKFLOWS = (("ci.yml", "CI"), ("Formatting", "Formatting"))
TEST_PATH = re.compile(r"(^|/)src/(test|androidTest)/|(^|/)[^/]*Tests?\.kt$")
COMMENT = re.compile(r"^\+\s*(//|/\*|\*(\s|/|$))")
ENV = {"GIT_AUTHOR_NAME": "Alex Perrin", "GIT_AUTHOR_EMAIL": "44126061+AlexPerrin@users.noreply.github.com",
       "GIT_COMMITTER_NAME": "Alex Perrin", "GIT_COMMITTER_EMAIL": "44126061+AlexPerrin@users.noreply.github.com"}


def git(repo, *args):
    return sh(["git", "-C", repo, *args], env=ENV)


def scan(diff):
    out, path, seen = [], None, set()
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            path = line.rsplit(" b/", 1)[-1]
        elif line.startswith("new file mode") and path and TEST_PATH.search(path):
            out.append(f"added test file {path}")
        elif line.startswith("+") and not line.startswith("+++") and path and path.endswith((".kt", ".kts", ".java")) \
                and COMMENT.match(line) and (path, line[1:].strip()) not in seen:
            seen.add((path, line[1:].strip()))
            out.append(f"added comment in {path}: {line[1:].strip()[:100]}")
    return out[:40]


def scratch_clone(cfg, slug):
    fork = cfg["paths"]["fork"]
    path = store.path("gates", slug, "or")
    if not os.path.isdir(os.path.join(path, ".git")):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        sh(["git", "clone", "-q", "--shared", "--no-checkout", fork, path])
        for name in ("fork", "origin"):
            url = git(fork, "remote", "get-url", name).stdout.strip()
            git(path, "remote", "remove", name)
            git(path, "remote", "add", name, url)
    return path


def main(slug, head, base, ev):
    cfg = store.config()
    ch = next((c for c in store.changes() if c["slug"] == slug), {})
    if not glob.glob(os.path.join(ev, "accuracy*.md")):
        print("missing accuracy*.md in the evidence dir")
        return 1
    branch = f"gate/{slug}"
    path = scratch_clone(cfg, slug)
    if git(path, "fetch", "-q", "fork", head, f"refs/heads/{branch}").returncode != 0 and git(path, "fetch", "-q", "fork", head).returncode != 0:
        print(f"cannot fetch {head[:9]} from the fork")
        return 1
    git(path, "fetch", "-q", "origin", "main")
    existing = git(path, "rev-parse", "-q", "--verify", "FETCH_HEAD").stdout.strip() if False else None
    at = git(path, "ls-remote", "fork", f"refs/heads/{branch}").stdout.split()
    scratch = at[0] if at else ""
    if scratch:
        git(path, "fetch", "-q", "fork", scratch)
        parents = git(path, "rev-list", "--parents", "-n", "1", scratch).stdout.split()[1:]
        if set(parents) != {head, base}:
            scratch = ""
    if not scratch:
        git(path, "checkout", "-q", "-B", branch, head)
        m = git(path, "merge", "--no-edit", "-q", base)
        if m.returncode != 0:
            files = git(path, "diff", "--name-only", "--diff-filter=U").stdout.split()
            git(path, "merge", "--abort")
            print(f"does not merge with upstream main {base[:9]}: {', '.join(files[:8])}")
            return 1
        scratch = git(path, "rev-parse", "HEAD").stdout.strip()
        if git(path, "push", "-q", "--force", "fork", f"{scratch}:refs/heads/{branch}").returncode != 0:
            print("cannot push the scratch branch to the fork")
            return 1
    print(f"scratch {scratch[:9]} = {head[:9]} + upstream main {base[:9]} on fork {branch}")
    for line in scan(git(path, "diff", "--unified=0", f"{base}...{head}").stdout):
        print(f"for the reviewer: {line}")
    F = Facts(cfg)
    pending = False
    for wf, name in WORKFLOWS:
        state = F.fork_ci(branch, scratch, name)
        if state is None:
            print(f"{name}: cannot be read")
            return 2
        if state == "none":
            sh(["gh", "workflow", "run", wf, "-R", cfg["repos"]["fork"], "--ref", branch])
            print(f"{name}: dispatched")
            pending = True
        elif state == "pending":
            print(f"{name}: running")
            pending = True
        elif state == "failure":
            print(f"{name}: FAILED at {scratch[:9]}")
            ok = False
        else:
            print(f"{name}: green at {scratch[:9]}")
    return 1 if not ok else 2 if pending else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
