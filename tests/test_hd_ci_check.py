"""The hand-over check's CI fact: the upstream PR's checks at the commit; no PR is pending, never a fail."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(__file__))
import hd_helpers as H
from hd import check, observe, store, tick
from hd.observe import FakeObserver, rollup_state

SHA, OTHER = "a" * 40, "b" * 40
B = "fix/stile"


def ch():
    return H.change("stile", "server", stage="dev", commit=SHA, owner="sd1", evidence="re/evidence/stile",
                    branch=B, pr="https://github.com/AlexPerrin/OpenRune-Server/pull/9")


def obs(**kw):
    f = dict(tips={("fork", B): SHA}, evidence={"re/evidence/stile": ["x"]}, docs={"accuracy/stile.md": "x"}, pins={},
             live={"integration": "c" * 40})
    f.update(kw)
    return FakeObserver(**f)


def ci_items(o):
    c = store.load("stile") if os.path.exists(store.path("stile")) else ch()
    return [i for i in check.items(c, o) if "CI" in i[1]]


class CiCheckTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def test_upstream_green_passes(self):
        o = obs(upstream_prs={B: {"number": 406, "head": SHA}}, upstream_ci={(406, SHA): "success"})
        self.assertEqual([i[0] for i in ci_items(o)], [True])

    def test_upstream_red_fails(self):
        o = obs(upstream_prs={B: {"number": 406, "head": SHA}}, upstream_ci={(406, SHA): "failure"})
        self.assertEqual([i[0] for i in ci_items(o)], [False])

    def test_upstream_running_waits(self):
        o = obs(upstream_prs={B: {"number": 406}}, upstream_ci={(406, SHA): "pending"})
        self.assertEqual([i[0] for i in ci_items(o)], [None])

    def test_fork_green_accepted_without_pr(self):
        self.assertEqual([i[0] for i in ci_items(obs(ci={(B, SHA): "success"}))], [True])

    def test_no_pr_is_pending_even_with_failed_fork_run(self):
        for fork in ("none", "failure", "pending"):
            with self.subTest(fork=fork):
                items = ci_items(obs(ci={(B, SHA): fork}))
                self.assertEqual([i[0] for i in items], [None])
                self.assertIn("CI pending: runs when the PR opens or the head moves", items[0][1])

    def test_pr_head_moved_is_pending(self):
        o = obs(upstream_prs={B: {"number": 406, "head": OTHER}})   # no checks at SHA
        self.assertEqual([i[0] for i in ci_items(o)], [None])

    def test_no_ci_does_not_return_to_ready_or_dispatch(self):
        ch()
        tick.tick(obs())
        c = store.load("stile")
        self.assertEqual(c.stage, "dev")
        self.assertEqual(c["owner"], "sd1")
        self.assertFalse(c.get("check"))


class RecordedNumberTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def test_recorded_upstream_pr_number_is_used_first(self):
        c = H.change("stile", "server", stage="dev", commit=SHA, owner="sd1", evidence="re/evidence/stile", branch=B,
                     pr="https://x/9", upstream_pr=406)
        o = obs(upstream_prs={406: {"number": 406, "head": SHA}}, upstream_ci={(406, SHA): "success"})
        self.assertEqual([i[0] for i in check.items(c, o) if "CI" in i[1]], [True])


class LookupTest(unittest.TestCase):
    """Observer.upstream_pr(branch): gh's --head takes a bare branch; the fork owner is filtered client-side."""
    def gh(self, prs):
        import json, stat, tempfile
        d = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, d, True)
        path = os.path.join(d, "gh")
        with open(path, "w") as f:
            f.write("#!/bin/sh\necho \"$@\" > %s/args\ncat <<'EOF'\n%s\nEOF\n" % (d, json.dumps(prs)))
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        self.args = os.path.join(d, "args")
        return observe.Observer(gh=path)

    def pr(self, n, owner, state="OPEN"):
        return {"number": n, "url": "u", "state": state, "isDraft": False, "headRefOid": SHA, "headRefName": B,
                "headRepositoryOwner": {"login": owner}, "mergedAt": None, "title": "t"}

    def test_owner_filtered_and_no_owner_prefix(self):
        o = self.gh([self.pr(1, "someoneelse"), self.pr(406, "AlexPerrin")])
        self.assertEqual(o.upstream_pr(B)["number"], 406)
        args = open(self.args).read()
        self.assertIn("--head " + B, args)
        self.assertNotIn("AlexPerrin:", args)

    def test_no_pr_of_ours(self):
        self.assertEqual(self.gh([self.pr(1, "someoneelse")]).upstream_pr(B), {})
        self.assertEqual(self.gh([]).upstream_pr(B), {})


class RollupTest(unittest.TestCase):
    def run_(self, name, concl="SUCCESS", status="COMPLETED"):
        return {"name": name, "conclusion": concl, "status": status}

    def test_states(self):
        ok = [self.run_("build & boot"), self.run_("gameval-conflicts")]
        self.assertEqual(rollup_state(ok), "success")
        self.assertEqual(rollup_state(ok[:1]), "pending")          # a required check not reported yet
        self.assertEqual(rollup_state(ok + [self.run_("x", "FAILURE")]), "failure")
        self.assertEqual(rollup_state(ok + [self.run_("x", "", "IN_PROGRESS")]), "pending")
        self.assertEqual(rollup_state([]), "none")

    def test_real_names_and_advisory_not_required(self):
        real = [self.run_("build & boot"), self.run_("spotless (advisory)"), self.run_("gameval-conflicts")]
        self.assertEqual(rollup_state(real), "success")
        self.assertEqual(rollup_state([real[0], real[2], self.run_("spotless (advisory)", "FAILURE")]), "success")


if __name__ == "__main__":
    unittest.main()
