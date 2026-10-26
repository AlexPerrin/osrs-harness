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

    def test_assign_skips_every_member(self):
        g(self.repo, "checkout", "-q", "-B", "dev/third", "main")
        open(os.path.join(self.repo, TOML), "a").write("third_flag = -1\n")
        gameval_ids.assign(self.repo, self.repo)
        self.assertIn("third_flag = 65533\n", open(os.path.join(self.repo, TOML)).read())


if __name__ == "__main__":
    unittest.main()
