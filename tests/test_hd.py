"""One test class per requirement of docs/PRD.md (R1–R7), on the sandbox and the fake facts of helpers.py."""
import io
import json
import os
import sys
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import SHA, R, Fake, Sandbox  # noqa: E402

from hd import cli, server, steps, tick  # noqa: E402

A, B, C, D = SHA["a"], SHA["b"], SHA["c"], SHA["d"]


def names(ctx):
    return [(ch["slug"], s.name, s.actor(ctx, ch)) for ch, s in steps.next_steps(ctx)]


class R1Goals(Sandbox):
    def test_orchestrator_listed_when_below_target_and_nothing_serves(self):
        self.goal()
        ctx = self.ctx(Fake(refs={"origin/main": A}))
        self.assertEqual([(c["slug"], r) for c, s, r, n in steps.dispatch(ctx)], [("client-api", "orchestrator")])

    def test_measurement_at_target_and_bound_to_the_live_tip(self):
        self.goal()
        self.store.save_record("client-api", "measure", {"value": 100, "base": A, "evidence": "r"})
        self.assertEqual(names(self.ctx(Fake(refs={"origin/main": A}))), [])
        self.assertEqual(names(self.ctx(Fake(refs={"origin/main": B}))), [("client-api", "measure", "orchestrator")])

    def test_a_serving_change_stands_in_for_the_measurement(self):
        self.goal()
        self.change("probe", goal="client-api")
        ctx = self.ctx(Fake(refs={"origin/main": A}))
        self.assertEqual([r for c, s, r, n in steps.dispatch(ctx)], ["client-dev"])

    def test_hd_measure_records_value_and_base(self):
        self.goal()
        rep = self.evidence("client-api", "report.md")
        with mock.patch.object(cli, "Facts", lambda cfg: Fake(refs={"origin/main": A})):
            cli.main(["measure", "client-api", "42", "--evidence", rep])
        self.assertEqual(self.store.record("client-api", "measure")["base"], A)


class R2Flow(Sandbox):
    def test_client_change_defined_to_live_without_a_person(self):
        self.change("c1")
        F = Fake(refs={"origin/client/c1": A, "origin/main": B})
        self.assertEqual([r for c, s, r, n in steps.dispatch(self.ctx(F))], ["client-dev"])
        self.evidence("c1", "repack.log", "logcat.txt")
        self.store.save_record("c1", "handover", {"head": A, "base": B, "evidence": "e"})
        self.assertEqual(names(self.ctx(F)), [("c1", "gate", "script")])
        tick.run(F)
        self.assertTrue(self.store.record("c1", "gate")["ok"])
        self.assertEqual(names(self.ctx(F)), [("c1", "merge", "script")])
        tick.run(F)
        self.assertIn(("git", self.store.config()["paths"]["client"], "merge", "--no-ff", "--no-edit", "-m",
                       mock.ANY, A), [c[:7] + (c[7],) if len(c) > 7 else c for c in F.calls])
        F.f["anc"] = {(B, A)}
        self.assertEqual(names(self.ctx(F)), [])
        F.f["refs"]["origin/main"] = C                                         # main moves on after the merge
        F.f["anc"].add((C, A))
        self.assertEqual(names(self.ctx(F)), [])                               # no re-gate of a merged change

    def test_the_client_gate_ties_the_probe_report_to_the_head(self):
        import importlib.util, subprocess as sp
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        spec = importlib.util.spec_from_file_location("gate_client", os.path.join(root, "gates", "client.py"))
        gate = importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)
        self.evidence("c1", "repack.log", "logcat.txt")
        ev = os.path.join(self.ev, "c1")
        open(os.path.join(ev, "repack.log"), "w").write("telemetry: x\n" * 7)
        open(os.path.join(ev, "api-probe.tsv"), "w").write("# build: v0.1.1-59-gabcdef123456\n")
        for out, ok in (("docs/a.md\n", 0), ("host/X.java\ndocs/a.md\n", 1)):
            with mock.patch.object(gate.subprocess, "run", return_value=R(0, out)), mock.patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(gate.main("c1", "f" * 40, B, ev), ok)

    def test_a_merge_conflict_is_the_devs_step(self):
        self.change("c1")
        self.store.save_record("c1", "handover", {"head": A, "base": B, "evidence": "e"})
        self.store.save_record("c1", "gate", {"head": A, "base": B, "ok": True, "detail": ""})
        F = Fake(refs={"origin/client/c1": A, "origin/main": B})
        self.assertEqual(names(self.ctx(F)), [("c1", "merge", "script")])
        self.store.write({"step": "merge", "head": A, "detail": "merge: conflict: X.java"}, "c1", "step.json")
        self.assertEqual(names(self.ctx(F)), [("c1", "merge", "client-dev")])
        self.assertIn("conflicted", steps.brief(self.ctx(F), self.ctx(F).by_slug["c1"], steps.MERGE, "c1-2"))

    def test_deps_gate_dispatch(self):
        self.change("srv", track="server")
        self.change("cli", deps=["srv"])
        F = Fake(refs={"fork/dev/srv": A, "origin/main": B, "origin/client/cli": ""})
        self.assertEqual([c["slug"] for c, s, r, n in steps.dispatch(self.ctx(F))], ["srv"])
        self.store.write({"integration": C}, "live.json")
        F.f["anc"] = {(C, A)}
        self.assertIn("cli", [c["slug"] for c, s, r, n in steps.dispatch(self.ctx(F))])

    def test_server_change_has_two_lists_and_publishes_one_step_per_pass(self):
        self.change("s", track="server")
        self.evidence("s", "accuracy.md", "pr-title.txt", "pr-body.md", "pr-comment.md")
        self.store.save_record("s", "handover", {"head": A, "base": B, "evidence": "e"})
        self.store.save_record("s", "gate", {"head": A, "base": B, "ok": True, "detail": "green"})
        F = Fake(refs={"fork/dev/s": A, "origin/main": B, "fork/local/integration-tools": D})
        self.assertEqual(steps.stage(self.ctx(F), self.ctx(F).by_slug["s"]), ["queue", "review"])
        self.store.save_record("s", "verdict", {"head": A, "base": B, "pass": True, "findings": []})
        self.assertEqual([s for c, s, a in names(self.ctx(F))], ["queue", "approve"])
        self.store.save_record("s", "approval", {"head": A})
        self.assertIn(("s", "push", "script"), names(self.ctx(F)))
        F.f["anc"] = {(A, A)}
        F.f["refs"]["fork/content/s"] = A
        self.assertIn(("s", "pr", "script"), names(self.ctx(F)))
        F.f["prs"] = {"content/s": {"number": 7, "state": "open", "draft": True, "head": A, "merged": False, "branch": "content/s", "title": "x"}}
        self.assertIn(("s", "ci", "wait"), names(self.ctx(F)))
        F.f["checks"] = {(7, A): "success"}
        F.f["comments"] = {7: [{"id": "m", "author": "maint", "body": "please", "at": "t", "kind": "comment"}]}
        self.assertIn(("s", "comment", "script"), names(self.ctx(F)))
        F.f["comments"][7].append({"id": "x", "author": "alexperrin", "body": "x\n\n" + steps.MARK.format(A[:12]), "at": "t", "kind": "comment"})   # the prepared text
        self.assertIn(("s", "ready", "script"), names(self.ctx(F)))
        F.f["prs"]["content/s"]["draft"] = False
        self.assertIn(("s", "merged", "wait"), names(self.ctx(F)))
        F.f["anc"].add((B, A))
        self.assertEqual(steps.stage(self.ctx(F), self.ctx(F).by_slug["s"])[1], "done")


class R3Integrity(Sandbox):
    def test_a_moved_head_voids_the_handover_and_the_gate(self):
        self.change("c1")
        self.store.save_record("c1", "handover", {"head": A, "base": B, "evidence": "e"})
        self.store.save_record("c1", "gate", {"head": A, "base": B, "ok": True, "detail": ""})
        self.assertEqual(names(self.ctx(Fake(refs={"origin/client/c1": A, "origin/main": B}))), [("c1", "merge", "script")])
        self.assertEqual(names(self.ctx(Fake(refs={"origin/client/c1": C, "origin/main": B}))), [("c1", "handover", "client-dev")])
        self.assertEqual(names(self.ctx(Fake(refs={"origin/client/c1": A, "origin/main": C}))), [("c1", "gate", "script")])

    def test_an_unknown_fact_stops_the_list(self):
        self.change("c1")
        self.assertEqual(names(self.ctx(Fake(refs={"origin/main": B}, unknown={"origin"}))), [])

    def test_handover_refused_without_evidence_or_at_another_commit(self):
        self.change("c1")
        with mock.patch.object(cli, "Facts", lambda cfg: Fake(refs={"origin/client/c1": A, "origin/main": B})):
            with self.assertRaises(SystemExit):
                cli.main(["handover", "c1", A])
            self.evidence("c1", "repack.log")
            with self.assertRaises(SystemExit):
                cli.main(["handover", "c1", C])
            cli.main(["handover", "c1", A])
        self.assertEqual(self.store.record("c1", "handover")["head"], A)

    def test_approve_binds_the_commit(self):
        self.change("s", track="server")
        self.store.save_record("s", "verdict", {"head": A, "base": B, "pass": True, "findings": []})
        with mock.patch.object(cli, "Facts", lambda cfg: Fake(refs={"fork/dev/s": A, "origin/main": B})):
            with self.assertRaises(SystemExit):
                cli.main(["approve", "s", C])
            cli.main(["approve", "s", A])
        self.assertEqual(self.store.record("s", "approval")["head"], A)
        self.assertEqual(names(self.ctx(Fake(refs={"fork/dev/s": C, "origin/main": B}))), [("s", "handover", "server-dev")])


class R4Authority(Sandbox):
    def guard(self, cmd, role="server-dev", slug="s"):
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks"))
        import hook
        url = {"fork": "git@github.com:AlexPerrin/OpenRune-Server.git", "origin": "https://github.com/OpenRune/OpenRune-Server.git"}
        run = lambda args, **k: type("R", (), {"returncode": 0, "stdout": url.get(args[-1], "") + "\n", "stderr": ""})()
        return hook.Guard(self.store.config(), role, slug, run=run).decide(cmd, self.tmp)

    def test_upstream_is_deny_by_default(self):
        self.assertIsNotNone(self.guard("gh pr comment 5 -R OpenRune/OpenRune-Server -b hi"))
        self.assertIsNotNone(self.guard("gh pr comment 5 -R OpenRune/OpenRune-Server -b hi", role="console"))
        self.assertIsNotNone(self.guard("gh api -X POST repos/OpenRune/OpenRune-Server/pulls/5/comments", role="console"))
        self.assertIsNone(self.guard("gh pr view 5 -R OpenRune/OpenRune-Server --json title"))
        self.assertIsNone(self.guard("gh api repos/OpenRune/OpenRune-Server/pulls/5"))
        self.assertIsNone(self.guard("git fetch https://github.com/OpenRune/OpenRune-Server.git main"))
        self.assertIsNotNone(self.guard("git push https://github.com/OpenRune/OpenRune-Server.git HEAD:main", role="console"))

    def test_fork_pushes_follow_the_role_table(self):
        self.assertIsNone(self.guard("git -C /x push fork HEAD:refs/heads/dev/s"))
        self.assertIsNotNone(self.guard("git -C /x push fork HEAD:refs/heads/content/s"))
        self.assertIsNotNone(self.guard("git -C /x push --force fork HEAD:refs/heads/dev/s"))
        self.assertIsNone(self.guard("git -C /x push fork HEAD:refs/heads/content/s", role="console"))
        self.assertIsNone(self.guard("git -C /x push fork --delete dev/s", role="console"))
        self.assertIsNone(self.guard("git -C /x remote set-url origin https://github.com/OpenRune/OpenRune-Server.git"))
        self.assertIsNotNone(self.guard("git push"))
        self.assertIsNotNone(self.guard("x=$(git -C /x push fork HEAD:dev/s)"))

    def test_releases_tags_scripts_and_approve_are_the_passs(self):
        self.assertIsNotNone(self.guard("gh release create v1 -R AlexPerrin/osrs-plugins-reverse", role="console"))
        self.assertIsNotNone(self.guard("git tag v1", role="console"))
        self.assertIsNotNone(self.guard("bash ~/osrs-harness/train/train.sh", role="console"))
        self.assertIsNotNone(self.guard("python3 ~/osrs-harness/hd.py approve s " + A))
        self.assertIsNone(self.guard("python3 ~/osrs-harness/hd.py approve s " + A, role="console"))
        self.assertIsNotNone(self.guard("docker compose --env-file switch.env up -d openrune", role="console"))

    def test_publish_runs_only_at_the_approved_head(self):
        self.change("s", track="server")
        self.store.save_record("s", "verdict", {"head": A, "base": B, "pass": True, "findings": []})
        self.store.save_record("s", "approval", {"head": C})
        F = Fake(refs={"fork/dev/s": A, "origin/main": B})
        self.store.save_record("s", "handover", {"head": A, "base": B, "evidence": "e"})
        self.store.save_record("s", "gate", {"head": A, "base": B, "ok": True, "detail": ""})
        self.assertIn(("s", "approve", "user"), names(self.ctx(F)))


class R5Recovery(Sandbox):
    def test_dead_console_ends_its_runs(self):
        self.store.save_run({"name": "r1", "agent_id": "x", "role": "client-dev", "change": "c1", "console_pid": 5, "console_start": "9", "ended": None})
        with mock.patch.object(tick, "sh"):
            tick.repairs(self.ctx(Fake(procs={(5, "9")})))
            self.assertIsNone(self.store.run("r1")["ended"])
            tick.repairs(self.ctx(Fake()))
        self.assertTrue(self.store.run("r1")["ended"])

    def test_dead_train_is_rerun_not_handed_to_the_integrator(self):
        self.change("s", track="server")
        self.store.save_record("s", "handover", {"head": A, "base": B, "evidence": "e"})
        self.store.save_record("s", "gate", {"head": A, "base": B, "ok": True, "detail": ""})
        self.store.write({"pid": "7", "start": "1", "step": "gate", "tools": D}, "train.json")
        F = Fake(refs={"fork/dev/s": A, "origin/main": B, "fork/local/integration-tools": D})
        with mock.patch.object(tick, "sh"):
            tick.repairs(self.ctx(F))
        self.assertTrue(steps.train_state()["ended"])
        self.assertEqual(steps.QUEUE.actor(self.ctx(F), self.ctx(F).by_slug["s"]), "script")
        self.store.write({"pid": "7", "start": "1", "step": "gate", "tools": D, "failed_step": "rebuild", "ended": "t"}, "train.json")
        self.assertEqual(steps.QUEUE.actor(self.ctx(F), self.ctx(F).by_slug["s"]), "integrator")
        F.f["refs"]["fork/local/integration-tools"] = C
        F.f["log"] = "integration: pin dev/t at bbbbbbbbb\n"
        self.assertEqual(steps.QUEUE.actor(self.ctx(F), self.ctx(F).by_slug["s"]), "integrator")   # a pin resolves nothing
        F.f["log"] = "integration: rr-cache for fix/22\n"
        self.assertEqual(steps.QUEUE.actor(self.ctx(F), self.ctx(F).by_slug["s"]), "script")

    def test_an_unbound_agent_is_bound_at_its_first_command(self):
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks"))
        import hook
        t = os.path.join(self.tmp, "agent-x.jsonl")
        with open(t, "w") as f:
            f.write(json.dumps({"type": "user", "message": {"role": "user", "content": f"Harness change `s` run `s-1` head `{A}` def `d`\n"}}) + "\n")
        data = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "agent_type": "server-dev", "agent_id": "x",
                "agent_transcript_path": t, "tool_input": {"command": "git status"}}
        with mock.patch("sys.stdout", new_callable=io.StringIO):
            hook.guard(data)
        self.assertEqual([(r["name"], r["agent_id"], r["change"]) for r in self.store.runs()], [("s-1", "x", "s")])

    def test_one_failed_train_is_one_integrator(self):
        F = Fake(refs={"fork/dev/s": A, "fork/dev/t": A, "origin/main": B, "fork/local/integration-tools": D})
        for s in ("s", "t"):
            self.change(s, track="server")
            self.store.save_record(s, "handover", {"head": A, "base": B, "evidence": "e"})
            self.store.save_record(s, "gate", {"head": A, "base": B, "ok": True, "detail": ""})
        self.store.write({"pid": "7", "start": "1", "step": "rebuild", "tools": D, "failed_step": "rebuild", "ended": "t"}, "train.json")
        self.assertEqual([(c["slug"], r) for c, s, r, n in steps.dispatch(self.ctx(F))], [("s", "integrator"), ("t", "server-qa")])   # one run per change
        self.store.save_run({"name": "s-9", "agent_id": "i", "role": "integrator", "change": "s", "head": D, "ended": None, "console_pid": os.getpid(), "console_start": "0"})
        F.f["procs"] = {(os.getpid(), "0")}
        F.f["refs"]["fork/local/integration-tools"] = C                                        # the integrator moved the tools branch
        with mock.patch.object(server, "start_train") as start, mock.patch.object(server, "pin", return_value="pinned"):
            self.assertIn("waiting for the integrator", steps.QUEUE.do(self.ctx(F), self.ctx(F).by_slug["s"]))
        self.assertFalse(start.called)                                                        # no train while the integrator works in its worktree

    def test_orphans_removed_and_docker_down_is_one_alert(self):
        self.store.save_run({"name": "r1", "agent_id": "x", "role": "server-dev", "change": "s", "ended": "t"})
        os.makedirs(os.path.join(self.tmp, "work", "agents", "r1"))
        F = Fake(containers=[{"name": "qa-dev-r1", "status": "running"}, {"name": "hd-boot-abc", "status": "exited"},
                             {"name": "osrs-openrune", "status": "running"}], docker_ok=False)
        with mock.patch.object(tick, "sh") as sh:
            out = tick.repairs(self.ctx(F))
        self.assertEqual(sorted(c.args[0][3] for c in sh.call_args_list), ["hd-boot-abc", "qa-dev-r1"])
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "work", "agents", "r1")))
        self.assertEqual(len(out), 3)
        self.assertEqual(len(tick.alerts(self.ctx(F))), 1)
        self.store.write({"integration": A, "image": "osrs-openrune:integration-aaaaaaa", "rollback": "osrs-openrune:rollback-x"}, "live.json")
        F.f["images"] = ["osrs-openrune:integration-aaaaaaa", "osrs-openrune:integration-bbbbbbb"]
        self.store.write({"pid": "7", "start": "1", "step": "image"}, "train.json")
        F.f["procs"] = {("7", "1")}
        with mock.patch.object(tick, "sh") as sh:
            tick.repairs(self.ctx(F))
        self.assertNotIn("rmi", [c.args[0][1] for c in sh.call_args_list])             # the train may be deploying it
        F.f["procs"] = set()
        with mock.patch.object(tick, "sh") as sh:
            tick.repairs(self.ctx(F))
        self.assertIn(["docker", "rmi", "osrs-openrune:integration-bbbbbbb"], [c.args[0] for c in sh.call_args_list])

    def test_a_stop_without_a_hand_back_is_a_pause(self):
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks"))
        import hook
        self.store.save_run({"name": "s-1", "agent_id": "x", "role": "server-dev", "change": "s", "started": "t", "ended": None})
        t = os.path.join(self.tmp, "agent-x.jsonl")
        turn = lambda blocks: json.dumps({"type": "assistant", "message": {"content": blocks, "usage": {"output_tokens": 1}}}) + "\n"
        open(t, "w").write(turn([{"type": "text", "text": "waiting on the build"}]))
        data = {"hook_event_name": "SubagentStop", "agent_type": "server-dev", "agent_id": "x", "agent_transcript_path": t}
        with mock.patch.object(hook.subprocess, "run") as tick_run:
            hook.stop(data)
            self.assertIsNone(self.store.run("s-1")["ended"])                       # paused, clone and container kept
            self.assertFalse(tick_run.called)
            open(t, "a").write(turn([{"type": "tool_use", "name": "SubagentHandback", "input": {}}]))
            hook.stop(data)
        self.assertTrue(self.store.run("s-1")["ended"])
        self.assertTrue(tick_run.called)
        self.store.save_run({"name": "s-2", "agent_id": "y", "role": "server-dev", "change": "s", "started": "t", "ended": None,
                             "transcript": t, "console_pid": os.getpid(), "console_start": "0"})
        F = Fake(procs={(os.getpid(), "0")})
        with mock.patch.object(tick, "sh"):
            self.assertIn("run s-2: handed back; ended", tick.repairs(self.ctx(F)))    # the stop hook ran before the flush
        self.assertTrue(self.store.run("s-2")["ended"])

    def test_one_changes_fault_stops_that_change_only(self):
        self.change("c1")
        self.change("bad", track="nope")
        F = Fake(refs={"origin/client/c1": A, "origin/main": B})
        self.assertEqual([c["slug"] for c, s in steps.next_steps(self.ctx(F))], ["c1"])
        self.assertIn('"kind": "error"', open(self.store.path("events.jsonl")).read())


class R6Economy(Sandbox):
    def test_no_agent_loops_on_the_same_input(self):
        self.change("c1")
        F = Fake(refs={"origin/client/c1": A, "origin/main": B})
        ctx = self.ctx(F)
        h = ctx.by_slug["c1"]["hash"]
        self.store.save_run({"name": "c1-1", "agent_id": "x", "role": "client-dev", "change": "c1", "head": A, "def_hash": h,
                             "step": "handover", "ended": "t", "last": "gave up"})
        self.assertEqual(steps.dispatch(self.ctx(F)), [])
        self.assertIn("gave up", steps.questions(self.ctx(F))[0][1])
        cli.main(["answer", "c1", "try the other way"])
        self.assertEqual([n for c, s, r, n in steps.dispatch(self.ctx(F))], ["c1-2"])
        self.evidence("c1", "x")
        self.store.save_record("c1", "handover", {"head": A, "base": B, "evidence": "e"})
        self.store.save_run({"name": "c1-2", "agent_id": "y", "role": "client-dev", "change": "c1", "head": A,
                             "def_hash": self.ctx(F).by_slug["c1"]["hash"], "step": "handover", "ended": "t", "record": True})
        self.store.save_record("c1", "gate", {"head": A, "base": B, "ok": False, "detail": "FAIL"})
        self.assertEqual([(s.name, n) for c, s, r, n in steps.dispatch(self.ctx(F))], [("gate", "c1-3")])   # a gate fix at A is new work
        self.assertIn("step `gate`", steps.brief(self.ctx(F), self.ctx(F).by_slug["c1"], steps.GATE, "c1-3").splitlines()[0])

    def test_agent_count_and_busy_changes(self):
        for i in range(5):
            self.change(f"c{i}", priority="P1" if i == 3 else "P2")
        self.store.save_run({"name": "c0-1", "agent_id": "x", "role": "client-dev", "change": "c0", "console_pid": 1, "console_start": "1", "ended": None})
        F = Fake(refs={"origin/main": B}, procs={(1, "1")})
        d = steps.dispatch(self.ctx(F))
        self.assertEqual([c["slug"] for c, s, r, n in d], ["c3", "c1"])

    def test_gate_not_run_twice_and_script_before_agent_before_user(self):
        self.change("s", track="server")
        self.store.save_record("s", "handover", {"head": A, "base": B, "evidence": "e"})
        self.store.save_record("s", "gate", {"head": A, "base": B, "ok": False, "detail": "FAIL x"})
        F = Fake(refs={"fork/dev/s": A, "origin/main": B})
        self.assertEqual(names(self.ctx(F)), [("s", "gate", "server-dev")])
        self.assertIn("gate failed", steps.brief(self.ctx(F), self.ctx(F).by_slug["s"], steps.GATE, "s-1").lower())
        self.store.save_record("s", "gate", {"head": A, "base": B, "ok": True, "detail": ""})
        self.store.save_record("s", "verdict", {"head": A, "base": B, "pass": False, "findings": ["x"]})
        b = steps.brief(self.ctx(F), self.ctx(F).by_slug["s"], steps.REVIEW, "s-2")
        self.assertIn("review failed", b.lower())
        self.assertIn("hd handover s <sha>", b)                                      # the dev owes a commit, not a verdict


class R7Visibility(Sandbox):
    def test_hd_lists_only_the_sections(self):
        self.goal()
        self.change("c1")
        with mock.patch.object(cli, "Facts", lambda cfg: Fake(refs={"origin/main": A})), mock.patch("sys.stdout") as out:
            cli.main(["--json"])
        d = json.loads("".join(c.args[0] for c in out.write.call_args_list))
        self.assertEqual(sorted(d), ["alerts", "cards", "changes", "goals", "questions", "running", "spawn"])
        self.assertEqual(sorted(s["name"] for s in d["spawn"]), ["c1-1", "client-api-1"])
        c1 = next(s for s in d["spawn"] if s["name"] == "c1-1")
        with open(c1["brief"]) as f:
            self.assertRegex(f.read().splitlines()[0], r"^Harness change `c1` run `c1-1` head `` def `\w{12}` step `handover`$")

    def test_a_pending_gate_is_recorded_once(self):
        self.change("s", track="server")
        self.store.save_record("s", "handover", {"head": A, "base": B, "evidence": "e"})
        F = Fake(refs={"fork/dev/s": A, "origin/main": B})
        with mock.patch.object(steps, "sh", return_value=R(2, "CI: running")):
            tick.run(F)
            tick.run(F)
        events = [json.loads(l) for l in open(self.store.path("events.jsonl"))]
        self.assertEqual(len([e for e in events if e["kind"] == "record" and e["record"] == "gate"]), 1)
        self.assertIsNone(self.store.record("s", "gate")["ok"])


class ServerTrack(Sandbox):
    def test_a_pr_is_a_draft_while_a_finding_on_it_is_unanswered(self):
        self.change("s", track="server")
        for k, d in (("handover", {"evidence": "e"}), ("gate", {"ok": True, "detail": ""}), ("verdict", {"pass": True, "findings": []})):
            self.store.save_record("s", k, {"head": A, "base": B, **d})
        self.store.save_record("s", "approval", {"head": A})
        F = Fake(refs={"fork/dev/s": A, "fork/dev/s-f1": C, "origin/main": B, "fork/content/s": A, "fork/local/integration-tools": D}, anc={(A, A)},
                 prs={"content/s": {"number": 7, "state": "open", "draft": False, "head": A, "merged": False, "branch": "content/s", "title": "x"}},
                 checks={(7, A): "success"}, comments={7: [{"id": "m", "author": "maint", "body": "x", "at": "t", "kind": "comment"},
                                                          {"id": "o", "author": "alexperrin", "body": f"Pushed `{A[:9]}`", "at": "t", "kind": "comment"}]})
        self.assertIn(("s", "merged", "wait"), names(self.ctx(F)))
        self.change("s-f1", track="server", finding="IC_1", pr=7, branch="content/s")
        self.assertIn(("s", "ready", "script"), names(self.ctx(F)))                       # planned work: back to draft
        with mock.patch.object(steps, "sh", return_value=R(0)) as sh:
            self.assertIn("drafted", steps.READY.do(self.ctx(F), self.ctx(F).by_slug["s"]))
        self.assertIn("--undo", sh.call_args[0][0])
        F.f["prs"]["content/s"]["draft"] = True
        self.assertIn(("s", "merged", "wait"), names(self.ctx(F)))
        self.store.save_record("s-f1", "handover", {"head": C, "base": B, "evidence": "e"})
        F.f["anc"].add((A, C))
        F.f["comments"][7].append({"id": "p", "author": "alexperrin", "body": f"Pushed `{C[:9]}`", "at": "t", "kind": "comment"})
        self.assertIn(("s", "ready", "script"), names(self.ctx(F)))                       # answered: out of draft again

    def test_a_pr_moved_past_the_head_and_a_dead_console(self):
        self.change("s", track="server")
        F = Fake(refs={"fork/dev/s": A, "origin/main": B}, anc={(C, A)},
                 prs={"content/s": {"number": 7, "state": "open", "draft": False, "head": C, "merged": False, "branch": "content/s", "title": "x"}})
        self.assertEqual(steps._ci_state(self.ctx(F), self.ctx(F).by_slug["s"]), "success")
        h = self.ctx(F).by_slug["s"]["hash"]
        self.store.save_run({"name": "s-1", "agent_id": "x", "role": "server-dev", "change": "s", "head": A, "def_hash": h,
                             "step": "handover", "ended": "t", "last": "console died", "reason": "console-died"})
        self.assertIsNone(steps._repeat(self.ctx(F), self.ctx(F).by_slug["s"], steps.HANDOVER, "server-dev"))

    def test_a_pr_is_ready_only_when_complete(self):
        self.change("s", track="server")
        for k, d in (("handover", {"evidence": "e"}), ("gate", {"ok": True, "detail": ""})):
            self.store.save_record("s", k, {"head": A, "base": B, **d})
        self.store.save_record("s", "verdict", {"head": A, "base": B, "pass": False, "findings": ["incomplete"]})
        F = Fake(refs={"fork/dev/s": A, "origin/main": B, "fork/content/s": A}, anc={(A, A)},
                 prs={"content/s": {"number": 7, "state": "open", "draft": False, "head": A, "merged": False, "branch": "content/s", "title": "x"}})
        with mock.patch.object(steps, "sh", return_value=R(0)) as sh, mock.patch.object(server, "pin", return_value="pinned"), \
                mock.patch.object(server, "start_train", return_value="started"):
            out = tick.run(F)
        self.assertTrue(any("s ready: drafted" in l for l in out))                 # review failed after ready: back to draft
        self.assertIn("--undo", sh.call_args[0][0])
        self.evidence("s", "pr-comment.md")
        with open(os.path.join(self.ev, "s", "pr-comment.md"), "w") as f:
            f.write("x\n## Checklist\n- [x] Builds\n- [ ] Matches the OSRS wiki\n\nNot done: pets\n")
        self.assertEqual(steps._incomplete(self.ctx(F).by_slug["s"]), ["unticked: Matches the OSRS wiki", "a Not done list"])
        self.store.save_record("s", "verdict", {"head": A, "base": B, "pass": True, "findings": []})
        self.store.save_record("s", "approval", {"head": A})
        F.f["checks"] = {(7, A): "success"}
        F.f["comments"] = {7: [{"id": "o", "author": "alexperrin", "body": "x\n## Checklist\n- [x] Builds\n- [ ] Matches the OSRS wiki\n\nNot done: pets\n" + steps.MARK.format(A[:12]), "at": "t", "kind": "comment"}]}
        self.assertIn(("s", "ready", "server-dev"), names(self.ctx(F)))      # ready PR, incomplete text: the dev's step, no draft
        self.assertFalse(steps._blocked(self.ctx(F), self.ctx(F).by_slug["s"]))

    def test_title_and_comment_follow_the_prepared_texts(self):
        self.change("s", track="server")
        self.evidence("s", "pr-title.txt", "pr-comment.md")
        for name, text in (("pr-title.txt", "feat: X"), ("pr-comment.md", "progress update")):
            with open(os.path.join(self.ev, "s", name), "w") as f:
                f.write(text)
        F = Fake(refs={"fork/dev/s": A}, prs={"content/s": {"number": 7, "state": "open", "draft": True, "head": A, "title": "old"}},
                 comments={7: [{"id": "IC_1", "author": "alexperrin", "body": "final update\n\n" + steps.MARK.format(A[:12]), "at": "t", "kind": "comment"}]})
        ch = self.ctx(F).by_slug["s"]
        self.assertFalse(steps._title_done(self.ctx(F), ch))
        self.assertFalse(steps._comment_done(self.ctx(F), ch))                    # names the head but says something else
        with mock.patch.object(steps, "sh", return_value=R(0)) as run:
            self.assertEqual(steps.COMMENT.do(self.ctx(F), ch), "comment edited")
            self.assertIn("id=IC_1", run.call_args[0][0])
            self.assertEqual(steps.TITLE.do(self.ctx(F), ch), "title set")
            self.assertIn("title=feat: X", run.call_args[0][0])
        F.f["prs"]["content/s"]["title"] = "feat: X"
        F.f["comments"][7][0]["body"] = "progress update\r\n\r\n" + steps.MARK.format(A[:12])
        self.assertTrue(steps._title_done(self.ctx(F), ch) and steps._comment_done(self.ctx(F), ch))

    def test_a_squash_merged_pr_is_done(self):
        self.change("s", track="server")
        F = Fake(refs={"fork/dev/s": A, "origin/main": B},
                 prs={"content/s": {"number": 7, "state": "merged", "draft": False, "head": A, "merged": True, "branch": "content/s"}})
        self.assertTrue(steps.done(self.ctx(F), self.ctx(F).by_slug["s"]))

    def test_pr_texts_are_the_publish_steps_concern(self):
        self.change("s", track="server")
        for k, d in (("handover", {"evidence": "e"}), ("gate", {"ok": True, "detail": ""}), ("verdict", {"pass": True, "findings": []})):
            self.store.save_record("s", k, {"head": A, "base": B, **d})
        self.store.save_record("s", "approval", {"head": A})
        F = Fake(refs={"fork/dev/s": A, "origin/main": B, "fork/content/s": A, "fork/local/integration-tools": D}, anc={(A, A)})
        self.assertIn(("s", "pr", "server-dev"), names(self.ctx(F)))          # no pr-title.txt or pr-body.md: the dev's step
        self.evidence("s", "pr-title.txt", "pr-body.md")
        self.assertIn(("s", "pr", "script"), names(self.ctx(F)))
        F.f["prs"] = {"content/s": {"number": 7, "state": "open", "draft": True, "head": A, "merged": False, "branch": "content/s", "title": "x"}}
        F.f["checks"] = {(7, A): "success"}
        self.assertIn(("s", "comment", "server-dev"), names(self.ctx(F)))    # no comment yet and none prepared: the dev writes it
        self.evidence("s", "pr-comment.md")
        self.assertIn(("s", "comment", "script"), names(self.ctx(F)))        # every PR gets a comment before ready
        F.f["comments"] = {7: [{"id": "m", "author": "maint", "body": "x", "at": "t", "kind": "comment"}]}
        F.f["comments"][7].append({"id": "o", "author": "alexperrin", "body": f"Pushed `{A[:9]}`", "at": "t", "kind": "comment"})
        self.assertIn(("s", "comment", "script"), names(self.ctx(F)))        # names the commit, but not the prepared text: edited
        F.f["comments"][7][-1]["body"] = "x\n" + steps.MARK.format(A[:12])
        self.assertIn(("s", "ready", "script"), names(self.ctx(F)))          # our comment names the commit and says the text
        F.f["comments"] = {7: [{"id": "b", "author": "github-actions", "bot": True, "body": "x", "at": "t", "kind": "comment"},
                              {"id": "g", "author": None, "body": "x", "at": "t", "kind": "comment"}]}
        self.assertIn(("s", "comment", "script"), names(self.ctx(F)))        # a bot's or a deleted account's comment is not ours
        F.f["refs"]["fork/dev/s"] = ""
        self.assertFalse(steps._comment_done(self.ctx(F), self.ctx(F).by_slug["s"]))   # no head: nothing can name it

    def test_the_gate_script_dispatches_ci_on_a_fresh_scratch_merge(self):
        import importlib.util
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        spec = importlib.util.spec_from_file_location("gate_server", os.path.join(root, "gates", "server.py"))
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        self.evidence("s", "accuracy.md")
        fake_git = lambda path, *a: R(0, "c" * 40 if a[0] == "rev-parse" else "")
        with mock.patch.object(gate, "scratch_clone", return_value="/x"), mock.patch.object(gate, "git", fake_git), \
                mock.patch.object(gate, "sh", lambda *a, **k: R(0)), \
                mock.patch.object(gate.Facts, "fork_ci", lambda self, b, s, w: "none"), \
                mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            self.assertEqual(gate.main("s", A, B, os.path.join(self.ev, "s")), 2)
        self.assertIn("dispatched", out.getvalue())
        self.change("p", track="server", branch="content/p")
        self.evidence("p", "accuracy.md")
        pr = {"number": 9, "state": "open", "draft": True, "head": A, "merged": False, "branch": "content/p", "mergeable": "MERGEABLE"}
        with mock.patch.object(gate.Facts, "pr", lambda self, b: pr), mock.patch.object(gate.Facts, "pr_checks", lambda self, n, s: "success"), \
                mock.patch.object(gate, "scratch_clone", side_effect=AssertionError("no scratch merge for a PR")), \
                mock.patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(gate.main("p", A, B, os.path.join(self.ev, "p")), 0)
            pr["mergeable"] = "CONFLICTING"
            self.assertEqual(gate.main("p", A, B, os.path.join(self.ev, "p")), 1)

    def test_list_and_pins(self):
        text = "# Upstream fixes\nfix/a\n# Content\ncontent/b\n# Local only\nlocal/c\n"
        self.assertEqual(server.listed(text, "dev/x", "# Content"), "# Upstream fixes\nfix/a\n# Content\ncontent/b\ndev/x\n# Local only\nlocal/c\n")
        self.assertEqual(server.listed(text, "fix/a", "# Upstream fixes"), text)
        self.assertEqual(server.pinned("fix/a 111\n", "fix/a", "222"), "fix/a 222\n")
        self.assertEqual(server.pinned("fix/a 111\n", "dev/x", "333"), "fix/a 111\ndev/x 333\n")

    def test_a_maintainer_finding_is_filed_once_as_a_p0_change(self):
        self.change("s", track="server")
        for k, d in (("handover", {"evidence": "e"}), ("gate", {"ok": True, "detail": ""}), ("verdict", {"pass": True, "findings": []})):
            self.store.save_record("s", k, {"head": A, "base": B, **d})
        self.store.save_record("s", "approval", {"head": A, "ts": "2026-10-25T10:00:00Z"})
        F = Fake(refs={"fork/dev/s": A, "origin/main": B, "fork/content/s": A},
                 prs={"content/s": {"number": 7, "state": "open", "draft": False, "head": A, "merged": False, "branch": "content/s", "title": "x"}},
                 checks={(7, A): "success"},
                 comments={7: [{"id": "IC_1", "author": "maint", "body": "please fix", "at": "2026-10-25T11:00:00Z", "kind": "comment"},
                               {"id": "IC_0", "author": "maint", "body": "old", "at": "2026-10-25T09:00:00Z", "kind": "comment"},
                               {"id": "IC_2", "author": "alexperrin", "body": steps.MARK.format(A[:12]), "at": "2026-10-25T10:30:00Z", "kind": "comment"}]})
        filed = server.findings(self.ctx(F))
        self.assertEqual(filed, ["s-fic1"])
        new = self.ctx(F).by_slug["s-fic1"]
        self.assertEqual((new["priority"], new["pr"], new["branch"], new["finding"]), ("P0", 7, "content/s", "IC_1"))
        self.assertEqual(server.findings(self.ctx(F)), [])
        F.f["comments"][7] += [{"id": "IC_3", "author": "maint", "body": "more", "at": "2026-10-25T12:00:00Z", "kind": "comment"},
                               {"id": "IC_4", "author": "alexperrin", "body": "done", "at": "2026-10-25T12:30:00Z", "kind": "comment"}]
        self.assertEqual(server.findings(self.ctx(F)), [])                   # answered by our later comment
