"""Actions that need the user's OK (BR-A1): a track's upstream items and a client release. Given in chat by the console;
nothing is recorded about them. The core collects the cards: each track's `needs_you(change, obs, idx)` (the server
track's approval card and its siblings, hd/tracks/server/cards.py) and the release batches below. Completion is
observed (the work is visible in the world), never written down: when the world has moved the card is gone from the
list. There is no approved, denied, stale or failed state.

  pending_actions(obs=None, idx=None)   [card]; each card is
      {id, kind: upstream|release, action, change, batch, commit, commands: [[argv]...], files: [path...],
       text: {title, body, comment}, record, verdict, checks, findings, diff ("base..head"), steps ([(step, done, why)]),
       caveats, note}
      tag-release a gated release batch with a tag: one `gh release create <tag> --target <commit>` with the APK;
                  choose-tag when it has none (the user picks, `hd release-request vX.Y.Z`).
  text_file(id, part, text)             write a text file a card's command reads
  render(card)                          the card as text, commands quoted for a shell
  release_published(batch, obs)         True when the release for the batch's tag exists on GitHub (observed)

Text files the commands read are written to `harness/state/actions/<id>.<part>.md` when the list is computed.
HD_GIT / HD_GH are not read here: the console runs the printed commands itself, after the user's yes.
"""
import os
import re

from . import batches, policy, state_dir, store, tracks


def _dir():
    return os.path.join(state_dir(), "actions")


def text_file(aid, part, text):
    p = os.path.join(_dir(), f"{aid}.{part}.md")
    os.makedirs(_dir(), exist_ok=True)
    with open(p, "w") as f:
        f.write(text.rstrip("\n") + "\n")
    return p


_text_file = text_file


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
        obs = tracks.Observer()
    idx = store.index() if idx is None else idx
    out = []
    for ch in idx.values():
        out += tracks.of(ch).needs_you(ch, obs, idx)
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
        lines.append(f"  record: {a['record']}")
    for c in a.get("checks") or []:
        lines.append(f"  check: {c}")
    for f in a.get("findings") or []:
        lines.append(f"  finding: {f}")
    for n, d, w in a.get("steps") or []:
        lines.append(f"  step {n}: {'done' if d else 'pending' if d is False else 'unknown'} ({w})")
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
