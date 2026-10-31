"""The facts (P1): git, GitHub, docker and the process table, read fresh by each pass and memoised for it. Every method
returns None when the fact could not be read; a None stops the step that needs it and is never read as False.
Tests replace `Facts` with a fake of the same methods.
"""
import json
import os
import subprocess


def sh(args, cwd=None, env=None, timeout=600):
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                              env=dict(os.environ, **(env or {})))
    except (OSError, subprocess.TimeoutExpired):
        return None


class Facts:
    def __init__(self, cfg):
        self.cfg = cfg
        self._memo = {}

    def _m(self, key, f):
        if key not in self._memo:
            self._memo[key] = f()
        return self._memo[key]

    # --- git ---------------------------------------------------------------------------------------------------------

    def git(self, repo, *args):
        return sh(["git", "-C", repo, *args])

    def fetch(self, repo, remote):
        """True once the remote was fetched in this pass; False when the fetch failed (its refs are then unknown)."""
        return self._m(("fetch", repo, remote), lambda: (r := self.git(repo, "fetch", "-q", "--prune", remote)) is not None
                       and r.returncode == 0)

    def remotes(self, repo):
        def f():
            r = self.git(repo, "remote")
            return r.stdout.split() if r is not None and r.returncode == 0 else []
        return self._m(("remotes", repo), f)

    def rev(self, repo, ref):
        """The sha of `ref`, '' when the ref does not exist, None when it cannot be read (a remote ref whose fetch failed)."""
        remote = ref.split("/", 1)[0]
        if remote in self.remotes(repo) and not self.fetch(repo, remote):
            return None
        r = self.git(repo, "rev-parse", "-q", "--verify", f"{ref}^{{commit}}")
        if r is None:
            return None
        return r.stdout.strip() if r.returncode == 0 else ""

    def contains(self, repo, ref, sha):
        """True when `ref` contains `sha`; None when either cannot be resolved."""
        tip = self.rev(repo, ref) if not self._is_sha(ref) else ref
        if not tip or not sha:
            return None if tip is None else False
        r = self.git(repo, "merge-base", "--is-ancestor", sha, tip)
        if r is None or r.returncode not in (0, 1):
            return None
        return r.returncode == 0

    @staticmethod
    def _is_sha(s):
        return len(s or "") == 40 and all(c in "0123456789abcdef" for c in s)

    # --- GitHub ------------------------------------------------------------------------------------------------------

    def gh(self, *args):
        def f():
            r = sh(["gh", *args])
            if r is None or r.returncode != 0:
                return None
            try:
                return json.loads(r.stdout) if r.stdout.strip() else {}
            except ValueError:
                return None
        return self._m(("gh", args), f)

    def pr(self, branch):
        """The upstream PR whose head is the fork's `branch`: {number, state, draft, head, merged, branch, mergeable, title, body}, {} when none,
        None when gh failed."""
        owner = self.cfg["repos"]["fork"].split("/")[0]
        prs = self.gh("pr", "list", "-R", self.cfg["repos"]["upstream"], "--head", branch, "--state", "all", "--limit",
                      "10", "--json", "number,state,isDraft,headRefOid,mergedAt,headRefName,headRepositoryOwner,mergeable,title,body")
        if prs is None:
            return None
        prs = [p for p in prs if (p.get("headRepositoryOwner") or {}).get("login") == owner]
        prs = [p for p in prs if p.get("state") == "OPEN"] or [p for p in prs if p.get("mergedAt")] or prs
        if not prs:
            return {}
        p = prs[0]
        return {"number": p["number"], "state": p["state"].lower(), "draft": bool(p.get("isDraft")),
                "head": p.get("headRefOid"), "merged": bool(p.get("mergedAt")), "branch": p.get("headRefName"),
                "mergeable": p.get("mergeable"), "title": p.get("title"), "body": p.get("body")}

    def pr_checks(self, number, sha):
        """'success' | 'failure' | 'pending' | 'none' (the PR head is not `sha`, or no checks yet) | None."""
        p = self.gh("pr", "view", str(number), "-R", self.cfg["repos"]["upstream"], "--json", "headRefOid,statusCheckRollup")
        if p is None:
            return None
        if p.get("headRefOid") != sha:
            return "none"
        return rollup(p.get("statusCheckRollup") or [])

    def pr_comments(self, number):
        """Comments and reviews, oldest first: [{id, author, bot, body, at, kind}]; None when gh failed."""
        p = self.gh("pr", "view", str(number), "-R", self.cfg["repos"]["upstream"], "--json", "comments,reviews")
        if p is None:
            return None
        out = [{"id": c.get("id"), "author": (c.get("author") or {}).get("login"), "bot": bool((c.get("author") or {}).get("is_bot")),
                "body": c.get("body") or "", "at": c.get("createdAt"), "kind": "comment"} for c in p.get("comments") or []]
        out += [{"id": r.get("id"), "author": (r.get("author") or {}).get("login"), "bot": bool((r.get("author") or {}).get("is_bot")),
                 "body": r.get("body") or "", "at": r.get("submittedAt"), "kind": f"review:{str(r.get('state', '')).lower()}"}
                for r in p.get("reviews") or []]
        return sorted(out, key=lambda c: c.get("at") or "")

    def fork_ci(self, branch, sha, workflow):
        """The fork workflow's conclusion at `sha` on `branch`: 'success' | 'failure' | 'pending' | 'none' | None."""
        runs = self.gh("run", "list", "-R", self.cfg["repos"]["fork"], "--branch", branch, "--limit", "20", "--json",
                       "headSha,conclusion,status,workflowName")
        if runs is None:
            return None
        at = [r for r in runs if r.get("headSha") == sha and r.get("workflowName") == workflow]
        if not at:
            return "none"
        c = at[0].get("conclusion")
        return "success" if c == "success" else "failure" if c in ("failure", "cancelled", "timed_out", "startup_failure") \
            else "pending"

    def release(self, tag):
        """{tag, assets[]} or {} when none, None when gh failed."""
        r = sh(["gh", "release", "view", tag, "-R", self.cfg["repos"]["client"], "--json", "tagName,assets"])
        if r is None:
            return None
        if r.returncode != 0:
            return {} if "release not found" in (r.stderr or "") else None
        try:
            d = json.loads(r.stdout)
        except ValueError:
            return None
        return {"tag": d.get("tagName"), "assets": [a.get("name") for a in d.get("assets") or []]}

    def gh_ok(self):
        return self._m(("gh_ok",), lambda: (r := sh(["gh", "auth", "status"])) is not None and r.returncode == 0)

    # --- docker and processes ----------------------------------------------------------------------------------------

    def docker_ok(self):
        return self._m(("docker",), lambda: (r := sh(["docker", "info"], timeout=60)) is not None and r.returncode == 0)

    def containers(self):
        """[{name, status}] of every container, None when docker cannot be read."""
        def f():
            r = sh(["docker", "ps", "-a", "--format", "{{.Names}}\t{{.State}}"], timeout=60)
            if r is None or r.returncode != 0:
                return None
            return [dict(zip(("name", "status"), l.split("\t"))) for l in r.stdout.splitlines() if "\t" in l]
        return self._m(("containers",), f)

    def images(self, repo):
        r = sh(["docker", "images", repo, "--format", "{{.Repository}}:{{.Tag}}"], timeout=60)
        return None if r is None or r.returncode != 0 else [l for l in r.stdout.splitlines() if l and ":<none>" not in l]

    def volumes(self):
        r = sh(["docker", "volume", "ls", "-q"], timeout=60)
        return None if r is None or r.returncode != 0 else r.stdout.split()

    @staticmethod
    def proc_start(pid):
        """The start time of `pid` (clock ticks since boot), or None when there is no such process."""
        try:
            with open(f"/proc/{pid}/stat") as f:
                return f.read().rsplit(")", 1)[1].split()[19]
        except (OSError, IndexError):
            return None

    def alive(self, pid, start):
        """The process is the one recorded: same pid and start time (a recycled pid is not alive)."""
        return bool(pid) and self.proc_start(pid) == str(start)


def rollup(checks):
    """A gh statusCheckRollup folded to 'success' | 'failure' | 'pending' | 'none'."""
    if not checks:
        return "none"
    states = []
    for c in checks:
        concl = str(c.get("conclusion") or c.get("state") or "").upper()
        if c.get("status") not in (None, "COMPLETED") or concl in ("", "PENDING", "EXPECTED"):
            states.append("pending")
        elif concl in ("SUCCESS", "NEUTRAL", "SKIPPED"):
            states.append("success")
        else:
            states.append("failure")
    return "failure" if "failure" in states else "pending" if "pending" in states else "success"
