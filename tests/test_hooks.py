"""deny_publish.py (the role guard), plus the shared shell parser, github_scope.py and publish_gate.py where they
share its target resolution. Temp repos whose remotes point at the fork or at OpenRune; no network."""
import json
import os
import subprocess
import sys
import unittest

from helpers import (FORK_SSH, FORK_URL, HOOKS, OURS_URL, UPSTREAM_URL, init_repo, tempdir)

sys.path.insert(0, HOOKS)
import deny_publish  # noqa: E402
import github_scope  # noqa: E402
import shellparse  # noqa: E402

FORK, DOCS, NONE = ["--fork-writes"], ["--docs-writes"], []
ALLOW, DENY = True, False


class DenyPublishTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls._tmp = tempfile.TemporaryDirectory(prefix="harness-hooks-")
        t = os.path.realpath(cls._tmp.name)
        # re/upstream-pr/or: origin IS OpenRune, fork is ours.
        cls.upr = init_repo(os.path.join(t, "upstream-pr", "or"), remotes={"origin": UPSTREAM_URL, "fork": FORK_SSH})
        # re/agents/<name>/or and docs clones: origin is the fork.
        cls.agent = init_repo(os.path.join(t, "agents", "sd1", "or"), remotes={"origin": FORK_URL})
        cls.docs = init_repo(os.path.join(t, "agents", "sq1", "docs"), remotes={"origin": FORK_URL})
        cls.ours = init_repo(os.path.join(t, "main"), remotes={"origin": OURS_URL})
        # The real agent clones: origin is the local push clone (re/upstream-pr/or), fork is the fork.
        cls.local = init_repo(os.path.join(t, "agents", "sd2", "or"), remotes={"origin": cls.upr, "fork": FORK_SSH})
        cls._env = os.environ.get("HOOK_PUSH_CLONE")
        os.environ["HOOK_PUSH_CLONE"] = cls.upr

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()
        if cls._env is None:
            os.environ.pop("HOOK_PUSH_CLONE", None)
        else:
            os.environ["HOOK_PUSH_CLONE"] = cls._env

    def decide(self, cmd, cwd, flags):
        cmd = cmd.format(upr=self.upr, agent=self.agent, docs=self.docs, ours=self.ours, local=self.local)
        return deny_publish.decide({"tool_input": {"command": cmd}, "cwd": getattr(self, cwd)}, flags)

    CASES = [
        # (command, cwd, flags, expected)
        # --- words as data are not commands (hd4, 2026-10-21: a grep pattern naming docker-compose and openrune.sh)
        ("grep -rnE 'openrune/(upstream|docker-compose|switch\\.env)|openrune\\.sh|qa\\.sh' tools docs | cut -c1-200", "ours", NONE, ALLOW),
        ('echo "docker rm osrs-openrune is the orchestrator\'s job"', "ours", NONE, ALLOW),
        ("docker rm -f osrs-openrune", "ours", FORK, DENY),
        ('bash -c "cd openrune && docker compose --env-file switch.env up -d --no-deps openrune"', "ours", FORK, DENY),
        ("docker compose -f openrune/docker-compose.yml ps", "ours", NONE, ALLOW),
        # --- reading a harness script is not running it (sd32, 2026-10-21)
        ("sed -n 1,47p tools/harness/integrate.py; cat re/harness/integration-tools/integration.lock | head", "ours", FORK, ALLOW),
        ("grep -n lease tools/harness/ship.sh tools/harness/deploy.sh", "agent", NONE, ALLOW),
        ("python3 tools/harness/integrate.py build --now", "ours", FORK, DENY),
        ("tools/harness/deploy.sh int-1", "ours", FORK, DENY),
        # --- the legitimate fork actions the old bare-word `upstream` rule denied
        ("tools/fork.sh pr-edit 21 pr-texts/stile-approach.upstream.body", "agent", FORK, ALLOW),
        ('git commit -m "qa: upstream gate FAIL" && git push origin x:docs', "docs", DOCS, ALLOW),
        ("git -C {upr} push fork fix/x", "ours", FORK, ALLOW),
        # --- fork pushes, resolved through the remote URL
        ("git -C {upr} push fork fix/x 2>&1 | tail -n 3", "ours", FORK, ALLOW),
        ("cd {upr} && git push fork fix/x", "ours", FORK, ALLOW),
        ("cd {upr}; git push -u fork HEAD:refs/heads/fix/x", "ours", FORK, ALLOW),
        ("git push origin fix/x", "agent", FORK, ALLOW),
        ("git push --force-with-lease origin fix/x", "agent", FORK, ALLOW),
        ('git commit -m "address upstream review" && git push origin fix/x', "agent", FORK, ALLOW),
        ("git push " + FORK_SSH + " fix/x", "ours", FORK, ALLOW),
        ("git -C {upr} push -o ci.skip fork fix/x >/dev/null 2>&1", "ours", FORK, ALLOW),
        # --- agent clones whose origin is the local push clone (a folder, not GitHub)
        ("git push origin docs", "local", FORK, ALLOW),
        ("git push origin fix/x", "local", DOCS, DENY),
        ("git push origin docs", "local", DOCS, ALLOW),
        ("git push fork fix/x", "local", FORK, ALLOW),
        ("git push upstream fix/x", "local", FORK, DENY),
        # --- pushes to OpenRune upstream, or targets the hook can't tell
        ("git push origin fix/x", "upr", FORK, DENY),
        ("git -C {upr} push origin fix/x", "agent", FORK, DENY),
        ("cd {upr} && git push origin fix/x", "agent", FORK, DENY),
        ("cd {agent} && git -C {upr} push origin fix/x", "agent", FORK, DENY),
        ("git push", "agent", FORK, DENY),
        ("git push --set-upstream", "agent", FORK, DENY),
        ("git push " + UPSTREAM_URL + " fix/x", "agent", FORK, DENY),
        ("git push nosuchremote fix/x", "agent", FORK, DENY),
        ("git -C {upr} push fork main", "ours", FORK, DENY),
        ("git push --mirror origin", "agent", FORK, DENY),
        ('bash -c "git push origin fix/x"', "agent", FORK, DENY),
        ("echo $(git push origin fix/x)", "agent", FORK, DENY),
        ("git push origin fix/x && git -C {upr} push origin fix/x", "agent", FORK, DENY),
        # --- gh writes
        ("gh pr edit 362 -R OpenRune/OpenRune-Server --body-file b", "agent", FORK, DENY),
        ("gh api -X PATCH repos/OpenRune/OpenRune-Server/pulls/362 -F body=@b", "agent", FORK, DENY),
        ("gh pr comment 362 --repo https://github.com/OpenRune/OpenRune-Server -b hi", "agent", FORK, DENY),
        ("gh api -X PATCH repos/AlexPerrin/OpenRune-Server/pulls/21 -F body=@pr-texts/x.upstream.body", "agent", FORK, ALLOW),
        ("gh pr create -R AlexPerrin/OpenRune-Server --base main --head fix/x --title upstream-ready", "agent", FORK, ALLOW),
        ("gh pr edit 21 --body-file b", "agent", FORK, DENY),   # target not named
        ("gh pr comment 21 -R AlexPerrin/OpenRune-Server -b x && gh pr comment 362 -R OpenRune/OpenRune-Server -b x",
         "agent", FORK, DENY),
        # --- fork.sh is fork-only by construction, unless the command names OpenRune upstream
        ("tools/fork.sh push fix/x --force-with-lease", "ours", FORK, ALLOW),
        ("tools/fork.sh pr-comment 21 notes/upstream-review.md", "ours", FORK, ALLOW),
        ("tools/fork.sh pr-create fix/x t OpenRune/OpenRune-Server", "ours", FORK, DENY),
        ("tools/fork.sh push fix/x", "ours", NONE, DENY),
        ("tools/fork.sh push fix/x", "ours", DOCS, DENY),
        # --- --docs-writes: a non-forced, single refspec onto docs, remote resolving to the fork
        ("git push origin HEAD:refs/heads/docs", "docs", DOCS, ALLOW),
        ("git push origin docs", "docs", DOCS, ALLOW),
        ("git -C {upr} push fork local-docs:docs", "ours", DOCS, ALLOW),
        ("git push --force origin x:docs", "docs", DOCS, DENY),
        ("git push -f origin x:docs", "docs", DOCS, DENY),
        ("git push origin +x:docs", "docs", DOCS, DENY),
        ("git push origin fix/x", "docs", DOCS, DENY),
        ("git push origin x:docs y:docs2", "docs", DOCS, DENY),
        ("git push origin x:docs", "upr", DOCS, DENY),
        ("git push", "docs", DOCS, DENY),
        ("gh pr comment 21 -R AlexPerrin/OpenRune-Server -b x", "docs", DOCS, DENY),
        # --- BR-P1: server-qa pushes the fork's gate scratch branches (forced allowed) and docs, nothing else
        ("git -C {upr} push --force fork HEAD:refs/heads/gate/feat", "ours", DOCS, ALLOW),
        ("git push origin abc123:refs/heads/gate/feat", "docs", DOCS, ALLOW),
        ("git push origin +abc123:gate/feat", "local", DOCS, ALLOW),
        ("git push origin :gate/feat", "docs", DOCS, DENY),
        ("git push origin --delete gate/feat", "docs", DOCS, DENY),
        ("git push origin x:gate/a y:gate/b", "docs", DOCS, DENY),
        ("git push origin x:gate/feat", "upr", DOCS, DENY),
        ("git push origin x:gate/feat", "docs", NONE, DENY),
        ("git push --force origin x:content/feat", "docs", DOCS, DENY),
        # --- the console runs the contribution after the user's yes: denied to every role
        ("python3 ~/osrs-harness/hd.py contribute feat --approved abc1234", "ours", FORK, DENY),
        ("python3 ~/osrs-harness/hd.py contribute feat --approved abc1234", "docs", DOCS, DENY),
        ("python3 ~/osrs-harness/hd.py gate-ci feat", "docs", DOCS, ALLOW),
        ("python3 ~/osrs-harness/hd.py gate feat PASS", "docs", DOCS, ALLOW),
        # --- client roles (no flags): no pushes or GitHub writes at all
        ("git push origin x", "agent", NONE, DENY),
        ("git -C {upr} push fork fix/x", "ours", NONE, DENY),
        ("tools/fork.sh pr-edit 21 b", "ours", NONE, DENY),
        ("gh pr edit 21 -R AlexPerrin/OpenRune-Server --body-file b", "ours", NONE, DENY),
        ("git push origin master:main", "ours", NONE, DENY),
        ("git stash push -m wip", "ours", NONE, ALLOW),
        ("git status && git log --oneline -3", "ours", NONE, ALLOW),
        ("gh pr view 362 -R OpenRune/OpenRune-Server", "ours", NONE, ALLOW),
        ("grep -rn upstream docs/", "ours", NONE, ALLOW),
        # --- orchestrator-only actions, whatever the flags
        ("openrune/upstream/openrune.sh deploy abc123", "ours", FORK, DENY),
        ("docker compose --env-file switch.env up -d", "ours", DOCS, DENY),
        ("python3 tools/progress.py", "ours", NONE, DENY),
        ("python3 tools/progress.py --dry-run", "ours", FORK, ALLOW),
    ]

    def test_table(self):
        for cmd, cwd, flags, expected in self.CASES:
            with self.subTest(cmd=cmd, cwd=cwd, flags=flags):
                reason = self.decide(cmd, cwd, flags)
                self.assertEqual(reason is None, expected, f"{'denied' if reason else 'allowed'}: {reason}")

    def test_reason_names_the_target(self):
        reason = self.decide("git push origin fix/x", "upr", FORK)
        self.assertIn("OpenRune/OpenRune-Server", reason)

    def test_hook_cli(self):
        """The hook as the agents run it: JSON on stdin, a deny decision or nothing on stdout."""
        def run(cmd, flags):
            data = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": self.agent})
            return subprocess.run([sys.executable, os.path.join(HOOKS, "deny_publish.py"), *flags], input=data,
                                  capture_output=True, text=True, env=dict(os.environ, HD_EVENTS=os.devnull)).stdout
        self.assertEqual(run("git push origin fix/x", FORK), "")
        self.assertIn('"deny"', run("git push origin fix/x", NONE))


class ShellParseTest(unittest.TestCase):
    def test_segments_keep_redirections(self):
        self.assertEqual(shellparse.segments("git push fork x 2>&1 | tail -3 && echo ok"),
                         ["git push fork x 2>&1", "tail -3", "echo ok"])
        self.assertEqual(shellparse.segments("a &>/dev/null; b"), ["a &>/dev/null", "b"])

    def test_words_drop_redirections_and_assignments(self):
        self.assertEqual(shellparse.words("FOO=1 git push fork x 2> /dev/null >out"), ["git", "push", "fork", "x"])

    def test_parse_push(self):
        p = shellparse.parse_push(["git", "-C", "/r", "-c", "a=b", "push", "-o", "x", "--force", "fork", "a:b"], "/")
        self.assertEqual((p["dir"], p["remote"], p["refspecs"]), ("/r", "fork", ["a:b"]))
        self.assertTrue(shellparse.forced(p))
        self.assertIsNone(shellparse.parse_push(["git", "stash", "push"], "/"))

    def test_upstream_name(self):
        self.assertTrue(shellparse.UPSTREAM_NAME.search("gh pr view -R OpenRune/OpenRune-Server"))
        self.assertTrue(shellparse.UPSTREAM_NAME.search("https://github.com/OpenRune/x"))
        self.assertFalse(shellparse.UPSTREAM_NAME.search("AlexPerrin/OpenRune-Server upstream re/upstream-pr/or"))


class GithubScopeTest(unittest.TestCase):
    def test_push_targets(self):
        t = tempdir(self)
        upr = init_repo(os.path.join(t, "or"), remotes={"origin": UPSTREAM_URL, "fork": FORK_SSH})
        self.assertEqual(github_scope.classify("git push origin fix/x 2>&1", upr)[0], "upstream")
        self.assertEqual(github_scope.classify("git push", upr)[0], "unknown")
        self.assertEqual(github_scope.classify("git status", upr)[0], "read")

    def run_scope(self, cmd, cwd):
        import subprocess
        data = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": cwd})
        r = subprocess.run([sys.executable, os.path.join(HOOKS, "github_scope.py")], input=data, capture_output=True,
                           text=True)
        return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] if r.stdout.strip() else None

    def test_variables_assigned_in_the_command(self):
        # The command that made the user approve a fork push (2026-10-20): `wt=...` then `git -C $wt push fork ...`.
        t = tempdir(self)
        os.makedirs(os.path.join(t, "re", "harness"))
        init_repo(os.path.join(t, "re", "harness", "integration-tools"), remotes={"fork": FORK_SSH})
        upr = init_repo(os.path.join(t, "or"), remotes={"origin": UPSTREAM_URL, "fork": FORK_SSH})
        self.assertEqual(self.run_scope("wt=re/harness/integration-tools && git -C $wt commit -q -m x -- a && "
                                        "git -C $wt push -q fork local/integration-tools:local/integration-tools", t),
                         None)   # no prompt (mixed command: the normal permission flow)
        self.assertEqual(self.run_scope("wt=re/harness/integration-tools && "
                                        "git -C $wt push -q fork local/integration-tools:local/integration-tools", t),
                         "allow")
        self.assertEqual(self.run_scope('d="' + upr + '"; git -C "${d}" push origin fix/x', t), "ask")

    def test_command_substitution_in_an_option(self):
        # The second fork push that prompted (2026-10-20): the lease value comes from $(git -C <dir> rev-parse ...).
        t = tempdir(self)
        os.makedirs(os.path.join(t, "re", "harness"))
        init_repo(os.path.join(t, "re", "harness", "integration"), remotes={"fork": FORK_SSH})
        upr = init_repo(os.path.join(t, "or"), remotes={"origin": UPSTREAM_URL, "fork": FORK_SSH})
        cmd = ("git -C re/harness/integration push -q --force-with-lease=integration:$(git -C re/harness/integration "
               "rev-parse fork/integration) fork HEAD:refs/heads/integration")
        self.assertEqual(self.run_scope(cmd, t), "allow")
        self.assertEqual(self.run_scope("git -C " + upr + " push --force-with-lease=x:$(git rev-parse y) origin x", t),
                         "ask")
        self.assertEqual(self.run_scope("echo $(git -C " + upr + " push origin x)", t), "ask")
        # the harness repo is ours too (2026-10-21: its first push asked)
        hr = init_repo(os.path.join(t, "osrs-harness"), remotes={"origin": "git@github.com:AlexPerrin/osrs-harness.git"})
        self.assertEqual(self.run_scope("git -C " + hr + " push -q origin main", t), "allow")
        # a read inside a substitution is not a write (sd35, 2026-10-21: `out=$(gh run list -R <fork> ...)` prompted)
        self.assertNotEqual(self.run_scope("out=$(gh run list -R AlexPerrin/OpenRune-Server --commit abc --json url); echo $out", t), "ask")
        self.assertEqual(self.run_scope("x=$(gh pr create -R OpenRune/OpenRune-Server --head AlexPerrin:fix/x --title t --body b)", t), "ask")

    def test_push_from_a_worktree_created_in_the_same_command(self):
        # The archive push that prompted (2026-10-20): `git -C clone worktree add $W fork/docs && ... cd $W && git push`.
        t = tempdir(self)
        upr = init_repo(os.path.join(t, "or"), remotes={"origin": UPSTREAM_URL, "fork": FORK_SSH})
        cmd = ("S=" + t + "/scratch; W=$S/docs-archive; rm -rf $W; git -C " + upr + " worktree add -q --detach $W fork/docs"
               " && cp a $W/b && cd $W && git add -A && git commit -q -m archive && git push fork HEAD:docs 2>&1 | tail -1")
        self.assertNotEqual(self.run_scope(cmd, t), "ask")
        self.assertNotEqual(self.run_scope("git -C " + upr + " worktree add " + t + "/w2 main && git -C " + t +
                                           "/w2 push fork HEAD:refs/heads/x", t), "ask")
        self.assertEqual(self.run_scope("git -C " + upr + " worktree add " + t + "/w3 main && cd " + t +
                                        "/w3 && git push origin HEAD:refs/heads/x", t), "ask")
        d = deny_publish.decide({"tool_input": {"command": "git -C " + upr + " worktree add -b y " + t + "/w4 && cd " + t +
                                                "/w4 && git push fork y"}, "cwd": t}, ["--fork-writes"])
        self.assertIsNone(d)

    def test_contribution_and_fork_actions(self):
        """`hd contribute` is the user's yes bound to a commit (publish_gate checks it): no second prompt; fork CI and
        gate scratch pushes never prompt; any other upstream write does."""
        t = tempdir(self)
        upr = init_repo(os.path.join(t, "or"), remotes={"origin": UPSTREAM_URL, "fork": FORK_SSH})
        self.assertEqual(self.run_scope("python3 /home/alex/osrs-harness/hd.py contribute feat --approved abc1234", t), "allow")
        self.assertEqual(self.run_scope("gh workflow run ci.yml -R AlexPerrin/OpenRune-Server --ref gate/feat", t), "allow")
        self.assertEqual(self.run_scope("gh workflow run ci.yml -R OpenRune/OpenRune-Server --ref main", t), "ask")
        self.assertEqual(self.run_scope("git -C " + upr + " push --force fork abc:refs/heads/gate/feat", t), "allow")
        self.assertEqual(self.run_scope("gh pr ready 7 -R OpenRune/OpenRune-Server", t), "ask")
        self.assertEqual(self.run_scope("gh pr ready 7 --undo -R OpenRune/OpenRune-Server", t), "ask")
        self.assertEqual(self.run_scope("gh pr comment 7 -R OpenRune/OpenRune-Server -b x", t), "ask")

    def test_help_is_read_only(self):
        t = tempdir(self)
        self.assertNotEqual(self.run_scope("gh pr edit 367 -R OpenRune/OpenRune-Server --help", t), "ask")
        self.assertEqual(self.run_scope("gh pr edit 367 -R OpenRune/OpenRune-Server --title x", t), "ask")


class PublishGateHeredocTest(unittest.TestCase):
    def test_note_mentioning_pr_create_is_not_gated(self):
        import subprocess
        cmd = "cat > /tmp/x.md <<'EOF'\nuse gh pr create -R OpenRune/OpenRune-Server and git tag v1.2.3\nEOF"
        data = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
        r = subprocess.run([sys.executable, os.path.join(HOOKS, "publish_gate.py")], input=data, capture_output=True,
                           text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "")


class PublishGateTest(unittest.TestCase):
    def setUp(self):
        import hd_helpers as H
        self.d = H.sandbox(self)

    def run_gate(self, cmd, **env):
        t = tempdir(self)
        data = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
        return subprocess.run([sys.executable, os.path.join(HOOKS, "publish_gate.py")], input=data, capture_output=True,
                              text=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=t, **env)).stdout

    def release(self, cmd, record=None, where="evidence", verdict="PASS"):
        """Run the gate on a release command in a client repo with one commit; the record (the commit, a sha, or
        None) is written under qa/ or the evidence tree."""
        from helpers import commit_file
        base = tempdir(self)
        root = init_repo(os.path.join(base, "client"))
        sha = commit_file(root, "a.txt", "a\n")
        ev = os.path.join(base, "ev")
        if record:
            c = sha if record == "head" else record
            path = (os.path.join(root, "qa", "client-1.2.3.md") if where == "qa"
                    else os.path.join(ev, "rel-1", "client-record.md"))
            os.makedirs(os.path.dirname(path))
            open(path, "w").write(f"- Commit: `{c}`\n\n## Verdict: **{verdict}**\n")
        return sha, self.run_gate(cmd.replace("SHA", sha), HD_CLIENT_ROOT=root, HD_EVIDENCE_DIR=ev)

    def test_release_target_flag_and_evidence_record(self):
        for cmd in ("gh release create v1.2.3 --target SHA", "gh release create v1.2.3 --target=SHA --title t"):
            self.assertEqual(self.release(cmd, "head")[1], "")

    def test_release_old_qa_record_and_positional_sha(self):
        self.assertEqual(self.release("gh release create v1.2.3 SHA", "head", where="qa")[1], "")
        self.assertEqual(self.release("git tag v1.2.3", "head", where="qa")[1], "")

    def test_release_denied_without_a_passing_record_at_the_commit(self):
        c = "gh release create v1.2.3 --target SHA"
        self.assertIn("no release record", self.release(c)[1])
        self.assertIn("no record passes", self.release(c, "head", verdict="FAIL")[1])
        self.assertIn("no record passes", self.release(c, "d" * 40)[1])

    def test_fork_pr_not_gated(self):
        self.assertEqual(self.run_gate("gh pr create -R AlexPerrin/OpenRune-Server --head AlexPerrin:fix/x --title t"), "")
        self.assertEqual(self.run_gate("gh pr create --title 'upstream gate notes' --body-file re/upstream-pr/b"), "")

    def test_upstream_pr_gated(self):
        self.assertIn('"deny"', self.run_gate("gh pr create -R OpenRune/OpenRune-Server --head AlexPerrin:fix/x"))
        self.assertIn('"deny"', self.run_gate("gh pr create --head AlexPerrin:fix/x --title t"))

    def test_direct_upstream_pr_needs_qa_record_at_the_branch_commit(self):
        import hd_helpers as H
        clone = init_repo(os.path.join(self.d, "clone"))
        from helpers import commit_file, git
        sha = commit_file(clone, "a.txt", "a\n")
        git(clone, "branch", "content/feat")
        cmd = "gh pr create -R OpenRune/OpenRune-Server --head AlexPerrin:content/feat --title t"
        env = {"INTEGRATION_CLONE": clone}
        H.change("feat", "server", stage="gate", commit=sha)
        self.assertIn("QA record missing", self.run_gate(cmd, **env))
        H.write_gate("feat", sha)
        self.assertEqual(self.run_gate(cmd, **env), "")
        H.write_gate("feat", "f" * 40)
        self.assertIn('"deny"', self.run_gate(cmd, **env))

    def test_contribute_is_bound_to_the_approved_commit_and_a_qa_record(self):
        import hd_helpers as H
        sha = "a" * 40
        H.change("feat", "server", stage="contribute", commit=sha)
        cmd = "python3 /h/hd.py contribute feat --approved "
        self.assertIn("no QA record", self.run_gate(cmd + sha))
        H.write_gate("feat", sha, "FAIL", findings=["x"])   # findings are on the card; they do not block the user's yes
        self.assertEqual(self.run_gate(cmd + sha[:12]), "")
        self.assertIn("approval is for bbbbbbbbb", self.run_gate(cmd + "b" * 40))
        self.assertIn("bound to the commit", self.run_gate("python3 /h/hd.py contribute feat"))
        self.assertIn("no change nope", self.run_gate("python3 /h/hd.py contribute nope --approved " + sha))
        H.write_gate("feat", "c" * 40)   # a record for another commit voids the approval
        self.assertIn("no QA record", self.run_gate(cmd + sha))

    def test_a_note_mentioning_contribute_is_not_a_command(self):
        cmd = "cat > /tmp/x.md <<'EOF'\npython3 hd.py contribute feat --approved abc1234\nEOF"
        self.assertEqual(self.run_gate(cmd), "")


class QaWriteScopeTest(unittest.TestCase):
    def run_scope(self, path):
        import qa_write_scope  # noqa: F401
        data = json.dumps({"tool_input": {"file_path": path}})
        return subprocess.run([sys.executable, os.path.join(HOOKS, "qa_write_scope.py")], input=data, capture_output=True,
                              text=True).stdout

    def test_qa_writes_its_record_in_the_evidence_dir_and_never_code(self):
        self.assertEqual(self.run_scope("/home/x/osrs-plugins-reverse/re/evidence/feat/gate.md"), "")
        self.assertEqual(self.run_scope("/home/x/osrs-plugins-reverse/re/evidence/feat/gate-ci.json"), "")
        self.assertEqual(self.run_scope("/home/x/osrs-plugins-reverse/qa/client-1.2.3.md"), "")
        self.assertIn('"deny"', self.run_scope("/home/x/src/OpenRune-Server/server/Foo.kt"))
        self.assertIn('"deny"', self.run_scope("/home/x/osrs-harness/hd/stages.py"))


if __name__ == "__main__":
    unittest.main()
