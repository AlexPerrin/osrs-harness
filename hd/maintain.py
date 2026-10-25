"""The repo's own upkeep, harness-internal work that needs no approval (the tick's last step). Everything is decided on
git facts; nothing is recorded but the events.

  run(idx, dry_run)   the actions taken (or, dry run, the ones due), each also a `maintain` event:
    1. `.claude/worktrees` is listed in `.git/info/exclude`
    2. when the only files that differ from HEAD are change-store files (harness/changes/), one pathspec-only commit
       records them (author Alex Perrin, Claude co-author line), on the harness live target branch
    3. while no agent run is alive: worktrees under `.claude/worktrees/` whose branch is merged into the live target and
       that are clean are removed, then the local branches merged into it (a branch a worktree has is never deleted)
  stale_holds(idx)    the holds nothing will clear: a hold on a finished change, a dep naming no change; the tick caches
                      them (`view/stale`) for `hd status`

The repo is the one that holds the change store (HD_MAINTAIN_REPO overrides it for tests); any other is left alone."""
import os
import subprocess

from . import HD_HOME, agents, changes_dir, events, policy, store
from .ship import AUTHOR, TRAILER

WORKTREES = ".claude/worktrees"


def _git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)


def _emit(out, action, detail):
    events.emit("maintain", action=action, detail=detail)
    out.append(f"{action}: {detail}")


def _ignore_worktrees(repo, dry_run, out):
    p = _git(repo, "rev-parse", "--path-format=absolute", "--git-path", "info/exclude").stdout.strip()
    if not p:
        return
    try:
        with open(p) as f:
            if {WORKTREES, WORKTREES + "/"} & set(f.read().splitlines()):
                return
    except OSError:
        pass
    if dry_run:
        out.append(f"ignore-worktrees: {WORKTREES} into {p} [dry run]")
        return
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a") as f:
        f.write(WORKTREES + "\n")
    _emit(out, "ignore-worktrees", f"{WORKTREES} in {p}")


def _commit_store(repo, dry_run, out):
    rel = os.path.relpath(changes_dir(), repo)
    if rel.startswith("..") or _git(repo, "branch", "--show-current").stdout.strip() != policy.live_target("harness"):
        return
    lines = _git(repo, "status", "--porcelain", "--untracked-files=all").stdout.splitlines()
    paths = [line[3:].strip('"') for line in lines]
    if not paths or any(not p.startswith(rel + "/") for p in paths):
        return
    if dry_run:
        out.append(f"commit-store: {len(paths)} change-store files [dry run]")
        return
    if _git(repo, "add", "--", rel).returncode != 0:
        return
    msg = f"harness: record the change store ({len(paths)} files)\n\n" + "\n".join(paths) + f"\n\n{TRAILER}"
    if _git(repo, "commit", "-q", f"--author={AUTHOR}", "-m", msg, "--", rel).returncode == 0:
        _emit(out, "commit-store", f"{len(paths)} files: " + ", ".join(os.path.basename(p) for p in paths[:6]))


def _worktrees(repo):
    """[(path, branch or None, head)] of the linked worktrees under `.claude/worktrees/`."""
    out, cur = [], {}
    for line in _git(repo, "worktree", "list", "--porcelain").stdout.splitlines() + [""]:
        if line:
            k, _, v = line.partition(" ")
            cur[k] = v
            continue
        if f"/{WORKTREES}/" in cur.get("worktree", ""):
            out.append((cur["worktree"], cur.get("branch", "").removeprefix("refs/heads/") or None, cur.get("HEAD")))
        cur = {}
    return out


def _tidy(repo, dry_run, out):
    target = policy.live_target("harness")
    if agents.running() or _git(repo, "rev-parse", "-q", "--verify", target).returncode != 0:
        return
    for path, branch, head in _worktrees(repo):
        merged = _git(repo, "merge-base", "--is-ancestor", branch or head, target).returncode == 0
        clean = not _git(path, "status", "--porcelain", "--untracked-files=all").stdout.strip()
        if not (merged and clean):
            continue
        if dry_run:
            out.append(f"remove-worktree: {path} [dry run]")
        elif _git(repo, "worktree", "remove", path).returncode == 0:
            _emit(out, "remove-worktree", f"{path} ({branch or 'detached'}) is merged into {target} and clean")
    held = {b for _, b, _ in _worktrees(repo)}
    here = _git(repo, "branch", "--show-current").stdout.strip()
    for name in _git(repo, "branch", "--format=%(refname:short)", "--merged", target).stdout.split():
        if name in (target, here) or name in held:
            continue
        if dry_run:
            out.append(f"delete-branch: {name} [dry run]")
        elif _git(repo, "branch", "-d", name).returncode == 0:
            _emit(out, "delete-branch", f"{name} is merged into {target}")


def stale_holds(idx):
    """[text] for the holds nothing will clear on its own."""
    out = []
    for slug, ch in idx.items():
        if ch.hold and ch.stage == ch.terminal:
            out.append(f"{slug}: {ch.hold} hold on a finished change ({ch.stage})")
        out += [f"{slug}: waits for {d}, which is no change" for d in ch.get("deps") or [] if d not in idx]
    return out


def run(idx, dry_run=False, repo=None):
    repo = repo or os.environ.get("HD_MAINTAIN_REPO") or HD_HOME
    out = []
    if os.path.relpath(changes_dir(), repo).startswith(".."):
        return out   # only the repo that holds the change store is maintained
    for step in (_ignore_worktrees, _commit_store, _tidy):
        step(repo, dry_run, out)
    store.rec_save("view", "stale", {"holds": stale_holds(idx)})
    return out
