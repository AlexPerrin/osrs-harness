"""The contribution (`hd contribute <slug> --approved <sha>`): the one atomic upstream sequence a change gets after the
gate PASS and the user's yes in chat (docs/PRD.md BR-A4):

  push -> open -> ci -> comment -> ready

  push     the commit is in the PR branch on the fork (fast-forward, or the merge commit the dev built; never a force)
  open     the OpenRune PR exists (a draft when this run creates it)
  ci       the PR's checks are green at exactly that commit; failure stops here, before the comment, the PR stays as it is
  comment  the PR carries this commit's comment (marked `<!-- hd-contribute:<sha12> -->`)
  ready    the PR is out of draft

Every step is an observed fact, so a re-run resumes at the first step that is not true. The approval is bound to the
commit: `--approved` must name the change's current commit, which must carry QA's record (the local file; its verdict
and findings are on the card the user decided on), so a resumed run continues only the exact approved commit and a
new commit needs a new QA record and a new yes. The console runs
this after the yes; agents cannot (hooks/deny_publish.py).

  steps(ch, obs)  [(name, done, why)]         the sequence as observed now (also shown in the user's card)
  texts(ch, obs)  {title, body, comment}      PR text: `pr-title.txt`, `pr-body.md`, `pr-comment.md` in the evidence dir,
                                              else pr-texts/<slug>.* (.comment, .update.md) on the fork's docs branch;
                                              no comment file: "Updated to <sha>." (never the hand-over summary)
  run(...)        (rc, lines)                 0 done, 1 stopped (CI red, a refusal, a failed command), 2 CI still running
                                              with wait off
"""
import os
import subprocess
import time

from ... import events, fork_clone, policy, store
from ...util import same_commit, short
from ..base import evidence_path, sync_evidence
from . import qa

STEPS = ("push", "open", "ci", "comment", "ready")


def marker(commit):
    return f"<!-- hd-contribute:{commit[:12]} -->"


def pr_slug(ch):
    """The docs-branch name of the PR text: the branch after its prefix (BR-C1)."""
    b = ch.get("branch") or ""
    return b.split("/", 1)[1] if "/" in b else ch["slug"]


def texts(ch, obs):
    ev = evidence_path(ch)

    def local(name):
        try:
            with open(os.path.join(ev, name)) as f:
                return f.read().strip()
        except OSError:
            return None
    slug = pr_slug(ch)
    title = local("pr-title.txt") or (obs.docs_file(f"pr-texts/{slug}.title") or "").strip() or None
    body = local("pr-body.md") or obs.docs_file(f"pr-texts/{slug}.upstream.body")
    comment = (local("pr-comment.md") or obs.docs_file(f"pr-texts/{slug}.comment")
               or obs.docs_file(f"pr-texts/{slug}.update.md") or f"Updated to {short(ch.get('commit') or '')}.")
    return {"title": title, "body": body, "comment": comment.strip()}


def _pr(ch, obs):
    return obs.upstream_pr(ch.get("upstream_pr") or ch.get("branch"))


def steps(ch, obs):
    """[(step, done: True|False|None, why)] in order; None = could not be read."""
    commit, branch = ch["commit"], ch["branch"]
    pr = _pr(ch, obs)
    out = []
    pushed = obs.contains("fork", branch, commit)
    out.append(("push", pushed, f"fork {branch} {'contains' if pushed else 'lacks'} {short(commit)}" if pushed is not None
                else "could not read the fork branch"))
    if pr is None:
        return out + [(s, None, "could not read the upstream PR") for s in STEPS[1:]]
    live = bool(pr) and pr.get("state") == "open"
    out.append(("open", live, f"PR #{pr['number']} open" if live else "no open upstream PR"))
    if not live:
        return out + [(s, False, "needs the PR") for s in STEPS[2:]]
    ci = obs.upstream_ci(pr["number"], commit)
    out.append(("ci", {"success": True, "failure": False}.get(ci),
                {"success": "CI green at the commit", "failure": "CI failed at the commit", "pending": "CI running at the commit",
                 "none": "no CI at the commit yet (the PR head is not it, or checks not started)", None: "CI could not be read"}[ci]))
    comments = obs.upstream_pr_reviews(pr["number"])
    posted = None if comments is None else any(marker(commit) in (c.get("body") or "") for c in comments)
    out.append(("comment", posted, "comment posted" if posted else "no comment for this commit yet" if posted is False
                else "could not read the comments"))
    out.append(("ready", not pr.get("draft"), "PR ready for review" if not pr.get("draft") else "PR is a draft"))
    return out


def refusal(ch, approved):
    """Why this contribution cannot start (None = it can): every precondition at once."""
    out = []
    if ch.get("track") != "server" or ch.fork_only:
        out.append("only a server change that is not local/* is contributed upstream")
    if not ch.get("commit"):
        return out + ["the change has no commit"]
    if not approved or not same_commit(approved, ch["commit"]):
        out.append(f"the approval is for {short(approved) or 'no commit'}, the change is at {short(ch['commit'])}: "
                   "approve this commit")
    if qa.gate_state(ch)[0] is None:
        out.append(f"no QA record at {short(ch['commit'])}: the aggregate runs first")
    if ch.hold:
        out.append(f"the change is on a `{ch.hold}` hold: {ch.hold_reason}")
    if ch.stage not in ("contribute", "review"):
        out.append(f"the change is at stage {ch.stage}, not contribute")
    return out


def _sh(argv, what):
    r = subprocess.run(argv, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{what}: {(r.stderr or r.stdout).strip()[-300:]}")
    return r.stdout.strip()


def _do(step, ch, obs, git, gh, tmp):
    rp = policy.repos()
    upstream, clone = rp["upstream"], fork_clone()
    commit, branch = ch["commit"], ch["branch"]
    pr = _pr(ch, obs)
    if step == "push":
        if ch.get("repo"):
            _sh([git, "-C", clone, "fetch", "-q", ch["repo"], commit], f"fetch {short(commit)} from {ch['repo']}")
        _sh([git, "-C", clone, "push", "-q", rp.get("fork_remote", "fork"), f"{commit}:refs/heads/{branch}"],
            "push to the PR branch (never a force: merge the PR head into the branch and hand over again)")
        _sh([git, "-C", clone, "fetch", "-q", rp.get("fork_remote", "fork")], "fetch the fork")
    elif step == "open":
        t = texts(ch, obs)
        if not (t["title"] and t["body"]):
            raise RuntimeError("PR text missing (pr-title.txt and pr-body.md in the evidence dir)")
        body = os.path.join(tmp, "body.md")
        with open(body, "w") as f:
            f.write(t["body"].rstrip() + "\n")
        url = _sh([gh, "pr", "create", "-R", upstream, "--draft", "--base", "main", "--head",
                   f"{rp['fork'].split('/')[0]}:{branch}", "--title", t["title"], "--body-file", body], "open the PR")
        number = url.rstrip("/").rsplit("/", 1)[-1]
        if number.isdigit():
            ch["upstream_pr"] = int(number)
            store.add_log(ch, f"contribute: upstream PR #{number} opened as a draft")
            store.save(ch)
    elif step == "comment":
        f = os.path.join(tmp, "comment.md")
        with open(f, "w") as fh:
            fh.write(texts(ch, obs)["comment"] + "\n\n" + marker(commit) + "\n")
        _sh([gh, "pr", "comment", str(pr["number"]), "-R", upstream, "--body-file", f], "comment")
    elif step == "ready":
        _sh([gh, "pr", "ready", str(pr["number"]), "-R", upstream], "move the PR out of draft")


def run(ch, obs, approved, git="git", gh="gh", wait=True, poll=30, sleep=time.sleep, tmp=None):
    import tempfile
    sync_evidence(ch)
    lines = []
    with tempfile.TemporaryDirectory(prefix="hd-contribute-") as td:
        while True:   # every pass ends in a return or one observed step more; CI waits on the fact
            obs.reset()
            ch = store.load(ch["slug"]) if store.exists(ch["slug"]) else ch
            why = refusal(ch, approved)   # the approval is for one commit: a hand-over during the CI wait stops the run
            if why:
                return 1, lines + ["refused: " + w for w in why]
            seq = steps(ch, obs)
            todo = next(((n, d, w) for n, d, w in seq if d is not True), None)
            if todo is None:
                events.emit("contribute", change=ch["slug"], commit=ch["commit"], result="done")
                return 0, lines + [f"done: {short(ch['commit'])} contributed (the PR is ready; merge is observed afterward)"]
            name, done, why = todo
            if name == "ci":
                if done is False:
                    events.emit("contribute", change=ch["slug"], commit=ch["commit"], result="ci-failed")
                    return 1, lines + [f"stopped before the comment: {why}; the PR stays as it is"]
                if why.startswith("CI could not"):
                    return 1, lines + [f"stopped: {why}"]
                if not wait:
                    return 2, lines + [f"waiting: {why}; run `hd contribute` again"]
                lines.append(f"waiting: {why}")
                sleep(poll)
                continue
            if done is None:
                return 1, lines + [f"stopped: {name}: {why}"]
            lines.append(f"{name}: {why}; doing it")
            try:
                _do(name, ch, obs, git, gh, td)
            except RuntimeError as e:
                events.emit("contribute", change=ch["slug"], commit=ch["commit"], result="stopped", step=name)
                return 1, lines + [f"stopped at {name}: {e}"]
            obs.reset()
            again = next((d for n, d, _ in steps(ch, obs) if n == name), None)
            if again is not True and name != "ci":
                return 1, lines + [f"stopped at {name}: the action ran but the fact is not observed yet ({again})"]
