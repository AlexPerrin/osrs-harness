"""The track interface (hd/tracks): the core orchestrates through it and imports no track internals; each track answers
the same questions (chain, facts, executor, cards, check items, briefs, commands)."""
import glob
import os
import re
import unittest

import hd_helpers as H
from hd_helpers import SHA, SHB

from hd import store, tracks
from hd.tracks.base import BaseTrack

HD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hd")


class RegistryTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def test_every_track_is_registered_and_unknown_falls_back_to_client(self):
        self.assertEqual([t.name for t in tracks.every()], ["client", "harness", "server"])
        self.assertIs(tracks.get("nope"), tracks.get("client"))
        self.assertIs(tracks.of(H.change("a-srv", "server")), tracks.get("server"))
        self.assertIs(tracks.of({"track": "harness"}), tracks.get("harness"))

    def test_chains_per_track_and_local_only(self):
        self.assertEqual(H.change("c-1", "client").chain(), ("backlog", "ready", "dev", "gate", "live"))
        self.assertEqual(H.change("h-1", "harness").terminal, "live")
        self.assertEqual(H.change("s-1", "server").chain(),
                         ("backlog", "ready", "dev", "gate", "contribute", "review", "merged"))
        loc = H.change("s-2", "server", branch="local/s-2", local_only=True)
        self.assertEqual((loc.terminal, "contribute" in loc.chain()), ("live", False))

    def test_a_stage_outside_the_chain_is_refused(self):
        ch = H.change("c-1", "client")
        with self.assertRaises(ValueError):
            store.set_stage(ch, "contribute")

    def test_the_tracks_add_their_keys_to_the_change_file(self):
        self.assertEqual(set(tracks.extra_keys()), {"upstream_pr", "finding", "review_seen"})
        ch = H.change("s-1", "server", upstream_pr=7, finding="IC_1")
        with open(ch.path) as f:
            front = f.read().split("---")[1]
        self.assertLess(front.index("booked") if "booked" in front else 0, front.index("upstream_pr"))
        self.assertEqual(store.load("s-1")["upstream_pr"], 7)

    def test_retired_stages_migrate_through_the_track(self):
        self.assertEqual(tracks.get("client").migrate_stage({"stage": "checked"}), "gate")
        srv = tracks.get("server")
        self.assertEqual([srv.migrate_stage({"stage": s}) for s in ("checked", "gated", "published", "live", "dev")],
                         ["gate", "contribute", "review", "gate", "dev"])
        self.assertEqual(srv.migrate_stage({"stage": "live", "local_only": True}), "live")


class ObserverTest(unittest.TestCase):
    def test_the_core_observer_knows_no_pull_requests_the_server_track_mixes_them_in(self):
        from hd import observe
        for name in ("upstream_pr", "upstream_ci", "fork_ci", "upstream_pr_reviews"):
            self.assertFalse(hasattr(observe.Observer, name), name)
            self.assertFalse(hasattr(observe.FakeObserver, name), name)
            self.assertTrue(hasattr(tracks.Observer, name), name)
            self.assertTrue(hasattr(tracks.FakeObserver, name), name)
        self.assertTrue(issubclass(tracks.Observer, observe.Observer))
        self.assertEqual(tracks.FakeObserver(upstream_prs={7: {"number": 7}}).upstream_pr(7), {"number": 7})


class CoreIsolationTest(unittest.TestCase):
    """The core imports no track internals and says nothing about PRs, CI or GitHub reviews."""
    CORE = ("actions", "agents", "check", "cli", "daemon", "drive", "heal", "kpi", "leases", "metrics", "policy", "stages",
            "store", "tick")
    BANNED = re.compile(r"tracks\.server|tracks\.client|tracks\.harness|upstream_pr|upstream_ci|fork_ci|\bPRs?\b|pull request|"
                        r"\bgate_state|statusCheckRollup")

    def test_core_modules(self):
        for name in self.CORE:
            with open(os.path.join(HD, name + ".py")) as f:
                text = f.read()
            hits = sorted(set(self.BANNED.findall(text)))
            self.assertEqual(hits, [], f"hd/{name}.py")

    def test_policy_keeps_each_tracks_settings_in_its_own_section(self):
        from hd import policy
        srv = policy.track("server")
        self.assertIn("ci_equivalence", srv)
        self.assertNotIn("reviewers", srv)
        self.assertEqual(sorted(srv["ci_equivalence"]),
                         ["fork_workflow", "fork_workflow_name", "format_workflow", "format_workflow_name", "upstream_advisory",
                          "upstream_required"])
        self.assertNotIn("reviewers", policy.repos())


class BaseTrackTest(unittest.TestCase):
    def test_defaults_do_nothing(self):
        t = BaseTrack()
        t.name = "x"
        self.assertEqual((t.facts({}, None), t.waiting("gate", {}), t.executor({}), t.finding_set({}),
                          t.needs_you({}, None, {}), t.check_items({}, None, "", []), t.brief({}, "dev"),
                          t.run_valid({}, {}), t.default_dod("s")), ({}, "", None, [], [], [], [], None, []))
        self.assertFalse(t.records_repo)
        self.assertEqual(t.migrate_stage({"stage": "checked"}), "gate")
        with self.assertRaises(SystemExit):
            t.record_gate({}, "PASS", "")


class ClientHarnessTrackTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def obs(self, **kw):
        return tracks.FakeObserver(**kw)

    def test_client_facts_and_waiting(self):
        ch = H.change("plug", "client", stage="gate", commit=SHA)
        t = tracks.of(ch)
        facts = t.facts(ch, self.obs(tips={("ours", "client/plug"): SHA}, contains={("ours", "master", SHA): False}))
        self.assertEqual(facts["tip"][0], SHA)
        self.assertEqual(facts["live"], (False, "master does not contain aaaaaaaaa"))
        self.assertEqual(t.waiting("gate", ch), "the merge into master")
        self.assertEqual((t.executor(ch), t.records_repo), (None, False))

    def test_harness_reads_this_repo_and_a_change_on_main_may_move(self):
        ch = H.change("hx", "harness", stage="gate", commit=SHA, branch="harness/hx")
        t = tracks.of(ch)
        self.assertEqual(t.repo_name(ch), "harness")
        self.assertFalse(t.moves_expected(ch))
        self.assertTrue(t.moves_expected(H.change("hy", "harness", commit=SHA, branch="main")))
        self.assertEqual(t.live_target(), "main")
        self.assertTrue(t.default_repo().endswith("osrs-harness") or os.path.isdir(t.default_repo()))

    def test_docs_only_client_change_needs_no_build_evidence(self):
        ch = H.change("docs", "client", stage="dev", commit=SHA)
        o = self.obs(tips={("ours", "client/docs"): SHA}, contains={("ours", "master", SHA): False},
                     changed={("base000", SHA): ["docs/a.md"]})
        items = tracks.of(ch).check_items(ch, o, "ev", [])
        self.assertTrue(all(ok for ok, _ in items), items)

    def test_client_build_evidence_names_what_is_missing(self):
        ch = H.change("net", "client", stage="dev", commit=SHA, network=True)
        o = self.obs(tips={("ours", "client/net"): SHA}, contains={("ours", "master", SHA): False})
        items = tracks.of(ch).check_items(ch, o, "ev", ["x.txt"])
        text = " | ".join(t for ok, t in items if not ok)
        self.assertIn("no repack log", text)
        self.assertIn("no device evidence", text)
        self.assertIn("netqa", text)


class ServerTrackInterfaceTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def test_server_answers_the_interface(self):
        t = tracks.get("server")
        ch = H.change("feat", "server", stage="gate", commit=SHA)
        self.assertTrue(t.records_repo)
        self.assertEqual(t.open_stages(ch), ("ready", "dev", "gate", "contribute"))
        self.assertEqual(t.waiting("contribute", ch), "the user's approval (hd contribute)")
        self.assertEqual(t.executor(ch), "gate")
        self.assertEqual(t.finding_set(ch), [])
        self.assertEqual(len(t.default_dod("s")), 4)
        self.assertIn("gate-ci", " ".join(t.brief(ch, "gate")))
        self.assertIn("AGENTS.md", " ".join(t.brief(ch, "dev")))

    def test_the_tracks_register_their_commands(self):
        import argparse
        p = argparse.ArgumentParser()
        sp = p.add_subparsers(dest="cmd")
        for t in tracks.every():
            t.register(sp)
        self.assertEqual(sorted(sp.choices), ["contribute", "gate-ci"])


if __name__ == "__main__":
    unittest.main()
