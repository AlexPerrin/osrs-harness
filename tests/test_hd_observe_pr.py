"""The observer's upstream PR lookup and CI rollup (what `hd contribute` waits on)."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(__file__))
from hd import tracks
from hd.tracks.server.github import rollup_state

SHA, OTHER = "a" * 40, "b" * 40
B = "fix/stile"


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
        return tracks.Observer(gh=path)

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
