"""hd.drive (v4): the console's one work list. Every item is derived from observed records and disappears when its fact
changes; the CLI commands the console runs (run-link, run-end, run-stopped) are what removes spawns and stops."""
import io
import json
import unittest
from contextlib import redirect_stdout

import hd_helpers as H
from hd_helpers import SHA

from hd import agents, cli, drive, store
from hd.tracks import FakeObserver

OBS = FakeObserver(upstream_prs={}, docs={}, records=[])


class DriveTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def test_spawn_request_until_linked_then_ended(self):
        rec = agents.spawn(H.change("feat", "client"), "client-dev", "dev")
        (s,) = drive.work(OBS)["spawn"]
        self.assertEqual((s["name"], s["role"], s["change"], s["worktree"]), (rec["name"], "client-dev", "feat", True))
        self.assertTrue(s["brief"].endswith(f"{rec['name']}.log"))
        self.assertIn(f"run-link {rec['name']} <agent-id>", s["link"])
        agents.link(rec["name"], "a-1")
        self.assertEqual(drive.work(OBS)["spawn"], [])
        agents.end(rec["name"], "ok")
        self.assertEqual(drive.work(OBS)["spawn"], [])

    def test_worktree_only_for_the_roles_that_have_it(self):
        agents.spawn(H.change("srv", "server"), "server-dev", "dev")
        self.assertFalse(drive.work(OBS)["spawn"][0]["worktree"])

    def test_stop_request_until_the_console_marks_it(self):
        rec = agents.spawn(H.change("feat", "client"), "client-dev", "dev")
        agents.stop(rec["name"], "lingering")   # never linked: nothing to TaskStop
        self.assertEqual(drive.work(OBS)["stop"], [])
        rec = agents.spawn(H.change("feat2", "client"), "client-dev", "dev")
        agents.link(rec["name"], "a-2")
        agents.stop(rec["name"], "lingering: x")
        (s,) = drive.work(OBS)["stop"]
        self.assertEqual((s["name"], s["agent_id"], s["why"]), (rec["name"], "a-2", "lingering: x"))
        agents.mark_stopped(rec["name"])
        self.assertEqual(drive.work(OBS)["stop"], [])

    def test_decisions_and_exceptions_follow_the_holds(self):
        ch = H.change("qq", "server")
        store.set_hold(ch, "decision", "fold into the PR branch?"); store.save(ch)
        ex = H.change("ee", "server")
        store.set_hold(ex, "exception", "ship: conflict"); store.save(ex)
        stuck = H.change("ff", "server", stage="dev", commit=SHA)
        store.set_hold(stuck, "failed", "gate FAIL"); store.save(stuck)
        w = drive.work(OBS)
        self.assertEqual([(d["change"], d["question"]) for d in w["decisions"]], [("qq", "fold into the PR branch?")])
        self.assertIn("unhold qq", w["decisions"][0]["clear"])
        whats = sorted(e["what"] for e in w["exceptions"])
        self.assertEqual(len(whats), 2)
        self.assertTrue(whats[0].startswith("ee is on an exception hold"))
        self.assertTrue(whats[1].startswith("ff (dev) is on a failed hold"))
        ch = store.load("qq"); store.clear_hold(ch, "answered"); store.save(ch)
        self.assertEqual(drive.work(OBS)["decisions"], [])

    def test_a_failed_hold_a_dev_will_pick_up_is_not_an_exception(self):
        ch = H.change("gg", "server", stage="gate", commit=SHA)
        store.set_hold(ch, "failed", "gate FAIL"); store.save(ch)
        self.assertEqual(drive.work(OBS)["exceptions"], [])

    def test_train_exception_needs_the_console_only_after_its_integrator_ended(self):
        store.rec_save("batches", "int-1", {"id": "int-1", "kind": "train", "step": "exception", "exception": "CONFLICT",
                                            "steps": [{"step": "exception", "started": "2026-10-24T00:00:00Z"}]})
        self.assertEqual(drive.work(OBS)["exceptions"], [])
        rec = agents.spawn(store.rec_load("batches", "int-1"), "integrator", "train")
        self.assertEqual(drive.work(OBS)["exceptions"], [])   # the integrator is running (and listed under spawn)
        agents.end(rec["name"], "ok")
        (e,) = drive.work(OBS)["exceptions"]
        self.assertIn("int-1", e["what"])
        self.assertTrue(any("resolve int-1" in c for c in e["commands"]))

    def test_render_and_nothing_to_do(self):
        self.assertEqual(drive.render(drive.work(OBS)), "nothing to do")
        agents.spawn(H.change("feat", "client"), "client-dev", "dev")
        text = drive.render(drive.work(OBS))
        self.assertIn("== Spawn", text)
        self.assertIn("isolation: worktree", text)


class CliTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def run_cli(self, *argv):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = cli.main(list(argv))
        return rc, out.getvalue()

    def test_removed_commands_are_gone(self):
        for cmd in ("approvals", "approve", "deny", "serve", "serve-stop", "tail"):
            with self.assertRaises(SystemExit):
                self.run_cli(cmd)

    def test_version_status_and_run_commands(self):
        self.assertEqual(self.run_cli("version")[1].strip(), "hd 4.0")
        H.change("feat", "client")
        rec = agents.spawn(store.load("feat"), "client-dev", "dev")
        status = self.run_cli("status")[1]
        self.assertIn("feat", status)
        self.assertIn("not spawned: hd drive", status)
        self.assertEqual(json.loads(self.run_cli("status", "--json")[1])["runs"][0]["name"], rec["name"])
        self.assertIn(rec["name"], self.run_cli("run-link", rec["name"], "a-9")[1])
        self.assertEqual(store.rec_load("runs", rec["name"])["agent_id"], "a-9")
        self.assertIn("ok", self.run_cli("run-end", rec["name"], "--tokens", "10", "--turns", "2")[1])
        self.assertEqual(store.load("feat")["cost"]["tokens"], 10)
        self.assertIn(f"{rec['name']}", self.run_cli("agents", "--all")[1])


if __name__ == "__main__":
    unittest.main()
