"""The harness track reads this repo's main (policy live_target), never the client repo's master; `hd dod` ticks
definition-of-done items on the store."""
import os, subprocess, sys, unittest
sys.path.insert(0, os.path.dirname(__file__))
import hd_helpers as H
from hd import check, cli, policy, ship, stages, store
from hd.observe import FakeObserver

SHA = "a" * 40
EV = {"re/evidence/hx": ["tests.txt"]}


def obs(**kw):
    f = dict(evidence=EV)
    f.update(kw)
    return FakeObserver(**f)


class PolicyTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def test_targets(self):
        self.assertEqual(policy.live_target("harness"), "main")
        self.assertEqual(policy.live_target("client"), "master")


class StagesTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def test_live_is_main_of_this_repo(self):
        ch = H.change("hx", "harness", stage="checked", commit=SHA, branch="harness/hx")
        o = obs(tips={("harness", "harness/hx"): SHA}, contains={("harness", "main", SHA): False})
        self.assertEqual(stages.derive(ch, o, {})[0], "checked")
        o = obs(tips={("harness", "harness/hx"): SHA}, contains={("harness", "main", SHA): True})
        self.assertEqual(stages.derive(ch, o, {})[:2], ("live", ""))

    def test_master_of_the_client_repo_is_not_read(self):
        ch = H.change("hx", "harness", stage="checked", commit=SHA, branch="harness/hx")
        o = obs(tips={("harness", "harness/hx"): SHA}, contains={("ours", "master", SHA): True})
        self.assertEqual(stages.derive(ch, o, {})[0], "checked")

    def test_handed_over_on_main_is_live_without_drift(self):
        ch = H.change("hx", "harness", stage="live", commit=SHA, branch="main")
        o = obs(tips={("harness", "main"): "b" * 40}, contains={("harness", "main", SHA): True})
        st, _, moved = stages.derive(ch, o, {})
        self.assertEqual((st, moved), ("live", None))


class CheckTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def texts(self, ch, o):
        return check.items(ch, o)

    def test_feature_branch_not_yet_on_main_passes(self):
        ch = H.change("hx", "harness", stage="dev", commit=SHA, branch="harness/hx", evidence="re/evidence/hx")
        o = obs(tips={("harness", "harness/hx"): SHA}, contains={("harness", "main", SHA): False})
        passed, its = check.run(ch, o)
        self.assertTrue(passed, its)
        self.assertTrue(any("not yet on main" in t for _, t in its))

    def test_feature_branch_already_on_main_fails(self):
        ch = H.change("hx", "harness", stage="dev", commit=SHA, branch="harness/hx", evidence="re/evidence/hx")
        o = obs(tips={("harness", "harness/hx"): SHA}, contains={("harness", "main", SHA): True})
        self.assertFalse(check.run(ch, o)[0])

    def test_handed_over_on_main_passes(self):
        ch = H.change("hx", "harness", stage="dev", commit=SHA, branch="main", evidence="re/evidence/hx")
        o = obs(tips={("harness", "main"): "b" * 40},
                contains={("harness", "main", SHA): True})
        passed, its = check.run(ch, o)
        self.assertTrue(passed, its)

    def test_main_not_containing_the_commit_fails(self):
        ch = H.change("hx", "harness", stage="dev", commit=SHA, branch="main", evidence="re/evidence/hx")
        o = obs(tips={("harness", "main"): "b" * 40}, contains={("harness", "main", SHA): False})
        self.assertFalse(check.run(ch, o)[0])

    def test_missing_branch_names_the_branch_not_master(self):
        ch = H.change("hx", "harness", stage="dev", commit=SHA, branch="main", evidence="re/evidence/hx")
        its = check.items(ch, obs(contains={("harness", "main", SHA): True}))
        self.assertTrue(any(o is False and "no local branch main" in t for o, t in its))
        self.assertFalse(any("master" in t for _, t in its))

    def test_client_still_reads_master(self):
        ch = H.change("plug", "client", stage="dev", commit=SHA, branch="client/plug", evidence="re/evidence/plug")
        o = obs(tips={("ours", "client/plug"): SHA}, contains={("ours", "master", SHA): False},
                evidence={"re/evidence/plug": ["x"]})
        self.assertTrue(any("not yet on master" in t for _, t in check.items(ch, o)))


class ShipTest(unittest.TestCase):
    def setUp(self):
        d = H.sandbox(self)
        from helpers import GIT_ENV, commit_file, git, init_repo
        self.repo = init_repo(os.path.join(d, "repo"), branch="main")
        commit_file(self.repo, "hd/a.txt", "a\n")
        git(self.repo, "checkout", "-q", "-b", "harness/hx")
        self.sha = commit_file(self.repo, "hd/b.txt", "b\n")
        git(self.repo, "checkout", "-q", "main")
        os.environ["HD_SHIP_REPO"] = self.repo
        self.addCleanup(os.environ.pop, "HD_SHIP_REPO", None)
        for k in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"):
            os.environ[k] = GIT_ENV[k]
            self.addCleanup(os.environ.pop, k, None)

    def test_harness_change_merges_into_main_without_push(self):
        ch = H.change("hx", "harness", stage="checked", commit=self.sha, branch="harness/hx")
        ok, msg = ship.merge_to_master(ch)
        self.assertTrue(ok, msg)
        self.assertIn("merged into main", msg)
        self.assertNotIn("pushed", msg)
        self.assertEqual(subprocess.run(["git", "-C", self.repo, "merge-base", "--is-ancestor", self.sha, "main"]).returncode, 0)

    def test_commit_already_on_main_is_shipped(self):
        from helpers import git
        git(self.repo, "merge", "-q", "--ff-only", self.sha)
        ch = H.change("hy", "harness", stage="checked", commit=self.sha, branch="main")
        self.assertEqual(ship.merge_to_master(ch), (True, "already on main"))


class DodTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)
        H.change("hx", "harness", stage="dev", dod=("one", "two", "three"), ticked=False)

    def test_ticks_the_named_items_only(self):
        self.assertEqual(cli.main(["dod", "hx", "1", "3"]) or 0, 0)
        ch = store.load("hx")
        self.assertEqual(ch.dod_unticked(), ["- [ ] two"])
        self.assertIn("- [x] one", ch.body)
        self.assertIn("dod ticked: 1, 3", ch.body)

    def test_out_of_range_changes_nothing(self):
        with self.assertRaises(SystemExit):
            cli.main(["dod", "hx", "1", "4"])
        self.assertEqual(len(store.load("hx").dod_unticked()), 3)

    def test_ticking_twice_is_harmless(self):
        cli.main(["dod", "hx", "2"])
        cli.main(["dod", "hx", "2", "2"])
        self.assertEqual(len(store.load("hx").dod_unticked()), 2)

    def test_unknown_change_exits(self):
        with self.assertRaises(SystemExit):
            cli.main(["dod", "nope", "1"])


if __name__ == "__main__":
    unittest.main()
