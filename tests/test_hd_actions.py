"""hd.actions (BR-A1..A5, v4): what a gated change or release batch needs from the user, computed from observed
state only. Completion is observed: the action disappears when the world has moved; nothing is recorded."""
import os
import unittest

import hd_helpers as H
from hd_helpers import SHA, SHB

from hd import actions, store
from hd.observe import FakeObserver

DOCS = {"pr-texts/feat.title": "Add feat\n", "pr-texts/feat.upstream.body": "Body\n\n## Caveats\n- one caveat\n"}


def obs(prs=None, docs=None, **kw):
    return FakeObserver(upstream_prs=prs if prs is not None else {}, docs=DOCS if docs is None else docs, records=[], **kw)


class UpstreamTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)
        H.change("feat", "server", stage="gated", commit=SHA)

    def one(self, o):
        got = actions.pending_actions(o)
        self.assertEqual(len(got), 1, got)
        return got[0]

    def test_open_pr_with_commands_and_text_file(self):
        a = self.one(obs())
        self.assertEqual((a["kind"], a["action"], a["change"], a["id"]), ("upstream", "open-pr", "feat", f"feat-open-pr-{SHA[:7]}"))
        cmd = a["commands"][0]
        self.assertEqual(cmd[:3], ["gh", "pr", "create"])
        self.assertIn("OpenRune/OpenRune-Server", cmd)
        self.assertIn("AlexPerrin:content/feat", cmd)
        self.assertEqual(cmd[cmd.index("--title") + 1], "Add feat")
        self.assertEqual(open(cmd[cmd.index("--body-file") + 1]).read(), "Body\n\n## Caveats\n- one caveat\n")
        self.assertEqual(a["caveats"], ["one caveat"])
        self.assertIn("gh pr create", actions.render(a))

    def test_open_pr_without_text_has_no_command(self):
        a = self.one(obs(docs={}))
        self.assertEqual(a["commands"], [])
        self.assertIn("PR text missing on docs: pr-texts/feat.*", a["note"])

    def test_draft_at_the_commit_needs_ready(self):
        a = self.one(obs(prs={"content/feat": {"number": 7, "state": "open", "draft": True, "head": SHA}}))
        self.assertEqual((a["action"], a["commands"]), ("ready-pr", [["gh", "pr", "ready", "7", "-R", "OpenRune/OpenRune-Server"]]))

    def test_head_behind_needs_push_then_comment(self):
        a = self.one(obs(prs={"content/feat": {"number": 7, "state": "open", "draft": False, "head": SHB}}))
        self.assertEqual(a["action"], "update-pr")
        push, comment = a["commands"]
        self.assertEqual(push[3], "push")
        self.assertEqual(push[-1], f"{SHA}:refs/heads/content/feat")
        self.assertEqual(comment[:4], ["gh", "pr", "comment", "7"])
        self.assertIn("Updated to " + SHA, open(comment[comment.index("--body-file") + 1]).read())

    def test_done_closed_merged_or_unreadable_is_nothing(self):
        for pr in ({"number": 7, "state": "open", "draft": False, "head": SHA},       # at the commit, open for review
                   {"number": 7, "state": "closed", "head": SHB},
                   {"number": 7, "state": "closed", "merged": True, "head": SHB}):
            self.assertEqual(actions.pending_actions(obs(prs={"content/feat": pr})), [])
        self.assertEqual(actions.pending_actions(obs(prs={"content/feat": None})), [])   # gh failed: no guess

    def test_only_gated_changes_with_a_commit(self):
        H.change("other", "server", stage="live", commit=SHA)
        H.change("nocommit", "server", stage="gated")
        self.assertEqual([a["change"] for a in actions.pending_actions(obs())], ["feat"])


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
