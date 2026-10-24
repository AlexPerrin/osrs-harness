"""Maintainer findings (BR-S4): a comment or review on a PR whose change reached `review` is filed once as one new
review-fix change, keyed by the comment's or review's id (`finding`), on the same branch and PR; it runs the full
process (dev, gate, approval, contribution). A change already carrying that id means it is filed. The bots and the
fork owner's own comments are not findings; neither is an approval or a dismissal. Only what is newer than the change's
`review_seen` counts; the first scan of a change at `review` sets it (what was said before is not re-filed).

  findings(pr_comments, owner)   [comment]       what counts as a maintainer finding, in order
  file(idx, obs)                 [slug]          create the missing review-fix changes (the tick's `findings` step)
  open_for(pr_number, idx)       [change]        review-fix changes on a PR that have not reached `review` yet
"""
import re

from ... import events, policy, store
from ...util import iso

SKIP_KINDS = ("review:approved", "review:dismissed", "review:pending")


def findings(comments, owner):
    out = []
    for c in comments or []:
        who = str(c.get("author") or "")
        if not c.get("id") or not (c.get("body") or "").strip() or who.lower() == owner.lower() or who.endswith("[bot]"):
            continue
        if c.get("kind") in SKIP_KINDS:
            continue
        out.append(c)
    return out


def open_for(pr_number, idx):
    return [c for c in idx.values() if c.get("finding") and c.get("upstream_pr") == pr_number and not c.reached("review")]


def _slug(parent, fid):
    tail = re.sub(r"[^a-z0-9]", "", str(fid).lower())[-6:] or "x"
    return f"{parent[:42]}-rf-{tail}"


def file(idx, obs):
    """File each unseen finding on the PRs of changes at `review`; returns the new slugs."""
    owner = policy.repos()["fork"].split("/")[0]
    known = {c.get("finding") for c in idx.values() if c.get("finding")}
    made = []
    for ch in list(idx.values()):
        if ch.stage != "review" or ch.get("finding") or ch.get("track") != "server":
            continue
        pr = obs.upstream_pr(ch.get("upstream_pr") or ch.get("branch"))
        if not pr or pr.get("state") != "open":
            continue
        comments = obs.upstream_pr_reviews(pr["number"])
        if comments is None:
            continue
        if not ch.get("review_seen"):
            ch["review_seen"] = iso()
            store.save(ch)
            continue
        for c in findings(comments, owner):
            if c["id"] in known or (c.get("at") or "") <= ch["review_seen"]:
                continue
            slug = _slug(ch["slug"], c["id"])
            if store.exists(slug):
                known.add(c["id"])
                continue
            quote = " ".join(c["body"].split())[:300]
            dod = [f"fix maintainer finding {c['id']} ({c.get('url') or 'PR #' + str(pr['number'])}) in a new commit on "
                   f"`{ch['branch']}`, off the PR head (merge upstream main when behind; never force); nothing deferred",
                   "self-check the diff against upstream AGENTS.md and CONTRIBUTING (no added comments or tests unless asked)",
                   "evidence: the fix checked in game, and `pr-comment.md` replying to the finding"]
            new = store.new(slug, "server", f"Review fix on PR #{pr['number']} ({ch['slug']}): {quote[:60]}", prio="P0",
                            dod=dod, branch=ch["branch"], spec=ch.get("spec"),
                            text=f"Finding {c['id']} by {c.get('author')} on PR #{pr['number']}:\n\n> {quote}")
            new["upstream_pr"], new["finding"] = pr["number"], c["id"]
            store.add_log(new, f"filed from {ch['slug']}: finding {c['id']}")
            store.save(new)
            events.emit("finding", change=slug, parent=ch["slug"], finding=c["id"], pr=pr["number"])
            known.add(c["id"])
            made.append(slug)
    return made
