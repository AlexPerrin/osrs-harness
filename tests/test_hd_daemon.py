"""hd.daemon: the loop (run once, errors as events) and the digest."""
import os
import unittest

import hd_helpers as H

from hd import daemon, events, store, util
from hd import tick as tick_mod


def at(ts, kind, **f):
    util.freeze(ts)
    return events.emit(kind, **f)


class RunTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)
        self.addCleanup(util.freeze, None)
        self.orig = tick_mod.tick
        self.addCleanup(setattr, tick_mod, "tick", self.orig)

    def test_once_writes_daemon_json(self):
        tick_mod.tick = lambda obs=None, dry_run=False: ["x"]
        util.freeze("2026-10-20T20:00:00Z")
        rec = daemon.run(interval=1, once=True)
        d = store.read_json(os.path.join(store.state_dir(), "daemon.json"))
        self.assertEqual(d["ticks"], 1)
        self.assertEqual(d["pid"], os.getpid())
        self.assertEqual(d["interval"], 1)
        self.assertEqual(d["last_tick"], "2026-10-20T20:00:00Z")
        self.assertEqual(d["actions"], 1)
        self.assertIsNotNone(d["tick_seconds"])
        self.assertEqual(rec["ticks"], 1)
        self.assertEqual([e["kind"] for e in events.read(kinds=["error"])], [])
        st = daemon.status()
        self.assertTrue(st["alive"])
        self.assertEqual(st["last_tick_local"], "4:00 PM EDT 10-20")

    def test_tick_error_is_an_event(self):
        def boom(obs=None, dry_run=False):
            raise RuntimeError("no")
        tick_mod.tick = boom
        daemon.run(interval=1, once=True)
        errs = events.read(kinds=["error"])
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs[0]["step"], "tick")
        self.assertIn("RuntimeError", errs[0]["error"])
        self.assertEqual(daemon.status()["ticks"], 1)

    def test_not_implemented_tick_is_an_event(self):
        from unittest import mock
        from hd import tick

        def boom(*a, **kw):
            raise NotImplementedError("stub")
        with mock.patch.object(tick, "tick", boom):
            daemon.run(interval=1, once=True)
        self.assertEqual(events.read(kinds=["error"])[0]["step"], "tick")

    def test_stop_without_daemon(self):
        self.assertTrue(daemon.stop()["stopped"])
        self.assertFalse(daemon.status()["alive"])


class DigestTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)
        self.addCleanup(util.freeze, None)

    def test_news_once(self):
        util.freeze("2026-10-20T20:00:00Z")
        self.assertEqual(daemon.digest(), "")
        at("2026-10-20T20:01:00Z", "lease", action="take", resource="device", holder="cd1")   # not news
        at("2026-10-20T20:02:00Z", "hold", change="feat", hold="failed", reason="spotless")
        at("2026-10-20T20:03:00Z", "deploy", result="ok", integration="a" * 40, image="osrs-openrune:241")
        at("2026-10-20T20:04:00Z", "batch", batch="t1", step="rolled-back", detail="timeout")
        at("2026-10-20T20:05:00Z", "heal", action="deadlock", resource="device", detect_min=1, recover_min=3)
        util.freeze("2026-10-20T20:07:00Z")
        text = daemon.digest()
        self.assertIn("feat failed: spotless", text)
        self.assertIn("deploy ok", text)
        self.assertIn("batch t1 rolled-back: timeout", text)
        self.assertIn("deadlock resolved", text)
        self.assertNotIn("lease", text)
        self.assertIn("4:02 PM EDT 10-20", text)
        with open(os.path.join(store.state_dir(), "digest.md")) as f:
            self.assertIn(text, f.read())
        self.assertEqual(daemon.digest(), "")
        at("2026-10-20T20:08:00Z", "hold", change="feat", hold="failed", reason="again")
        self.assertIn("feat failed: again", daemon.digest())
        self.assertEqual(daemon.digest(), "")
        self.assertIn("feat failed: spotless", daemon.digest(since="2026-10-20T20:00:00Z"))


if __name__ == "__main__":
    unittest.main()
