"""The server lifecycle dev -> QA aggregate -> approval card -> contribution (docs/PROBLEM.md section 4): the hand-over that
refuses an incomplete one, QA's record (`hd gate`), the gate's build evidence on a scratch merge (`hd gate-ci`) and the
atomic contribution (`hd contribute`), each against temp git repos or a simulated GitHub; no network."""
import io
import json
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

import hd_helpers as H
from hd_helpers import SHA, SHB
from helpers import commit_file, git, init_repo

from hd import cli, events, store
from hd.tracks.server import contribute, gateci
from hd.tracks import FakeObserver


def run_cli(*argv):
    out = io.StringIO()
    with redirect_stdout(out):
        rc = cli.main(list(argv))
    return rc, out.getvalue()


class HandoverTest(unittest.TestCase):
    """`hd handover` runs the check itself: an incomplete hand-over is refused and nothing is recorded."""

    def setUp(self):
        self.d = H.sandbox(self)
        H.env(self, INTEGRATION_CLONE=os.path.join(self.d, "noclone"))
        self.dev = init_repo(os.path.join(self.d, "dev"))
        commit_file(self.dev, "a.txt", "a\n")
        git(self.dev, "checkout", "-q", "-b", "content/feat")
        self.sha = commit_file(self.dev, "b.txt", "b\n")
        self.ev = os.path.join(self.d, "evidence", "feat")
        os.makedirs(self.ev)
        H.change("feat", "server", stage="dev", owner="sd1", ticked=True)

    def hand_over(self, *extra):
        return run_cli("handover", "feat", "--branch", "content/feat", "--commit", self.sha, "--evidence", self.ev,
                       "--repo", self.dev, "--summary", "built", *extra)

    def write(self, *names):
        for n in names:
            with open(os.path.join(self.ev, n), "w") as f:
                f.write("x\n")

    def test_incomplete_is_refused_with_every_item_and_records_nothing(self):
        with self.assertRaises(SystemExit) as e:
            self.hand_over()
        msg = str(e.exception)
        self.assertIn("hand-over refused, nothing recorded", msg)
        self.assertIn("evidence dir", msg)
        self.assertIn("no accuracy spec", msg)
        self.assertIn("PR text missing", msg)
        ch = store.load("feat")
        self.assertEqual((ch.stage, ch.get("commit"), ch["owner"]), ("dev", None, "sd1"))
        self.assertEqual(events.read(kinds=["check"])[-1]["result"], "FAIL")
        self.assertEqual(events.read(kinds=["handover"]), [])

    def test_unticked_definition_of_done_is_refused(self):
        self.write("accuracy.md", "pr-title.txt", "pr-body.md")
        ch = store.load("feat"); ch.body = ch.body.replace("- [x]", "- [ ]"); store.save(ch)
        with self.assertRaises(SystemExit) as e:
            self.hand_over()
        self.assertIn("unticked", str(e.exception))

    def test_an_unticked_contribution_item_does_not_block_the_hand_over(self):
        self.write("accuracy.md", "pr-title.txt", "pr-body.md")
        ch = store.load("feat"); ch.body += "- [ ] the contribution step: PR opened upstream\n"; store.save(ch)
        rc, out = self.hand_over()
        self.assertEqual(store.load("feat").stage, "gate")

    def test_a_recorded_evidence_dir_is_copied_into_the_slug_dir(self):
        from hd.tracks.base import evidence_path, sync_evidence
        self.write("accuracy.md", "pr-title.txt", "pr-body.md")
        other = os.path.join(os.path.dirname(evidence_path(store.load("feat"))), "content-feat")
        os.makedirs(other)
        open(os.path.join(other, "pr-body.md"), "w").write("b")
        ch = store.load("feat"); ch["evidence"] = other
        sync_evidence(ch)
        self.assertTrue(os.path.exists(os.path.join(evidence_path(ch), "pr-body.md")))
        self.assertEqual(evidence_path(ch), os.path.join(os.path.dirname(other), "feat"))

    def test_complete_hand_over_moves_to_gate_and_records_the_clone(self):
        self.write("accuracy.md", "pr-title.txt", "pr-body.md")
        rc, out = self.hand_over()
        ch = store.load("feat")
        self.assertEqual((ch.stage, ch["commit"], ch["repo"], ch["branch"]), ("gate", self.sha, os.path.realpath(self.dev), "content/feat"))
        self.assertIn("the gate follows", out)
        self.assertEqual(events.read(kinds=["check"])[-1]["result"], "PASS")
        self.assertEqual([(e["from"], e["to"]) for e in events.read(kinds=["stage"]) if e["change"] == "feat"][-1], ("dev", "gate"))

    def test_a_failed_hold_clears_a_decision_one_stays(self):
        self.write("accuracy.md", "pr-title.txt", "pr-body.md")
        ch = store.load("feat"); store.set_hold(ch, "failed", "fix it"); store.save(ch)
        self.hand_over()
        self.assertIsNone(store.load("feat").hold)
        ch = store.load("feat"); store.set_hold(ch, "decision", "ask the user"); store.save(ch)
        self.hand_over()
        self.assertEqual(store.load("feat").hold, "decision")

    def test_a_commit_that_is_not_the_branch_tip_is_refused(self):
        self.write("accuracy.md", "pr-title.txt", "pr-body.md")
        commit_file(self.dev, "c.txt", "c\n")
        with self.assertRaises(SystemExit) as e:
            self.hand_over()
        self.assertIn("is at", str(e.exception))

    def test_block_fail_and_unhold_reset_the_booking(self):
        ch = store.load("feat"); ch["booked"] = {"dev": "k"}; store.save(ch)
        run_cli("block", "feat", "why", "--by", "other")
        self.assertIsNone(store.load("feat")["booked"])


class GateCliTest(unittest.TestCase):
    """`hd gate` records QA's aggregate: it checks the record, then sets no stage and no hold."""

    def setUp(self):
        H.sandbox(self)
        H.change("feat", "server", stage="gate", commit=SHA, owner="sq1")

    def gate(self, verdict):
        return run_cli("gate", "feat", verdict, "note")

    def test_pass_needs_the_record_and_green_ci_at_the_commit(self):
        with self.assertRaises(SystemExit) as e:
            self.gate("PASS")
        self.assertIn("no gate record", str(e.exception))
        H.write_gate("feat", SHA, ci=None)
        with self.assertRaises(SystemExit) as e:
            self.gate("PASS")
        self.assertIn("no green CI", str(e.exception))
        H.write_gate("feat", SHA)
        self.assertIn("gate PASS recorded", self.gate("PASS")[1])
        ch = store.load("feat")
        self.assertIsNone(ch["owner"])
        self.assertEqual(events.read(kinds=["gate"])[-1]["result"], "PASS")

    def test_fail_with_findings_holds_nothing_and_books_nothing(self):
        H.write_gate("feat", SHA, "FAIL", findings=["head regression", "added comment in A.kt"], ci="failure",
                     checks={"ci": "FAIL", "style": "FAIL"})
        self.gate("FAIL")
        ch = store.load("feat")
        self.assertEqual((ch.stage, ch.hold), ("gate", None))
        from hd import stages
        self.assertIsNone(stages.next_executor(ch))
        self.assertEqual(events.read(kinds=["gate"])[-1]["findings"], 2)
        self.assertEqual(events.read(kinds=["hold"]), [])

    def test_a_record_for_another_commit_is_refused(self):
        H.write_gate("feat", SHB)
        with self.assertRaises(SystemExit) as e:
            self.gate("PASS")
        self.assertIn("record is for", str(e.exception))

    def test_only_a_server_change_has_a_gate_record(self):
        H.change("plug", "client", stage="gate", commit=SHA)
        with self.assertRaises(SystemExit):
            run_cli("gate", "plug", "PASS")


class StatefulObs(FakeObserver):
    """CI state of the scratch branch, switchable per test."""
    states = ["pending"]

    def fork_ci(self, branch, sha, workflow=None):
        return self.states.pop(0) if len(self.states) > 1 else self.states[0]


def stub_gh(d, log):
    p = H.stub(d, "gh", f'echo "$@" >> {log}\n')
    return p


class GateCiTest(unittest.TestCase):
    """The scratch merge with current upstream main, the fork's gate/<slug> branch, CI observed, the diff scan."""

    def setUp(self):
        self.d = H.sandbox(self)
        d = self.d
        self.up = init_repo(os.path.join(d, "up.git"), branch="main", bare=True)
        seed = init_repo(os.path.join(d, "seed"), branch="main")
        git(seed, "remote", "add", "origin", self.up)
        commit_file(seed, "server/A.kt", "class A\n")
        git(seed, "push", "-q", "origin", "main")
        self.fork = init_repo(os.path.join(d, "fork.git"), branch="main", bare=True)
        self.clone = init_repo(os.path.join(d, "OpenRune-Server"), branch="main",
                               remotes={"origin": self.up, "fork": self.fork})
        git(self.clone, "pull", "-q", "origin", "main")
        H.env(self, INTEGRATION_CLONE=self.clone)
        self.dev = os.path.join(d, "dev")
        git(d, "clone", "-q", self.up, self.dev)
        git(self.dev, "checkout", "-q", "-b", "content/feat")
        self.sha = commit_file(self.dev, "server/B.kt", "class B\n")
        self.seed = seed
        self.gh_log = os.path.join(d, "gh.log")
        self.gh = stub_gh(d, self.gh_log)
        self.ch = H.change("feat", "server", stage="gate", commit=self.sha, repo=self.dev)

    def upstream_moves(self, rel="server/C.kt", text="class C\n"):
        commit_file(self.seed, rel, text)
        git(self.seed, "push", "-q", "origin", "main")

    def run_ci(self, state="success", wait=True):
        obs = StatefulObs()
        obs.states = ["none", state] if state == "success" else [state]
        return gateci.run(store.load("feat"), obs, gh=self.gh, wait=wait, poll=0, sleep=lambda s: None), obs

    def result(self):
        with open(os.path.join(self.d, "evidence", "feat", "gate-ci.json")) as f:
            return json.load(f)

    def test_merges_with_current_upstream_main_pushes_the_scratch_branch_and_dispatches_ci(self):
        self.upstream_moves()   # main moved on since the dev branched
        (rc, lines), _ = self.run_ci("success")
        self.assertEqual(rc, 0, lines)
        r = self.result()
        self.assertEqual((r["commit"], r["result"]), (self.sha, "success"))
        scratch = git(self.fork, "rev-parse", "refs/heads/gate/feat")
        self.assertEqual(scratch, r["scratch"])
        self.assertNotEqual(scratch, self.sha)   # a merge commit on top of upstream main
        self.assertEqual(git(self.fork, "rev-list", "--parents", "-n1", scratch).split()[1:3].count(self.sha), 1)
        self.assertEqual(git(self.fork, "show", "-s", "--format=%an", scratch), "Alex Perrin")
        self.assertIn("workflow run ci.yml -R AlexPerrin/OpenRune-Server --ref gate/feat", open(self.gh_log).read())
        self.assertEqual(git(self.up, "rev-parse", "refs/heads/main"), r["upstream_main"])
        self.assertEqual(subprocess.run(["git", "-C", self.fork, "rev-parse", "-q", "--verify", "refs/heads/content/feat"],
                                        capture_output=True).returncode, 1)   # the change's own branch never moves

    def test_a_conflict_with_upstream_main_is_a_finding_not_a_crash(self):
        self.upstream_moves("server/B.kt", "class B2\n")
        (rc, lines), _ = self.run_ci()
        self.assertEqual(rc, 1)
        r = self.result()
        self.assertEqual(r["result"], "conflict")
        self.assertIn("does not merge with upstream main", r["findings"][0])
        self.assertIn("server/B.kt", r["findings"][0])

    def test_the_formatting_workflow_is_dispatched_and_a_red_one_fails_the_gate(self):
        class Fmt(StatefulObs):
            seen = []

            def fork_ci(self, b, s, w=None):
                if w != "Formatting":
                    return "success"
                self.seen.append(1)
                return "none" if len(self.seen) == 1 else "failure"
        rc, lines = gateci.run(store.load("feat"), Fmt(), gh=self.gh, poll=0, sleep=lambda s: None)
        self.assertEqual(rc, 1, lines)
        self.assertEqual((self.result()["result"], self.result()["format"]), ("success", "failure"))
        self.assertIn("workflow run Formatting -R AlexPerrin/OpenRune-Server --ref gate/feat", open(self.gh_log).read())

    def test_red_ci_is_a_failure_result(self):
        (rc, _), _ = self.run_ci("failure")
        self.assertEqual((rc, self.result()["result"]), (1, "failure"))

    def test_no_wait_reports_running_and_a_rerun_resumes_without_a_second_push_or_dispatch(self):
        (rc, lines), _ = self.run_ci("none", wait=False)
        self.assertEqual(rc, 2)
        self.assertEqual(self.result()["result"], "pending")
        scratch = git(self.fork, "rev-parse", "refs/heads/gate/feat")
        dispatches = open(self.gh_log).read().count("workflow run")
        (rc, lines), _ = self.run_ci("pending", wait=False)
        self.assertEqual(rc, 2)
        self.assertTrue(any(l.startswith("resume:") for l in lines), lines)
        self.assertEqual(open(self.gh_log).read().count("workflow run"), dispatches)   # CI already runs at that commit
        (rc, _), _ = self.run_ci("success")
        self.assertEqual((rc, self.result()["result"]), (0, "success"))
        self.assertEqual(git(self.fork, "rev-parse", "refs/heads/gate/feat"), scratch)

    def test_a_moved_upstream_main_or_a_new_commit_starts_over(self):
        self.run_ci("success")
        first = self.result()["scratch"]
        self.upstream_moves()
        (rc, lines), _ = self.run_ci("success")
        self.assertFalse(any(l.startswith("resume:") for l in lines))
        self.assertNotEqual(self.result()["scratch"], first)

    def test_unreadable_ci_stops_instead_of_waiting_forever(self):
        class Dead(StatefulObs):
            def fork_ci(self, b, s, w=None):
                return None
        rc, lines = gateci.run(store.load("feat"), Dead(), gh=self.gh, poll=0, sleep=lambda s: None)
        self.assertEqual(rc, 1)
        self.assertIn("CI could not be read", lines[-1])

    def test_scan_finds_added_tests_and_comments_only(self):
        diff = "\n".join([
            "diff --git a/server/Foo.kt b/server/Foo.kt", "--- a/server/Foo.kt", "+++ b/server/Foo.kt", "@@ -1 +1,3 @@",
            "+    // explains the thing", "+    val x = 1  // trailing is not a comment line", "-// removed comment",
            "+/** kdoc */", "diff --git a/server/src/test/FooTest.kt b/server/src/test/FooTest.kt", "new file mode 100644",
            "+++ b/server/src/test/FooTest.kt", "+// a comment in a test file", "diff --git a/README.md b/README.md",
            "+// not code"])
        found = gateci.scan(diff)
        self.assertEqual(found, ["added comment in server/Foo.kt: // explains the thing",
                                 "added comment in server/Foo.kt: /** kdoc */",
                                 "added test file server/src/test/FooTest.kt",
                                 "added comment in server/src/test/FooTest.kt: // a comment in a test file"])

    def test_the_diff_scan_lands_in_the_result_file(self):
        git(self.dev, "checkout", "-q", "content/feat")
        sha = commit_file(self.dev, "server/D.kt", "class D\n// why\n")
        ch = store.load("feat"); ch["commit"] = sha; store.save(ch)
        (rc, _), _ = self.run_ci("success")
        self.assertEqual(self.result()["findings"], ["added comment in server/D.kt: // why"])


class World:
    """A simulated upstream PR for `hd contribute`: the commands the sequence runs change what it observes."""

    def __init__(self, commit):
        self.commit, self.pushed, self.pr, self.comments, self.ci, self.calls = commit, False, None, [], "pending", []

    def sh(self, argv, what):
        if "fetch" in argv:
            return ""
        self.calls.append(what)
        if "push" in argv:
            self.pushed = True
        elif argv[1:3] == ["pr", "create"]:
            self.pr = {"number": 7, "state": "open", "draft": "--draft" in argv, "head": self.commit}
            return "https://github.com/OpenRune/OpenRune-Server/pull/7"
        elif argv[1:3] == ["pr", "comment"]:
            self.comments.append({"id": "c1", "author": "AlexPerrin", "body": open(argv[argv.index("--body-file") + 1]).read(),
                                  "kind": "comment"})
        elif argv[1:3] == ["pr", "ready"]:
            self.pr["draft"] = False
        return ""

    def obs(self):
        w = self

        class O(FakeObserver):
            def contains(self, repo, ref, sha):
                return w.pushed

            def upstream_pr(self, key):
                return w.pr or {}

            def upstream_ci(self, number, sha):
                return w.ci if w.pr else "none"

            def upstream_pr_reviews(self, number):
                return list(w.comments)
        return O(docs={"pr-texts/feat.title": "Add feat", "pr-texts/feat.upstream.body": "Body"})


class ContributeTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)
        self.sha = SHA
        H.change("feat", "server", stage="contribute", commit=SHA, summary="adds the feature")
        H.write_gate("feat", SHA)
        self.w = World(SHA)
        p = mock.patch.object(contribute, "_sh", self.w.sh)
        p.start()
        self.addCleanup(p.stop)

    def go(self, approved=SHA, wait=True, ci_after=1):
        ticks = []

        def sleep(_):
            ticks.append(1)
            if len(ticks) >= ci_after:
                self.w.ci = "success"
        return contribute.run(store.load("feat"), self.w.obs(), approved, wait=wait, poll=0, sleep=sleep)

    def test_the_whole_sequence_in_order(self):
        rc, lines = self.go()
        self.assertEqual(rc, 0, lines)
        w = self.w
        self.assertEqual(w.calls, ["push to the PR branch (never a force: merge the PR head into the branch and hand over again)",
                                   "open the PR", "comment", "move the PR out of draft"])
        self.assertTrue(w.pr["draft"] is False)
        self.assertIn("<!-- hd-contribute:" + SHA[:12] + " -->", w.comments[0]["body"])
        self.assertIn("adds the feature", w.comments[0]["body"])
        self.assertEqual(store.load("feat")["upstream_pr"], 7)
        self.assertEqual(events.read(kinds=["contribute"])[-1]["result"], "done")
        self.assertTrue(any("waiting: CI running" in l or "waiting: no CI" in l for l in lines), lines)

    def test_refused_without_the_exact_approved_commit_or_a_record(self):
        rc, lines = self.go(approved=SHB)
        self.assertEqual(rc, 1)
        self.assertIn("approve this commit", lines[0])
        self.assertEqual(self.w.calls, [])
        os.remove(os.path.join(H.evidence_dir_for("feat"), "gate.md"))
        rc, lines = self.go()
        self.assertTrue(any("no QA record" in l for l in lines))
        self.assertEqual(self.w.calls, [])

    def test_a_failing_record_does_not_refuse_the_users_decision(self):
        H.write_gate("feat", SHA, "FAIL", findings=["style"], checks={"style": "FAIL"})
        rc, _ = self.go()
        self.assertEqual(rc, 0)

    def test_red_ci_stops_before_the_comment_and_leaves_the_pr_as_it_is(self):
        self.w.ci = "failure"
        rc, lines = contribute.run(store.load("feat"), self.w.obs(), SHA, poll=0, sleep=lambda s: None)
        self.assertEqual(rc, 1)
        self.assertIn("stopped before the comment", lines[-1])
        self.assertEqual(self.w.comments, [])
        self.assertTrue(self.w.pr["draft"])
        self.assertEqual(events.read(kinds=["contribute"])[-1]["result"], "ci-failed")

    def test_a_rerun_resumes_at_the_first_unobserved_step(self):
        rc, _ = self.go(wait=False)
        self.assertEqual(rc, 2)   # pushed and opened, CI still running
        self.assertEqual(len(self.w.calls), 2)
        rc, lines = self.go(wait=False)
        self.assertEqual(rc, 2)
        self.assertEqual(len(self.w.calls), 2)   # nothing repeated while waiting
        self.w.ci = "success"
        rc, _ = self.go()
        self.assertEqual(rc, 0)
        self.assertEqual(len(self.w.calls), 4)
        calls = len(self.w.calls)
        rc, lines = self.go()   # everything observed: nothing to do
        self.assertEqual((rc, len(self.w.calls)), (0, calls))
        self.assertEqual(len(self.w.comments), 1)

    def test_a_resumed_run_continues_only_the_approved_commit(self):
        self.go(wait=False)
        ch = store.load("feat"); ch["commit"] = SHB; store.save(ch)
        H.write_gate("feat", SHB)
        rc, lines = contribute.run(store.load("feat"), self.w.obs(), SHA, wait=False)
        self.assertEqual(rc, 1)
        self.assertIn("approve this commit", lines[0])

    def test_an_existing_ready_pr_is_not_reopened_and_gets_the_comment(self):
        self.w.pushed = True
        self.w.pr = {"number": 7, "state": "open", "draft": False, "head": SHA}
        self.w.ci = "success"
        ch = store.load("feat"); ch["upstream_pr"] = 7; store.save(ch)
        rc, _ = self.go()
        self.assertEqual((rc, self.w.calls), (0, ["comment"]))

    def test_only_a_server_change_not_local_is_contributed(self):
        H.change("loc", "server", stage="contribute", commit=SHA, branch="local/loc", local_only=True)
        self.assertTrue(any("only a server change" in r for r in contribute.refusal(store.load("loc"), SHA)))
        ch = store.load("feat"); store.set_hold(ch, "decision", "needs you"); store.save(ch)
        self.assertTrue(any("hold" in r for r in contribute.refusal(store.load("feat"), SHA)))


class TaskStopTest(unittest.TestCase):
    """The stop hook keeps a gate agent from ending before its aggregate is on disk (`hd gate` wrote the log line)."""

    def setUp(self):
        self.d = H.sandbox(self)
        H.change("feat", "server", stage="gate", commit=SHA, owner="sq1")

    def stop(self, stage):
        t = os.path.join(self.d, "transcript.jsonl")
        with open(t, "w") as f:
            f.write(f"Harness change `feat` (server track, stage `{stage}`). Your name is `sq1`, role `x`.\n")
        hook = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks", "task_stop.py")
        return subprocess.run([sys.executable, hook], input=json.dumps({"transcript_path": t}), capture_output=True,
                              text=True, env=dict(os.environ)).stdout

    def test_gate_blocks_until_the_aggregate_is_recorded_at_the_commit(self):
        self.assertIn("aggregate is not on disk", self.stop("gate"))
        H.write_gate("feat", SHA, "FAIL", findings=["x"])
        run_cli("gate", "feat", "FAIL", "one finding")
        self.assertEqual(self.stop("gate"), "")
        ch = store.load("feat"); ch["commit"] = SHB; store.save(ch)   # a new commit voids it
        self.assertIn("aggregate is not on disk", self.stop("gate"))

    def test_dev_blocks_until_handed_over(self):
        ch = store.load("feat"); ch.update(stage="dev", commit=None); store.save(ch)
        out = self.stop("dev")
        self.assertIn("without a hand-over", out)
        self.assertIn("refuses an incomplete one", out)


if __name__ == "__main__":
    unittest.main()
