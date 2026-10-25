"""Fixtures for the hd (harness v3) tests: a temp harness dir (changes, state, policy copy), the
FakeObserver, and change factories. Nothing touches the real store, or the network."""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)   # the harness repo
sys.path.insert(0, ROOT)

ENV_KEYS = ("HD_HARNESS_DIR", "HD_STATE_DIR", "HD_EVENTS", "HD_POLICY", "HD_EVIDENCE_DIR", "HD_NO_FETCH", "HD_NO_RECOUNT")


def write_test_policy(dest):
    """The real policy's structure with the numeric knobs the tests rely on pinned, so a change of the live values
    (capacity) never changes a test: 3 agents, 2 builds, 2 clients, 1 image."""
    import yaml
    with open(os.path.join(ROOT, "harness", "policy.yaml")) as f:
        pol = yaml.safe_load(f)
    pol["capacity"] = {"agent": 3, "build": 2, "client": 2, "image": 1}
    with open(dest, "w") as f:
        yaml.safe_dump(pol, f)


def sandbox(test):
    """A temp harness dir with the real policy copied in; environment pointed at it for the test's duration."""
    d = tempfile.mkdtemp(prefix="hd-test-")
    test.addCleanup(shutil.rmtree, d, True)
    harness = os.path.join(d, "harness")
    os.makedirs(os.path.join(harness, "changes"))
    os.makedirs(os.path.join(harness, "state"))
    os.makedirs(os.path.join(d, "evidence"))
    write_test_policy(os.path.join(harness, "policy.yaml"))
    old = {k: os.environ.get(k) for k in ENV_KEYS}
    os.environ.update(HD_HARNESS_DIR=harness, HD_STATE_DIR=os.path.join(harness, "state"),
                      HD_EVENTS=os.path.join(harness, "state", "events.jsonl"),
                      HD_POLICY=os.path.join(harness, "policy.yaml"),
                      HD_EVIDENCE_DIR=os.path.join(d, "evidence"), HD_NO_FETCH="1", HD_NO_RECOUNT="1")

    def restore():
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    test.addCleanup(restore)
    from hd import policy
    policy._cache.clear()
    test.addCleanup(policy._cache.clear)
    return d


def change(slug="feat", track="server", stage="ready", branch=None, commit=None, dod=("done",), ticked=True, **kw):
    from hd import store
    ch = store.new(slug, track, slug, dod=list(dod), stage="ready" if dod else "backlog",
                   branch=branch or (f"content/{slug}" if track == "server" else f"client/{slug}"))
    ch["stage"] = stage
    if commit:
        ch["commit"] = commit
    if ticked:
        ch.body = ch.body.replace("- [ ] ", "- [x] ")
    ch.update(kw)
    store.save(ch)
    return store.load(slug)


SHA = "a" * 40
SHB = "b" * 40


def env(test, **kv):
    """Set environment variables for the test's duration (None removes)."""
    old = {k: os.environ.get(k) for k in kv}
    for k, v in kv.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v

    def restore():
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    test.addCleanup(restore)


def dead_pid():
    """A pid that belonged to a process that has exited (reaped, so os.kill(pid, 0) fails)."""
    import subprocess
    p = subprocess.Popen(["true"])
    p.wait()
    return p.pid


def stub(d, name, body):
    """An executable script in d; returns its path."""
    p = os.path.join(d, name)
    with open(p, "w") as f:
        f.write("#!/usr/bin/env bash\n" + body)
    os.chmod(p, 0o755)
    return p


CHECKS = ("accuracy", "ci", "format", "scope", "style", "text", "ingame")


def gate_text(commit, verdict="PASS", findings=(), branch="content/feat", checks=None):
    """QA's aggregate record in the format `hd gate` checks."""
    checks = dict({n: "PASS" for n in CHECKS}, **(checks or {}))
    lines = [f"# Gate: {branch}", f"- Branch: `{branch}`", f"- Commit: `{commit}`", "- Tests: server:app; CI run 123", f"## Gate: **{verdict}**", "## Checks"]
    lines += [f"- {n}: {r}" + (" reason" if r == "N/A" else "") for n, r in checks.items()]
    lines += ["## Findings"] + ([f"- {f}" for f in findings] or ["- none"])
    return "\n".join(lines) + "\n"


def write_gate(slug, commit, verdict="PASS", findings=(), ci="success", **kw):
    """QA's evidence files for a change: gate.md and gate-ci.json in its evidence dir."""
    import json
    from hd import evidence_dir
    d = os.path.join(evidence_dir(), slug)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "gate.md"), "w") as f:
        f.write(gate_text(commit, verdict, findings, **kw))
    if ci:
        with open(os.path.join(d, "gate-ci.json"), "w") as f:
            json.dump({"commit": commit, "result": ci, "scratch": "s" * 40, "upstream_main": "m" * 40, "findings": []}, f)


def evidence_dir_for(slug):
    from hd import evidence_dir
    return os.path.join(evidence_dir(), slug)
