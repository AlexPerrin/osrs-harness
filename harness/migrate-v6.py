#!/usr/bin/env python3
"""One-off v6 -> v7 migration of the change definitions.
  migrate.py [--dir <changes dir>] [--apply]      convert the files: delete done and v6-harness changes, keep the open
                                                  ones with the definition keys only, strip the log
  migrate.py --cutover [--apply]                  the facts v6 established: dev refs at the handed-over commits
                                                  (fork dev/<slug>, client origin/client/<slug>), evidence copied,
                                                  handover records; review-stage changes also gate, verdict and
                                                  approval records (their PRs are ready at that head); backlog
                                                  changes get a question.
Dry unless --apply."""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

import yaml

HD = os.path.expanduser("~/osrs-harness")
FORK = os.path.expanduser("~/src/OpenRune-Server")
CLIENT = os.path.expanduser("~/osrs-plugins-reverse")
KEEP = ("slug", "track", "title", "deps", "created", "network")
apply = "--apply" in sys.argv
cutover = "--cutover" in sys.argv
d = sys.argv[sys.argv.index("--dir") + 1] if "--dir" in sys.argv else f"{HD}/harness/changes"
now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load(p):
    raw = open(p).read()
    m = re.match(r"\A---\n(.*?)\n---\n?(.*)\Z", raw, re.S)
    return yaml.safe_load(m.group(1)), m.group(2)


def sh(*args):
    print("  $", " ".join(args))
    if apply:
        r = subprocess.run(args, capture_output=True, text=True)
        if r.returncode:
            print("   !", (r.stderr or r.stdout).strip()[-200:])


def record(slug, kind, data):
    p = f"{HD}/harness/state/{slug}/{kind}.json"
    print(f"  record {p} {json.dumps(data)[:80]}")
    if apply:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        data.setdefault("ts", now)
        json.dump(data, open(p, "w"), indent=1, sort_keys=True)


if not cutover:
    n_del = n_keep = 0
    for p in sorted(glob.glob(f"{d}/*.md")):
        meta, body = load(p)
        if meta.get("stage") in ("live", "merged") or meta["track"] == "harness":
            n_del += 1
            print("delete", meta["slug"], meta.get("stage"), meta["track"])
            if apply:
                os.remove(p)
            continue
        new = {k: meta[k] for k in KEEP if meta.get(k) not in (None, [], "")}
        new["priority"] = meta.get("prio", "P2")
        new["kind"] = "local" if meta.get("local_only") else "change"
        if meta.get("branch") and meta["track"] == "server":
            new["branch"] = meta["branch"]
        if meta.get("upstream_pr"):
            new["pr"] = meta["upstream_pr"]
        body = re.sub(r"\n## Log\n.*\Z", "\n", body, flags=re.S).rstrip() + "\n"
        order = ["slug", "track", "kind", "title", "priority", "deps", "created", "branch", "pr", "network"]
        new = {k: new[k] for k in order if k in new}
        n_keep += 1
        print("keep", meta["slug"], meta.get("stage"), meta["track"])
        if apply:
            with open(p, "w") as f:
                f.write("---\n" + yaml.safe_dump(new, sort_keys=False).strip() + "\n---\n" + body)
    print(n_del, "deleted;", n_keep, "kept")
    sys.exit()

# --cutover: run against the v6 files on branch main (git show) so the state keys are still there
files = subprocess.run(["git", "-C", HD, "ls-tree", "--name-only", "main", "harness/changes/"], capture_output=True, text=True).stdout.split()
base_fork = subprocess.run(["git", "-C", FORK, "rev-parse", "origin/main"], capture_output=True, text=True).stdout.strip()
base_client = subprocess.run(["git", "-C", CLIENT, "rev-parse", "origin/main"], capture_output=True, text=True).stdout.strip()
for f in files:
    raw = subprocess.run(["git", "-C", HD, "show", f"main:{f}"], capture_output=True, text=True).stdout
    m = re.match(r"\A---\n(.*?)\n---\n?(.*)\Z", raw, re.S)
    meta = yaml.safe_load(m.group(1))
    slug, stage, track, commit = meta["slug"], meta.get("stage"), meta["track"], meta.get("commit")
    if stage in ("live", "merged") or track == "harness":
        continue
    print(f"{slug} ({track} {stage})")
    if stage == "backlog":
        record(slug, "ask", {"question": "from the v6 backlog: start this change?", "options": ["yes", "drop it"]})
        continue
    if not commit:
        continue
    ev = meta.get("evidence")
    if ev and os.path.isdir(ev):
        print(f"  copy {ev} -> {HD}/evidence/{slug}")
        if apply:
            shutil.copytree(ev, f"{HD}/evidence/{slug}", dirs_exist_ok=True)
    if track == "server":
        src = meta.get("repo") or FORK
        if src != FORK:
            sh("git", "-C", FORK, "fetch", "-q", src, commit)
        sh("git", "-C", FORK, "push", "-q", "fork", f"{commit}:refs/heads/dev/{slug}")
        record(slug, "handover", {"head": commit, "base": base_fork, "evidence": f"{HD}/evidence/{slug}", "summary": meta.get("summary") or "v6 hand-over"})
        if stage == "review":
            record(slug, "gate", {"head": commit, "base": base_fork, "ok": True, "detail": "v6 gate PASS (fork CI green on the scratch merge)"})
            record(slug, "verdict", {"head": commit, "base": base_fork, "pass": True, "findings": []})
            record(slug, "approval", {"head": commit})
    elif track == "client":
        sh("git", "-C", CLIENT, "push", "-q", "origin", f"{commit}:refs/heads/client/{slug}")
        record(slug, "handover", {"head": commit, "base": base_client, "evidence": f"{HD}/evidence/{slug}", "summary": meta.get("summary") or "v6 hand-over"})
