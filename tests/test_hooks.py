"""The hooks (R6, R7, R8, R31): run start and stop bound to the change from the transcripts, the stop block, usage
from the transcript, and the one guard table. The hooks run as subprocesses with a temp state dir."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(HOME, "hooks")
sys.path.insert(0, HOME)
sys.path.insert(0, HOOKS)

BRIEF = "Harness change `stile-approach` (server track, stage `dev`). Read the change file first.\nmore"


def line(kind, content, usage=None, agent="a1"):
    msg = {"role": "user" if kind == "user" else "assistant", "content": content}
    if usage:
        msg["usage"] = usage
    return json.dumps({"type": kind, "agentId": agent, "sessionId": "s1", "message": msg})


class Env(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.state = os.path.join(self.tmp, "state")
        self.proj = os.path.join(self.tmp, "projects")
        os.makedirs(os.path.join(self.proj, "s1", "subagents"))
        self.parent = os.path.join(self.proj, "s1.jsonl")
        open(self.parent, "w").close()
        self.env = dict(os.environ, HD_STATE=self.state, HD_HOME=HOME)
        from hd import records
        self.records = records
        os.environ["HD_STATE"] = self.state

    def tearDown(self):
        shutil.rmtree(self.tmp)
        os.environ.pop("HD_STATE", None)

    def subagent(self, agent="a1", first=BRIEF, usages=()):
        p = os.path.join(self.proj, "s1", "subagents", f"agent-{agent}.jsonl")
        with open(p, "w") as f:
            f.write(line("user", first, agent=agent) + "\n")
            for u in usages:
                f.write(line("assistant", [{"type": "text", "text": "x"}], usage=u, agent=agent) + "\n")
        return p

    def hook(self, name, payload):
        r = subprocess.run([sys.executable, os.path.join(HOOKS, name)], input=json.dumps(payload), capture_output=True,
                           text=True, env=self.env, timeout=60)
        return json.loads(r.stdout) if r.stdout.strip() else None

    def start(self, agent="a1", role="server-dev", **extra):
        return self.hook("run_start.py", {"session_id": "s1", "transcript_path": self.parent, "cwd": HOME,
                                          "agent_id": agent, "agent_type": role, **extra})

    def stop(self, agent="a1", role="server-dev", active=False, last="done"):
        return self.hook("run_stop.py", {"session_id": "s1", "transcript_path": self.parent, "agent_id": agent,
                                         "agent_type": role, "stop_hook_active": active,
                                         "agent_transcript_path": self.subagent_path(agent),
                                         "last_assistant_message": last})

    def subagent_path(self, agent):
        return os.path.join(self.proj, "s1", "subagents", f"agent-{agent}.jsonl")

    def events(self, kind=None):
        p = os.path.join(self.state, "events.jsonl")
        if not os.path.exists(p):
            return []
        with open(p) as f:
            evs = [json.loads(l) for l in f]
        return [e for e in evs if kind is None or e["kind"] == kind]


class RunStartTest(Env):
    def test_binds_the_change_from_the_subagent_transcript(self):
        self.subagent()
        self.start()
        r = self.records.run("a1")
        self.assertEqual((r["role"], r["change"], r["ended"]), ("server-dev", "stile-approach", None))
        self.assertIn("console_pid", r)
        self.assertEqual(self.events("run")[0]["action"], "start")

    def test_ignores_an_agent_of_no_harness_role_and_no_change(self):
        self.subagent(first="Find every caller of foo.")
        self.start(role="general-purpose")
        self.assertIsNone(self.records.run("a1"))

    def test_falls_back_to_the_agent_call_in_the_parent_transcript(self):
        with open(self.parent, "w") as f:
            f.write(json.dumps({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Agent", "input": {"subagent_type": "server-dev", "prompt": BRIEF}}]}}) + "\n")
        self.start()
        self.assertEqual(self.records.run("a1")["change"], "stile-approach")


class RunStopTest(Env):
    USAGE = ({"input_tokens": 5, "output_tokens": 10, "cache_read_input_tokens": 100, "cache_creation_input_tokens": 1},
             {"input_tokens": 1, "output_tokens": 20, "cache_read_input_tokens": 200})

    def test_a_stop_without_the_record_ends_as_no_record_with_a_hold(self):
        self.subagent(usages=self.USAGE)
        self.start()
        self.assertIsNone(self.stop(last="I give up"))
        r = self.records.run("a1")
        self.assertEqual(r["exit"], "no-record")
        self.assertEqual(r["usage"], {"input": 6, "output": 30, "cache_read": 300, "cache_creation": 1, "turns": 2})
        hold = self.records.record("stile-approach", "hold")
        self.assertEqual(hold["by"], "a1")
        self.assertIn("I give up", hold["text"])

    def test_handover_written_since_the_start_lets_it_stop(self):
        self.subagent(usages=self.USAGE)
        self.start()
        self.records.save_record("stile-approach", "handover", {"sha": "abc"})
        self.assertIsNone(self.stop())
        r = self.records.run("a1")
        self.assertEqual((r["exit"], r["usage"]["output"]), ("ok", 30))
        self.assertEqual(self.events("run")[-1]["exit"], "ok")

    def test_an_old_handover_does_not_count(self):
        self.records.save_record("stile-approach", "handover", {"sha": "old", "ts": "2000-01-01T00:00:00Z"})
        self.subagent()
        self.start()
        self.assertIsNone(self.stop())
        self.assertEqual(self.records.run("a1")["exit"], "no-record")

    def test_a_question_asked_by_this_run_lets_it_stop(self):
        self.subagent()
        self.start()
        self.records.save_record("stile-approach", "hold", {"text": "which id?", "by": "a1"})
        self.assertIsNone(self.stop())
        self.assertEqual(self.records.run("a1")["exit"], "ok")

    def test_qa_owes_a_verdict_and_the_integrator_a_resolution(self):
        self.subagent(agent="q1")
        self.start(agent="q1", role="server-qa")
        self.stop(agent="q1", role="server-qa")
        self.assertEqual(self.records.run("q1")["exit"], "no-record")
        self.subagent(agent="q2")
        self.start(agent="q2", role="server-qa")
        self.records.save_record("stile-approach", "verdict", {"sha": "abc", "verdict": "PASS"})
        self.stop(agent="q2", role="server-qa")
        self.assertEqual(self.records.run("q2")["exit"], "ok")
        self.subagent(agent="i1", first="Harness change `t-1` (train)")
        self.start(agent="i1", role="integrator")
        self.stop(agent="i1", role="integrator")
        self.assertEqual(self.records.run("i1")["exit"], "no-record")

    def test_a_start_that_could_not_see_the_prompt_is_bound_at_stop(self):
        self.records.save_run({"agent_id": "a1", "role": "server-dev", "change": None, "console_pid": 1,
                               "started": self.records.now(), "ended": None, "exit": None})
        self.subagent()
        self.stop()
        self.assertEqual(self.records.run("a1")["change"], "stile-approach")

    def test_a_stop_the_start_hook_missed_is_still_recorded(self):
        self.subagent(usages=self.USAGE)
        self.records.save_record("stile-approach", "handover", {"sha": "abc"})
        self.assertIsNone(self.stop())
        self.assertEqual(self.records.run("a1")["change"], "stile-approach")


class GuardTest(Env):
    def setUp(self):
        super().setUp()
        from guard import Guard
        self.Guard = Guard
        self.repo = os.path.join(self.tmp, "repo")
        subprocess.run(["git", "init", "-q", self.repo], check=True)
        for name, url in (("fork", "https://github.com/AlexPerrin/OpenRune-Server.git"),
                          ("upstream", "git@github.com:OpenRune/OpenRune-Server.git"),
                          ("client", "https://github.com/AlexPerrin/osrs-plugins-reverse"),
                          ("local", os.path.join(self.tmp, "clone"))):
            subprocess.run(["git", "-C", self.repo, "remote", "add", name, url], check=True)
        self.cfg = self.records.config()

    def deny(self, role, cmd, slug="stile-approach"):
        return self.Guard(self.cfg, role, slug).decide(cmd, self.repo)

    def test_pushes_by_role_and_ref(self):
        self.assertIsNone(self.deny("server-dev", "git push fork HEAD:dev/stile-approach"))
        self.assertIsNone(self.deny("server-dev", "git push -u fork dev/stile-approach"))
        self.assertIn("may push only", self.deny("server-dev", "git push fork dev/other"))
        self.assertIn("may push only", self.deny("server-dev", "git push fork HEAD:content/stile-approach"))
        self.assertIn("may push only", self.deny("server-dev", "git push fork main"))
        self.assertIn("not one of our repos", self.deny("server-dev", "git push upstream dev/stile-approach"))
        self.assertIn("OpenRune upstream", self.deny("server-dev", "git push git@github.com:OpenRune/OpenRune-Server.git x"))
        self.assertIn("bare", self.deny("server-dev", "git push"))
        self.assertIsNone(self.deny("server-dev", "git push local anything:main"))
        self.assertIn("forced", self.deny("server-dev", "git push -f fork dev/stile-approach"))
        self.assertIsNone(self.deny("server-qa", "git push -f fork HEAD:gate/stile-approach"))
        self.assertIsNone(self.deny("server-qa", "git push fork HEAD:docs"))
        self.assertIn("forced", self.deny("server-qa", "git push -f fork HEAD:docs"))
        self.assertIn("may push only", self.deny("harness-dev", "git push fork HEAD:dev/stile-approach"))
        self.assertIsNone(self.deny("client-dev", "git push client HEAD:client/stile-approach"))
        self.assertIsNone(self.deny("console", "git push fork main"))
        self.assertIn("not one of our repos", self.deny("console", "git push upstream main"))
        self.assertIn("substitution", self.deny("console", "echo $(git push fork x)"))
        self.assertIsNone(self.deny("server-dev", "cd sub && git -C .. push fork HEAD:dev/stile-approach"))

    def test_github_writes(self):
        self.assertIsNone(self.deny("server-dev", "gh pr create -R AlexPerrin/OpenRune-Server --title t --body b"))
        self.assertIn("upstream", self.deny("server-dev", "gh pr create -R OpenRune/OpenRune-Server --title t"))
        self.assertIn("name one", self.deny("server-dev", "gh pr create --title t --body b"))
        self.assertIn("may not write", self.deny("client-dev", "gh pr comment 3 -R AlexPerrin/OpenRune-Server -b x"))
        self.assertIsNone(self.deny("console", "gh pr comment 1 -R AlexPerrin/osrs-harness -b hi"))
        self.assertIn("release", self.deny("console", "gh release create v0.1.3 -R AlexPerrin/osrs-plugins-reverse"))
        self.assertIsNone(self.deny("client-dev", "gh pr view 3 -R OpenRune/OpenRune-Server"))
        self.assertIn("upstream", self.deny("console", "gh api -X POST repos/OpenRune/OpenRune-Server/issues/1/comments -f body=x"))

    def test_live_stack_and_publish_are_the_ticks(self):
        self.assertIn("compose", self.deny("console", "docker compose --env-file switch.env up -d --no-deps openrune"))
        self.assertIsNone(self.deny("console", "docker compose ps"))
        self.assertIn("docker write", self.deny("server-dev", "docker stop osrs-openrune"))
        self.assertIsNone(self.deny("server-dev", "docker stop qa-dev-sd1"))
        self.assertIn("tick", self.deny("server-dev", "bash ~/osrs-harness/train/deploy.sh int-1"))
        self.assertIn("tick", self.deny("console", "python3 hd/publish.py stile-approach"))
        self.assertIn("tag", self.deny("console", "git tag v0.1.3"))
        self.assertIsNone(self.deny("console", "git tag -l"))
        self.assertIn("compose", self.deny("console", "bash -c 'docker compose up -d openrune'"))

    def test_hd_approve_is_the_consoles(self):
        self.assertIn("console alone", self.deny("server-dev", "python3 ~/osrs-harness/hd.py approve x abc"))
        self.assertIsNone(self.deny("console", "python3 ~/osrs-harness/hd.py approve x abc"))
        self.assertIsNone(self.deny("server-dev", "python3 ~/osrs-harness/hd.py handover x --sha abc"))

    def test_denial_is_an_event_through_the_hook(self):
        out = self.hook("guard.py", {"tool_name": "Bash", "tool_input": {"command": "git push upstream main"},
                                     "cwd": self.repo, "agent_type": "server-dev", "agent_id": "a1"})
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(self.events("denial")[0]["role"], "server-dev")
        self.assertIsNone(self.hook("guard.py", {"tool_name": "Bash", "tool_input": {"command": "ls"}, "cwd": self.repo}))


if __name__ == "__main__":
    unittest.main()
