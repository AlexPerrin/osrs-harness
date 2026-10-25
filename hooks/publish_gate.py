#!/usr/bin/env python3
"""PreToolUse hook (Bash), every session: the publish gate (skill server-track, docs/PRD.md BR-A2, BR-A4). The
server track's rules are hd/tracks/server/hooks.py; this entry point parses the command and denies on its answer.

An upstream contribution is bound to a commit twice over:
  - `hd contribute <slug> --approved <sha>` is denied unless QA's record (the local file `gate.md` in the change's
    evidence dir, its verdict and findings on the card the user decided on) exists at exactly the change's commit and
    `<sha>` is that commit: the user's yes in chat is bound to the sha the console types, so a new commit, a record for
    another commit or a missing record stops the run.
  - a direct `gh pr create` against upstream (OpenRune/*, or --head AlexPerrin:<branch>) is denied unless a change on
    that branch has QA's record at the commit the branch is at (fork/<branch> in the fork clone, else the local one).
A client release (`git tag` / `gh release create` with a semver tag) needs qa/client-<version>.md with PASS at the
tagged commit. Fork PRs are not gated. Commands run inside scripts are not visible to this hook; they still go through
the ask rule (github_scope.py).
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hdpaths  # noqa: E402

ROOT = os.environ.get("HD_CLIENT_ROOT") or os.path.expanduser("~/osrs-plugins-reverse")   # the client checkout; CLAUDE_PROJECT_DIR is the harness
CLONE = hdpaths.fork_clone()


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": f"Publish gate: {reason} (skill server-track, the gate record).",
    }}))
    sys.exit(0)


def git(*args):
    r = subprocess.run(["git", "-C", CLONE, *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def release_gate(cmd):
    """Client release gate: tagging or `gh release create` with a semver tag vX.Y.Z[-pre] (https://semver.org;
    the older client-v prefix too) needs qa/client-X.Y.Z[-pre].md with `## Verdict: **PASS**` for the commit
    being tagged (the tag's, else HEAD)."""
    m = re.search(r"\b(?:git\s+tag|gh\s+release\s+create)\b(?:\s+-\S+)*\s+((?:client-)?v([0-9][0-9A-Za-z.\-+]*))(?:\s+([0-9a-f]{7,40}|HEAD|master))?", cmd)
    if not m:
        return
    tag, version, target = m.group(1), m.group(2), m.group(3)
    run = lambda *a: (subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True).stdout or "").strip()
    sha = run("rev-parse", "-q", "--verify", f"refs/tags/{tag}^{{commit}}") or run("rev-parse", target or "HEAD")
    path = os.path.join(ROOT, "qa", f"client-{version}.md")
    if not os.path.isfile(path):
        deny(f"no release record qa/client-{version}.md; client-qa runs the release gate on {sha[:9]} first")
    text = open(path).read()
    commit = re.search(r"^- Commit: `([0-9a-f]{7,40})`", text, re.M)
    verdict = re.search(r"^## Verdict: \*\*(PASS|FAIL)\*\*", text, re.M)
    if not (commit and verdict and verdict.group(1) == "PASS" and sha.startswith(commit.group(1))):
        deny(f"{tag} would tag {sha[:9]}, but qa/client-{version}.md says "
             f"{verdict.group(1) if verdict else 'no verdict'} at {commit.group(1)[:9] if commit else 'no commit'}")
    sys.exit(0)


def main():
    cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
    # Heredoc bodies are file contents (notes, scripts), not commands: a note that mentions `gh pr create` or a
    # release tag must not trip the gates.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import shellparse
    cmd = shellparse.strip_heredocs(cmd)
    release_gate(cmd)
    from hd.tracks.server import hooks as server_hooks   # the server track's rules (hd/tracks/server/hooks.py)
    reason = server_hooks.contribute_deny(cmd)
    if reason:
        deny(reason)
    if not re.search(r"\bgh\s+pr\s+create\b", cmd):
        return
    head = re.search(r"--head[=\s]+[\"']?(?:AlexPerrin:)?([A-Za-z0-9._/-]+)", cmd)
    repo = re.search(r"(?:-R|--repo)[=\s]+[\"']?(?:https?://github\.com/)?([A-Za-z0-9._-]+/[A-Za-z0-9._-]+)", cmd)
    on_fork = bool(repo) and repo.group(1).lower() == "alexperrin/openrune-server"
    upstream = (re.search(r"(?<![A-Za-z0-9_-])OpenRune/OpenRune|github\.com[:/]+OpenRune/", cmd, re.I)
                or (not on_fork and head and re.search(r"--head[=\s]+[\"']?AlexPerrin:", cmd)))
    if on_fork and not re.search(r"(?<![A-Za-z0-9_-])OpenRune/OpenRune", cmd, re.I) or not upstream:
        return  # a fork PR or not an upstream PR
    if not head:
        deny("upstream `gh pr create` needs an explicit --head AlexPerrin:<branch> so its gate record can be checked")
    branch = head.group(1)
    sha = (git("rev-parse", "--verify", "-q", f"refs/remotes/fork/{branch}")
           or git("rev-parse", "--verify", "-q", f"refs/heads/{branch}") or "").strip()
    if not sha:
        deny(f"no branch {branch} on the fork or in the fork clone")
    reason = server_hooks.direct_pr_deny(branch, sha)
    if reason:
        deny(reason)


if __name__ == "__main__":
    main()
