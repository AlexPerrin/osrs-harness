#!/usr/bin/env python3
"""The harness gate: gates/harness.py <slug> <head> <base> <evidence>. The test suite at <head> in a throwaway worktree
with its own state dir. Exit 0 ok, 1 fail; stdout is the test run's tail."""
import os
import shutil
import subprocess
import sys
import tempfile

HD_HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(slug, head, base, ev):
    wt = tempfile.mkdtemp(prefix=f"hd-gate-{slug}-")
    try:
        subprocess.run(["git", "-C", HD_HOME, "worktree", "add", "-q", "--detach", wt, head], check=True, capture_output=True)
        env = dict(os.environ, HD_STATE=os.path.join(wt, "state"), HD_HOME=wt)
        r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=wt, env=env,
                           capture_output=True, text=True, timeout=900)
        print("\n".join((r.stdout + r.stderr).strip().splitlines()[-15:]))
        return 0 if r.returncode == 0 else 1
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"tests could not run: {e}")
        return 1
    finally:
        subprocess.run(["git", "-C", HD_HOME, "worktree", "remove", "--force", wt], capture_output=True)
        shutil.rmtree(wt, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
