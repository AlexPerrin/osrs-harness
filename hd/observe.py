"""External truth (BR-H1), read fresh each tick and memoised for the tick: git refs in the clones, docker images and
containers, the live server, processes. Everything the stage preconditions and the checks need goes through one
observer, so a test replaces it with a fake. The core constructs `hd.tracks.Observer` / `FakeObserver`: these classes
plus each track's observation mixin (GitHub: hd/tracks/server/github.py).

Repos: `ours` = this checkout (master); `fork` = the push clone's `fork` remote; `upstream` = the push clone's
`origin` remote; an absolute path = a dev's clone. `fetch()` refreshes the remotes once per tick; HD_NO_FETCH=1 skips
network (tests, offline)."""
import glob
import json
import os
import re
import subprocess

from . import HD_HOME, ROOT, fork_clone, store
from . import policy
from .util import pid_alive


def _run(args, cwd=None, timeout=60):
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None


class Observer:
    def __init__(self, ours=None, clone=None, gh=None):
        rp = policy.repos()
        self.ours = ours or ROOT
        self.clone = clone or fork_clone()
        self.fork_remote = rp.get("fork_remote", "fork")
        self.upstream_remote = rp.get("upstream_remote", "origin")
        self.fork_repo = rp.get("fork", "AlexPerrin/OpenRune-Server")
        self.upstream_repo = rp.get("upstream", "OpenRune/OpenRune-Server")
        self.docs_branch = rp.get("docs_branch", "docs")
        self.gh = gh or "gh"
        self._memo = {}
        self._fetched = False

    def reset(self):
        self._memo.clear()
        self._fetched = False

    def _m(self, key, fn):
        if key not in self._memo:
            self._memo[key] = fn()
        return self._memo[key]

    # --- git --------------------------------------------------------------------------------------------------------

    def fetch(self):
        if self._fetched or os.environ.get("HD_NO_FETCH"):
            return
        self._fetched = True
        if os.path.isdir(self.clone):
            _run(["git", "-C", self.clone, "fetch", "-q", "--prune", self.fork_remote], timeout=120)
            _run(["git", "-C", self.clone, "fetch", "-q", self.upstream_remote, "main"], timeout=120)

    def _repo(self, repo):
        if repo == "harness":
            return HD_HOME
        if os.path.isabs(str(repo)):
            return repo   # a dev's clone (a change's `repo`)
        return self.ours if repo == "ours" else self.clone

    def _ref(self, repo, name):
        if repo in ("ours", "harness") or os.path.isabs(str(repo)):
            return f"refs/heads/{name}"
        if repo == "fork":
            return f"refs/remotes/{self.fork_remote}/{name}"
        return f"refs/remotes/{self.upstream_remote}/{name}"

    def rev(self, repo, ref):
        def f():
            r = _run(["git", "-C", self._repo(repo), "rev-parse", "-q", "--verify", f"{ref}^{{commit}}"])
            return r.stdout.strip() if r and r.returncode == 0 else None
        return self._m(("rev", repo, ref), f)

    def branch_tip(self, repo, branch):
        self.fetch()
        return self.rev(repo, self._ref(repo, branch))

    def upstream_main(self):
        self.fetch()
        return self.rev("upstream", self._ref("upstream", "main"))

    def contains(self, repo, ref, sha):
        """ref (a branch name for ours/fork/upstream, or a sha) contains sha; None when either is unknown."""
        self.fetch()
        target = ref if re.fullmatch(r"[0-9a-f]{7,40}", ref or "") else self._ref(repo, ref)

        def f():
            d = self._repo(repo)
            if self.rev(repo, target) is None or self.rev(repo, sha) is None:
                return None
            r = _run(["git", "-C", d, "merge-base", "--is-ancestor", sha, target])
            return None if r is None else r.returncode == 0
        return self._m(("contains", repo, target, sha), f)

    def merge_base(self, repo, a, b):
        def f():
            r = _run(["git", "-C", self._repo(repo), "merge-base", a, b])
            return r.stdout.strip() if r and r.returncode == 0 else None
        return self._m(("mb", repo, a, b), f)

    def changed_files(self, repo, base, sha):
        r = _run(["git", "-C", self._repo(repo), "diff", "--name-only", base, sha])
        return r.stdout.split() if r and r.returncode == 0 else None

    def show(self, repo, ref, path_):
        def f():
            r = _run(["git", "-C", self._repo(repo), "show", f"{ref}:{path_}"])
            return r.stdout if r and r.returncode == 0 else None
        return self._m(("show", repo, ref, path_), f)

    def docs_file(self, path_):
        """A file on the fork's docs branch (remote first, then a local docs branch)."""
        self.fetch()
        for ref in (self._ref("fork", self.docs_branch), f"refs/heads/{self.docs_branch}"):
            t = self.show("fork", ref, path_)
            if t is not None:
                return t
        return None

    def pin(self, branch):
        """The integration pin of a branch (integration.lock on the fork's local/integration-tools)."""
        self.fetch()
        text = self.show("fork", self._ref("fork", "local/integration-tools"), "integration.lock") or ""
        for line in text.splitlines():
            w = line.split()
            if len(w) >= 2 and w[0] == branch:
                return w[1]
        return None

    def integration_list(self):
        self.fetch()
        text = self.show("fork", self._ref("fork", "local/integration-tools"), "integration.txt") or ""
        return [l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]

    # --- github -----------------------------------------------------------------------------------------------------

    def _gh_json(self, args, timeout=40):
        r = _run([self.gh, *args], timeout=timeout)
        if not r or r.returncode != 0:
            return None
        try:
            return json.loads(r.stdout or "null")
        except ValueError:
            return None


    def release(self, tag):
        """{tag, url} of the GitHub release for `tag` in our repo, {} when none, None when gh failed."""
        def f():
            r = _run([self.gh, "release", "view", tag, "-R", policy.repos()["ours"], "--json", "tagName,url"], timeout=40)
            if not r:
                return None
            if r.returncode != 0:
                return {} if "not found" in (r.stderr or "").lower() else None
            try:
                d = json.loads(r.stdout or "null") or {}
            except ValueError:
                return None
            return {"tag": d.get("tagName"), "url": d.get("url")} if d else {}
        return self._m(("release", tag), f)


    # --- docker and the live server ---------------------------------------------------------------------------------

    def live(self):
        return store.live()

    def docker_images(self, repo="osrs-openrune"):
        def f():
            r = _run(["docker", "images", repo, "--format", "{{.Repository}}:{{.Tag}}\t{{.ID}}"])
            if not r or r.returncode != 0:
                return None
            return {l.split("\t")[0]: l.split("\t")[1] for l in r.stdout.splitlines() if "\t" in l}
        return self._m(("images", repo), f)

    def container(self, name):
        def f():
            r = _run(["docker", "inspect", name, "--format", "{{.Config.Image}}\t{{.Image}}\t{{.State.Status}}\t{{.State.StartedAt}}"])
            if not r or r.returncode != 0:
                return None
            w = r.stdout.strip().split("\t")
            return {"image": w[0], "image_id": w[1], "status": w[2], "started": w[3]} if len(w) == 4 else None
        return self._m(("container", name), f)

    def containers(self, prefix=""):
        def f():
            r = _run(["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}\t{{.Image}}"])
            if not r or r.returncode != 0:
                return None
            out = []
            for l in r.stdout.splitlines():
                w = l.split("\t")
                if len(w) == 3 and w[0].startswith(prefix):
                    out.append({"name": w[0], "status": w[1], "image": w[2]})
            return out
        return self._m(("containers", prefix), f)

    # --- local facts --------------------------------------------------------------------------------------------------

    def evidence_files(self, d):
        if not d:
            return []
        if not os.path.isabs(d):
            d = os.path.join(ROOT, d)
        try:
            return sorted(os.listdir(d))
        except OSError:
            return []

    def evidence_glob(self, d, pattern):
        if not os.path.isabs(d):
            d = os.path.join(ROOT, d)
        return sorted(glob.glob(os.path.join(d, pattern)))

    def read_file(self, p):
        try:
            with open(p, errors="replace") as f:
                return f.read()
        except OSError:
            return None

    def alive(self, pid):
        return pid_alive(pid)


class FakeObserver(Observer):
    """Tests: answers from dicts. facts keys: tips {(repo, branch): sha}, contains {(repo, ref, sha): bool},
    pins {branch: sha}, live {...}, evidence {dir: [names]}, files {path: text}, alive {pid: bool}, upstream_main sha,
    changed {(base, sha): [paths]}, docs {path: text}, images {tag: id}, containers {name: dict}; a track's mixin adds
    its own (hd/tracks/server/github.py)."""

    def __init__(self, **facts):
        self.f = facts
        self._memo = {}

    def reset(self):
        pass

    def fetch(self):
        pass

    def rev(self, repo, ref):
        return self.f.get("revs", {}).get((repo, ref))

    def branch_tip(self, repo, branch):
        return self.f.get("tips", {}).get((repo, branch))

    def upstream_main(self):
        return self.f.get("upstream_main")

    def contains(self, repo, ref, sha):
        return self.f.get("contains", {}).get((repo, ref, sha))

    def merge_base(self, repo, a, b):
        return self.f.get("merge_base", {}).get((repo, a, b), "base000")

    def changed_files(self, repo, base, sha):
        return self.f.get("changed", {}).get((base, sha), ["src/x.kt"])

    def show(self, repo, ref, path_):
        return self.f.get("show", {}).get((repo, ref, path_))

    def docs_file(self, path_):
        return self.f.get("docs", {}).get(path_)

    def pin(self, branch):
        return self.f.get("pins", {}).get(branch)

    def integration_list(self):
        return self.f.get("integration_list", list(self.f.get("pins", {})))

    def release(self, tag):
        return self.f.get("releases", {}).get(tag, {})

    def live(self):
        return self.f.get("live", store.live())

    def docker_images(self, repo="osrs-openrune"):
        return self.f.get("images", {})

    def container(self, name):
        return self.f.get("containers", {}).get(name)

    def containers(self, prefix=""):
        return [dict(v, name=k) for k, v in self.f.get("containers", {}).items() if k.startswith(prefix)]

    def evidence_files(self, d):
        return self.f.get("evidence", {}).get(d, [])

    def evidence_glob(self, d, pattern):
        import fnmatch
        return [os.path.join(d, n) for n in self.evidence_files(d) if fnmatch.fnmatch(n, pattern)]

    def read_file(self, p):
        return self.f.get("files", {}).get(p, self.f.get("files", {}).get(os.path.basename(p)))

    def alive(self, pid):
        return self.f.get("alive", {}).get(pid, False)
