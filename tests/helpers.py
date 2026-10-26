"""A sandbox (state, definitions, config in a temp dir) and a fake facts source for the tests."""
import os
import shutil
import tempfile
import unittest
from unittest import mock

HD_HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHA = {k: k * 40 for k in "abcdef0123456789"}


class R:
    def __init__(self, rc=0, out="", err=""):
        self.returncode, self.stdout, self.stderr = rc, out, err


class Fake:
    """The facts a test sets: refs {ref: sha}, anc {(tip, sha)} containment, prs {branch: pr}, checks {(n, sha): state},
    comments {n: [..]}, ci {(branch, sha, wf): state}, releases {tag: {...}}, procs {(pid, start)}, containers, images."""
    def __init__(self, **f):
        self.f = f
        self.calls = []
        self.unknown = set(f.get("unknown", ()))

    def git(self, repo, *args):
        self.calls.append(("git", repo) + args)
        if args[:2] == ("branch", "--show-current"):
            return R(0, self.f.get("branch", "master") + "\n")
        if args[0] == "log":
            return R(0, self.f.get("log", ""))
        return R(0, "")

    def fetch(self, repo, remote):
        return remote not in self.unknown

    def remotes(self, repo):
        return ["origin", "fork"]

    def rev(self, repo, ref):
        if ref in self.unknown or ref.split("/")[0] in self.unknown:
            return None
        return self.f.get("refs", {}).get(ref, "")

    def contains(self, repo, ref, sha):
        tip = ref if len(ref) == 40 else self.rev(repo, ref)
        if tip is None or not sha:
            return None if tip is None else False
        return tip == sha or (tip, sha) in self.f.get("anc", set())

    def pr(self, branch):
        return self.f.get("prs", {}).get(branch, {})

    def pr_checks(self, n, sha):
        return self.f.get("checks", {}).get((n, sha), "none")

    def pr_comments(self, n):
        return self.f.get("comments", {}).get(n, [])

    def fork_ci(self, branch, sha, wf):
        return self.f.get("ci", {}).get((branch, sha, wf), "none")

    def release(self, tag):
        return self.f.get("releases", {}).get(tag, {})

    def gh_ok(self):
        return self.f.get("gh_ok", True)

    def docker_ok(self):
        return self.f.get("docker_ok", True)

    def containers(self):
        return self.f.get("containers", [])

    def images(self, repo):
        return self.f.get("images", [])

    def alive(self, pid, start):
        return (pid, start) in self.f.get("procs", set())


class Sandbox(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hd-test-")
        self.state = os.path.join(self.tmp, "state")
        self.defs = os.path.join(self.tmp, "defs")
        self.ev = os.path.join(self.tmp, "evidence")
        for d in ("client", "fork", "work"):
            os.makedirs(os.path.join(self.tmp, d))
        cfg = os.path.join(self.tmp, "hd.yaml")
        with open(os.path.join(HD_HOME, "hd.yaml")) as f:
            text = f.read().replace("~/osrs-plugins-reverse", os.path.join(self.tmp, "client")) \
                .replace("~/src/OpenRune-Server", os.path.join(self.tmp, "fork")).replace("~/src/openrune-work", os.path.join(self.tmp, "work"))
        with open(cfg, "w") as f:
            f.write(text)
        self.env = mock.patch.dict(os.environ, {"HD_STATE": self.state, "HD_DEFS": self.defs, "HD_CONFIG": cfg})
        self.env.start()
        from hd import steps, store
        self.store, self.steps = store, steps
        self._ev = mock.patch.object(steps, "evidence", lambda ch: os.path.join(self.ev, ch["slug"]))
        self._ev.start()

    def tearDown(self):
        self._ev.stop()
        self.env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def change(self, slug, track="client", body="## Change\nx\n## Definition of done\n- y\n", **meta):
        m = {"slug": slug, "track": track, "kind": "change", "priority": "P2", "deps": [], "created": "2026-10-25T00:00:00Z",
             "title": slug, **meta}
        return self.store.save_definition("changes", slug, m, body)

    def goal(self, slug="client-api", target=100):
        return self.store.save_definition("goals", slug, {"slug": slug, "track": "client", "target": target, "measure": "x.sh"}, "## Goal\n")

    def evidence(self, slug, *names):
        d = os.path.join(self.ev, slug)
        os.makedirs(d, exist_ok=True)
        for n in names:
            with open(os.path.join(d, n), "w") as f:
                f.write("telemetry: x\n" * 7 + "patched RSA modulus at 0x1\npatched /jav_config.ws at 0x2\n"
                        "patched /x/net/openid/appauth/n.smali\n" if n.startswith("repack")
                        else f"Pushed `{SHA['a'][:9]}`\n" if n == "pr-comment.md" else "x\n")   # a prepared comment names its head
        return d

    def ctx(self, F):
        return self.steps.Ctx(self.store.config(), F)
