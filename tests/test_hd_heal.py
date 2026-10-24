"""hd heal (BR-H2): idle locks, lingering agents, dead runs, stale containers, dead batch steps, deadlock;
a broken step never stops the others."""
import os
import unittest

import hd_helpers as H
from hd_helpers import SHA

from hd import agents, batches, events, heal, leases, store, util
from hd.observe import FakeObserver


class HealTest(unittest.TestCase):
    def setUp(self):
        self.d = H.sandbox(self)
        H.env(self, HD_DOCKER=H.stub(self.d, "docker", 'echo "$@" >> "$(dirname "$0")/docker.log"\n'))
        self.addCleanup(util.freeze, None)

    def docker_log(self):
        try:
            with open(os.path.join(self.d, "docker.log")) as f:
                return f.read().splitlines()
        except OSError:
            return []

    def test_boot_container_kept_while_its_image_step_runs(self):
        store.rec_save("batches", "int-1", {"id": "int-1", "kind": "train", "step": "imaging", "steps": []})
        obs = FakeObserver(containers={"hd-boot-abc": {"status": "Exited (1) 15 seconds ago"}})
        self.assertEqual(heal.run(obs, {}), [])
        store.rec_save("batches", "int-1", {"id": "int-1", "kind": "train", "step": "exception", "steps": []})
        self.assertEqual(heal.run(obs, {}), ["container hd-boot-abc removed (Exited (1) 15 seconds ago)"])

    def test_idle_lease_reclaimed_with_evidence(self):
        util.freeze("2026-10-21T01:00:00Z")
        leases.take("ghidra", "sq1", "gate", container="qa-or-feat")
        obs = FakeObserver(containers={"qa-or-feat": {"status": "running"}})
        self.assertEqual(heal.run(obs, {}), [])   # the attached container runs
        util.freeze("2026-10-21T02:00:00Z")
        self.assertEqual(heal.run(obs, {}), [])   # the attached container runs
        obs = FakeObserver(containers={"qa-or-feat": {"status": "exited"}})
        acts = heal.run(obs, {})
        self.assertEqual(len(acts), 2)   # the reclaim, then the exited container's removal
        self.assertIn("lock ghidra reclaimed from sq1: attached container qa-or-feat is not running", acts[0])
        self.assertEqual(acts[1], "container qa-or-feat removed (exited)")
        self.assertIsNone(leases.status("ghidra")["holder"])
        ev = [e for e in events.read(kinds=["lease"]) if e["action"] == "reclaim"][-1]
        self.assertEqual((ev["holder"], ev["resource"]), ("sq1", "ghidra"))
        self.assertIn("attached container qa-or-feat is not running", ev["why"])

    def test_lingering_agent_stopped(self):
        util.freeze("2026-10-21T01:00:00Z")
        ch = H.change("feat", "server")
        rec = agents.spawn(ch, "server-dev", "dev")
        ch = store.load("feat")
        store.set_stage(ch, "checked", "check PASS", commit=SHA)
        ch["owner"] = None   # the check clears the owner
        store.save(ch)
        acts = heal.run(FakeObserver(), store.index())
        self.assertEqual(acts, [f"agent {rec['name']} stopped: lingering: owner is None (change at checked)"])
        r = store.rec_load(agents.RUNS, rec["name"])
        self.assertEqual(r["exit"], "stopped:lingering: owner is None (change at checked)")
        self.assertEqual(store.load("feat").stage, "checked")

    def test_dead_run_without_handover_back_to_ready(self):
        ch = H.change("feat", "server", stage="dev", owner="sd9")
        store.rec_save(agents.RUNS, "sd9", {"name": "sd9", "role": "server-dev", "change": "feat", "stage": "dev",
                                            "console": True, "started": util.iso(), "log": "/x", "ended": None})
        agents.end("sd9", "ok")
        self.assertIsNone(store.load("feat")["owner"])
        acts = heal.run(FakeObserver(), store.index())
        self.assertEqual(acts, ["change feat back to ready: run sd9 ended without a hand-over"])
        back = store.load("feat")
        self.assertEqual((back.stage, back["owner"]), ("ready", None))
        self.assertIn("dev -> ready: run sd9 ended without a hand-over", back.body)
        ev = events.read(kinds=["stage"])[-1]
        self.assertEqual((ev["change"], ev["from"], ev["to"]), ("feat", "dev", "ready"))
        # a change in dev whose agent is alive, or handed over, stays
        H.change("busy", "server")
        agents.spawn(store.load("busy"), "server-dev", "dev")
        H.change("handed", "server", stage="dev", commit=SHA)
        self.assertEqual(heal.run(FakeObserver(), store.index()), [])

    def test_exited_containers_removed(self):
        obs = FakeObserver(containers={"qa-or-feat": {"status": "Exited (0) 2 hours ago", "image": "x"},
                                       "qa-or-live": {"status": "Up 3 hours", "image": "x"},
                                       "hd-boot-int-1": {"status": "Exited (137) 1 hour ago", "image": "y"},
                                       "osrs-openrune": {"status": "Exited (1) 5 min ago", "image": "z"}})
        acts = heal.run(obs, {})
        self.assertEqual(acts, ["container qa-or-feat removed (Exited (0) 2 hours ago)",
                                "container hd-boot-int-1 removed (Exited (137) 1 hour ago)"])
        self.assertEqual(self.docker_log(), ["rm -f qa-or-feat", "rm -f hd-boot-int-1"])
        self.assertEqual([e["container"] for e in events.read(kinds=["heal"])], ["qa-or-feat", "hd-boot-int-1"])

    def test_dead_batch_step_is_exception(self):
        store.rec_save(batches.BATCHES, "int-1", {"id": "int-1", "kind": "train", "step": "gating", "pid": H.dead_pid(),
                                                  "includes": ["feat"], "steps": []})
        store.rec_save(batches.BATCHES, "int-2", {"id": "int-2", "kind": "train", "step": "gating", "pid": os.getpid()})
        store.rec_save(batches.BATCHES, "int-3", {"id": "int-3", "kind": "train", "step": "queued", "pid": H.dead_pid()})
        obs = FakeObserver(alive={os.getpid(): True})
        acts = heal.run(obs, {})
        self.assertEqual(len(acts), 1)
        self.assertIn("batch int-1 exception: process", acts[0])
        b = store.rec_load(batches.BATCHES, "int-1")
        self.assertEqual((b["step"], b["pid"]), ("exception", None))
        self.assertIn("died during gating", b["exception"])
        self.assertEqual(b["steps"][-1]["step"], "exception")
        self.assertEqual(store.rec_load(batches.BATCHES, "int-2")["step"], "gating")
        self.assertEqual(store.rec_load(batches.BATCHES, "int-3")["step"], "queued")
        ev = events.read(kinds=["batch"])[-1]
        self.assertEqual((ev["batch"], ev["step"]), ("int-1", "exception"))
        self.assertEqual(heal.run(obs, {}), [])

    def test_a_broken_step_never_stops_the_others(self):
        orig = batches.open_batches
        batches.open_batches = lambda kind=None: (_ for _ in ()).throw(RuntimeError("corrupt batch"))
        self.addCleanup(setattr, batches, "open_batches", orig)
        obs = FakeObserver(containers={"qa-or-x": {"status": "Exited (0) 1 hour ago"}})
        acts = heal.run(obs, {})
        self.assertEqual(acts, ["container qa-or-x removed (Exited (0) 1 hour ago)"])
        errs = {(e["step"], e["error"]) for e in events.read(kinds=["error"])}
        self.assertIn(("dead_batches", "RuntimeError: corrupt batch"), errs)


if __name__ == "__main__":
    unittest.main()
