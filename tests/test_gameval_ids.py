import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gates"))
import gameval_ids  # noqa: E402

MAXES = "[max_ids]\nvarp = 5724\n"
TOML = "content/a/src/main/resources/gamevals.toml"


def g(repo, *a):
    subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t", *a], check=True, capture_output=True)


class GamevalIds(unittest.TestCase):
    """Two branches built at once take one id: the later holder fails the check, and assign skips every member's ids."""

    def setUp(self):
        d = tempfile.mkdtemp()
        self.repo, origin, fork = (os.path.join(d, n) for n in ("or", "origin.git", "fork.git"))
        for bare in (origin, fork):
            g(d, "init", "-q", "--bare", bare)
        g(d, "init", "-q", "-b", "main", self.repo)
        g(self.repo, "remote", "add", "origin", origin)
        g(self.repo, "remote", "add", "fork", fork)
        self.commit(".data/gamevals-binary/max-ids.toml", MAXES)
        self.commit(TOML, "[gamevals.varp]\nmain_one = 65535\n")
        g(self.repo, "push", "-q", "origin", "main")
        g(self.repo, "checkout", "-q", "--orphan", "tools")
        self.commit("integration.txt", "")
        g(self.repo, "push", "-q", "fork", "tools:local/integration-tools")
        for b, name in (("dev/first", "first_due"), ("dev/second", "second_kit")):
            g(self.repo, "checkout", "-q", "-B", b, "main")
            self.commit(TOML, f"[gamevals.varp]\nmain_one = 65535\n{name} = 65534\n")
            g(self.repo, "push", "-q", "fork", b)

    def commit(self, path, text):
        p = os.path.join(self.repo, path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(text)
        g(self.repo, "add", path)
        g(self.repo, "commit", "-q", "-m", path)

    def test_later_holder_renumbers(self):
        self.assertEqual(gameval_ids.check(self.repo, "fork/dev/first"), 0)
        self.assertEqual(gameval_ids.check(self.repo, "fork/dev/second"), 1)

    def test_an_id_upstream_main_took_later_fails_the_branch(self):
        g(self.repo, "checkout", "-q", "main")
        self.commit(".data/gamevals-binary/max-ids.toml", "[max_ids]\nvarp = 65534\n")   # main took 65534 as a base id
        self.commit(TOML, "[gamevals.varp]\nmain_one = 65535\nfoundry = 65534\n")
        g(self.repo, "push", "-q", "origin", "main")
        self.assertEqual(gameval_ids.check(self.repo, "fork/dev/first"), 1)
        g(self.repo, "checkout", "-q", "-B", "dev/fifth", "main")                         # a branch on the new main
        self.commit("x.txt", "x")
        g(self.repo, "push", "-q", "fork", "dev/fifth")
        self.assertEqual(gameval_ids.check(self.repo, "fork/dev/fifth"), 0)                # main's id is not the branch's

    def test_assign_skips_every_member(self):
        g(self.repo, "checkout", "-q", "-B", "dev/third", "main")
        open(os.path.join(self.repo, TOML), "a").write("third_flag = -1\n")
        gameval_ids.assign(self.repo, self.repo)
        self.assertIn("third_flag = 65533\n", open(os.path.join(self.repo, TOML)).read())

    def test_session_trailer_fails_the_gate(self):
        import server
        g(self.repo, "checkout", "-q", "-B", "dev/fourth", "main")
        g(self.repo, "commit", "-q", "--allow-empty", "-m", "feat: x\n\nClaude-Session: https://claude.ai/code/s")
        self.assertEqual(len(server.session_tagged(self.repo, "HEAD", "origin/main", "fork/content/none")), 1)
        self.assertEqual(server.session_tagged(self.repo, "fork/dev/first", "origin/main"), [])


if __name__ == "__main__":
    unittest.main()
