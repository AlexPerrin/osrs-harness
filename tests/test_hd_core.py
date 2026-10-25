"""hd foundation: the store (BR-C1, BR-C3), the event log (BR-H4), the generic lifecycle (BR-C4, BR-S9), the hand-over check, the shared-resource locks (BR-R1..R4)."""
import os
import unittest

import hd_helpers as H
from hd_helpers import SHA, SHB

from hd import check, events, leases, policy, stages, store, util


class StoreTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def test_new_ready_needs_dod(self):
        with self.assertRaises(ValueError):
            store.new("xx", "server", "x")
        ch = store.new("xx", "server", "x", stage="backlog")
        self.assertEqual(ch.stage, "backlog")
        self.assertFalse(ch.has_dod())

    def test_roundtrip_and_log(self):
        ch = store.new("feat-a", "client", "Feat A", dod=["built", "tried on the device"], network=True)
        self.assertEqual(ch["role"], "client-dev")
        self.assertEqual(ch.dod_unticked(), ["- [ ] built", "- [ ] tried on the device"])
        store.set_stage(ch, "dev", "dispatched", commit=None)
        store.set_hold(ch, "failed", "fix the thing")
        store.save(ch)
        back = store.load("feat-a")
        self.assertEqual(back.stage, "dev")
        self.assertEqual(back.hold, "failed")
        self.assertEqual(back.hold_reason, "fix the thing")
        self.assertTrue(back["network"])
        self.assertIn("ready -> dev: dispatched", back.body)
        self.assertEqual([m for _, m in back.log_lines()][0], "created (ready)")
        store.clear_hold(back)
        self.assertIsNone(back.hold)

    def test_bad_slug(self):
        with self.assertRaises(ValueError):
            store.new("Bad Slug", "client", "x", dod=["a"])

    def test_state_records_and_live(self):
        store.rec_save("runs", "sd1", {"role": "server-dev"})
        self.assertEqual(store.rec_load("runs", "sd1")["role"], "server-dev")
        self.assertEqual([r["id"] for r in store.rec_all("runs")], ["sd1"])
        store.rec_delete("runs", "sd1")
        self.assertEqual(store.rec_all("runs"), [])
        store.set_live({"integration": SHA})
        self.assertEqual(store.live()["integration"], SHA)


class EventsTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def test_append_only_utc(self):
        util.freeze("2026-10-21T01:00:00Z")
        self.addCleanup(util.freeze, None)
        events.emit("stage", change="a", **{"from": "ready", "to": "dev"})
        util.freeze("2026-10-21T02:00:00Z")
        events.emit("lease", action="take", resource="ghidra", holder="cd1")
        evs = events.read()
        self.assertEqual([e["kind"] for e in evs], ["stage", "lease"])
        self.assertEqual(evs[0]["ts"], "2026-10-21T01:00:00Z")
        self.assertEqual(events.read(kinds=["lease"])[0]["holder"], "cd1")
        self.assertEqual(len(events.read(since="2026-10-21T01:30:00Z")), 1)
        self.assertEqual(events.read(change="a")[0]["to"], "dev")
        with open(events.path()) as f:
            self.assertEqual(len(f.read().splitlines()), 2)


class StagesTest(unittest.TestCase):
    """The generic climb (the chains and facts come from the tracks, hd/tracks/)."""

    def setUp(self):
        H.sandbox(self)

    def obs(self, **facts):
        from hd.tracks import FakeObserver
        return FakeObserver(**facts)

    def test_deps_block_ready(self):
        dep = H.change("srv", "server", stage="gate", commit=SHA)
        cli = H.change("cli", "client", deps=["srv"])
        idx = store.index()
        st, why, _ = stages.derive(cli, self.obs(), idx)
        self.assertEqual(st, "ready")
        self.assertIn("waiting for srv (gate)", why)
        dep["live_commit"] = SHA   # the test server runs it: live, whatever the server's own chain says
        store.save(dep)
        st, why, _ = stages.derive(cli, self.obs(), store.index())
        self.assertEqual(why, "a free slot")

    def test_client_live_is_master(self):
        ch = H.change("plug", "client", stage="gate", commit=SHA)
        o = self.obs(tips={("ours", "client/plug"): SHA}, contains={("ours", "master", SHA): False})
        st, why, _ = stages.derive(ch, o, {})
        self.assertEqual(st, "gate")
        self.assertIn("the merge into master", why)
        o = self.obs(tips={("ours", "client/plug"): SHA}, contains={("ours", "master", SHA): True})
        self.assertEqual(stages.derive(ch, o, {})[:2], ("live", ""))

    def test_unknown_never_regresses(self):
        ch = H.change("plug", "client", stage="live", commit=SHA)
        o = self.obs(tips={("ours", "client/plug"): SHA}, contains={})
        self.assertEqual(stages.derive(ch, o, {})[0], "live")

    def test_reached_is_relative_to_the_chain(self):
        self.assertFalse(H.change("a-cli", "client", stage="dev").reached("gate"))
        self.assertTrue(H.change("a-cl2", "client", stage="live").reached("gate"))

    def test_next_executor_core_rules(self):
        self.assertEqual(stages.next_executor(H.change("ch-a", "client")), "dev")
        self.assertIsNone(stages.next_executor(H.change("ch-d", "client", stage="gate", commit=SHA)))
        ch = H.change("ch-e", "client", stage="gate", commit=SHA)
        store.set_hold(ch, "failed", "the user asked for a fix"); store.save(ch)
        self.assertEqual(stages.next_executor(store.load("ch-e")), "dev")
        ch = H.change("ch-f", "client", deps=["ch-a"])   # an open dep blocks: derived from the index, never held
        self.assertEqual(stages.next_executor(ch), "dev")
        self.assertIsNone(stages.next_executor(ch, store.index()))
        ch = H.change("ch-g", "client")
        store.set_hold(ch, "decision", "ask"); store.save(ch)
        self.assertIsNone(stages.next_executor(store.load("ch-g")))

    def test_booking_key_is_the_head_and_the_finding_set(self):
        """BR-S9: the same head and finding set is the same key; a verifier is keyed by the head alone."""
        ch = H.change("feat", "server", stage="gate", commit=SHA)
        k1 = stages.booking_key(ch, "dev")
        self.assertEqual(k1, stages.booking_key(ch, "dev"))
        ch["commit"] = SHB
        self.assertNotEqual(k1, stages.booking_key(ch, "dev"))
        self.assertEqual(stages.booking_key(ch, "gate"), SHB)
        ch["booked"] = {"dev": stages.booking_key(ch, "dev")}
        self.assertTrue(stages.would_loop(ch, "dev"))
        self.assertFalse(stages.would_loop(ch, "gate"))


class CheckTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def obs(self, **facts):
        from hd.tracks import FakeObserver
        return FakeObserver(**facts)

    def test_client_full(self):
        ch = H.change("plug", "client", stage="dev", commit=SHA, evidence="re/evidence/plug")
        o = self.obs(tips={("ours", "client/plug"): SHA}, contains={("ours", "master", SHA): False},
                     evidence={"re/evidence/plug": ["repack.log", "logcat-plug.txt"]},
                     files={"repack.log": "telemetry: a\n" * 7})
        ok, its = check.run(ch, o)
        self.assertTrue(ok, check.render(ch, its))
        o.f["files"]["repack.log"] = "telemetry: a\n" * 6
        ok, its = check.run(ch, o)
        self.assertFalse(ok)
        self.assertTrue(any("6 telemetry lines" in t for _, t in its))

    def test_client_docs_only(self):
        ch = H.change("docs", "client", stage="dev", commit=SHA)
        o = self.obs(tips={("ours", "client/docs"): SHA}, contains={("ours", "master", SHA): False},
                     changed={("base000", SHA): ["docs/a.md", "README.md"]})
        ok, its = check.run(ch, o)
        self.assertTrue(ok, check.render(ch, its))

    def test_client_network_and_master(self):
        ch = H.change("net", "client", stage="dev", commit=SHA, network=True, evidence="re/evidence/net")
        o = self.obs(tips={("ours", "client/net"): SHA}, contains={("ours", "master", SHA): True},
                     evidence={"re/evidence/net": ["repack.log", "logcat.txt"]}, files={"repack.log": "telemetry: x\n" * 7})
        ok, its = check.run(ch, o)
        self.assertFalse(ok)
        texts = [t for o_, t in its if not o_]
        self.assertTrue(any("already on master" in t for t in texts))
        self.assertTrue(any("netqa" in t for t in texts))


class LeaseTest(unittest.TestCase):
    """The locks on shared resources (integration, live-server, ghidra); client instances are not resources."""

    def setUp(self):
        H.sandbox(self)

    def test_take_and_release(self):
        ok, _ = leases.take("ghidra", "cd1", "write", pid=os.getpid(), change="plug")
        self.assertTrue(ok)
        ok, msg = leases.take("ghidra", "cd2", "other")
        self.assertFalse(ok)
        self.assertIn("held by cd1", msg)
        self.assertTrue(leases.holds("ghidra", "cd1"))
        self.assertEqual(leases.status("ghidra")["change"], "plug")
        ok, _ = leases.release("ghidra", "cd2")
        self.assertFalse(ok)
        ok, _ = leases.release("ghidra", "cd1")
        self.assertTrue(ok)
        self.assertIsNone(leases.status("ghidra")["holder"])
        kinds = [e["action"] for e in events.read(kinds=["lease"])]
        self.assertEqual(kinds, ["take", "deny", "release"])

    def test_the_daemon_releases_any_holder(self):
        leases.take("integration", "ig1", "train")
        ok, _ = leases.release("integration", leases.DAEMON)
        self.assertTrue(ok)

    def test_client_instances_are_not_resources(self):
        """Dispatch waits on slots only: no device or desktop lock, grant, drain or instance list exists."""
        self.assertEqual(sorted(policy.resources()), ["ghidra", "integration", "live-server"])
        for name in ("device", "desktop", "desktop2"):
            ok, msg = leases.take(name, "cd1", "x")
            self.assertFalse(ok)
            self.assertIn("unknown resource", msg)
        for gone in ("grant", "revoke", "drain", "undrain", "heartbeat"):
            self.assertFalse(hasattr(leases, gone), gone)
        for t in policy.get()["tracks"].values():
            self.assertNotIn("instances", t)
            self.assertNotIn("qa_instances", t)
        self.assertFalse(hasattr(policy, "instances"))

    def test_bound_to_the_run_process(self):
        """feedback-atomic-not-time: a lock of a daemon-spawned agent is in use while its process lives, idle the
        moment the run ended or its process died, whatever the clock says."""
        store.rec_save("runs", "sd9", {"name": "sd9", "pid": os.getpid(), "ended": None})
        leases.take("ghidra", "sd9", "ab")
        self.assertEqual(leases.status("ghidra")["pid"], os.getpid())
        util.freeze(util.now() + __import__("datetime").timedelta(hours=9))
        self.addCleanup(util.freeze, None)
        self.assertEqual(leases.idle("ghidra"), (False, f"pid {os.getpid()} alive"))
        store.rec_save("runs", "sd9", {"name": "sd9", "pid": os.getpid(), "ended": "2026-10-21T00:00:00Z", "exit": "ok"})
        idle, why = leases.idle("ghidra")
        self.assertTrue(idle)
        self.assertIn("run sd9 ended", why)
        leases.reclaim("ghidra", why)
        self.assertIsNone(leases.status("ghidra")["holder"])
        ev = events.read(kinds=["lease"])[-1]
        self.assertEqual((ev["action"], ev["holder"]), ("reclaim", "sd9"))

    def test_nothing_attached_is_never_idle_by_the_clock(self):
        leases.take("ghidra", "sq1", "gate")
        util.freeze(util.now() + __import__("datetime").timedelta(hours=40))
        self.addCleanup(util.freeze, None)
        self.assertEqual(leases.idle("ghidra"), (False, "nothing attached"))

    def test_dead_attached_pid_is_idle(self):
        leases.take("ghidra", "sd1", "ab", pid=2 ** 22 + 12345)
        idle, why = leases.idle("ghidra")
        self.assertTrue(idle)
        self.assertIn("is dead", why)

    def test_unknown_resource(self):
        ok, msg = leases.take("toaster", "x")
        self.assertFalse(ok)


class PolicyTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def test_roles_and_tracks(self):
        self.assertEqual(policy.role_for("server", "dev"), "server-dev")
        self.assertEqual(policy.role_for("server", "gate"), "server-qa")
        self.assertEqual(policy.role_for("client", "gate"), "client-qa")
        self.assertEqual(policy.branch_track("fix/x"), "server")
        self.assertEqual(policy.branch_track("client/x"), "client")
        self.assertIsNone(policy.branch_track("acc/x"))


class UtilTest(unittest.TestCase):
    def test_local_time(self):
        self.assertEqual(util.local("2026-10-20T23:50:00Z"), "7:50 PM EDT 10-20")
        self.assertEqual(util.ago("2026-10-20T23:50:00Z", util.parse("2026-10-21T00:13:00Z")), "23 min")
        self.assertTrue(util.slug_ok("fix-genie"))
        self.assertFalse(util.slug_ok("Fix Genie"))


if __name__ == "__main__":
    unittest.main()
