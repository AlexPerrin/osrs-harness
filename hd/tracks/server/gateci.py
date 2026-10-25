"""The gate's build evidence (`hd gate-ci <slug>`, BR-S7): the handed-over commit merged with current upstream main in a
scratch clone, pushed to the fork's `gate/<slug>` scratch branch (a fork action: no approval), CI dispatched there and
its conclusion observed. Nothing about the change's own branch moves and no push is needed for the gate to start: the
commit is read from the dev's clone (`repo`).

Steps, each an observed fact, so a re-run resumes at the first one that is not true:
  1 scratch clone has the commit and upstream main      3 the scratch branch is on the fork at the merge commit
  2 the merge is clean (else result `conflict`)         4 a CI run and a Formatting run exist at that commit, then their conclusions

The result is the local file `gate-ci.json` in the change's evidence dir: {commit, upstream_main, scratch, result
(success|failure|pending|conflict: the CI workflow), format (success|failure: the Formatting workflow), findings}. `findings` are the machine-found defects of the net diff against
upstream main (a test file, an added comment line: upstream AGENTS.md); the gate record lists them with its own.
`hd gate PASS` needs result and format `success` at the commit. The dispatched workflows and the run names that stand for
the upstream checks are the policy's `tracks.server.ci_equivalence`. A new commit voids the file (the commit is its key).

  run(ch, obs, git, gh, wait, poll, sleep) -> (rc, lines)   rc 0 success, 1 failure/conflict, 2 still running (no wait)
  scan(diff) -> [finding]                                     the diff scan alone
"""
import json
import os
import re
import subprocess
import time

from ... import fork_clone, policy, state_dir
from ...util import atomic_write
from ..base import evidence_path, sync_evidence
from . import qa

TEST_PATH = re.compile(r"(^|/)src/(test|androidTest)/|(^|/)[^/]*Tests?\.kt$")
COMMENT = re.compile(r"^\+\s*(//|/\*|\*(\s|/|$))")
ENV = {"GIT_AUTHOR_NAME": "Alex Perrin", "GIT_AUTHOR_EMAIL": "44126061+AlexPerrin@users.noreply.github.com",
       "GIT_COMMITTER_NAME": "Alex Perrin", "GIT_COMMITTER_EMAIL": "44126061+AlexPerrin@users.noreply.github.com"}


def scan(diff):
    """Machine-found style findings in a unified diff (`git diff --unified=0`): added test files and added comment lines."""
    out, path, added = [], None, set()
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            path = line.rsplit(" b/", 1)[-1]
        elif line.startswith("new file mode") and path and TEST_PATH.search(path):
            out.append(f"added test file {path}")
        elif line.startswith("+") and not line.startswith("+++") and path and path.endswith((".kt", ".kts", ".java")) \
                and COMMENT.match(line):
            key = (path, line[1:].strip())
            if key not in added:
                added.add(key)
                out.append(f"added comment in {path}: {line[1:].strip()[:100]}")
    if len(out) > 40:
        out = out[:40] + [f"... and {len(out) - 40} more"]
    return out


def _git(repo, *args, git="git"):
    return subprocess.run([git, "-C", repo, *args], capture_output=True, text=True, env=dict(os.environ, **ENV))


def _must(r, what):
    if r.returncode != 0:
        raise RuntimeError(f"{what}: {(r.stderr or r.stdout).strip()[-300:]}")
    return r.stdout.strip()


def result_path(ch):
    return os.path.join(evidence_path(ch), qa.CI_FILE)


def _save(ch, data):
    atomic_write(result_path(ch), json.dumps(data, indent=1, sort_keys=True) + "\n")
    return data


def _scratch(ch, git):
    """The scratch clone (created once under the state dir): remotes `fork` and `upstream` as the push clone has them."""
    base = fork_clone()
    path = os.path.join(state_dir(), "gates", ch["slug"], "or")
    if not os.path.isdir(os.path.join(path, ".git")):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        _must(subprocess.run([git, "clone", "-q", "--shared", "--no-checkout", base, path], capture_output=True, text=True),
              "clone")
        rp = policy.repos()
        for name, remote in (("fork", rp.get("fork_remote", "fork")), ("upstream", rp.get("upstream_remote", "origin"))):
            url = _must(_git(base, "remote", "get-url", remote, git=git), f"remote {remote} of the push clone")
            _git(path, "remote", "remove", name, git=git)
            _must(_git(path, "remote", "add", name, url, git=git), f"add remote {name}")
    return path


def run(ch, obs, git="git", gh=None, wait=True, poll=30, sleep=time.sleep):
    gh = gh or getattr(obs, "gh", "gh")
    commit, slug = ch.get("commit"), ch["slug"]
    if not commit:
        return 1, ["no hand-over: the change has no commit"]
    sync_evidence(ch)
    branch = f"gate/{slug}"
    lines = []
    prev = qa.read_ci(ch)
    try:
        path = _scratch(ch, git)
        main = ""
        _must(_git(path, "fetch", "-q", "upstream", "main", git=git), "fetch upstream main")
        main = _must(_git(path, "rev-parse", "refs/remotes/upstream/main", git=git), "upstream main")
        if prev.get("commit") == commit and prev.get("upstream_main") == main and prev.get("scratch"):
            data = dict(prev)
            lines.append(f"resume: scratch {data['scratch'][:9]} (commit {commit[:9]} + upstream main {main[:9]})")
        else:
            src = ch.get("repo") or fork_clone()
            r = _git(path, "fetch", "-q", src, commit, git=git)
            if r.returncode != 0:
                r = _git(path, "fetch", "-q", src, f"refs/heads/{ch['branch']}", git=git)
            _must(r, f"fetch {commit[:9]} from {src}")
            _must(_git(path, "cat-file", "-e", f"{commit}^{{commit}}", git=git), f"commit {commit[:9]} not in {src}")
            _must(_git(path, "checkout", "-q", "-B", branch, commit, git=git), "checkout")
            lines.append(f"commit {commit[:9]} read from {src}; upstream main {main[:9]}")
            m = _git(path, "merge", "--no-edit", "-q", "refs/remotes/upstream/main", git=git)
            if m.returncode != 0:
                files = _git(path, "diff", "--name-only", "--diff-filter=U", git=git).stdout.split()
                _git(path, "merge", "--abort", git=git)
                data = _save(ch, {"commit": commit, "upstream_main": main, "result": "conflict",
                                  "findings": [f"does not merge with upstream main {main[:9]}: " + ", ".join(files[:8])]})
                return 1, lines + [f"FAIL: {data['findings'][0]}"]
            scratch = _must(_git(path, "rev-parse", "HEAD", git=git), "scratch head")
            diff = _git(path, "diff", "--unified=0", "refs/remotes/upstream/main...%s" % commit, git=git).stdout
            data = {"commit": commit, "upstream_main": main, "scratch": scratch, "result": "pending", "findings": scan(diff)}
            _must(_git(path, "push", "-q", "--force", "fork", f"{scratch}:refs/heads/{branch}", git=git), "push the scratch branch")
            lines.append(f"scratch {scratch[:9]} pushed to fork {branch}")
            _save(ch, data)
        scratch = data["scratch"]
        eq = policy.track("server").get("ci_equivalence") or {}
        flows = (("result", eq.get("fork_workflow", "ci.yml"), eq.get("fork_workflow_name", "CI")),
                 ("format", eq.get("format_workflow", "Formatting"), eq.get("format_workflow_name", "Formatting")))
        states = {}
        for key, workflow, name in flows:
            states[key] = obs.fork_ci(branch, scratch, name)
            if states[key] is None:
                raise RuntimeError(f"{name} could not be read (gh failed)")
            if states[key] == "none":
                _must(subprocess.run([gh, "workflow", "run", workflow, "-R", policy.repos()["fork"], "--ref", branch],
                                     capture_output=True, text=True), f"dispatch {workflow}")
                lines.append(f"{name} dispatched ({workflow})")
        while any(st in ("none", "pending") for st in states.values()):
            if not wait:
                return 2, lines + ["CI still running at the scratch commit: run `hd gate-ci` again"]
            sleep(poll)
            obs.reset()
            for key, _, name in flows:
                states[key] = obs.fork_ci(branch, scratch, name)
                if states[key] is None:
                    raise RuntimeError(f"{name} could not be read (gh failed)")
        for key, _, name in flows:
            data[key] = "success" if states[key] == "success" else "failure"
            lines.append(f"{name} {data[key]} at {scratch[:9]}")
        _save(ch, data)
        for f in data["findings"]:
            lines.append(f"finding: {f}")
        return (0 if all(st == "success" for st in states.values()) else 1), lines
    except RuntimeError as e:
        return 1, lines + [f"gate-ci stopped: {e}"]
