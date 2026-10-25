"""What is stored (P2): definitions (committed under harness/), records, runs and events (harness/state/, git-ignored;
`HD_STATE` overrides). Nothing here derives anything.

  config()                         hd.yaml (`HD_CONFIG` overrides)
  changes() / goals()              the definitions: front matter plus `body` and `hash` (R3: the no-loop rule)
  save_definition(kind, slug, meta, body)   writes harness/<kind>/<slug>.md
  record(slug, kind) / save_record / drop_record    harness/state/<slug>/<kind>.json, one writer each
  valid(rec, head, base=None)      the judgment covers this head (and base)
  runs() / run(name) / save_run    harness/state/runs/<name>.json, written by the hook
  read(*parts) / write(data, *parts)   one JSON file under the state dir (atomic)
  event(kind, **fields)            one line of events.jsonl
  locked()                         the one flock on the state dir: every pass and every record write holds it
"""
import contextlib
import fcntl
import glob
import hashlib
import json
import os
import re
import time

HD_HOME = os.environ.get("HD_HOME") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONT = re.compile(r"\A---\n(.*?)\n---\n?(.*)\Z", re.S)


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def state_dir():
    return os.environ.get("HD_STATE") or os.path.join(HD_HOME, "harness", "state")


def config():
    import yaml
    with open(os.environ.get("HD_CONFIG") or os.path.join(HD_HOME, "hd.yaml")) as f:
        cfg = yaml.safe_load(f) or {}
    cfg["paths"] = {k: os.path.expanduser(v) for k, v in (cfg.get("paths") or {}).items()}
    return cfg


# --- definitions -----------------------------------------------------------------------------------------------------

def _defs_dir(kind):
    return os.path.join(os.environ.get("HD_DEFS") or os.path.join(HD_HOME, "harness"), kind)


def _load(path):
    import yaml
    with open(path, "rb") as f:
        raw = f.read()
    m = FRONT.match(raw.decode(errors="replace"))
    if not m:
        return None
    meta = yaml.safe_load(m.group(1)) or {}
    meta.update(body=m.group(2), hash=hashlib.sha1(raw).hexdigest()[:12], path=path)
    meta.setdefault("slug", os.path.basename(path)[:-3])
    meta.setdefault("deps", [])
    meta.setdefault("kind", "change")
    meta.setdefault("priority", "P2")
    return meta


def _all(kind):
    out = []
    for p in sorted(glob.glob(os.path.join(_defs_dir(kind), "*.md"))):
        d = _load(p)
        if d is None:
            event("error", file=p, detail="no front matter")
        else:
            out.append(d)
    return out


def changes():
    return _all("changes")


def goals():
    return _all("goals")


def save_definition(kind, slug, meta, body):
    import yaml
    d = _defs_dir(kind)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"{slug}.md")
    with open(p, "w") as f:
        f.write("---\n" + yaml.safe_dump(meta, sort_keys=False).strip() + "\n---\n" + body.rstrip() + "\n")
    return p


# --- state ----------------------------------------------------------------------------------------------------------

def path(*parts):
    return os.path.join(state_dir(), *parts)


def read(*parts):
    try:
        with open(path(*parts)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def write(data, *parts):
    p = path(*parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p + ".tmp", "w") as f:
        json.dump(data, f, indent=1, sort_keys=True)
    os.replace(p + ".tmp", p)
    return data


def event(kind, **fields):
    line = {"ts": now(), "kind": kind, **fields}
    os.makedirs(state_dir(), exist_ok=True)
    if os.path.exists(path("events.jsonl")) and os.path.getsize(path("events.jsonl")) > 20_000_000:
        os.replace(path("events.jsonl"), path("events.1.jsonl"))   # one generation kept
    with open(path("events.jsonl"), "a") as f:
        f.write(json.dumps(line, sort_keys=True) + "\n")
    return line


@contextlib.contextmanager
def locked():
    os.makedirs(state_dir(), exist_ok=True)
    with open(path(".lock"), "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        yield


def record(slug, kind):
    return read(slug, f"{kind}.json")


def save_record(slug, kind, data):
    data.setdefault("ts", now())
    write(data, slug, f"{kind}.json")
    event("record", change=slug, record=kind, head=data.get("head"))
    return data


def drop_record(slug, kind):
    try:
        os.remove(path(slug, f"{kind}.json"))
    except OSError:
        pass


def valid(rec, head, base=None):
    """The judgment covers `head` (and `base`); a moved head or base voids it (R3)."""
    return bool(rec) and bool(head) and rec.get("head") == head and (base is None or rec.get("base") == base)


def run(name):
    return read("runs", f"{name}.json")


def save_run(rec):
    return write(rec, "runs", f"{rec['name']}.json")


def runs():
    out = []
    for p in sorted(glob.glob(path("runs", "*.json"))):
        try:
            with open(p) as f:
                out.append(json.load(f))
        except (OSError, ValueError):
            pass
    return out
