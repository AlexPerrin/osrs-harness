"""hd.actions (BR-A1..A5): what a change at `contribute` or a release batch needs from the user, computed from observed
state and QA's local record only. Completion is observed: the action disappears when the world has moved; nothing is
recorded."""
import os
import unittest

import hd_helpers as H
from hd_helpers import SHA, SHB

from hd import actions, store
from hd.tracks import FakeObserver

DOCS = {"pr-texts/feat.title": "Add feat\n", "pr-texts/feat.upstream.body": "Body\n\n## Caveats\n- one caveat\n"}


def obs(prs=None, docs=None, **kw):
    return FakeObserver(upstream_prs=prs if prs is not None else {}, docs=DOCS if docs is None else docs, **kw)


class ContributionTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)
        H.change("feat", "server", stage="contribute", commit=SHA)
        H.write_gate("feat", SHA)

    def one(self, o):
        got = actions.pending_actions(o)
        self.assertEqual(len(got), 1, got)
        return got[0]

    def test_one_command_bound_to_the_commit(self):
        a = self.one(obs(contains={("fork", "content/feat", SHA): False}))
        self.assertEqual((a["kind"], a["action"], a["change"], a["id"]), ("upstream", "contribute", "feat", f"feat-contribute-{SHA[:7]}"))
        (cmd,) = a["commands"]
        self.assertEqual(cmd[2:], ["contribute", "feat", "--approved", SHA])
        self.assertEqual(a["text"]["title"], "Add feat")
        self.assertEqual(a["caveats"], ["one caveat"])
        self.assertIn("accuracy: PASS", a["checks"])
        self.assertTrue(a["record"].endswith("feat/gate.md"))
        self.assertEqual([n for n, _, _ in a["steps"]][:2], ["push", "open"])
        text = actions.render(a)
        self.assertIn("contribute feat --approved " + SHA, text)
        self.assertIn("check: ci: PASS", text)
        self.assertEqual(a["verdict"], "PASS")
        self.assertIn("step push: pending", text)

    def test_findings_are_on_the_card_and_do_not_hide_it(self):
        H.write_gate("feat", SHA, "FAIL", findings=["head regression"], checks={"style": "FAIL"})
        a = self.one(obs())
        self.assertIn("style: FAIL reason".replace(" reason", ""), [c.replace(" reason", "") for c in a["checks"]])
        self.assertEqual(a["findings"], ["head regression"])
        self.assertIn("finding: head regression", actions.render(a))

    def test_without_pr_text_the_card_says_so(self):
        a = self.one(obs(docs={}))
        self.assertIn("PR text missing", a["note"])

    def test_nothing_before_qa_or_while_held_or_after(self):
        os.remove(os.path.join(H.evidence_dir_for("feat"), "gate.md"))
        self.assertEqual(actions.pending_actions(obs()), [])
        H.write_gate("feat", SHA)
        ch = store.load("feat"); store.set_hold(ch, "failed", "fix it"); store.save(ch)
        self.assertEqual(actions.pending_actions(obs()), [])
        ch = store.load("feat"); store.clear_hold(ch); ch["stage"] = "review"; store.save(ch)
        self.assertEqual(actions.pending_actions(obs()), [])

    def test_partial_run_shows_its_observed_steps(self):
        o = obs(prs={"content/feat": {"number": 7, "state": "open", "draft": True, "head": SHA}},
                contains={("fork", "content/feat", SHA): True}, upstream_ci={(7, SHA): "success"}, reviews={7: []})
        a = self.one(o)
        steps = {n: d for n, d, _ in a["steps"]}
        self.assertEqual((steps["push"], steps["open"], steps["ci"], steps["comment"], steps["ready"]),
                         (True, True, True, False, False))

    def test_draft_card_for_a_review_fix_on_a_ready_pr(self):
        H.change("feat-rf", "server", stage="dev", branch="content/feat", upstream_pr=7, finding="IC_1")
        ready = obs(prs={7: {"number": 7, "state": "open", "draft": False, "head": SHB}, "content/feat": {"number": 7, "state": "open", "draft": False, "head": SHB}})
        cards = {a["action"]: a for a in actions.pending_actions(ready)}
        self.assertIn("draft-pr", cards)
        self.assertEqual(cards["draft-pr"]["commands"], [["gh", "pr", "ready", "7", "-R", "OpenRune/OpenRune-Server", "--undo"]])
        draft = obs(prs={7: {"number": 7, "state": "open", "draft": True, "head": SHB}, "content/feat": {"number": 7, "state": "open", "draft": True, "head": SHB}})
        self.assertNotIn("draft-pr", {a["action"] for a in actions.pending_actions(draft)})


class ReleaseTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def batch(self, **kw):
        b = {"id": "rel-1", "kind": "release", "step": "gated", "includes": ["a", "b"], "steps": [], "commit": SHA}
        b.update(kw)
        store.rec_save("batches", "rel-1", b)

    def test_without_a_tag_the_user_chooses_one(self):
        self.batch()
        (a,) = actions.pending_actions(obs())
        self.assertEqual((a["action"], a["commands"]), ("choose-tag", []))
        self.assertIn("hd release-request", a["note"])

    def test_tag_from_the_request_file_makes_one_release_command(self):
        self.batch()
        from hd.util import write_json
        write_json(os.path.join(store.state_dir(), "release.request"), {"tag": "v1.2.3"})
        (a,) = actions.pending_actions(obs())
        self.assertEqual((a["action"], a["id"]), ("tag-release", "rel-1-tag-release-v1.2.3"))
        (cmd,) = a["commands"]
        self.assertEqual(cmd[:4], ["gh", "release", "create", "v1.2.3"])
        self.assertEqual(cmd[cmd.index("--target") + 1], SHA)
        self.assertEqual(open(cmd[cmd.index("--notes-file") + 1]).read(), "# v1.2.3\n\n- a\n- b\n")

    def test_observed_release_removes_the_action(self):
        self.batch(tag="v1.2.3")
        self.assertEqual(len(actions.pending_actions(obs())), 1)
        done = obs(releases={"v1.2.3": {"tag": "v1.2.3", "url": "u"}})
        self.assertEqual(actions.pending_actions(done), [])
        self.assertTrue(actions.release_published(store.rec_load("batches", "rel-1"), done))

    def test_only_gated_batches(self):
        self.batch(step="gating", tag="v1.2.3")
        self.assertEqual(actions.pending_actions(obs()), [])


if __name__ == "__main__":
    unittest.main()
