"""The server track's items for the user (BR-A1), from observed facts and QA's local record alone; nothing is recorded,
completion is the observation that removes a card.

  contribution(ch, obs)   the approval card of a change at `contribute`: the exact command `hd contribute <slug>
                          --approved <sha>` (the yes is bound to the sha), QA's verdict, every check line and finding,
                          the PR text, caveats, the diff range, and the sequence's observed steps (a partly run
                          sequence stays listed; the same commit continues without a new ask)
  draft(ch, obs)          a review-fix change is open on a PR that is ready: moving it to draft is asked each time
"""
import os

from ... import HD_HOME, actions, policy
from ..base import evidence_path
from . import contribute, qa


def _caveats(body):
    out, inside = [], False
    for line in (body or "").splitlines():
        if line.startswith("## "):
            inside = line.strip().lower() == "## caveats"
        elif inside and line.startswith("- "):
            out.append(line[2:].strip())
    return out


def _diff(ch, obs):
    mb = obs.merge_base(ch.get("repo") or "fork", f"refs/remotes/{policy.repos().get('upstream_remote', 'origin')}/main",
                        ch["commit"])
    return f"{mb}..{ch['commit']}" if mb else None


def contribution(ch, obs):
    commit = ch["commit"]
    aid = f"{ch['slug']}-contribute-{commit[:7]}"
    t = contribute.texts(ch, obs)
    files = [actions.text_file(aid, "comment", t["comment"])]
    if t["body"]:
        files.append(actions.text_file(aid, "body", t["body"]))
    note = None
    if not (t["title"] and t["body"]) and not ch.get("upstream_pr"):
        note = "PR text missing: pr-title.txt and pr-body.md in the evidence dir (the sequence stops at `open`)"
    verdict, findings = qa.gate_state(ch)
    parsed = qa.read_record(ch) or {}
    checks = [f"{n}: {r} {why}".rstrip() for n, (r, why) in (parsed.get("checks") or {}).items()]
    cmd = ["python3", os.path.join(HD_HOME, "hd.py"), "contribute", ch["slug"], "--approved", commit]
    return {"id": aid, "kind": "upstream", "action": "contribute", "change": ch["slug"], "batch": None, "commit": commit,
            "commands": [cmd], "files": files, "text": {"title": t["title"] or "", "body": t["body"] or "", "comment": t["comment"]},
            "record": qa.record_path(ch), "verdict": verdict, "checks": checks, "findings": findings,
            "diff": _diff(ch, obs), "steps": list(contribute.steps(ch, obs)), "caveats": _caveats(t["body"]), "note": note}


def draft(ch, obs):
    pr = obs.upstream_pr(ch.get("upstream_pr"))
    if not pr or pr.get("state") != "open" or pr.get("draft"):
        return None
    upstream = policy.repos()["upstream"]
    return {"id": f"{ch['slug']}-draft-pr-{pr['number']}", "kind": "upstream", "action": "draft-pr", "change": ch["slug"],
            "batch": None, "commit": ch.get("commit") or "",
            "commands": [["gh", "pr", "ready", str(pr["number"]), "-R", upstream, "--undo"]], "files": [], "text": {},
            "record": None, "checks": [], "findings": [], "diff": None, "steps": [], "caveats": [],
            "note": f"PR #{pr['number']} is ready for review but {ch['slug']} carries an open maintainer finding "
                    f"({ch.get('finding')}): moving it to draft is optional and yours; without it the fix still follows"}
