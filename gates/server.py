#!/usr/bin/env python3
"""The server gate (ARCHITECTURE 4): gates/server.py <slug> <head> <base> <evidence>. Exit 0 ok, 1 fail, 2 pending.

  1. the evidence dir holds the accuracy spec (accuracy*.md); the PR texts are the publish steps' concern; every
     custom gameval id is free in upstream main, the train and the other open dev heads (gameval_ids.py); no commit
     not yet on upstream main or the PR branch carries a Claude-Session trailer
  2. the net diff <base>...<head> scanned: added test files and comment lines are printed for the reviewer; a module
     whose main sources gain a call of the item-moving API (MOVES) with no test source of that module added or changed
     fails (upstream AGENTS.md: a dupe test for every flow that moves items; skill dupe-check), each flow named
  3. a change whose PR is at <head>: GitHub's own merge state and the checks on the PR head (no scratch merge); else
     the scratch merge <head> + upstream main (<base>) in state/gates/<slug>/or, pushed to the fork's gate/<slug>; the
     merge commit on the fork with those two parents is reused
  4. the fork's CI and Formatting workflows at the scratch commit: dispatched when absent, pending while they run, ok
     when both are green
"""
import glob
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hd import steps, store  # noqa: E402
from hd.facts import Facts, sh  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gameval_ids  # noqa: E402

WORKFLOWS = (("ci.yml", "CI"), ("Formatting", "Formatting"))
TEST_PATH = re.compile(r"(^|/)src/(test|androidTest)/|(^|/)[^/]*Tests?\.kt$")
# the fork's item-moving API: api/invtx, ProtectedAccess, ObjRepository (ground), the shop operations
MOVES = re.compile(r"\b(inv(Add|Del|Transfer|Move|Replace|Swap|TakeFee|Transaction|Drop|Equip|Sell)[A-Za-z]*|wornUnequip"
                   r"|shopBuy|objRepo\.(add|del))\(")
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


def dupes(diff):
    """(lines for the reviewer, the modules whose added main lines move items with no test source added or changed)."""
    flows, tested, path = {}, set(), None
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            path = line.rsplit(" b/", 1)[-1]
            if "/src/test/" in path:
                tested.add(path.split("/src/test/")[0])
        elif line.startswith("+") and not line.startswith("+++") and path and "/src/main/" in path \
                and path.endswith((".kt", ".java")) and not COMMENT.match(line):
            flows.setdefault(path, set()).update(m.group(1) for m in MOVES.finditer(line))
    out, missing = [], set()
    for p, calls in sorted((p, c) for p, c in flows.items() if c):
        mod = p.split("/src/main/")[0]
        if mod not in tested:
            missing.add(mod)
        out.append(f"item flow in {p}: {', '.join(sorted(calls))} ({'dupe tests changed' if mod in tested else 'NO dupe test'})")
    return out, sorted(missing)


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


def session_tagged(repo, head, *known):
    known = [k for k in known if k and git(repo, "rev-parse", "-q", "--verify", k).returncode == 0]
    log = git(repo, "log", "--format=%H%x00%B%x01", head, "--not", *known).stdout
    return [c.strip()[:9] for c in log.split("\x01") if "\nClaude-Session:" in c]


def main(slug, head, base, ev):
    cfg = store.config()
    if not glob.glob(os.path.join(ev, "accuracy*.md")):
        print("missing accuracy*.md in the evidence dir")
        return 1
    fork = os.path.expanduser(cfg["paths"]["fork"])
    if gameval_ids.check(fork, head, slug):   # an id another branch going live already holds fails here, not in the train
        return 1
    F = Facts(cfg)
    ch = next((c for c in store.changes() if c["slug"] == slug), None)
    tagged = session_tagged(fork, head, "origin/main", f"fork/{steps.public_branch(ch)}" if ch else "")
    if tagged:   # upstream is never force-pushed: the trailer would stay public
        print(f"commits with a Claude-Session trailer (reword before the push): {', '.join(tagged)}")
        return 1
    diff = git(fork, "diff", "--unified=0", f"{base}...{head}")
    if diff.returncode != 0:
        print(f"cannot diff {base[:9]}...{head[:9]} in the fork clone")
        return 2
    flows, missing = dupes(diff.stdout)
    for line in scan(diff.stdout) + flows:
        print(f"for the reviewer: {line}")
    if missing:
        print(f"moves items with no dupe test in the same module (skill dupe-check): {', '.join(missing)}")
        return 1
    pr = F.pr(steps.public_branch(ch)) if ch else None
    if pr and pr.get("head") == head and pr["state"] == "open":   # GitHub already merges and checks the PR head
        if pr.get("mergeable") == "CONFLICTING":
            print(f"PR #{pr['number']} does not merge with upstream main")
            return 1
        if pr.get("mergeable") != "MERGEABLE":
            print(f"PR #{pr['number']}: merge state not computed yet")
            return 2
        checks = F.pr_checks(pr["number"], head)
        print(f"PR #{pr['number']} mergeable; upstream checks at {head[:9]}: {checks}")
        return {"success": 0, "failure": 1}.get(checks, 2)
    branch = f"gate/{slug}"
    path = scratch_clone(cfg, slug)
    if git(path, "fetch", "-q", "fork", head, f"refs/heads/{branch}").returncode != 0 and git(path, "fetch", "-q", "fork", head).returncode != 0:
        print(f"cannot fetch {head[:9]} from the fork")
        return 2
    git(path, "fetch", "-q", "origin", "main")
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
            return 2
    print(f"scratch {scratch[:9]} = {head[:9]} + upstream main {base[:9]} on fork {branch}")
    ok, pending = True, False
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
