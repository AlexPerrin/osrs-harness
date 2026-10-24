"""The tick (BR-C2, BR-C4, BR-C5, BR-S4, BR-S9, BR-H1): each step with the agent,
batch and heal modules stubbed, FakeObserver for the world, a temp git repo for the client merge."""
import os
import subprocess
import unittest
from unittest import mock

import hd_helpers as H
from hd_helpers import SHA, SHB

from hd import drive, events, leases, stages, store, tick
from hd.tracks import FakeObserver


def stub_modules(test, **over):
    """Stub the modules the tick calls that other tests cover; return the call log."""
    calls = []
    stubs = {
        "agents.running": lambda: [], "agents.spawn": None,
        "batches.enqueue": lambda ch: calls.append(("enqueue", ch["slug"])) or True,
        "batches.advance": lambda obs: [], "batches.deploy_ready": lambda obs: None,
        "batches.deploy": lambda b, obs: (True, "deploying"), "batches.repin_due": lambda obs: None,
        "batches.repin": lambda obs: "repinned", "batches.release_due": lambda idx: None,
        "batches.new_release": lambda slugs: {"id": "rel-1"}, "batches.status": lambda: [],
        "heal.run": lambda obs, idx: [],
    }

    def spawn(ch, role, ex):
        calls.append(("spawn", ch["slug"], role, ex))
        ch["owner"] = f"{role}-x"
        store.set_stage(ch, "dev", "dispatched") if ex == "dev" else None
        store.save(ch)
        return {"name": f"{role}-x", "role": role, "pid": None}
    stubs["agents.spawn"] = spawn
    stubs.update(over)
    for dotted, fn in stubs.items():
        mod, name = dotted.split(".")
        p = mock.patch.object(getattr(tick, mod), name, fn)
        p.start()
        test.addCleanup(p.stop)
    return calls


class ReleasePublishedTest(unittest.TestCase):
    """A gated release batch becomes `published` when its GitHub release is observed, and not before."""
    def setUp(self):
        H.sandbox(self)
        store.rec_save("batches", "rel-1", {"id": "rel-1", "kind": "release", "step": "gated", "includes": [],
                                            "steps": [], "tag": "v1.2.3"})
        stub_modules(self)

    def test_published_only_when_the_release_exists(self):
        tick.tick(FakeObserver())
        self.assertEqual(store.rec_load("batches", "rel-1")["step"], "gated")
        out = tick.tick(FakeObserver(releases={"v1.2.3": {"tag": "v1.2.3", "url": "u"}}))
        self.assertEqual(store.rec_load("batches", "rel-1")["step"], "published")
        self.assertIn("release rel-1: published (v1.2.3)", " ".join(out))


class ReconcileTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)
        self.calls = stub_modules(self)

    def test_drift_repaired_and_logged(self):
        """BR-H1: the recorded stage follows the observation, both ways, with an event."""
        H.change("plug", "client", stage="gate", commit=SHA)
        obs = FakeObserver(tips={("ours", "client/plug"): SHA}, contains={("ours", "master", SHA): True})
        tick.tick(obs)
        self.assertEqual(store.load("plug").stage, "live")
        self.assertEqual(store.load("plug")["live_commit"], SHA)
        ev = [e for e in events.read(kinds=["stage"]) if e.get("change") == "plug"]
        self.assertEqual((ev[-1]["from"], ev[-1]["to"]), ("gate", "live"))
        # a revert: master no longer contains it -> drift back to gate
        obs = FakeObserver(tips={("ours", "client/plug"): SHA}, contains={("ours", "master", SHA): False})
        tick.tick(obs)
        self.assertEqual(store.load("plug").stage, "gate")
        self.assertTrue(events.read(kinds=["drift"]))

    def test_new_commit_reenters_at_ready(self):
        """BR-C2: a new commit on the branch voids the hand-over, the QA record and the booking."""
        H.change("feat", "server", stage="gate", commit=SHA, repo="/dev/clone", booked={"dev": "k", "gate": SHA})
        H.write_gate("feat", SHA)
        obs = FakeObserver(tips={("/dev/clone", "content/feat"): SHB}, pins={}, live={"integration": "c" * 40})
        tick.tick(obs)
        ch = store.load("feat")
        self.assertIsNone(ch["commit"])
        self.assertIsNone(ch["booked"])
        ev = [e for e in events.read(kinds=["stage"]) if e.get("change") == "feat"]
        self.assertEqual((ev[0]["from"], ev[0]["to"], ev[0]["commit"]), ("gate", "ready", SHB))
        self.assertIn(("spawn", "feat", "server-dev", "dev"), self.calls)   # re-dispatched in the same tick
        # a dev working on a fix pushes to the branch: not a re-entry while it owns the change
        owned = H.change("owned", "server", stage="gate", commit=SHA, owner="sd9", repo="/dev/clone")
        store.set_hold(owned, "failed", "fix the findings"); store.save(owned)
        tick.tick(FakeObserver(tips={("/dev/clone", "content/owned"): SHB}, pins={}, live={"integration": "c" * 40}))
        self.assertEqual(store.load("owned")["commit"], SHA)
        self.assertEqual(store.load("owned")["owner"], "sd9")

    def test_a_contributed_change_is_not_reentered_by_its_own_pr(self):
        H.change("feat", "server", stage="review", commit=SHA, upstream_pr=7, repo="/dev/clone")
        H.write_gate("feat", SHA)
        tick.tick(FakeObserver(tips={("/dev/clone", "content/feat"): SHB},
                               upstream_prs={7: {"number": 7, "state": "open", "draft": False, "head": SHA}}))
        ch = store.load("feat")
        self.assertEqual((ch.stage, ch["commit"]), ("review", SHA))

    def test_deps_hold_set_and_cleared(self):
        """BR-C4: a dep is done for the client when the test server runs it, whatever its upstream stage."""
        H.change("srv", "server", stage="gate", commit=SHA)
        H.change("cli", "client", deps=["srv"])
        tick.tick(FakeObserver(tips={("fork", "content/srv"): SHA}, pins={}, live={"integration": "c" * 40}))
        cli = store.load("cli")
        self.assertEqual(cli.hold, "blocked")
        self.assertEqual([c for c in self.calls if c[0] == "spawn" and c[1] == "cli"], [])   # not dispatched while blocked
        tick.tick(FakeObserver(tips={("fork", "content/srv"): SHA}, pins={"content/srv": SHA}, live={"integration": "c" * 40},
                               contains={("fork", "c" * 40, SHA): True}))
        srv = store.load("srv")
        self.assertEqual((srv.stage, srv["live_commit"]), ("gate", SHA))   # live, the upstream stage untouched
        self.assertIsNone(store.load("cli").hold)
        self.assertIn(("spawn", "cli", "client-dev", "dev"), self.calls)

    def test_a_local_only_change_ends_at_live(self):
        H.change("loc", "server", stage="gate", commit=SHA, branch="local/loc", local_only=True)
        tick.tick(FakeObserver(tips={("fork", "local/loc"): SHA}, pins={"local/loc": SHA}, live={"integration": "c" * 40},
                               contains={("fork", "c" * 40, SHA): True}))
        self.assertEqual(store.load("loc").stage, "live")


class TrainQueueTest(unittest.TestCase):
    """The test server and the upstream flow are independent: a handed-over server change joins the train at once."""
    def setUp(self):
        H.sandbox(self)
        self.calls = stub_modules(self)

    def obs(self, **kw):
        f = dict(tips={("fork", "content/feat"): SHA}, pins={}, live={"integration": "c" * 40})
        f.update(kw)
        return FakeObserver(**f)

    def test_handed_over_change_is_queued_without_any_gate(self):
        H.change("feat", "server", stage="gate", commit=SHA)
        acts = tick.tick(self.obs())
        self.assertIn(("enqueue", "feat"), self.calls)
        self.assertEqual(store.load("feat").stage, "gate")   # no QA record: still queued
        self.assertTrue(any("queued for the next train" in a for a in acts))

    def test_only_what_the_fork_has_is_queued(self):
        H.change("feat", "server", stage="gate", commit=SHA)
        tick.tick(self.obs(tips={("fork", "content/feat"): SHB}))
        tick.tick(self.obs(tips={}))
        self.assertNotIn(("enqueue", "feat"), self.calls)

    def test_a_hold_keeps_it_off_the_train_but_qa_findings_do_not(self):
        H.change("held", "server", stage="gate", commit=SHA, branch="content/held")
        ch = store.load("held"); store.set_hold(ch, "failed", "train gate"); store.save(ch)
        H.change("found", "server", stage="contribute", commit=SHA, branch="content/found")
        H.write_gate("found", SHA, "FAIL", findings=["x"])
        tick.tick(self.obs(tips={("fork", "content/held"): SHA, ("fork", "content/found"): SHA}))
        queued = [c[1] for c in self.calls if c[0] == "enqueue"]
        self.assertEqual(queued, ["found"])

    def test_already_pinned_commit_is_not_queued(self):
        H.change("feat", "server", stage="gate", commit=SHA)
        obs = self.obs(pins={"content/feat": SHA}, contains={("fork", "c" * 40, SHA): True})
        tick.tick(obs)
        self.assertNotIn(("enqueue", "feat"), self.calls)
        self.assertEqual(store.load("feat")["live_commit"], SHA)   # observed live, still at gate


class NoLoopTest(unittest.TestCase):
    """BR-S9: a dev or QA run is booked only for a head or finding set that was not booked before."""
    def setUp(self):
        H.sandbox(self)
        self.calls = stub_modules(self)

    def test_same_facts_make_a_durable_decision_hold(self):
        ch = H.change("feat", "server", stage="gate", commit=SHA)
        store.set_hold(ch, "failed", "fix the findings"); ch["booked"] = {"dev": stages.booking_key(ch, "dev")}
        store.save(ch)
        acts = tick.tick(FakeObserver(tips={("fork", "content/feat"): SHA}))
        self.assertEqual([c for c in self.calls if c[0] == "spawn"], [])
        ch = store.load("feat")
        self.assertEqual(ch.hold, "decision")
        self.assertIn("needs you", ch.hold_reason)
        self.assertTrue(any("decision hold" in a for a in acts))
        tick.tick(FakeObserver(tips={("fork", "content/feat"): SHA}))   # durable: no second run on a later tick
        self.assertEqual([c for c in self.calls if c[0] == "spawn"], [])
        self.assertEqual(drive.work(FakeObserver())["decisions"][0]["change"], "feat")

    def test_a_new_head_or_a_new_finding_set_is_booked(self):
        ch = H.change("feat", "server", stage="gate", commit=SHA)
        store.set_hold(ch, "failed", "fix it"); ch["booked"] = {"dev": stages.booking_key(ch, "dev")}
        ch["commit"] = SHB
        store.save(ch)
        tick.tick(FakeObserver(tips={("fork", "content/feat"): SHB}))
        self.assertIn(("spawn", "feat", "server-dev", "dev"), self.calls)

    def test_qa_is_booked_once_per_commit(self):
        ch = H.change("feat", "server", stage="gate", commit=SHA)
        ch["booked"] = {"gate": SHA}
        store.save(ch)
        tick.tick(FakeObserver(tips={("fork", "content/feat"): SHA}))
        self.assertEqual([c for c in self.calls if c[0] == "spawn"], [])
        self.assertEqual(store.load("feat").hold, "decision")

    def test_unhold_resets_the_booking(self):
        from hd import cli
        ch = H.change("feat", "server", stage="gate", commit=SHA)
        store.set_hold(ch, "decision", "needs you"); ch["booked"] = {"gate": SHA}; store.save(ch)
        cli.main(["unhold", "feat", "go on"])
        self.assertIsNone(store.load("feat")["booked"])
        tick.tick(FakeObserver(tips={("fork", "content/feat"): SHA}))
        self.assertIn(("spawn", "feat", "server-qa", "gate"), self.calls)

    def test_a_dry_run_holds_nothing(self):
        ch = H.change("feat", "server", stage="gate", commit=SHA)
        ch["booked"] = {"gate": SHA}; store.save(ch)
        acts = tick.tick(FakeObserver(tips={("fork", "content/feat"): SHA}), dry_run=True)
        self.assertIsNone(store.load("feat").hold)
        self.assertTrue(any("would hold" in a for a in acts))


class FindingsStepTest(unittest.TestCase):
    """BR-S4: a maintainer finding is filed once, keyed by its id."""
    def setUp(self):
        H.sandbox(self)
        self.calls = stub_modules(self)
        H.change("feat", "server", stage="review", commit=SHA, upstream_pr=7, review_seen="2026-10-24T00:00:00Z", prio="P2")
        H.write_gate("feat", SHA)
        self.pr = {"number": 7, "state": "open", "draft": False, "head": SHA}

    def obs(self, reviews):
        return FakeObserver(tips={("fork", "content/feat"): SHA}, upstream_prs={7: self.pr}, reviews={7: reviews})

    def finding(self, fid="IC_kwDOabc123", at="2026-10-24T05:00:00Z", **kw):
        return dict({"id": fid, "author": "maintainer", "body": "please drop the extra test", "at": at, "kind": "comment",
                     "url": "https://github.com/OpenRune/OpenRune-Server/pull/7#issuecomment-1"}, **kw)

    def test_filed_once_as_a_review_fix_change_on_the_same_branch(self):
        acts = tick.tick(self.obs([self.finding()]))
        (new,) = [c for c in store.all_changes() if c.get("finding")]
        self.assertEqual((new["finding"], new["branch"], new["upstream_pr"], new["track"], new["prio"]),
                         ("IC_kwDOabc123", "content/feat", 7, "server", "P0"))
        self.assertTrue(new.has_dod())
        self.assertIn("please drop the extra test", new.body)
        self.assertTrue(any("maintainer finding filed" in a for a in acts))
        self.assertEqual(events.read(kinds=["finding"])[0]["finding"], "IC_kwDOabc123")
        tick.tick(self.obs([self.finding()]))
        self.assertEqual(len([c for c in store.all_changes() if c.get("finding")]), 1)   # keyed by the id: once

    def test_not_findings(self):
        mine = self.finding("c1", author="AlexPerrin")
        bot = self.finding("c2", author="github-actions[bot]")
        approval = self.finding("c3", kind="review:approved")
        empty = self.finding("c4", body="  ")
        old = self.finding("c5", at="2026-10-23T00:00:00Z")
        tick.tick(self.obs([mine, bot, approval, empty, old]))
        self.assertEqual([c for c in store.all_changes() if c.get("finding")], [])

    def test_the_first_scan_sets_the_baseline(self):
        ch = store.load("feat"); ch["review_seen"] = None; store.save(ch)
        tick.tick(self.obs([self.finding()]))
        self.assertEqual([c for c in store.all_changes() if c.get("finding")], [])
        self.assertTrue(store.load("feat")["review_seen"])

    def test_a_review_fix_change_does_not_file_findings_itself(self):
        tick.tick(self.obs([self.finding()]))
        (new,) = [c for c in store.all_changes() if c.get("finding")]
        new["stage"] = "review"; new["commit"] = SHB; store.save(new)
        tick.tick(self.obs([self.finding(), self.finding("IC_2", body="another")]))
        self.assertEqual(len([c for c in store.all_changes() if c.get("finding")]), 2)   # filed from the parent only


class ShipTest(unittest.TestCase):
    def setUp(self):
        d = H.sandbox(self)
        self.calls = stub_modules(self)
        from helpers import commit_file, git, init_repo
        self.repo = init_repo(os.path.join(d, "repo"))
        commit_file(self.repo, "host/a.txt", "a\n")
        git(self.repo, "checkout", "-q", "-b", "client/plug")
        self.sha = commit_file(self.repo, "host/b.txt", "b\n")
        git(self.repo, "checkout", "-q", "master")
        os.environ["HD_SHIP_REPO"] = self.repo
        os.environ["HD_NO_PUSH"] = "1"
        from helpers import GIT_ENV
        for k in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"):
            os.environ[k] = GIT_ENV[k]
            self.addCleanup(os.environ.pop, k, None)
        self.addCleanup(os.environ.pop, "HD_SHIP_REPO", None)
        self.addCleanup(os.environ.pop, "HD_NO_PUSH", None)

    def test_handed_over_client_change_merges_into_master(self):
        H.change("plug", "client", stage="gate", commit=self.sha)
        obs = FakeObserver(tips={("ours", "client/plug"): self.sha}, contains={("ours", "master", self.sha): False})
        acts = tick.tick(obs)
        self.assertTrue(any("merged into master" in a for a in acts), acts)
        log = subprocess.run(["git", "-C", self.repo, "log", "-1", "--format=%s%n%b"], capture_output=True, text=True).stdout
        self.assertIn("Merge client/plug: plug", log)
        self.assertIn("Co-Authored-By: Claude", log)
        self.assertEqual(subprocess.run(["git", "-C", self.repo, "merge-base", "--is-ancestor", self.sha, "master"]).returncode, 0)
        self.assertTrue(events.read(kinds=["ship"]))

    def test_merge_failure_is_an_exception_hold(self):
        H.change("plug", "client", stage="gate", commit="f" * 40)
        obs = FakeObserver(tips={("ours", "client/plug"): "f" * 40}, contains={("ours", "master", "f" * 40): False})
        tick.tick(obs)
        ch = store.load("plug")
        self.assertEqual(ch.hold, "exception")


class DispatchTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)
        self.calls = stub_modules(self)

    def test_priority_and_slots(self):
        """BR-C5 and BR-R5: P1 first; server has 2 dev slots, client 1; the rest are stalled."""
        H.change("s-p2", "server", prio="P2"); H.change("s-p1", "server", prio="P1"); H.change("s-p3", "server", prio="P3")
        H.change("c-a", "client"); H.change("c-b", "client")
        tick.tick(FakeObserver())
        spawned = [c[1] for c in self.calls if c[0] == "spawn"]
        self.assertEqual(spawned, ["s-p1", "c-a", "s-p2"])
        t = events.read(kinds=["tick"])[-1]
        self.assertEqual(sorted(t["stalled"]), ["c-b", "s-p3"])

    def test_dispatch_waits_only_on_slots(self):
        """No instance lock exists: a held shared-resource lock never stalls a dispatch."""
        H.change("c-a", "client")
        leases.take("ghidra", "other", "busy"); leases.take("live-server", "other", "busy")
        tick.tick(FakeObserver())
        self.assertIn(("spawn", "c-a", "client-dev", "dev"), self.calls)
        self.assertNotIn("c-a", events.read(kinds=["tick"])[-1]["stalled"])

    def test_qa_is_booked_for_a_handed_over_server_change_before_it_is_live(self):
        """The aggregate does not wait for the test server."""
        H.change("feat", "server", stage="gate", commit=SHA)
        tick.tick(FakeObserver(tips={("fork", "content/feat"): SHA}, pins={}, live={"integration": "c" * 40}))
        self.assertIn(("spawn", "feat", "server-qa", "gate"), self.calls)

    def test_no_dod_no_dispatch(self):
        ch = store.new("nodod", "server", "x", stage="backlog")
        tick.tick(FakeObserver())
        self.assertEqual([c for c in self.calls if c[0] == "spawn"], [])


class DeployTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def test_deploy_takes_the_live_server_lock(self):
        """BR-B3: a pending deploy takes `live-server` for the daemon and deploys; nothing else is drained or awaited."""
        batch = {"id": "int-1", "step": "imaged"}
        deployed = []
        self.calls = stub_modules(self, **{"batches.deploy_ready": lambda obs: batch,
                                           "batches.deploy": lambda b, obs: deployed.append(b["id"]) or (True, "ok")})
        leases.take("ghidra", "cd1", "write", pid=os.getpid())   # another resource's holder does not matter
        tick.tick(FakeObserver())
        self.assertEqual(deployed, ["int-1"])
        self.assertEqual(leases.status("live-server")["holder"], leases.DAEMON)
        self.assertEqual(leases.status("ghidra")["holder"], "cd1")

    def test_deploy_waits_while_the_live_server_is_locked_by_another(self):
        batch = {"id": "int-2", "step": "imaged"}
        deployed = []
        self.calls = stub_modules(self, **{"batches.deploy_ready": lambda obs: batch,
                                           "batches.deploy": lambda b, obs: deployed.append(b["id"]) or (True, "ok")})
        leases.take("live-server", "someone", "manual restart")
        acts = tick.tick(FakeObserver())
        self.assertEqual(deployed, [])
        self.assertTrue(any("held by someone" in a for a in acts), acts)
        leases.release("live-server", "someone")
        tick.tick(FakeObserver())
        self.assertEqual(deployed, ["int-2"])


class IsolationTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def test_a_failing_step_does_not_stop_the_tick(self):
        def boom(obs):
            raise RuntimeError("gate exploded")
        calls = stub_modules(self, **{"batches.advance": boom})
        H.change("c-a", "client")
        acts = tick.tick(FakeObserver())
        self.assertTrue(any("error" in a for a in acts))
        self.assertIn(("spawn", "c-a", "client-dev", "dev"), calls)
        self.assertEqual(events.read(kinds=["error"])[0]["step"], "ship")

    def test_dry_run_changes_nothing(self):
        calls = stub_modules(self)
        H.change("c-a", "client")
        acts = tick.tick(FakeObserver(), dry_run=True)
        self.assertTrue(any("[dry run]" in a for a in acts))
        self.assertEqual([c for c in calls if c[0] == "spawn"], [])
        self.assertEqual(events.read(kinds=["tick"]), [])


if __name__ == "__main__":
    unittest.main()
