"""The server track's view of GitHub: the PR bucket (an upstream PR's state, head, checks, comments and reviews) and
the fork's CI. Mixed into the observer the core uses (`hd.tracks.Observer`, `hd.tracks.FakeObserver`), so the core
never imports it; only the server track calls these.

CI equivalence (policy `tracks.server.ci_equivalence`): the checks an upstream PR must show green
(`upstream_required`, matched by substring; `upstream_advisory` ones are shown, never required) are covered, for the
gate, by one green run of the fork's workflow `fork_workflow_name` on the gate's scratch branch.

  GitHub          the real methods (gh)       fork_ci, upstream_ci, upstream_pr, upstream_pr_reviews
  FakeGitHub      tests: facts `ci`, `upstream_ci`, `upstream_prs`, `reviews`
  rollup_state    a gh statusCheckRollup folded to 'success' | 'failure' | 'pending' | 'none'
"""
from ... import policy


def ci_equivalence():
    return policy.track("server").get("ci_equivalence") or {}


def rollup_state(checks):
    """Fold a gh statusCheckRollup (check runs: status/conclusion/name; statuses: state/context) to
    'success' | 'failure' | 'pending' | 'none'."""
    seen, states = [], []
    eq = ci_equivalence()
    advisory = [a.lower() for a in eq.get("upstream_advisory") or []]
    required = [r.lower() for r in eq.get("upstream_required") or []]
    checks = [c for c in checks if not any(a in (c.get("name") or c.get("context") or "").lower() for a in advisory)]
    for c in checks:
        name = (c.get("name") or c.get("context") or "").lower()
        concl = str(c.get("conclusion") or c.get("state") or "").upper()
        if c.get("status") not in (None, "COMPLETED") or concl in ("", "PENDING", "EXPECTED"):
            states.append("pending")
        elif concl in ("SUCCESS", "NEUTRAL", "SKIPPED"):
            states.append("success")
        else:
            states.append("failure")
        seen.append(name)
    if not checks:
        return "none"
    if "failure" in states:
        return "failure"
    if "pending" in states or not all(any(r in n for n in seen) for r in required):
        return "pending"
    return "success"



def _fork_repo():
    return policy.repos().get("fork", "AlexPerrin/OpenRune-Server")


def _upstream_repo():
    return policy.repos().get("upstream", "OpenRune/OpenRune-Server")


class GitHub:
    """Methods mixed into the core observer (it provides `_gh_json` and `_m`)."""

    def fork_ci(self, branch, sha):
        """'success' | 'failure' | 'pending' | 'none' (no run at the sha) | None (gh failed)."""
        def f():
            runs = self._gh_json(["run", "list", "-R", _fork_repo(), "--branch", branch, "--limit", "20", "--json",
                                  "headSha,conclusion,status,workflowName,url"])
            if runs is None:
                return None
            at = [r for r in runs if r.get("headSha") == sha and r.get("workflowName") == ci_equivalence().get("fork_workflow_name", "CI")]
            if not at:
                return "none"
            c = at[0].get("conclusion")
            if c == "success":
                return "success"
            if c in ("failure", "cancelled", "timed_out", "startup_failure"):
                return "failure"
            return "pending"
        return self._m(("ci", branch, sha), f)

    def upstream_ci(self, number, sha):
        """The upstream PR's checks at its head `sha`: 'success' | 'failure' | 'pending' | 'none' (PR head is not `sha`,
        or no checks yet) | None (gh failed). Success needs every check green, with build & boot and gameval-conflicts
        among them (policy ci_equivalence)."""
        def f():
            p = self._gh_json(["pr", "view", str(number), "-R", _upstream_repo(), "--json", "headRefOid,statusCheckRollup"])
            if p is None:
                return None
            if p.get("headRefOid") != sha:
                return "none"
            return rollup_state(p.get("statusCheckRollup") or [])
        return self._m(("upstream_ci", str(number), sha), f)

    def upstream_pr(self, number_or_branch):
        """{number, url, state (open|closed), draft, head, merged, title} or {} when none, None when gh failed."""
        def f():
            if isinstance(number_or_branch, int) or str(number_or_branch).isdigit():
                p = self._gh_json(["pr", "view", str(number_or_branch), "-R", _upstream_repo(), "--json",
                                   "number,url,state,isDraft,headRefOid,mergedAt,title,headRefName,reviewRequests"])
                if p is None:
                    return None
                prs = [p]
            else:
                # gh's --head takes a bare branch name (an `owner:branch` form finds nothing): filter on the fork owner here
                owner = _fork_repo().split("/")[0]
                prs = self._gh_json(["pr", "list", "-R", _upstream_repo(), "--head", str(number_or_branch),
                                     "--state", "all", "--limit", "10", "--json",
                                     "number,url,state,isDraft,headRefOid,mergedAt,title,headRefName,headRepositoryOwner,reviewRequests"])
                if prs is not None:
                    prs = [p for p in prs if (p.get("headRepositoryOwner") or {}).get("login") == owner]
                if prs is None:
                    return None
                prs = [p for p in prs if p.get("state") == "OPEN"] or [p for p in prs if p.get("mergedAt")] or prs
            if not prs:
                return {}
            p = prs[0]
            return {"number": p["number"], "url": p.get("url"), "state": str(p.get("state", "")).lower(),
                    "draft": bool(p.get("isDraft")), "head": p.get("headRefOid"), "merged": bool(p.get("mergedAt")),
                    "title": p.get("title"), "branch": p.get("headRefName"),
                    "reviewers": [r.get("login") or r.get("name") for r in p.get("reviewRequests") or []]}
        return self._m(("upstream_pr", str(number_or_branch)), f)

    def upstream_pr_reviews(self, number):
        """Comments and reviews on an upstream PR, oldest first: [{id, author, body, at, kind}]; None when gh failed."""
        def f():
            p = self._gh_json(["pr", "view", str(number), "-R", _upstream_repo(), "--json", "comments,reviews"])
            if p is None:
                return None
            out = []
            for c in p.get("comments") or []:
                out.append({"id": c.get("id"), "author": (c.get("author") or {}).get("login"), "body": c.get("body", ""),
                            "at": c.get("createdAt"), "kind": "comment", "url": c.get("url")})
            for r in p.get("reviews") or []:
                out.append({"id": r.get("id"), "author": (r.get("author") or {}).get("login"), "body": r.get("body", ""),
                            "at": r.get("submittedAt"), "kind": f"review:{str(r.get('state', '')).lower()}"})
            return sorted(out, key=lambda x: x.get("at") or "")
        return self._m(("reviews", number), f)



class FakeGitHub:
    """Methods mixed into the core fake observer."""

    def fork_ci(self, branch, sha):
        return self.f.get("ci", {}).get((branch, sha), "none")

    def upstream_ci(self, number, sha):
        return self.f.get("upstream_ci", {}).get((number, sha), "none")

    def upstream_pr(self, key):
        u = self.f.get("upstream_prs", {})
        return u.get(key, u.get(str(key), {}))

    def upstream_pr_reviews(self, number):
        return self.f.get("reviews", {}).get(number, [])

