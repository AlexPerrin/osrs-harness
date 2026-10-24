"""The integration deny rules in deny_publish.py and LOCK_DIR in device-lock.sh. Temp lock dirs only."""
import os
import shutil
import subprocess
import sys
import unittest

from helpers import GIT_ENV, HARNESS_TOOLS, HOOKS, ROOT, commit_file, git, init_repo, read_task, tempdir, write_task

sys.path.insert(0, HOOKS)
import deny_publish  # noqa: E402

LIVE_LINE = "- 2026-10-20T04:44:42Z Live 2026-10-20 04:44 UTC (integration e5b18a87b, image integration-e5b18a8).\n"


class IntegrationDenyTest(unittest.TestCase):
    """The orchestrator-only integration steps, denied to every agent role whatever its flags."""
    CASES = [
        # (command, cwd (relative to a temp root), denied)
        ("tools/harness/deploy.sh int-20261020-1", ".", True),
        ("tools/harness/ship.sh fix-x", ".", True),
        ("LOCK_NAME=desktop tools/device-lock.sh reclaim idle", ".", True),
        ("LOCK_NAME=desktop tools/device-lock.sh revoke sd28", ".", True),
        ("tools/harness/ship.sh fix-x --dry-run", ".", True),
        ("bash tools/harness/image.sh re/harness/qa/x int-20261020-1", ".", True),
        ("/home/alex/osrs-plugins-reverse/tools/harness/deploy.sh", ".", True),
        ("./deploy.sh int-1", "tools/harness", True),
        ("./image.sh clone int-1", "tools/harness", True),
        ("cd tools/harness && ./deploy.sh int-1", ".", True),
        ("python3 tools/harness/orchestrate.py deploy", ".", True),
        ("tools/harness/orchestrate.py deploy int-20261020-1", ".", True),
        ("tools/harness/orchestrate.py integrate build --now", ".", True),
        ("tools/harness/orchestrate.py integrate status", ".", True),
        ("tools/harness/integrate.py build --now", ".", True),
        ("python3 tools/harness/integrate.py enqueue fix-x", ".", True),
        ("./integrate.py status", "tools/harness", True),
        ("tools/harness/orchestrate.py image int-20261020-1", ".", True),
        ("docker tag osrs-openrune:integration-e5b18a8 osrs-openrune:latest", ".", True),
        ("docker image tag osrs-openrune:x osrs-openrune:rollback-1", ".", True),
        ("docker rm -f osrs-openrune", ".", True),
        ("docker container rm osrs-openrune-http", ".", True),
        ("docker rmi osrs-openrune:bootcheck23", ".", True),
        ("docker image rm osrs-openrune:old", ".", True),
        ("docker restart osrs-openrune", ".", True),
        ("docker stop osrs-openrune-http-desktop", ".", True),
        ("docker compose -f openrune/docker-compose.yml up -d --no-deps openrune", ".", True),
        ("docker compose up -d --no-deps openrune", "openrune", True),
        ("cd openrune && docker compose up -d", ".", True),
        ("docker-compose -p osrs-openrune down", ".", True),
        ("docker compose --project-directory openrune restart", ".", True),
        ('bash -c "docker compose -f openrune/docker-compose.yml up -d"', ".", True),
        ("docker compose -f openrune/docker-compose.yml build openrune", ".", True),
        # --- allowed: reads, the agents' own containers, mentions that run nothing
        ("tools/harness/orchestrate.py status", ".", False),
        ("tools/harness/orchestrate.py next --track server", ".", False),
        ("python3 tools/harness/orchestrate.py status | grep deploy", ".", False),
        ("docker ps --filter name=osrs-openrune", ".", False),
        ("docker logs --tail 50 osrs-openrune", ".", False),
        ("docker exec osrs-openrune-http test -e /tmp/local-auth-user", ".", False),
        ("docker images osrs-openrune", ".", False),
        ("docker image ls osrs-openrune", ".", False),
        ("docker inspect osrs-openrune", ".", False),
        ("docker rm -f qa-or-server qa-or-http", ".", False),
        ("docker rmi qa-branch:sd31", ".", False),
        ("docker compose -f openrune/docker-compose.yml ps", ".", False),
        ("docker compose logs --tail 20 openrune", "openrune", False),
        ("docker compose -f openrune/docker-compose.yml config", ".", False),
        ("grep -n deploy docs/ARCHITECTURE.md", ".", False),
        ("ls tools/harness", ".", False),
        ("./deploy.sh", "elsewhere", False),
    ]

    def setUp(self):
        self.root = tempdir(self)
        for d in ("tools/harness", "openrune", "elsewhere"):
            os.makedirs(os.path.join(self.root, d))

    def test_table(self):
        for flags in ([], ["--fork-writes"], ["--docs-writes"]):
            for cmd, cwd, denied in self.CASES:
                with self.subTest(cmd=cmd, cwd=cwd, flags=flags):
                    reason = deny_publish.decide({"tool_input": {"command": cmd},
                                                  "cwd": os.path.normpath(os.path.join(self.root, cwd))}, flags)
                    self.assertEqual(reason is not None, denied, reason)
                    if denied:
                        self.assertIn("Only the orchestrator", reason)

    def test_scripts_in_this_repos_train_dir_are_denied(self):
        """The train scripts moved to <harness repo>/train/: the absolute path still resolves to ours (denied)."""
        for name in ("deploy.sh", "image.sh", "integrate.py"):
            with self.subTest(name=name):
                cmd = os.path.join(ROOT, "train", name) + " int-1"
                reason = deny_publish.decide({"tool_input": {"command": cmd}, "cwd": self.root}, [])
                self.assertIsNotNone(reason)

    def test_hook_cli(self):
        import json
        data = json.dumps({"tool_name": "Bash", "tool_input": {"command": "tools/harness/deploy.sh x"}, "cwd": self.root})
        out = subprocess.run([sys.executable, os.path.join(HOOKS, "deny_publish.py"), "--fork-writes"], input=data,
                             capture_output=True, text=True, env=dict(os.environ, HD_EVENTS=os.devnull)).stdout
        self.assertIn('"deny"', out)
        self.assertIn("integration images, deploys", out)


class LockDirTest(unittest.TestCase):
    """device-lock.sh is a wrapper over `hd lease` (harness v3): the lease lives in the hd state dir and LOCK_DIR
    holds only the v2 mirror files (osrs-<name>.lock/owner while held, osrs-<name>-status)."""

    def setUp(self):
        import hd_helpers
        self.d = hd_helpers.sandbox(self)
        self.lock_dir = os.environ["HD_LOCK_DIR"]

    def run_lock(self, *args, name="device"):
        env = dict(os.environ, LOCK_NAME=name, LOCK_DIR=self.lock_dir)
        return subprocess.run(["bash", os.path.join(ROOT, "device-lock.sh"), *args], capture_output=True, text=True, env=env)

    def test_lock_dir_holds_every_file(self):
        who = "sd99"
        self.assertEqual(self.run_lock("grant", who, "30", "reuse", name="desktop").returncode, 0)
        r = self.run_lock("take", who, "ab test", name="desktop")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(os.path.isfile(os.path.join(self.lock_dir, "osrs-desktop.lock", "owner")))
        self.assertIn("taking desktop (sd99 dev, ab test)", open(os.path.join(self.lock_dir, "osrs-desktop.lock", "owner")).read())
        self.assertNotEqual(self.run_lock("status", name="desktop").returncode, 0)
        self.assertEqual(self.run_lock("take", "other", "x", name="desktop").returncode, 1)
        self.assertEqual(self.run_lock("free", who, name="desktop").returncode, 0)
        self.assertFalse(os.path.exists(os.path.join(self.lock_dir, "osrs-desktop.lock")))
        self.assertEqual(self.run_lock("status", name="desktop").returncode, 0)

    def test_default_is_tmp(self):
        src = open(os.path.join(ROOT, "device-lock.sh")).read()
        self.assertIn("HD_LOCK_DIR=${LOCK_DIR:-${HD_LOCK_DIR:-/tmp}}", src)
