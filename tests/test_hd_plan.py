"""v6 core: cross-track priority (BR-C5), capacity classes (BR-R5), durable holds (BR-S2), no timed mechanisms (BR-S10)
and the maintenance tick. Policy is the live structure (`H.sandbox`); git is a temp repo."""
import io
import os
import subprocess
import unittest
from contextlib import redirect_stdout

import hd_helpers as H
import yaml
from hd_helpers import SHA

from hd import batches, capacity, cli, events, maintain, policy, priority, stages, store, tick
from hd.tracks import FakeObserver


LIVE_POLICY = os.path.join(H.ROOT, "harness", "policy.yaml")


def set_policy(**top):
    """Rewrite the sandbox policy's top-level keys."""
    p = os.environ["HD_POLICY"]
    with open(p) as f:
        pol = yaml.safe_load(f)
    pol.update(top)
    with open(p, "w") as f:
        yaml.safe_dump(pol, f)
    policy._cache.clear()


def order(idx):
    return [ch["slug"] for ch in sorted(idx.values(), key=lambda c: priority.rank(c, idx))]


class PriorityTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def test_a_blocker_takes_the_priority_of_the_changes_waiting_on_it_across_tracks(self):
        H.change("srv", "server", prio="P3")
        H.change("other", "server", prio="P2")
        H.change("cli", "client", prio="P1", deps=["srv"])
        idx = store.index()
        self.assertEqual(priority.effective(idx["srv"], idx), 1)
        self.assertEqual(order(idx), ["cli", "srv", "other"])

    def test_inheritance_is_transitive_and_survives_a_cycle(self):
        H.change("aa", "server", prio="P3"); H.change("bb", "server", prio="P3", deps=["aa"])
        H.change("cc", "client", prio="P0", deps=["bb"])
        idx = store.index()
        self.assertEqual(priority.effective(idx["aa"], idx), 0)
        H.change("xx", "server", prio="P2", deps=["yy"]); H.change("yy", "server", prio="P1", deps=["xx"])
        idx = store.index()
        self.assertEqual((priority.effective(idx["xx"], idx), priority.effective(idx["yy"], idx)), (1, 1))

    def test_a_live_blocker_or_a_finished_dependent_gives_no_boost(self):
        H.change("srv", "server", stage="gate", commit=SHA, prio="P3", live_commit=SHA)
        H.change("cli", "client", prio="P0", deps=["srv"])
        idx = store.index()
        self.assertEqual(priority.effective(idx["srv"], idx), 3, "the blocker is live")
        H.change("srv2", "server", prio="P3")
        H.change("done", "client", stage="live", prio="P0", deps=["srv2"])
        idx = store.index()
        self.assertEqual(priority.effective(idx["srv2"], idx), 3, "the dependent is finished")

    def test_settle_first_outranks_the_derived_priority_and_is_data(self):
        H.change("fix-review", "server", prio="P3", finding="comment 9")
        H.change("urgent", "server", prio="P0")
        H.change("cli", "client", prio="P0", deps=["urgent"])
        self.assertEqual(order(store.index())[0], "fix-review")
        set_policy(settle_first=False)
        self.assertEqual(order(store.index())[-1], "fix-review")

    def test_dispatch_candidates_follow_the_rank(self):
        H.change("s3", "server", prio="P3"); H.change("s1", "server", prio="P1"); H.change("rf", "server", prio="P2", finding="c1")
        ctx = tick.Ctx(FakeObserver(), True)
        self.assertEqual([c[0]["slug"] for c in tick.candidates(ctx)], ["rf", "s1", "s3"])


class CapacityTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def run_of(self, role):
        return {"name": role + "-x", "role": role}

    def test_live_policy_defines_the_classes_and_two_clients(self):
        with open(LIVE_POLICY) as f:
            pol = yaml.safe_load(f)
        self.assertEqual(sorted(pol["capacity"]), ["agent", "build", "client", "device", "image"])
        self.assertEqual((pol["capacity"]["client"], pol["capacity"]["device"]), (2, 2))
        self.assertIn("device", pol["agents"]["roles"]["client-dev"]["uses"])
        self.assertNotIn("client", pol["agents"]["roles"]["client-dev"]["uses"])
        for role, r in pol["agents"]["roles"].items():
            self.assertTrue(set(r["uses"]) <= set(pol["capacity"]), role)
        self.assertFalse(any(k.endswith("dev_slots") for t in pol["tracks"].values() for k in t))

    def test_a_role_fits_until_a_class_it_uses_is_full(self):
        set_policy(capacity={"agent": 9, "build": 9, "client": 2, "device": 1, "image": 1})
        running = [self.run_of("client-dev"), self.run_of("server-qa")]
        self.assertEqual(capacity.full("client-dev", running), "device")
        self.assertIsNone(capacity.full("server-qa", running[:1]), "QA's desktop clients do not take the device")
        self.assertIsNone(capacity.full("server-dev", running), "server-dev uses no client")
        self.assertIsNone(capacity.full("client-dev", running[1:]))
        self.assertEqual(capacity.full("client-dev", [], []), None)
        set_policy(capacity={"agent": 9, "build": 9, "client": 2, "device": 0, "image": 1})
        self.assertEqual(capacity.full("client-dev", []), "device", "capacity 0 holds client-dev back")
        self.assertIsNone(capacity.full("client-qa", []))

    def test_the_agent_class_caps_the_total(self):
        running = [self.run_of("harness-dev")] * 3
        self.assertEqual(capacity.full("harness-dev", running), "agent")

    def test_a_train_step_holds_its_class(self):
        set_policy(capacity={"agent": 9, "build": 1, "client": 2, "device": 1, "image": 1})
        self.assertIsNone(capacity.full("server-dev", [], [{"step": "queued"}]))
        self.assertEqual(capacity.full("server-dev", [], [{"step": "gating"}]), "build")
        self.assertEqual(capacity.used([], [{"step": "imaging"}])["image"], 1)

    def test_a_waiting_change_is_stalled_not_locked(self):
        set_policy(capacity={"agent": 9, "build": 9, "client": 2, "device": 0, "image": 1})
        H.change("c-a", "client"); H.change("s-a", "server")
        out = tick.tick(FakeObserver(), dry_run=True)
        self.assertIn("c-a: client-dev waits for a free device slot [dry run]", out)
        self.assertIn("would dispatch server-dev for s-a (dev) [dry run]", out)

    def test_lint_names_an_undefined_class(self):
        with open(os.environ["HD_POLICY"]) as f:
            pol = yaml.safe_load(f)
        pol["agents"]["roles"]["harness-dev"]["uses"] = ["agent", "gpu"]
        with open(os.environ["HD_POLICY"], "w") as f:
            yaml.safe_dump(pol, f)
        policy._cache.clear()
        out = io.StringIO()
        with redirect_stdout(out):
            rc = cli.cmd_lint(None)
        self.assertEqual(rc, 1)
        self.assertIn("harness-dev uses capacity class gpu", out.getvalue())


class HoldTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def test_blocked_is_derived_never_stored(self):
        self.assertNotIn("blocked", store.HOLDS)
        H.change("dep", "server"); H.change("cli", "client", deps=["dep"])
        tick.tick(FakeObserver(), dry_run=True)
        self.assertIsNone(store.load("cli").hold)
        path = store.path("old")
        H.change("old", "client")
        with open(path) as f:
            text = f.read().replace("hold: null", "hold: {kind: blocked, reason: waiting for dep, since: x}")
        with open(path, "w") as f:
            f.write(text)
        self.assertIsNone(store.load("old").hold, "a stored blocked hold of an earlier policy is dropped on load")

    def test_hd_block_adds_the_edge_and_no_hold(self):
        H.change("cli", "client"); H.change("srv", "server")
        args = type("A", (), {"slug": "cli", "by": "srv", "why": "needs the quest"})()
        with redirect_stdout(io.StringIO()):
            cli.cmd_block(args)
        ch = store.load("cli")
        self.assertEqual((ch["deps"], ch.hold), (["srv"], None))
        self.assertIsNone(stages.next_executor(ch, store.index()))

    def test_a_decision_hold_survives_the_reconciler(self):
        """No tick step clears a decision hold: deps live, the branch moved, the change handed over elsewhere."""
        H.change("srv", "server", stage="gate", commit=SHA, live_commit=SHA)
        ch = H.change("cli", "client", deps=["srv"])
        store.set_hold(ch, "decision", "which approach?"); store.save(ch)
        for _ in range(2):
            tick.tick(FakeObserver(tips={("fork", "content/srv"): SHA}, pins={"content/srv": SHA}), dry_run=False)
        self.assertEqual(store.load("cli").hold, "decision")
        self.assertIsNone(stages.next_executor(store.load("cli"), store.index()))

    def test_an_unmet_dep_never_replaces_a_decision_hold(self):
        H.change("dep", "server")
        ch = H.change("cli", "client", deps=["dep"])
        store.set_hold(ch, "decision", "ask"); store.save(ch)
        tick.tick(FakeObserver(), dry_run=False)
        self.assertEqual((store.load("cli").hold, store.load("cli").hold_reason), ("decision", "ask"))

    def test_only_unhold_clears_a_decision_hold(self):
        ch = H.change("cli", "client")
        store.set_hold(ch, "decision", "ask"); ch["booked"] = {"dev": "k"}; store.save(ch)
        with redirect_stdout(io.StringIO()):
            cli.cmd_unhold(type("A", (), {"slug": "cli", "why": "go with A"})())
        ch = store.load("cli")
        self.assertEqual((ch.hold, ch["booked"]), (None, None))


class NoTimersTest(unittest.TestCase):
    def setUp(self):
        H.sandbox(self)

    def test_policy_has_no_time_knob(self):
        def keys(d):
            for k, v in d.items():
                yield k
                if isinstance(v, dict):
                    yield from keys(v)
        with open(LIVE_POLICY) as f:
            names = list(keys(yaml.safe_load(f)))
        self.assertEqual([k for k in names if k.endswith(("_minutes", "_seconds")) or "debounce" in k or "timeout" in k
                          or "heartbeat" in k], [])

    def test_a_running_step_is_never_cut_off_by_the_clock(self):
        b = {"id": "int-1", "kind": "train", "step": "gating", "pid": os.getpid(), "log": "/dev/null",
             "steps": [{"step": "gating", "started": "2020-01-01T00:00:00Z"}]}
        self.assertIsNone(batches._poll(b, FakeObserver()))
        self.assertEqual(b["step"], "gating")

    def test_a_queued_entry_starts_a_train_with_no_wait(self):
        self.assertTrue(hasattr(batches, "_queued"))
        self.assertFalse(hasattr(batches, "_due"))
        self.assertFalse(hasattr(batches, "_timeout_minutes"))


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout


class MaintainTest(unittest.TestCase):
    """`maintain.run` on a temp repo that holds the sandbox's harness dir."""

    def setUp(self):
        self.d = H.sandbox(self)
        H.env(self, GIT_COMMITTER_NAME="Committer", GIT_COMMITTER_EMAIL="c@example.com", GIT_AUTHOR_NAME="Someone",
              GIT_AUTHOR_EMAIL="s@example.com", HD_MAINTAIN_REPO=self.d)
        git(self.d, "init", "-q", "-b", "main")
        with open(os.path.join(self.d, ".gitignore"), "w") as f:
            f.write("harness/state/\nevidence/\n")
        H.change("one", "harness")
        git(self.d, "add", "-A")
        git(self.d, "commit", "-q", "-m", "init")

    def run_(self, dry_run=False):
        return maintain.run(store.index(), dry_run=dry_run)

    def test_only_store_files_differing_are_committed_pathspec_only(self):
        H.change("two", "client")
        ch = store.load("one"); store.add_log(ch, "note"); store.save(ch)
        out = self.run_()
        self.assertTrue(any(a.startswith("commit-store: 2 files") for a in out), out)
        self.assertEqual(git(self.d, "status", "--porcelain").strip(), "")
        self.assertEqual(sorted(git(self.d, "show", "--name-only", "--format=", "HEAD").split()),
                         ["harness/changes/one.md", "harness/changes/two.md"])
        body = git(self.d, "log", "-1", "--format=%an <%ae>%n%B")
        self.assertIn("Alex Perrin <44126061+AlexPerrin@users.noreply.github.com>", body)
        self.assertIn("Co-Authored-By: Claude", body)
        self.assertEqual(self.run_(), [], "nothing left to do")

    def test_another_changed_file_means_no_commit(self):
        H.change("two", "client")
        with open(os.path.join(self.d, "hd.py"), "w") as f:
            f.write("x\n")
        self.assertFalse([a for a in self.run_() if a.startswith("commit-store")])
        self.assertIn("harness/changes/two.md", git(self.d, "status", "--porcelain", "-uall"))

    def test_dry_run_changes_nothing(self):
        H.change("two", "client")
        out = self.run_(dry_run=True)
        self.assertIn("commit-store: 1 change-store files [dry run]", out)
        self.assertIn("ignore-worktrees: .claude/worktrees into", out[0])
        self.assertIn("harness/changes/two.md", git(self.d, "status", "--porcelain", "-uall"))
        exclude = os.path.join(self.d, ".git", "info", "exclude")
        with open(exclude) as f:
            self.assertNotIn(".claude/worktrees", f.read())

    def test_the_worktree_dir_is_ignored_once(self):
        self.assertTrue(any(a.startswith("ignore-worktrees") for a in self.run_()))
        self.assertFalse(any(a.startswith("ignore-worktrees") for a in self.run_()))
        with open(os.path.join(self.d, ".git", "info", "exclude")) as f:
            self.assertEqual(f.read().split().count(".claude/worktrees"), 1)

    def worktree(self, name, commit=False, dirty=False):
        path = os.path.join(self.d, ".claude", "worktrees", name)
        git(self.d, "worktree", "add", "-q", "-b", name, path)
        if commit:
            with open(os.path.join(path, "f.txt"), "w") as f:
                f.write("work\n")
            git(path, "add", "f.txt")
            git(path, "commit", "-q", "-m", "work")
        if dirty:
            with open(os.path.join(path, "g.txt"), "w") as f:
                f.write("wip\n")
        return path

    def test_merged_clean_worktrees_and_branches_go_while_no_agent_runs(self):
        gone = self.worktree("merged")
        unmerged = self.worktree("ahead", commit=True)
        dirty = self.worktree("dirty", dirty=True)
        git(self.d, "branch", "stale-merged")
        out = self.run_()
        self.assertTrue(any(a.startswith("remove-worktree") and "merged" in a for a in out), out)
        self.assertFalse(os.path.isdir(gone))
        self.assertTrue(os.path.isdir(unmerged) and os.path.isdir(dirty))
        branches = git(self.d, "branch", "--format=%(refname:short)").split()
        self.assertNotIn("merged", branches)
        self.assertNotIn("stale-merged", branches)
        self.assertIn("ahead", branches)
        self.assertIn("dirty", branches)
        self.assertIn("main", branches)

    def test_nothing_is_removed_while_an_agent_run_is_alive(self):
        path = self.worktree("fresh")
        store.rec_save("runs", "hd1", {"name": "hd1", "role": "harness-dev", "change": "one", "stage": "dev"})
        out = self.run_()
        self.assertFalse([a for a in out if a.startswith(("remove-worktree", "delete-branch"))])
        self.assertTrue(os.path.isdir(path))

    def test_a_repo_that_does_not_hold_the_store_is_left_alone(self):
        other = os.path.join(self.d, "elsewhere")
        os.makedirs(other)
        git(other, "init", "-q", "-b", "main")
        git(other, "commit", "-q", "--allow-empty", "-m", "init")
        git(other, "branch", "stale-merged")
        self.assertEqual(maintain.run(store.index(), repo=other), [])
        self.assertIn("stale-merged", git(other, "branch", "--format=%(refname:short)"))

    def test_stale_holds_are_listed(self):
        ch = H.change("fin", "client", stage="live", commit=SHA)
        store.set_hold(ch, "decision", "old question"); store.save(ch)
        H.change("lost", "client", deps=["nowhere"])
        stale = maintain.stale_holds(store.index())
        self.assertEqual(sorted(stale), ["fin: decision hold on a finished change (live)", "lost: waits for nowhere, which is no change"])
        self.run_()
        self.assertEqual(sorted(store.rec_load("view", "stale")["holds"]), sorted(stale))


if __name__ == "__main__":
    unittest.main()
