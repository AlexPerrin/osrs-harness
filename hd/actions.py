"""Actions that need the user's OK (v4). Upstream actions on an OpenRune PR and client releases are given in chat in
the console session; nothing is recorded about them. This module computes, from git and GitHub state alone, what each
gated change or gated release batch needs next, with the exact commands and the text files the commands read.
Completion is observed (the PR exists at the commit, the release exists), never written down: when the world has
moved the action is gone from the list. There is no approved, denied, stale or failed state.

  pending_actions(obs=None, idx=None)   [action]; each action is
      {id, kind: upstream|release, action: open-pr|update-pr|ready-pr|tag-release|choose-tag,
       change, batch, commit, commands: [[argv]...], files: [path...], text: {title, body, comment},
       record (the gate record name), diff ("base..head"), caveats, note}
      A gated server change (stage `gated`, branch and commit) needs: open-pr when no upstream PR exists, ready-pr
      when the PR is a draft at the commit, update-pr (push the commit, then comment) when the PR head is behind it;
      nothing when the PR is at the commit, closed or merged, or gh cannot be read. PR text comes from the fork's docs
      branch (pr-texts/<slug>.title, .upstream.body, .update.md). A gated release batch needs tag-release (one
      `gh release create <tag> --target <commit>` with the APK) once it has a tag, else choose-tag.
  render(action)                        the action as text, commands quoted for a shell
  release_published(batch, obs)         True when the release for the batch's tag exists on GitHub (observed)

Text files the commands read are written to `harness/state/actions/<id>.<part>.md` when the list is computed.
HD_GIT / HD_GH are not read here: the console runs the printed commands itself, after the user's yes.
"""
import os
import re

from . import ROOT, batches, policy, stages, state_dir, store
from .util import short

PR_URL = re.compile(r"/pull/(\d+)")


def _dir():
    return os.path.join(state_dir(), "actions")


def _text_file(aid, part, text):
    p = os.path.join(_dir(), f"{aid}.{part}.md")
    os.makedirs(_dir(), exist_ok=True)
    with open(p, "w") as f:
        f.write(text.rstrip("\n") + "\n")
    return p


def _pr_slug(ch):
    """The docs-branch name of the change's PR text: the branch after its prefix (BR-C1)."""
    b = ch.get("branch") or ""
    return b.split("/", 1)[1] if "/" in b else ch["slug"]


def _caveats(body):
    out, inside = [], False
    for line in (body or "").splitlines():
        if line.startswith("## "):
            inside = line.strip().lower() == "## caveats"
        elif inside and line.startswith("- "):
            out.append(line[2:].strip())
    return out


def _head_at(pr, commit):
    head = str(pr.get("head") or "")
    return bool(head) and (head.startswith(commit) or commit.startswith(head))


def needed(pr, commit):
    """What a gated change needs from its upstream PR state, or None (nothing: done, closed, or unreadable)."""
    if pr is None:
        return None
    if not pr:
        return "open-pr"
    if pr.get("merged") or pr.get("state") != "open":
        return None
    if _head_at(pr, commit):
        return "ready-pr" if pr.get("draft") else None
    return "update-pr"


def _upstream(ch, obs):
    if ch.stage != "gated" or not (ch.get("branch") and ch.get("commit")):
        return None
    branch, commit = ch["branch"], ch["commit"]
    pr = obs.upstream_pr(ch.get("upstream_pr") or branch)
    action = needed(pr, commit)
    if action is None:
        return None
    aid = f"{ch['slug']}-{action}-{short(commit, 7)}"
    rp = policy.repos()
    upstream, clone = rp["upstream"], os.path.join(ROOT, rp.get("fork_clone", "re/upstream-pr/or"))
    slug = _pr_slug(ch)
    title = obs.docs_file(f"pr-texts/{slug}.title")
    body = obs.docs_file(f"pr-texts/{slug}.upstream.body")
    text, commands, files, note = {"title": (title or "").strip(), "body": body or ""}, [], [], None
    if action == "open-pr":
        if title and body:
            f = _text_file(aid, "body", body)
            files.append(f)
            commands = [["gh", "pr", "create", "-R", upstream, "--base", "main", "--head", f"AlexPerrin:{branch}",
                         "--title", text["title"], "--body-file", f]]
        else:
            note = f"PR text missing on docs: pr-texts/{slug}.*"
    elif action == "ready-pr":
        commands = [["gh", "pr", "ready", str(pr["number"]), "-R", upstream]]
    else:
        comment = obs.docs_file(f"pr-texts/{slug}.update.md") or f"Updated to {commit}: {ch.get('summary') or ''}".rstrip()
        text["comment"] = comment
        f = _text_file(aid, "comment", comment)
        files.append(f)
        commands = [["git", "-C", clone, "push", rp.get("fork_remote", "fork"), f"{commit}:refs/heads/{branch}"],
                    ["gh", "pr", "comment", str(pr["number"]), "-R", upstream, "--body-file", f]]
    mb = obs.merge_base("fork", f"refs/remotes/{rp.get('upstream_remote', 'origin')}/main", commit)
    rec = stages.gate_record(obs.docs_records(), branch, commit)
    return {"id": aid, "kind": "upstream", "action": action, "change": ch["slug"], "batch": None, "commit": commit,
            "commands": commands, "files": files, "text": text, "record": rec[0] if rec else None,
            "diff": f"{mb}..{commit}" if mb else None, "caveats": _caveats(body), "note": note}


def release_tag(batch):
    """The tag a release batch carries: its own, else the one in `harness/state/release.request`."""
    return batch.get("tag") or (store.read_json(os.path.join(state_dir(), "release.request"), {}) or {}).get("tag")


def release_published(batch, obs):
    """The GitHub release for the batch's tag exists (observed)."""
    tag = release_tag(batch)
    return bool(tag) and bool(obs.release(tag))


def _release(batch, obs):
    tag, commit = release_tag(batch), batch.get("commit") or ""
    if not tag:
        return {"id": f"{batch['id']}-choose-tag", "kind": "release", "action": "choose-tag", "change": None,
                "batch": batch["id"], "commit": commit, "commands": [], "files": [], "text": {}, "record": batch.get("record"),
                "diff": None, "caveats": [],
                "note": "the user picks the version tag: `hd release-request vX.Y.Z` (the tag is then used by the release)"}
    aid = f"{batch['id']}-tag-release-{tag}"
    includes = batch.get("includes") or []
    notes = f"# {tag}\n\n" + "\n".join(f"- {s}" for s in includes) + "\n"
    f = _text_file(aid, "notes", notes)
    cmd = ["gh", "release", "create", tag, "--repo", policy.repos()["ours"], "--target", commit, "--title", tag,
           "--notes-file", f]
    apk = batch.get("apk")
    if apk and os.path.isfile(apk):
        cmd.append(apk)
    return {"id": aid, "kind": "release", "action": "tag-release", "change": None, "batch": batch["id"], "commit": commit,
            "commands": [cmd], "files": [f], "text": {"title": tag, "body": notes}, "record": batch.get("record"),
            "diff": None, "caveats": [], "note": None}


def pending_actions(obs=None, idx=None):
    if obs is None:
        from .observe import Observer
        obs = Observer()
    idx = store.index() if idx is None else idx
    out = []
    for ch in idx.values():
        a = _upstream(ch, obs)
        if a:
            out.append(a)
    for b in batches.open_batches("release"):
        if b.get("step") == "gated" and not release_published(b, obs):
            out.append(_release(b, obs))
    return out


def quote(w):
    return w if re.fullmatch(r"[A-Za-z0-9_@%+=:,./-]+", w) else "'" + w.replace("'", "'\\''") + "'"


def render(a):
    lines = [f"{a['id']}: {a['kind']} {a['action']}" + (f" for change {a['change']}" if a.get("change") else "")
             + (f" batch {a['batch']}" if a.get("batch") else "")]
    if a.get("note"):
        lines.append(f"  note: {a['note']}")
    for cmd in a.get("commands") or []:
        lines.append("  $ " + " ".join(quote(w) for w in cmd))
    if a.get("record"):
        lines.append(f"  gate record: {a['record']}")
    if a.get("diff"):
        lines.append(f"  diff: {a['diff']}")
    for c in a.get("caveats") or []:
        lines.append(f"  caveat: {c}")
    t = a.get("text") or {}
    if t.get("title"):
        lines.append(f"  title: {t['title']}")
    for part in ("body", "comment"):
        if t.get(part):
            lines.append(f"  {part}:")
            lines += ["    " + l for l in t[part].rstrip().splitlines()]
    for f in a.get("files") or []:
        lines.append(f"  text file: {f}")
    return "\n".join(lines)
