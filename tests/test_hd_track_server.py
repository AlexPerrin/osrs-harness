"""The server track (hd/tracks/server): its chain and facts, QA's record, the hand-over check, the approval gate that
is the user's alone (BR-S3, BR-S9, BR-C2, BR-C7, BR-C8)."""
import unittest

import hd_helpers as H
from hd_helpers import SHA, SHB

from hd import check, stages, store, tracks
from hd.tracks.server import qa


class ServerChainTest(unittest.TestCase):
    """The chains (dev -> gate -> contribute -> review -> merged; client and harness end at live) from facts."""

    def setUp(self):
        H.sandbox(self)

    def obs(self, **facts):
        from hd.tracks import FakeObserver
        return FakeObserver(**facts)

    def test_server_live_needs_pin_and_live_integration(self):
        ch = H.change("feat", "server", stage="gate", commit=SHA)
        live = {"integration": "c" * 40}
        met, why = tracks.get("server").live_fact(ch, self.obs(pins={}, live=live))
        self.assertEqual((met, why), (False, "integration pin is absent, not aaaaaaaaa (next train)"))
        met, why = tracks.get("server").live_fact(ch, self.obs(pins={"content/feat": SHA}, live=live,
                                                 contains={("fork", "c" * 40, SHA): True}))
        self.assertTrue(met)
        self.assertIsNone(tracks.get("server").live_fact(ch, self.obs(pins={"content/feat": SHA}, live={}))[0])

    def test_qa_record_is_bound_to_the_commit(self):
        """A record at another commit says nothing (BR-C2); live is not a precondition of the contribution."""
        ch = H.change("feat", "server", stage="gate", commit=SHA)
        o = self.obs(tips={("fork", "content/feat"): SHA}, pins={}, live={"integration": "c" * 40})
        st, why, _ = stages.derive(ch, o, {})
        self.assertEqual(st, "gate")
        self.assertIn("QA's aggregate", why)
        H.write_gate("feat", SHB)
        self.assertEqual(qa.gate_state(ch), (None, []))
        self.assertEqual(stages.derive(ch, o, {})[0], "gate")
        H.write_gate("feat", SHA)
        st, why, _ = stages.derive(ch, o, {})
        self.assertEqual(st, "contribute")
        self.assertTrue(why.startswith("the user's approval"), why)

    def test_a_change_already_ready_upstream_needs_no_record(self):
        """Contributed before QA's record existed: it keeps its upstream stage and books no QA run."""
        ch = H.change("feat", "server", stage="review", commit=SHA, upstream_pr=7)
        o = self.obs(tips={("fork", "content/feat"): SHA},
                     upstream_prs={7: {"number": 7, "state": "open", "draft": False, "head": SHA}})
        self.assertEqual(stages.derive(ch, o, {})[0], "review")
        self.assertIsNone(stages.next_executor(ch))

    def test_a_failing_aggregate_still_reaches_the_approval_card(self):
        """The only gate is the user's approval: findings go on the card, no hold, no dev."""
        ch = H.change("feat", "server", stage="gate", commit=SHA)
        H.write_gate("feat", SHA, "FAIL", findings=["head regression", "added comment in A.kt"], checks={"style": "FAIL"})
        self.assertEqual(qa.gate_state(ch), ("FAIL", ["head regression", "added comment in A.kt"]))
        o = self.obs(tips={("fork", "content/feat"): SHA})
        self.assertEqual(stages.derive(ch, o, {})[0], "contribute")
        ch["stage"] = "contribute"
        self.assertIsNone(stages.next_executor(ch))
        self.assertIsNone(ch.hold)

    def test_review_and_merged(self):
        ch = H.change("feat", "server", stage="contribute", commit=SHA, upstream_pr=354)
        H.write_gate("feat", SHA)
        base = dict(tips={("fork", "content/feat"): SHA})
        o = self.obs(upstream_prs={354: {"number": 354, "state": "open", "draft": True, "head": SHA}}, **base)
        st, why, _ = stages.derive(ch, o, {})
        self.assertEqual(st, "contribute")
        self.assertIn("draft", why)
        o = self.obs(upstream_prs={354: {"number": 354, "state": "open", "draft": False, "head": SHB}}, **base)
        self.assertEqual(stages.derive(ch, o, {})[0], "contribute")   # the head lacks the commit
        o = self.obs(upstream_prs={354: {"number": 354, "state": "open", "draft": False, "head": SHB}},
                     contains={("fork", SHB, SHA): True}, **base)
        self.assertEqual(stages.derive(ch, o, {})[0], "review")       # a merge commit on top still has it
        o = self.obs(upstream_prs={354: {"number": 354, "state": "open", "draft": False, "head": SHA}}, **base)
        self.assertEqual(stages.derive(ch, o, {})[0], "review")
        o = self.obs(upstream_prs={354: {"number": 354, "state": "closed", "merged": True, "head": SHA}},
                     contains={("upstream", "main", SHA): True}, **base)
        self.assertEqual(stages.derive(ch, o, {})[0], "merged")

    def test_local_only_ends_at_live(self):
        ch = H.change("loc", "server", stage="gate", commit=SHA, branch="local/loc", local_only=True)
        o = self.obs(tips={("fork", "local/loc"): SHA}, pins={"local/loc": SHA}, live={"integration": "c" * 40},
                     contains={("fork", "c" * 40, SHA): True})
        st, why, _ = stages.derive(ch, o, {})
        self.assertEqual((st, why), ("live", ""))
        self.assertEqual(stages.terminal(ch), "live")
        self.assertIsNone(stages.next_executor(ch))   # never gated (BR-C7)

    def test_new_commit_reenters(self):
        """BR-C2: the branch tip in the dev's clone moved past the handed-over commit, before the contribution."""
        ch = H.change("feat", "server", stage="gate", commit=SHA, repo="/dev/clone")
        o = self.obs(tips={("/dev/clone", "content/feat"): SHB})
        _, _, moved = stages.derive(ch, o, {})
        self.assertEqual(moved, SHB)
        ch["stage"] = "review"   # contributed: the PR's own commits move the branch, not a re-entry
        self.assertIsNone(stages.derive(ch, o, {})[2])

    def test_unknown_never_regresses(self):
        ch = H.change("feat", "server", stage="review", commit=SHA, upstream_pr=1)
        H.write_gate("feat", SHA)
        o = self.obs(tips={("fork", "content/feat"): SHA}, upstream_prs={1: None})
        self.assertEqual(stages.derive(ch, o, {})[0], "review")

    def test_retired_stages_migrate(self):
        for old, new in (("checked", "gate"), ("gated", "contribute"), ("published", "review")):
            ch = H.change("old-" + old, "server", stage=old, commit=SHA, gated_commit=SHA, pr="u")
            back = store.load(ch["slug"])
            self.assertEqual(back.stage, new)
            self.assertNotIn("gated_commit", back)
        self.assertEqual(H.change("old-live", "server", stage="live", commit=SHA).stage, "gate")
        self.assertEqual(H.change("old-cli", "client", stage="live", commit=SHA).stage, "live")

    def test_next_executor(self):
        self.assertEqual(stages.next_executor(H.change("ch-a", "server")), "dev")
        self.assertEqual(stages.next_executor(H.change("ch-b", "server", stage="gate", commit=SHA)), "gate")
        H.write_gate("ch-b", SHA, "FAIL", findings=["x"])
        self.assertIsNone(stages.next_executor(store.load("ch-b")))   # a finding alone books nothing
        self.assertIsNone(stages.next_executor(H.change("ch-c", "server", stage="gate", commit=SHA, local_only=True)))
        self.assertIsNone(stages.next_executor(H.change("ch-d", "client", stage="gate", commit=SHA)))
        ch = H.change("ch-e", "server", stage="contribute", commit=SHA)
        store.set_hold(ch, "failed", "the user wants the findings fixed"); store.save(ch)
        self.assertEqual(stages.next_executor(store.load("ch-e")), "dev")
        ch = H.change("ch-f", "server")
        store.set_hold(ch, "blocked", "deps"); store.save(ch)
        self.assertIsNone(stages.next_executor(store.load("ch-f")))

    def test_booking_key_changes_with_the_head_and_the_findings(self):
        """BR-S9: the same head and finding set is the same key."""
        ch = H.change("feat", "server", stage="gate", commit=SHA)
        k1 = stages.booking_key(ch, "dev")
        self.assertEqual(k1, stages.booking_key(ch, "dev"))
        H.write_gate("feat", SHA, "FAIL", findings=["a"])
        k2 = stages.booking_key(ch, "dev")
        self.assertNotEqual(k1, k2)
        ch["commit"] = SHB
        self.assertNotEqual(k2, stages.booking_key(ch, "dev"))
        ch["finding"] = "IC_1"
        self.assertNotEqual(stages.booking_key(ch, "dev"), stages.booking_key(store.Change(dict(ch, finding=None)), "dev"))
        self.assertEqual(stages.booking_key(ch, "gate"), SHB)
        ch["booked"] = {"dev": stages.booking_key(ch, "dev")}
        self.assertTrue(stages.would_loop(ch, "dev"))
        self.assertFalse(stages.would_loop(ch, "gate"))


class GateRecordTest(unittest.TestCase):
    """What `hd gate` accepts: QA's record, bound to the commit, every check named and every finding listed."""

    def test_pass_needs_green_ci_at_the_commit_and_no_findings(self):
        ci = {"commit": SHA, "result": "success"}
        self.assertEqual(qa.record_problems(H.gate_text(SHA), SHA, "PASS", ci), [])
        self.assertTrue(any("record is for" in p for p in qa.record_problems(H.gate_text(SHB), SHA, "PASS", ci)))
        self.assertTrue(any("no green CI" in p for p in qa.record_problems(H.gate_text(SHA), SHA, "PASS", {})))
        self.assertTrue(any("no green CI" in p for p in qa.record_problems(
            H.gate_text(SHA), SHA, "PASS", {"commit": SHB, "result": "success"})))
        self.assertTrue(any("finding" in p for p in qa.record_problems(H.gate_text(SHA, findings=["x"]), SHA, "PASS", ci)))
        self.assertTrue(any("failed checks" in p for p in qa.record_problems(H.gate_text(SHA, checks={"scope": "FAIL"}), SHA, "PASS", ci)))

    def test_fail_lists_findings_and_needs_no_ci(self):
        text = H.gate_text(SHA, "FAIL", ["a", "b"], checks={"ci": "FAIL"})
        self.assertEqual(qa.record_problems(text, SHA, "FAIL", {}), [])
        self.assertTrue(any("without a finding" in p for p in qa.record_problems(H.gate_text(SHA, "FAIL"), SHA, "FAIL")))
        self.assertEqual(qa.findings_of(text), ["a", "b"])

    def test_every_check_is_named_and_the_verdict_matches(self):
        text = H.gate_text(SHA).replace("- ingame: PASS\n", "")
        self.assertTrue(any("ingame" in p for p in qa.record_problems(text, SHA, "PASS", {"commit": SHA, "result": "success"})))
        self.assertTrue(any("verdict line" in p for p in qa.record_problems(H.gate_text(SHA), SHA, "FAIL")))
        self.assertTrue(any("no gate record" in p for p in qa.record_problems("", SHA, "PASS")))


class ServerCheckTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def obs(self, **facts):
        from hd.tracks import FakeObserver
        return FakeObserver(**facts)

    def test_server(self):
        """The hand-over check: the branch in the dev's clone at the commit, accuracy spec, PR text; CI and the merge with
        upstream main are QA's."""
        ch = H.change("feat", "server", stage="dev", commit=SHA, evidence="re/evidence/feat", repo="/dev/clone")
        o = self.obs(tips={("/dev/clone", "content/feat"): SHA},
                     evidence={"re/evidence/feat": ["accuracy.md", "pr-title.txt", "pr-body.md"]})
        ok, its = check.run(ch, o)
        self.assertTrue(ok, check.render(ch, its))
        o.f["evidence"]["re/evidence/feat"] = ["notes.txt"]
        ok, its = check.run(ch, o)
        texts = [t for ok_, t in its if not ok_]
        self.assertTrue(any("no accuracy spec" in t for t in texts), texts)
        self.assertTrue(any("PR text missing" in t for t in texts), texts)
        o.f["docs"] = {"accuracy/feat.md": "# spec", "pr-texts/feat.title": "t", "pr-texts/feat.upstream.body": "b"}
        self.assertTrue(check.run(ch, o)[0])
        o.f["tips"][("/dev/clone", "content/feat")] = SHB
        ok, its = check.run(ch, o)
        self.assertTrue(any("is at bbbbbbbbb, not aaaaaaaaa" in t for _, t in its))

    def test_server_local_needs_no_pr_text_and_no_spec(self):
        ch = H.change("loc", "server", stage="dev", commit=SHA, branch="local/loc", local_only=True, evidence="re/evidence/loc")
        o = self.obs(tips={("fork", "local/loc"): SHA}, evidence={"re/evidence/loc": ["x"]}, docs={})
        ok, its = check.run(ch, o)
        self.assertTrue(ok, check.render(ch, its))

    def test_unticked_definition_of_done_fails(self):
        ch = H.change("un", "server", stage="dev", commit=SHA, ticked=False, repo="/r", evidence="e")
        ok, its = check.run(ch, self.obs(tips={("/r", "content/un"): SHA}, evidence={"e": ["accuracy.md", "pr-title.txt", "pr-body.md"]}))
        self.assertFalse(ok)
        self.assertTrue(any("unticked" in t for _, t in its))


class ServerHooksTest(unittest.TestCase):
    """The hook rules (hd/tracks/server/hooks.py); the entry points in hooks/ are tested in test_hooks.py."""

    def setUp(self):
        H.sandbox(self)

    def test_contribute_needs_the_record_and_the_named_commit(self):
        from hd.tracks.server import hooks
        H.change("feat", "server", stage="contribute", commit=SHA)
        cmd = "python3 /h/hd.py contribute feat --approved "
        self.assertIsNone(hooks.contribute_deny("ls"))
        self.assertIn("no QA record", hooks.contribute_deny(cmd + SHA))
        H.write_gate("feat", SHA)
        self.assertIsNone(hooks.contribute_deny(cmd + SHA[:10]))
        self.assertIn("approval is for", hooks.contribute_deny(cmd + SHB))
        self.assertIn("bound to the commit", hooks.contribute_deny("python3 /h/hd.py contribute feat"))

    def test_direct_pr_needs_a_record_at_the_branch_commit(self):
        from hd.tracks.server import hooks
        H.change("feat", "server", stage="gate", commit=SHA)
        self.assertIn("QA record missing", hooks.direct_pr_deny("content/feat", SHA))
        self.assertIn("no change for", hooks.direct_pr_deny("content/other", SHA))
        H.write_gate("feat", SHA)
        self.assertIsNone(hooks.direct_pr_deny("content/feat", SHA))
        self.assertIn("QA record", hooks.direct_pr_deny("content/feat", SHB))

    def test_command_and_push_shapes(self):
        from hd.tracks.server import hooks
        dest = lambda r: r.lstrip("+").split(":")[-1].removeprefix("refs/heads/")
        self.assertTrue(hooks.is_contribute(["python3", "/x/hd.py", "contribute", "feat"]))
        self.assertFalse(hooks.is_contribute(["python3", "/x/hd.py", "gate-ci", "feat"]))
        self.assertFalse(hooks.is_contribute(["grep", "contribute", "hd.py"]))
        self.assertTrue(hooks.is_scratch_push(["+abc:refs/heads/gate/feat"], [], dest))
        self.assertFalse(hooks.is_scratch_push([":gate/feat"], [], dest))
        self.assertFalse(hooks.is_scratch_push(["a:gate/x", "b:gate/y"], [], dest))
        self.assertFalse(hooks.is_scratch_push(["abc:content/feat"], [], dest))
        self.assertFalse(hooks.is_scratch_push(["abc:gate/feat"], ["--delete"], dest))


if __name__ == "__main__":
    unittest.main()
