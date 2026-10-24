"""hd agents (BR-G1..G4): the brief, spawn (a booked console run), run-link, run-end, stop, lingering."""
import os
import unittest

import hd_helpers as H
from hd_helpers import SHA

from hd import agents, events, leases, store, util

HD = agents.HD


class AgentsTest(unittest.TestCase):
    def setUp(self):
        self.d = H.sandbox(self)
        self.addCleanup(util.freeze, None)

    def test_brief_dev(self):
        ch = H.change("feat", "server")
        store.set_hold(ch, "failed", "gate FAIL: the drop rate is 1/128, not 1/64")
        ch["owner"] = "sd31"
        store.save(ch)
        ch = store.load("feat")
        b = agents.brief(ch, "server-dev", "dev")
        self.assertTrue(b.startswith("Harness change `feat`"), b.splitlines()[0])
        for want in ("Your name is `sd31`", f"Change file: {ch.path}",
                     "Start your own client (its own port and account state)", "stop it when you are done",
                     f"{HD} handover feat --branch content/feat --commit <sha> --evidence "
                     f"{os.environ['HD_EVIDENCE_DIR']}/feat --summary",
                     f"{HD} block feat --by <other-slug>", f"{HD} new --track server --slug <x>", f"{HD} fail feat",
                     f"Evidence goes in {os.environ['HD_EVIDENCE_DIR']}/feat/",
                     "Hold `failed`: gate FAIL: the drop rate is 1/128, not 1/64", "SAME branch `content/feat`",
                     "accuracy/<slug>.md", "green CI", "<scratchpad>/<your-name>/", "never screenshots",
                     "## Definition of done", "- [x] done"):
            self.assertIn(want, b, want)
        self.assertNotIn("## Log", b)
        self.assertNotIn("lease", b.lower())   # no instance grants or lock steps in a brief
        self.assertNotIn("Instances granted", b)

    def test_brief_gate_and_train(self):
        ch = H.change("feat", "server", stage="live", commit=SHA, owner="sq31")
        b = agents.brief(ch, "server-qa", "gate")
        self.assertIn(f"{HD} gate feat PASS|FAIL", b)
        self.assertIn(f"`content/feat` at `{SHA}`", b)
        batch = {"id": "int-20261021-1", "kind": "train", "step": "exception", "exception": "CONFLICT in Foo.kt",
                 "owner": "ig1"}
        b = agents.brief(batch, "integrator", "train")
        self.assertTrue(b.startswith("Harness change `int-20261021-1`"))
        self.assertIn(f"{HD} resolve int-20261021-1", b)
        self.assertIn("CONFLICT in Foo.kt", b)
        self.assertIn(f"Work from the OpenRune fork clone {agents.fork_clone()}", b)

    def test_integrator_is_booked_for_its_batch(self):
        store.rec_save("batches", "int-2", {"id": "int-2", "kind": "train", "step": "exception", "exception": "x"})
        rec = agents.spawn(store.rec_load("batches", "int-2"), "integrator", "train")
        self.assertEqual((rec["stage"], rec["batch"], rec["role"]), ("train", "int-2", "integrator"))
        self.assertIn(f"Work from the OpenRune fork clone {agents.fork_clone()}", open(rec["log"]).read())

    def test_spawn_books_a_console_run(self):
        ch = H.change("feat", "server")
        rec = agents.spawn(ch, "server-dev", "dev")
        self.assertEqual(rec["name"], "sd31")
        self.assertEqual((rec["console"], rec.get("agent_id")), (True, None))
        self.assertNotIn("budget", rec)
        self.assertNotIn("instances", rec)   # dispatch books a slot only; the agent starts its own client
        back = store.load("feat")
        self.assertEqual((back.stage, back["owner"]), ("dev", "sd31"))
        self.assertNotIn("instances", back)
        self.assertIn("ready -> dev: dispatched to sd31", back.body)
        self.assertEqual(store.rec_load(agents.RUNS, "sd31")["change"], "feat")
        with open(rec["log"]) as f:
            self.assertTrue(f.read().startswith("Harness change `feat`"))
        ev = [e for e in events.read(kinds=["agent"]) if e["action"] == "start"][-1]
        self.assertEqual((ev["name"], ev["stage"]), ("sd31", "dev"))
        req = [e for e in events.read(kinds=["agent"]) if e["action"] == "request"][-1]
        self.assertEqual((req["name"], req["role"], req["worktree"], req["log"]), ("sd31", "server-dev", False, rec["log"]))
        self.assertEqual([r["name"] for r in agents.running()], ["sd31"])   # counts against the cap and the slots

    def test_spawn_gate_and_failed_hold_kept(self):
        ch = H.change("feat", "server", stage="live", commit=SHA)
        store.set_hold(ch, "failed", "fix it")
        store.save(ch)
        rec = agents.spawn(store.load("feat"), "server-qa", "gate")
        self.assertEqual(rec["name"], "sq31")
        back = store.load("feat")
        self.assertEqual((back.stage, back.hold), ("live", "failed"))
        rec = agents.spawn(H.change("plug", "client"), "client-dev", "dev")
        self.assertEqual(rec["name"], "cd48")

    def test_run_end_books_cost_and_frees(self):
        ch = H.change("feat", "server")
        rec = agents.spawn(ch, "server-dev", "dev")
        leases.take("ghidra", rec["name"], "write")
        agents.link(rec["name"], "agent-1")
        r = agents.end(rec["name"], "ok", turns=42, tokens=6200, minutes=25.0, result="handed over")
        self.assertEqual((r["exit"], r["turns"], r["tokens"], r["agent_id"]), ("ok", 42, 6200, "agent-1"))
        back = store.load("feat")
        self.assertEqual(back["cost"], {"runs": 1, "turns": 42, "tokens": 6200, "minutes": 25.0})
        self.assertIsNone(back["owner"])
        self.assertIn(f"run {rec['name']} ended: 42 turns, 6200 tokens, exit ok", back.body)
        ev = events.read(kinds=["agent"])[-1]
        self.assertEqual((ev["action"], ev["tokens"], ev["exit"]), ("end", 6200, "ok"))
        self.assertIsNone(leases.status("ghidra")["holder"])   # a run's locks end with it
        self.assertEqual(agents.running(), [])
        again = agents.end(rec["name"], "error")   # ended once
        self.assertEqual(again["exit"], "ok")
        self.assertIsNone(agents.end("nobody"))

    def test_stop_books_the_end_and_asks_the_console(self):
        ch = H.change("feat", "server")
        rec = agents.spawn(ch, "server-dev", "dev")
        r = agents.stop(rec["name"], "test")
        self.assertEqual(r["exit"], "stopped:test")
        self.assertTrue(store.rec_load(agents.RUNS, rec["name"])["ended"])
        self.assertEqual(events.read(kinds=["agent"])[-1]["exit"], "stopped:test")
        self.assertEqual(agents.running(), [])
        self.assertIsNone(agents.stop("nobody", "x"))
        sr = [e for e in events.read(kinds=["agent"]) if e["action"] == "stop-request"]
        self.assertEqual((sr[-1]["name"], sr[-1]["why"]), (rec["name"], "test"))
        self.assertFalse(store.rec_load(agents.RUNS, rec["name"]).get("stop_done"))
        agents.mark_stopped(rec["name"])
        self.assertTrue(store.rec_load(agents.RUNS, rec["name"])["stop_done"])

    def test_lingering_on_the_owner_field_alone(self):
        util.freeze("2026-10-21T01:00:00Z")
        ch = H.change("feat", "server")
        rec = agents.spawn(ch, "server-dev", "dev")
        self.assertEqual(agents.lingering(store.index()), [])
        ch = store.load("feat")
        store.set_stage(ch, "checked", "hand-over check PASS", commit=SHA)
        ch["owner"] = None   # the check clears the owner (tick.run_check)
        store.save(ch)
        got = agents.lingering(store.index())   # at once: no grace (feedback-atomic-not-time)
        self.assertEqual([(r["name"], why) for r, why in got], [(rec["name"], "lingering: owner is None (change at checked)")])
        # a dev run on a live change under a failed hold (BR-S3) is not lingering while it owns the change
        held = H.change("fixme", "server", stage="live", commit=SHA)
        store.set_hold(held, "failed", "gate FAIL"); store.save(held)
        rec2 = agents.spawn(store.load("fixme"), "server-dev", "dev")
        util.freeze("2026-10-21T01:30:00Z")
        self.assertNotIn(rec2["name"], [r["name"] for r, _ in agents.lingering(store.index())])
        agents.stop(rec2["name"], "test")

    def test_lingering_gate_and_train(self):
        util.freeze("2026-10-21T01:00:00Z")
        ch = H.change("feat", "server", stage="live", commit=SHA)
        agents.spawn(ch, "server-qa", "gate")
        store.rec_save("batches", "int-1", {"id": "int-1", "kind": "train", "step": "exception", "exception": "x"})
        batch = store.rec_load("batches", "int-1")
        agents.spawn(batch, "integrator", "train")
        util.freeze("2026-10-21T01:30:00Z")
        self.assertEqual(agents.lingering(store.index()), [])
        ch = store.load("feat")
        ch["gated_commit"] = SHA
        store.save(ch)
        store.rec_save("batches", "int-1", dict(batch, step="rebuilding"))
        util.freeze("2026-10-21T01:40:00Z")
        whys = sorted(why for _, why in agents.lingering(store.index()))
        self.assertEqual(whys, ["lingering: batch at rebuilding", "lingering: gate recorded"])


    def test_gate_of_live_change_ignores_its_old_batch(self):
        # a live change carries the batch it went live in (step `live`); its own gate run must not follow that step
        ch = H.change("feat", "server", stage="live", commit=SHA, batch="int-1")
        store.rec_save("batches", "int-1", {"id": "int-1", "kind": "train", "step": "live"})
        rec = agents.spawn(ch, "server-qa", "gate")
        self.assertNotIn("batch", rec)
        self.assertEqual(agents.lingering(store.index()), [])


if __name__ == "__main__":
    unittest.main()


if __name__ == "__main__":
    unittest.main()
