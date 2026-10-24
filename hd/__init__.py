"""harnessd (hd): built against docs/PRD.md.

A change is the only unit of work; stages are observed, never set by hand; resources are leases; every state change
is an event; agents execute one stage and are spawned by the console session; two kinds of action need the user's OK in chat. The package:

  util      clock (UTC in, US Eastern out), atomic files, slugs
  events    append-only events.jsonl (BR-H4)
  store     change / lease / run / batch records on disk
  policy    harness/policy.yaml: tracks, roles, resources, limits (BR-P*)
  stages    the lifecycle and each stage's precondition per track (BR-C*, BR-S*)
  observe   external truth: git refs, fork CI, GitHub PRs, docker, processes (BR-H1)
  check     the hand-over check (the `checked` precondition)
  leases    the lease service (BR-R*)
  agents    stage executors booked by the daemon, spawned by the console (BR-G*)
  batches   trains and releases: queue, rebuild, gate, image, deploy (BR-B*)
  actions   what needs the user's OK, observed from the remotes (BR-A*)
  drive     the console's work list (`hd drive`)
  heal      repairs (BR-H2, BR-H3)
  tick      observe -> advance -> dispatch -> heal -> log
  daemon    the tick loop and the digest
  kpi       the harness KPIs from the event log

Paths: HD_HOME is this repo (osrs-harness); ROOT is the client checkout (HD_CLIENT_ROOT, default
~/osrs-plugins-reverse; the main checkout also from a worktree), where evidence, worktrees and the client build live;
the server side is isolated from it: SERVER_HOME (HD_SERVER_HOME, default ~/src) holds the fork clone OpenRune-Server
and openrune-work/ (integration build, tools worktree, qa clones, images, the agents' clones);
HARNESS = HD_HOME/harness (changes/ and policy.yaml are committed; state/ is git-ignored). HD_HARNESS_DIR overrides
HARNESS (tests).
"""
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
HD_HOME = os.path.dirname(HERE)   # this repo (osrs-harness): hd/, hooks/, harness/, tests/
_REPO = os.environ.get("HD_CLIENT_ROOT") or os.path.expanduser("~/osrs-plugins-reverse")   # the client checkout


def _main_checkout(root):
    r = subprocess.run(["git", "-C", root, "rev-parse", "--path-format=absolute", "--git-common-dir"],
                       capture_output=True, text=True)
    common = r.stdout.strip()
    if r.returncode == 0 and common.endswith("/.git"):
        return common[:-len("/.git")]
    return root


ROOT = _main_checkout(_REPO)


def server_home():
    return os.path.expanduser(os.environ.get("HD_SERVER_HOME") or "~/src")


def fork_clone():
    """The push clone of the fork: remote `fork` = AlexPerrin/OpenRune-Server, `origin` = upstream."""
    return os.environ.get("INTEGRATION_CLONE") or os.path.join(server_home(), "OpenRune-Server")


def server_work():
    return os.path.join(server_home(), "openrune-work")


def server_tools():
    """The fork's local/server-tools branch checked out: qa.sh, fork.sh, the cache scripts, the live stack's compose."""
    return os.environ.get("HD_SERVER_TOOLS") or os.path.join(server_work(), "server-tools")


def harness_dir():
    return os.environ.get("HD_HARNESS_DIR") or os.path.join(HD_HOME, "harness")


def changes_dir():
    return os.path.join(harness_dir(), "changes")


def state_dir():
    return os.environ.get("HD_STATE_DIR") or os.path.join(harness_dir(), "state")


def evidence_dir():
    return os.environ.get("HD_EVIDENCE_DIR") or os.path.join(ROOT, "re", "evidence")


def policy_path():
    return os.environ.get("HD_POLICY") or os.path.join(harness_dir(), "policy.yaml")
