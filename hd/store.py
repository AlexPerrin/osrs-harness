"""The store: a cache of observed facts, human-readable, one file per record.

Changes: `harness/changes/<slug>.md`, YAML front matter + body (`## Change`, `## Definition of done` with
checkboxes, `## Log` with dated lines). Front matter keys (the order they are written in):
  slug, track (client|server|harness), title, prio (P0-P3), role (the dev role that executes `dev`),
  stage (a stage of the track's chain, hd/tracks), hold ({kind, reason, since} or null),
  deps (slugs), branch, commit (the handed-over commit), repo (the clone the commit is in), local_only (ends at the
  test server: chain ending at live), owner (the agent in dev), evidence (dir), spec, network (client: touches
  networking), summary, live_commit (the live target carries the commit), booked ({dev|gate: key} of the last booked
  run: BR-S9), batch, cost ({runs, turns, tokens, minutes}), created, updated; then the keys each track adds
  (`tracks.extra_keys()`).

State records (git-ignored, `harness/state/<kind>/<id>.json`): leases, runs, batches, actions (text files), images;
`live.json` (what the live server runs) and `daemon.json` (the daemon's pid and last tick).
"""
import glob
import os
import re

import yaml

from . import changes_dir, state_dir
from .util import atomic_write, iso, read_json, slug_ok, write_json

TRACKS = ("client", "server", "harness")
HOLDS = ("blocked", "decision", "failed", "exception")
PRIOS = ("P0", "P1", "P2", "P3")
ROLES = {"client": "client-dev", "server": "server-dev", "harness": "harness-dev"}
QA_ROLES = {"client": "client-qa", "server": "server-qa"}
KEYS = ("slug", "track", "title", "prio", "role", "stage", "hold", "deps", "branch", "commit", "repo", "local_only",
        "owner", "evidence", "spec", "network", "summary", "live_commit", "booked", "batch", "cost", "created", "updated")
LIST_KEYS = ("deps",)
RETIRED_KEYS = ("instances", "gated_commit", "published_commit", "pr", "ci", "check")
FRONT = re.compile(r"---\n(.*?)\n---\n?(.*)", re.S)


class Change(dict):
    """The front matter as a dict, plus `.body`."""

    def __init__(self, meta=None, body=""):
        super().__init__(meta or {})
        self.body = body

    @property
    def slug(self):
        return self["slug"]

    @property
    def stage(self):
        return self.get("stage") or "backlog"

    @property
    def hold(self):
        return (self.get("hold") or {}).get("kind")

    @property
    def hold_reason(self):
        return (self.get("hold") or {}).get("reason")

    @property
    def path(self):
        return path(self["slug"])

    def chain(self):
        """The stages this change moves through, from its track."""
        from . import tracks
        return tracks.of(self).chain(self)

    @property
    def terminal(self):
        return self.chain()[-1]

    def reached(self, stage):
        """The change is at or past `stage` of its chain. `live` on a chain that does not contain it is the live target's
        own fact (`live_commit`, set by the tick), independent of the chain's stages."""
        chain = self.chain()
        if stage not in chain:
            return stage == "live" and (bool(self.get("live_commit")) or self.stage == chain[-1])
        return chain.index(self.stage) >= chain.index(stage) if self.stage in chain else False

    def dod_unticked(self):
        return re.findall(r"^- \[ \] .*", self.body, re.M)

    def tick_dod(self, numbers):
        """Tick definition-of-done items by 1-based position among the `- [ ]` / `- [x]` lines; returns the ticked
        texts. ValueError on a number out of range (nothing changes)."""
        items = list(re.finditer(r"^- \[[ x]\] ", self.body, re.M))
        bad = [n for n in numbers if not 1 <= n <= len(items)]
        if bad:
            raise ValueError(f"no definition-of-done item {', '.join(map(str, bad))} (the change has {len(items)})")
        texts = []
        for n in sorted(set(numbers), reverse=True):
            m = items[n - 1]
            texts.insert(0, self.body[m.end():].split("\n", 1)[0])
            self.body = self.body[:m.start()] + "- [x] " + self.body[m.end():]
        return texts

    def has_dod(self):
        return bool(re.search(r"^- \[[ x]\] ", self.body, re.M)) and "(write the definition of done" not in self.body

    def log_lines(self):
        return re.findall(r"^- (\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ) (.*)$", self.body, re.M)


def _migrate_stage(meta):
    """A stage of a retired chain maps onto the track's current one (`track.migrate_stage`); the tick re-derives the
    rest from facts."""
    from . import tracks
    return tracks.get(meta.get("track")).migrate_stage(meta)


def path(slug):
    return os.path.join(changes_dir(), f"{slug}.md")


def exists(slug):
    return os.path.isfile(path(slug))


def load(slug):
    p = path(slug)
    with open(p) as f:
        text = f.read()
    m = FRONT.match(text)
    if not m:
        raise ValueError(f"{p}: no front matter")
    meta = yaml.safe_load(m.group(1)) or {}
    for k in RETIRED_KEYS:
        meta.pop(k, None)   # dropped on the next save
    meta["stage"] = _migrate_stage(meta)
    for k in LIST_KEYS:
        if meta.get(k) is None:
            meta[k] = []
    return Change(meta, m.group(2))


def save(ch):
    if not slug_ok(ch.get("slug", "")):
        raise ValueError(f"bad slug {ch.get('slug')!r}")
    ch["updated"] = iso()
    for k in LIST_KEYS:
        if ch.get(k) is None:
            ch[k] = []
    from . import tracks
    ordered = {k: ch[k] for k in KEYS + tracks.extra_keys() if k in ch}
    ordered.update({k: v for k, v in ch.items() if k not in ordered})
    front = yaml.safe_dump(ordered, sort_keys=False, allow_unicode=True, width=200).rstrip("\n")
    atomic_write(ch.path, f"---\n{front}\n---\n{ch.body.rstrip()}\n")
    return ch


def all_changes():
    out = []
    for p in sorted(glob.glob(os.path.join(changes_dir(), "*.md"))):
        try:
            out.append(load(os.path.basename(p)[:-3]))
        except (ValueError, yaml.YAMLError):
            continue
    return out


def index():
    return {c["slug"]: c for c in all_changes()}


def add_log(ch, msg):
    line = f"- {iso()} {msg}"
    if re.search(r"^## Log\s*$", ch.body, re.M):
        ch.body = ch.body.rstrip() + "\n" + line
    else:
        ch.body = ch.body.rstrip() + "\n\n## Log\n" + line
    return ch


def new(slug, track, title, prio="P2", role=None, deps=(), dod=(), text="", branch=None, stage="ready",
        network=False, spec=None, local_only=False):
    if not slug_ok(slug):
        raise ValueError(f"bad slug {slug!r}")
    if track not in TRACKS:
        raise ValueError(f"track {track!r}")
    if exists(slug):
        raise FileExistsError(slug)
    if stage not in ("backlog", "ready"):
        raise ValueError("a new change starts at backlog or ready")
    if stage == "ready" and not dod:
        raise ValueError("a change leaves backlog only with a definition of done (BR-C3)")
    ch = Change({"slug": slug, "track": track, "title": title, "prio": prio, "role": role or ROLES[track],
                 "stage": stage, "hold": None, "deps": list(deps), "branch": branch, "commit": None,
                 "local_only": bool(local_only), "owner": None, "created": iso()})
    if network:
        ch["network"] = True
    if spec:
        ch["spec"] = spec
    body = f"## Change\n{text or title}\n\n## Definition of done\n"
    body += "\n".join(f"- [ ] {d}" for d in dod) if dod else "- [ ] (write the definition of done before ready)"
    ch.body = body + "\n"
    add_log(ch, f"created ({stage})")
    return save(ch)


def set_stage(ch, stage, why="", commit=None):
    """Record an observed stage (the daemon's, never an operator's: BR-S2). Returns the previous stage."""
    if stage not in ch.chain():
        raise ValueError(stage)
    before = ch.stage
    ch["stage"] = stage
    if commit:
        ch["commit"] = commit
    add_log(ch, f"{before} -> {stage}" + (f": {why}" if why else ""))
    return before


def set_hold(ch, kind, reason):
    if kind not in HOLDS:
        raise ValueError(kind)
    ch["hold"] = {"kind": kind, "reason": reason, "since": iso()}
    add_log(ch, f"hold {kind}: {reason}")
    return ch


def clear_hold(ch, why=""):
    if ch.get("hold"):
        add_log(ch, f"hold {ch.hold} cleared" + (f": {why}" if why else ""))
    ch["hold"] = None
    return ch


# --- state records -------------------------------------------------------------------------------------------------

def _rec_dir(kind):
    return os.path.join(state_dir(), kind)


def rec_path(kind, rid):
    return os.path.join(_rec_dir(kind), f"{rid}.json")


def rec_load(kind, rid):
    return read_json(rec_path(kind, rid))


def rec_save(kind, rid, obj):
    obj = dict(obj)
    obj.setdefault("id", rid)
    obj["updated"] = iso()
    write_json(rec_path(kind, rid), obj)
    return obj


def rec_delete(kind, rid):
    try:
        os.remove(rec_path(kind, rid))
    except OSError:
        pass


def rec_all(kind):
    out = []
    for p in sorted(glob.glob(os.path.join(_rec_dir(kind), "*.json"))):
        r = read_json(p)
        if isinstance(r, dict):
            r.setdefault("id", os.path.basename(p)[:-5])
            out.append(r)
    return out


def live_path():
    return os.path.join(state_dir(), "live.json")


def live():
    """What the live server runs: {integration, image, image_id, rollback, since, upstream_main}."""
    return read_json(live_path(), {})


def set_live(obj):
    obj = dict(obj)
    obj["updated"] = iso()
    write_json(live_path(), obj)
    return obj
