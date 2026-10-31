#!/usr/bin/env python3
"""Custom gameval ids, unique across everything that goes live together.

The official ids are the cache's (.data/gamevals-binary/max-ids.toml: 0..max per table is reserved). Every id above
that is ours, and upstream's fix_gameval_conflicts.py picks "the highest free" from one branch alone, so two branches
built at once take the same id. Here the set is upstream main + every branch the train merges (integration.txt, at
its pin) + the dev head of every open server change, read from the fork clone <repo>.

  gameval_ids.py check <repo> <ref> [<slug>]   ids in <ref> that another member holds under another name; exit 1 if any
  gameval_ids.py assign <repo> <worktree>      give every `name = -1` (and `name=-1` in .rscm) in <worktree> the
                                               highest id free in every member; then fix_gameval_conflicts.py --check
<slug> leaves out the change's own dev head and its public branch (the head replaces them).
"""
import os
import re
import subprocess
import sys
from collections import defaultdict

SECTION = re.compile(r"^\s*\[gamevals\.([^.\]]+)\]\s*$")
KV = re.compile(r"^(\s*)([^=#\[]+?)(\s*=\s*)(-?\d+)(\s*)$")
TOP = {"area": 32766}   # the server keeps area ids in a short
MAX = 65535
TOOLS = "fork/local/integration-tools"


def git(repo, *a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True).stdout


def gameval_files(repo, ref):
    return [p for p in git(repo, "ls-tree", "-r", "--name-only", ref).split()
            if (p.endswith("/gamevals.toml") and p.startswith(("content/", "api/")) and
                not {"build", "out", "target"} & set(p.lower().split("/")))
            or (p.startswith(".data/gamevals/") and p.endswith(".rscm"))]


def entries(text, path):
    """(table, name, id) for each gameval line of one file."""
    table = os.path.basename(path)[:-5] if path.endswith(".rscm") else None
    for line in text.splitlines():
        s = SECTION.match(line)
        if s:
            table = None if s.group(1) == "dbcol" else s.group(1)
            continue
        m = KV.match(line.strip() if path.endswith(".rscm") else line)
        if table and m:
            yield table, m.group(2).strip(), int(m.group(4))


def ids(repo, ref, maxes=None):
    """{(table, id): name} of the custom ids at <ref>: past <ref>'s own max ids, or past `maxes` (another ref's)."""
    maxes = maxes or max_ids(git(repo, "show", f"{ref}:.data/gamevals-binary/max-ids.toml"))
    out = {}
    for p in gameval_files(repo, ref):
        for t, name, i in entries(git(repo, "show", f"{ref}:{p}"), p):
            if i > maxes.get(t, -1):
                out[(t, i)] = name
    return out


def max_ids(text):
    return {k.strip(): int(v) for k, v in (l.split("=", 1) for l in text.split("[max_ids]", 1)[-1].splitlines()
                                            if "=" in l and not l.strip().startswith("#"))}


def members(repo, slug=None):
    """[(label, ref)]: upstream main, the train's branches at their pins, the open dev heads."""
    git(repo, "fetch", "-q", "fork")
    git(repo, "fetch", "-q", "origin", "main")
    pins = dict(l.split()[:2] for l in git(repo, "show", f"{TOOLS}:integration.lock").splitlines() if len(l.split()) >= 2)
    own = set()
    if slug:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from hd import steps, store
        ch = next((c for c in store.changes() if c["slug"] == slug), None)
        own = {f"dev/{slug}"} | ({steps.public_branch(ch)} if ch else set())
    out = [("upstream main", "origin/main")]
    for b in git(repo, "show", f"{TOOLS}:integration.txt").splitlines():
        b = b.strip()
        if b and not b.startswith("#") and b not in own:
            out.append((b, pins.get(b) if pins.get(b) and git(repo, "cat-file", "-t", pins[b]).strip() else f"fork/{b}"))
    for r in git(repo, "for-each-ref", "--format=%(refname:short)", "refs/remotes/fork/dev/").split():
        b = r[len("fork/"):]
        if b not in own and subprocess.run(["git", "-C", repo, "merge-base", "--is-ancestor", r, "origin/main"]).returncode:
            out.append((b, r))   # a dev head already in upstream main is done
    return out


def since(repo, ref, name, i):
    """When <ref>'s history first gave <name> the id <i> (the earlier holder keeps it)."""
    ts = git(repo, "log", "--format=%ct", "-G", rf"^\s*{re.escape(name)}\s*=\s*{i}\s*$", ref, "--").split()
    return int(ts[-1]) if ts else 0


def check(repo, ref, slug=None):
    mine = ids(repo, ref)
    bad = [f"area.{n} = {i} is past the server's area limit {TOP['area']}" for (t, i), n in mine.items()
           if t == "area" and i > TOP["area"]]
    base = max_ids(git(repo, "show", f"{ref}:.data/gamevals-binary/max-ids.toml"))
    for label, r in dict(members(repo, slug)).items():
        for (t, i), n in ids(repo, r, base).items():   # past <ref>'s max: an id upstream main took since <ref>'s base counts
            if (t, i) in mine and mine[(t, i)] != n and (label == "upstream main" or   # upstream main never renumbers
                                                         (since(repo, r, n, i), n) < (since(repo, ref, mine[(t, i)], i), mine[(t, i)])):   # a tie: the name
                bad.append(f"{t}.{mine[(t, i)]} = {i} is {t}.{n} on {label}, which had it first: renumber with "
                           f"`gameval_ids.py assign` (name = -1)")
    print("\n".join(bad) or f"gameval ids at {ref}: unique across upstream main, the train and the open dev heads")
    return 1 if bad else 0


def assign(repo, tree):
    taken = defaultdict(set)
    for _label, r in members(repo):
        for t, i in ids(repo, r):
            taken[t].add(i)
    maxes = max_ids(open(os.path.join(tree, ".data/gamevals-binary/max-ids.toml")).read())
    files = [os.path.join(d, f) for base in ("content", "api") for d, _, fs in os.walk(os.path.join(tree, base))
             if not {"build", "out", "target"} & set(d.lower().split(os.sep)) for f in fs if f == "gamevals.toml"]
    gv = os.path.join(tree, ".data", "gamevals")
    files += [os.path.join(gv, f) for f in sorted(os.listdir(gv)) if f.endswith(".rscm")] if os.path.isdir(gv) else []
    for p in files:
        for t, _n, i in entries(open(p).read(), p):
            taken[t].add(i)
    for p in files:
        lines, table, changed = open(p).read().split("\n"), os.path.basename(p)[:-5] if p.endswith(".rscm") else None, False
        for k, line in enumerate(lines):
            s = SECTION.match(line)
            if s:
                table = None if s.group(1) == "dbcol" else s.group(1)
                continue
            m = KV.match(line.strip() if p.endswith(".rscm") else line)
            if table and m and m.group(4) == "-1":
                new = next(i for i in range(TOP.get(table, MAX), maxes.get(table, -1), -1) if i not in taken[table])
                taken[table].add(new)
                lines[k] = re.sub(r"-1(\s*)$", f"{new}\\1", line)
                changed = True
                print(f"{table}.{m.group(2).strip()} = {new}")
        if changed:
            open(p, "w").write("\n".join(lines))
    return 0


if __name__ == "__main__":
    cmd, *a = sys.argv[1:]
    sys.exit({"check": check, "assign": assign}[cmd](*a))
