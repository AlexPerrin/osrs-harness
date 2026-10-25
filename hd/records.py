"""The state dir (`harness/state/`, git-ignored; `HD_STATE` overrides): every record has one owner (R3) and the
log is append-only (R30). Nothing here derives anything.

  state_dir()                      the directory
  config()                         hd.yaml (repos, roles, capacity)
  now()                            UTC ISO second
  read(*parts) / write(data, *parts)   one JSON file under the state dir (write is atomic)
  event(kind, **fields)            append one line to events.jsonl
  run(agent_id) / save_run(rec) / runs()          runs/<agent_id>.json, written by the hooks only
  record(slug, kind) / save_record(slug, kind, data) / drop_record(slug, kind)   records/<slug>/<kind>.json
  train(id) / save_train(rec)      trains/<id>.json, written by train.py and `hd resolve`
"""
import json
import os
import time

HD_HOME = os.environ.get("HD_HOME") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def state_dir():
    return os.environ.get("HD_STATE") or os.path.join(HD_HOME, "harness", "state")


def config():
    import yaml
    with open(os.environ.get("HD_CONFIG") or os.path.join(HD_HOME, "hd.yaml")) as f:
        return yaml.safe_load(f) or {}


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


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
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=1, sort_keys=True)
    os.replace(tmp, p)
    return data


def event(kind, **fields):
    line = {"ts": now(), "kind": kind, **fields}
    p = path("events.jsonl")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps(line, sort_keys=True) + "\n")
    return line


# --- runs (hooks) ---------------------------------------------------------------------------------------------------

def run(agent_id):
    return read("runs", f"{agent_id}.json")


def save_run(rec):
    return write(rec, "runs", f"{rec['agent_id']}.json")


def runs():
    d = path("runs")
    out = []
    for name in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if name.endswith(".json"):
            r = read("runs", name)
            if r:
                out.append(r)
    return out


# --- per-change records ---------------------------------------------------------------------------------------------

def record(slug, kind):
    return read("records", slug, f"{kind}.json")


def save_record(slug, kind, data):
    data.setdefault("ts", now())
    write(data, "records", slug, f"{kind}.json")
    event("record", change=slug, record=kind, **{k: v for k, v in data.items() if k in ("sha", "verdict", "by", "kind")})
    return data


def drop_record(slug, kind):
    try:
        os.remove(path("records", slug, f"{kind}.json"))
        return True
    except OSError:
        return False


# --- trains ---------------------------------------------------------------------------------------------------------

def train(train_id):
    return read("trains", f"{train_id}.json")


def save_train(rec):
    return write(rec, "trains", f"{rec['id']}.json")
