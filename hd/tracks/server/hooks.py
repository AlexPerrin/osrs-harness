"""The server track's hook logic (the entry points are hooks/publish_gate.py, github_scope.py, deny_publish.py, which only
parse the command and ask here). Pure functions on strings and the store.

  contribute_deny(cmd)           reason when `hd contribute <slug> --approved <sha>` must not run: no QA record at the
                                 change's commit, or the approval names another commit (the user's yes is bound to the sha)
  direct_pr_deny(branch, sha)    reason when a direct upstream PR creation must not run: no change on the branch has
                                 QA's record at the commit the branch is at
  is_contribute(words)           the command is `<python> .../hd.py contribute ...` (the console's one upstream sequence)
  is_scratch_push(refspecs, opts, dest)   one refspec creating or updating a fork `gate/<name>` scratch branch (forced
                                 allowed, never a deletion): server-qa's only push besides `docs`
"""
import re

from ...util import same_commit
from . import qa

CONTRIBUTE = re.compile(r"\bhd\.py\s+contribute\b(.*)")


def contribute_deny(cmd):
    from ... import store
    m = CONTRIBUTE.search(cmd)
    if not m:
        return None
    rest = m.group(1)
    slug = re.search(r"^\s+([a-z0-9][a-z0-9.-]+)", rest)
    approved = re.search(r"--approved[=\s]+([0-9a-f]{7,40})", rest)
    if not slug or not approved:
        return "`hd contribute <slug> --approved <sha>`: the user's approval is bound to the commit, name it"
    if not store.exists(slug.group(1)):
        return f"no change {slug.group(1)}"
    ch = store.load(slug.group(1))
    if qa.gate_state(ch)[0] is None:
        return f"{ch['slug']} has no QA record at {str(ch.get('commit'))[:9]}; the aggregate runs first"
    if not same_commit(approved.group(1), ch.get("commit")):
        return (f"the approval is for {approved.group(1)[:9]}, but {ch['slug']} is at {str(ch.get('commit'))[:9]}: "
                "a new commit needs a new QA record and a new yes")
    return None


def direct_pr_deny(branch, sha):
    from ... import store
    seen = []
    for ch in store.all_changes():
        if ch.get("branch") != branch or ch.get("track") != "server":
            continue
        verdict, _ = qa.gate_state(ch)
        if verdict and same_commit(ch.get("commit"), sha):
            return None
        seen.append(f"{ch['slug']}: QA record {verdict or 'missing'} at {str(ch.get('commit'))[:9]}")
    if not seen:
        return f"no change for {branch}; the server-qa aggregate records {sha[:9]} first"
    return f"{branch} is at {sha[:9]}, but no change has a QA record at it ({'; '.join(seen)})"


def is_contribute(words):
    for i, w in enumerate(words[:3]):
        if w.endswith("hd.py") and words[i + 1:i + 2] == ["contribute"]:
            return True
    return False


def is_scratch_push(refspecs, opts, dest):
    return (len(refspecs) == 1 and not refspecs[0].startswith(":") and "--delete" not in opts
            and "--mirror" not in opts and dest(refspecs[0]).startswith("gate/"))
