"""hd: the harness v4 command line (python3 ~/osrs-harness/hd.py <command>).

Changes
  new --track t --slug s --title "..." [--prio P2] [--dod "item"]... [--deps a,b] [--branch b] [--spec n] [--network]
      [--local-only] [--backlog] [--text "..."] [--server-dod]
  list [--track t] [--stage s] [--all]      show <slug>      log <slug> "msg"      lint
  handover <slug> --branch b --commit sha [--evidence dir] [--summary "..."] [--repo dir]
                                          the dev's hand-over: runs the check now and refuses an incomplete one
  block <slug> --by <other> ["why"]       a dep edge: the change waits for <other> (BR-C4); no hold
  fail <slug> "why"                       an agent that cannot finish: a decision hold
  gate <slug> PASS|FAIL ["note"]          the track's verifier record (server: QA's aggregate, checked against the commit)
  hold <slug> decision|failed|exception "reason"   an operator's hold (never a stage: BR-S2);  unhold <slug>
  resolve <batch> "note" [--decision]     the integrator recorded a resolution and the train resumes; --decision: nothing
                                          recorded, the user decides (no resume)
  check <slug>                            run the hand-over check now and print it
  brief <slug> [--stage dev|gate]         the spawn brief      dispatch <slug>   book a run now (the console spawns it)
  note "text" [--kind user|upstream|...]  a note event (the console records the user's messages as kind user)
  agents [--all]                          agent runs: role, change, stage, tokens so far, linked or not
  run-link <name> <agent-id>              the console: the Agent-tool id of a spawned run
  run-end <name> [--exit ok] [--turns n] [--tokens n] [--minutes m]   the console: the run ended
  run-stopped <name>                      the console: the stopped run's agent was TaskStopped
Track commands (hd/tracks, each track registers its own; server: gate-ci, contribute)
  gate-ci <slug> [--no-wait]              the server gate's build evidence (scratch merge + fork CI)
  contribute <slug> --approved <sha> [--no-wait]   the atomic upstream sequence after the user's yes (resumable)
Console
  drive [--json]                          the console's work list: spawns, stops, user OKs, decisions, exceptions
  actions [--json]                        upstream actions and releases that need the user's OK (observed, never recorded)
Daemon
  status [--json]   tick [--dry-run]   run [--interval 60] [--once]   start [--interval]   stop   (the tick loop)
  daemon-status     digest
Shared-resource locks (integration, live-server, ghidra)
  lease take <res> <who> "what" [--pid n] [--container c]   lease release <res> <who>   lease reclaim <res> "why"
  lease status [<res>]   lease holds <res> <who>
Batches, events
  batches   train [--now]   resume <batch>
  release-request <tag>   events [--kind k] [--change s] [--limit n]   kpi
"""
import argparse
import json
import os
import subprocess
import sys

from . import ROOT, capacity, events, leases, policy, store, tracks
from .util import iso, local, slug_ok

T = "    "


def _load(slug):
    if not store.exists(slug):
        sys.exit(f"hd: no change {slug}")
    return store.load(slug)


def cmd_new(a):
    dod = list(a.dod or [])
    spec = a.spec
    if a.server_dod:
        if a.track != "server":
            sys.exit("hd: --server-dod is for --track server")
        spec = spec or (a.branch.split("/", 1)[-1] if a.branch else a.slug)
        dod = tracks.get("server").default_dod(spec) + dod
    branch = a.branch
    if not branch and a.track == "client":
        branch = f"client/{a.slug}"
    try:
        ch = store.new(a.slug, a.track, a.title, prio=a.prio, deps=[d for d in (a.deps or "").split(",") if d],
                       dod=dod, text=a.text or "", branch=branch, stage="backlog" if a.backlog or not dod else "ready",
                       network=a.network, spec=spec, local_only=a.local_only or str(branch or "").startswith("local/"))
    except (ValueError, FileExistsError) as e:
        sys.exit(f"hd: {e}")
    events.emit("stage", change=ch["slug"], **{"from": None, "to": ch.stage}, why="created")
    print(ch["slug"])


def fmt(ch, waiting=None):
    hold = f" [{ch.hold}: {ch.hold_reason[:50]}]" if ch.hold else ""
    own = f" @{ch['owner']}" if ch.get("owner") else ""
    w = f"  waits: {waiting}" if waiting else ""
    return f"{ch.get('prio') or '--':3} {ch['track']:8} {ch.stage:10} {ch['slug']:40}{own}{hold}{w}  {ch.get('title', '')[:60]}"


def cmd_list(a):
    waiting = (store.rec_load("view", "waiting") or {}).get("waiting", {})
    from .stages import terminal
    for ch in store.all_changes():
        if a.track and ch["track"] != a.track:
            continue
        if a.stage and ch.stage != a.stage:
            continue
        if not a.all and not a.stage and ch.stage == terminal(ch):
            continue
        print(fmt(ch, waiting.get(ch["slug"])))


def cmd_show(a):
    with open(store.path(a.slug)) as f:
        print(f.read(), end="")


def cmd_log(a):
    ch = _load(a.slug)
    store.add_log(ch, a.message)
    store.save(ch)


def cmd_dod(a):
    """Tick definition-of-done items on the store's copy of the change (agents cannot edit change files)."""
    ch = _load(a.slug)
    try:
        texts = ch.tick_dod(a.numbers)
    except ValueError as e:
        sys.exit(f"hd: {e}")
    nums = sorted(set(a.numbers))
    store.add_log(ch, "dod ticked: " + ", ".join(map(str, nums)))
    store.save(ch)
    events.emit("dod", change=a.slug, items=nums)
    for n, t in zip(nums, texts):
        print(f"{a.slug}: [x] {n} {t[:90]}")


def cmd_note(a):
    events.emit("note", text=a.text, note_kind=a.kind)
    print("noted")


def cmd_handover(a):
    """Record a hand-over only when its check passes: the items it prints are the dev's to fix in the same run."""
    from . import check
    ch = _load(a.slug)
    repo = a.repo or tracks.of(ch).default_repo()
    r = subprocess.run(["git", "-C", repo, "rev-parse", "--verify", "-q", a.commit + "^{commit}"], capture_output=True, text=True)
    sha = r.stdout.strip()
    if not sha:
        sys.exit(f"hd: commit {a.commit} not found in {repo} (use --repo <clone>)")
    trial = store.Change(dict(ch), ch.body)
    trial.update(branch=a.branch, commit=sha)
    if a.evidence:
        trial["evidence"] = a.evidence
    if tracks.of(ch).records_repo and a.repo:
        trial["repo"] = os.path.realpath(a.repo)
    passed, items = check.run(trial, _obs())
    events.emit("check", change=ch["slug"], result="PASS" if passed else "FAIL", items=[t for ok, t in items if not ok])
    if not passed:
        sys.exit("hd: hand-over refused, nothing recorded; fix these and run it again\n" + check.render(trial, items))
    ch.update({k: trial[k] for k in ("branch", "commit", "evidence", "repo") if k in trial})
    if a.summary:
        ch["summary"] = a.summary
    before = ch.stage
    store.set_stage(ch, "gate", "hand-over recorded")
    if ch.hold == "failed":
        store.clear_hold(ch, "handed over (BR-S3)")   # a decision hold is not the dev's to clear
    store.add_log(ch, f"handover {a.branch}@{sha[:9]}: {a.summary or ''}")
    store.save(ch)
    events.emit("handover", change=ch["slug"], branch=a.branch, commit=sha, owner=ch.get("owner"))
    events.emit("stage", change=ch["slug"], **{"from": before, "to": "gate"}, commit=sha, why="hand-over")
    print(f"{ch['slug']}: handed over at {sha[:9]}; the {'gate' if ch['track'] == 'server' else 'merge'} follows")


def cmd_block(a):
    ch = _load(a.slug)
    if a.by not in ch["deps"]:
        ch["deps"].append(a.by)
    store.add_log(ch, f"blocked by {a.by}" + (f": {a.why}" if a.why else ""))
    ch["owner"], ch["booked"] = None, None
    if ch.stage == "dev":
        store.set_stage(ch, "ready", f"blocked by {a.by}")
    store.save(ch)
    events.emit("block", change=ch["slug"], by=a.by, reason=a.why)
    if not store.exists(a.by):
        print(f"hd: note: {a.by} does not exist yet; create it with `hd new --track server --slug {a.by} ...`", file=sys.stderr)
    print(f"{ch['slug']}: blocked by {a.by}")


def cmd_fail(a):
    ch = _load(a.slug)
    store.set_hold(ch, "decision", a.why)
    ch["owner"] = None
    if ch.stage == "dev" and not ch.get("commit"):
        store.set_stage(ch, "ready", "agent could not finish")
    store.save(ch)
    events.emit("hold", change=ch["slug"], hold="decision", reason=a.why)
    print(f"{ch['slug']}: decision hold: {a.why}")


def cmd_hold(a):
    """BR-S2: an operator adds a hold or a note, never a stage."""
    ch = _load(a.slug)
    store.set_hold(ch, a.kind, a.reason)
    ch["owner"] = None
    store.save(ch)
    events.emit("hold", change=ch["slug"], hold=a.kind, reason=a.reason, by="operator")
    print(f"{ch['slug']}: {a.kind} hold")


def cmd_unhold(a):
    ch = _load(a.slug)
    store.clear_hold(ch, a.why or "cleared by the operator")
    ch["booked"] = None   # the operator's answer is a new fact: the next run may be booked (BR-S9)
    store.save(ch)
    events.emit("hold", change=ch["slug"], hold="none", reason=a.why, by="operator")
    print(f"{ch['slug']}: hold cleared")


def cmd_gate(a):
    if not store.exists(a.slug) and store.rec_load("batches", a.slug):
        b = store.rec_load("batches", a.slug)
        b["step"] = "gated" if a.verdict == "PASS" else "failed"
        b["verdict"] = {"result": a.verdict, "note": a.note, "at": iso()}
        store.rec_save("batches", a.slug, b)
        events.emit("batch", batch=a.slug, step=b["step"], detail=a.note, batch_kind=b.get("kind"))
        print(f"{a.slug}: release gate {a.verdict} recorded")
        return
    ch = _load(a.slug)
    tracks.of(ch).record_gate(ch, a.verdict, a.note)
    print(f"{ch['slug']}: gate {a.verdict} recorded")


def cmd_resolve(a):
    from . import batches
    b = store.rec_load("batches", a.batch)
    if not b:
        sys.exit(f"hd: no batch {a.batch}")
    b["resolution"] = a.note
    if a.decision:
        # nothing was recorded: the train stays at exception for the user, no resume, no second integrator
        b["decision"] = a.note
        store.rec_save("batches", a.batch, b)
        events.emit("batch", batch=a.batch, step="decision", detail=a.note[:300], batch_kind=b.get("kind"))
        print(f"{a.batch}: decision recorded; the train waits (not resumed)")
        return
    store.rec_save("batches", a.batch, b)
    events.emit("batch", batch=a.batch, step="resolved", detail=a.note)
    print(batches.resume(a.batch))


def _obs():
    return tracks.Observer()


def cmd_check(a):
    from . import check
    ch = _load(a.slug)
    passed, items = check.run(ch, _obs())
    print(check.render(ch, items))
    return 0 if passed else 1


def cmd_brief(a):
    from . import agents
    ch = _load(a.slug)
    role = policy.role_for(ch["track"], a.stage)
    print(agents.brief(ch, role, a.stage))


def cmd_dispatch(a):
    from . import agents, stages
    ch = _load(a.slug)
    ex = a.stage or stages.next_executor(ch) or "dev"
    role = policy.role_for(ch["track"], ex)
    r = agents.spawn(ch, role, ex)
    print(f"{r.get('name')} ({role}) -> {ch['slug']} ({ex}); booked, `hd drive` lists it for the console; brief {r.get('log')}")


def cmd_agents(a):
    rows = store.rec_all("runs") if a.all else agents_running()
    if not rows:
        print("no running agents")
    for r in rows:
        state = f"ended {str(r.get('exit'))[:30]}" if r.get("ended") else ("running" if r.get("agent_id") else "booked, not spawned")
        print(f"{r['name']:5} {r['role']:11} {str(r.get('change')):34} {r.get('stage'):5} since {local(r.get('started'))}  "
              f"tokens {r.get('tokens') or 0:<9} {state}")
        print(f"      brief: {r['log']}")


def agents_running():
    from . import agents
    return agents.running()


def cmd_run_end(a):
    from . import agents
    r = agents.end(a.name, a.exit, a.turns, a.tokens, a.minutes, a.result or "")
    print(f"{a.name}: {r.get('exit') if r else 'no such run'}")


def cmd_run_link(a):
    from . import agents
    agents.link(a.name, a.agent_id)
    print(f"{a.name} <- {a.agent_id}")


def cmd_run_stopped(a):
    from . import agents
    r = agents.mark_stopped(a.name)
    print(f"{a.name}: {'stop done' if r else 'no such run'}")


def cmd_drive(a):
    from . import drive
    w = drive.work(_obs())
    print(json.dumps(w, indent=1, default=str) if a.json else drive.render(w))


def cmd_actions(a):
    from . import actions
    rows = actions.pending_actions(_obs())
    if a.json:
        print(json.dumps(rows, indent=1, default=str))
        return
    if not rows:
        print("no actions need the user's OK")
    for r in rows:
        print(actions.render(r))
        print()


def cmd_lint(a):
    bad = 0
    idx = store.index()
    classes = set(capacity.limits())
    uses = [(f"role {r}", v.get("uses", [])) for r, v in policy.roles().items()]
    uses += [(f"batch step {k}", v) for k, v in (policy.get().get("batches", {}).get("uses") or {}).items()]
    for what, used in uses:
        for c in used:
            if c not in classes:
                print(f"lint: {what} uses capacity class {c}, which policy `capacity` does not define"); bad += 1
    for ch in idx.values():
        for d in ch.get("deps") or []:
            if d not in idx:
                print(f"lint: {ch['slug']}: dep {d} unknown"); bad += 1
        if ch.stage not in ch.chain():
            print(f"lint: {ch['slug']}: stage {ch.stage}"); bad += 1
        if ch.stage != "backlog" and not ch.has_dod():
            print(f"lint: {ch['slug']}: {ch.stage} without a definition of done"); bad += 1
        if ch.reached("gate") and not (ch.get("branch") and ch.get("commit")) and not (ch.stage == "live" and ch["track"] != "server"):
            print(f"lint: {ch['slug']}: {ch.stage} without branch and commit"); bad += 1
        if ch.get("track") == "server" and ch.get("branch") and policy.branch_track(ch["branch"]) is None:
            print(f"lint: {ch['slug']}: branch {ch['branch']} is not content/, fix/ or local/ (BR-C1)"); bad += 1
    seen = set()

    def dfs(n, stack):
        nonlocal bad
        if n in stack:
            print("lint: cycle " + " -> ".join(stack + [n])); bad += 1; return
        if n in seen:
            return
        for d in idx.get(n, {}).get("deps") or []:
            dfs(d, stack + [n])
        seen.add(n)
    for s in idx:
        dfs(s, [])
    print(f"lint: {len(idx)} changes, {bad} problems")
    return 1 if bad else 0


def status_view():
    """The status as a dict: changes with why they wait, open batches, locks, agent runs, daemon."""
    from . import batches, daemon
    waiting = (store.rec_load("view", "waiting") or {}).get("waiting", {})
    return {"changes": [{"slug": c["slug"], "track": c["track"], "stage": c.stage, "hold": c.hold, "owner": c.get("owner"),
                         "prio": c.get("prio"), "waiting": waiting.get(c["slug"]), "title": c.get("title")}
                        for c in store.all_changes()],
            "batches": [{k: b.get(k) for k in ("id", "kind", "step", "includes", "exception")} for b in batches.open_batches()],
            "leases": {r: {"holder": st.get("holder"), "purpose": st.get("purpose"), "since": st.get("since")}
                       for r, st in leases.status_all().items()},
            "runs": [{k: r.get(k) for k in ("name", "role", "change", "stage", "agent_id")} for r in agents_running()],
            "stale": (store.rec_load("view", "stale") or {}).get("holds", []),
            "daemon": daemon.status()}


def cmd_status(a):
    v = status_view()
    if a.json:
        print(json.dumps(v, indent=1, default=str))
        return
    d = v["daemon"]
    print(f"harnessd {'alive' if d.get('alive') else 'not running'}; last tick {d.get('last_tick_local') or '-'}")
    from .stages import terminal
    for ch in store.all_changes():
        if ch.stage == terminal(ch):
            continue
        print(fmt(ch, next((c["waiting"] for c in v["changes"] if c["slug"] == ch["slug"]), None)))
    for b in v["batches"]:
        print(f"batch {b['id']:18} {b['kind']:8} {b['step']:10} {', '.join(b.get('includes') or []) or '-'}"
              + (f"  exception: {str(b['exception'])[:80]}" if b.get("exception") else ""))
    for r, st in v["leases"].items():
        print(f"lease {r:12} {st.get('holder') or 'free':10} {st.get('purpose') or ''}")
    for t in v["stale"]:
        print(f"stale {t}")
    for r in v["runs"]:
        print(f"run {r['name']:5} {r['role']:11} {r['change']} ({r['stage']})" + ("" if r.get("agent_id") else "  [not spawned: hd drive]"))


def cmd_tick(a):
    from . import tick
    for line in tick.tick(dry_run=a.dry_run):
        print(line)


def cmd_run(a):
    from . import daemon
    daemon.run(a.interval, once=a.once)


def cmd_start(a):
    from . import daemon
    print(f"harnessd started (pid {daemon.start(a.interval)}); the console runs `hd drive`")


def cmd_stop(a):
    from . import daemon
    print(daemon.stop())


def cmd_daemon_status(a):
    from . import daemon
    print(json.dumps(daemon.status(), indent=1))


def cmd_digest(a):
    from . import daemon
    print(daemon.digest() or "(nothing new)")


def cmd_lease(a):
    act = a.action
    if act == "status":
        rows = leases.status_all() if not a.res else {a.res: leases.status(a.res)}
        for r, st in rows.items():
            if st.get("holder"):
                print(f"{r:12} held by {st['holder']} ({st.get('purpose') or ''}) since {local(st.get('since'))}")
            else:
                print(f"{r:12} free")
        return 0
    if act == "take":
        ok, msg = leases.take(a.res, a.who, a.what or "", pid=a.pid, container=a.container); print(msg); return 0 if ok else 1
    if act == "release":
        ok, msg = leases.release(a.res, a.who); print(msg); return 0 if ok else 1
    if act == "reclaim":
        ok, msg = leases.reclaim(a.res, a.what or "reclaimed by hand"); print(msg); return 0
    if act == "holds":
        ok = leases.holds(a.res, a.who); print("yes" if ok else "no"); return 0 if ok else 1
    sys.exit(f"hd lease: unknown action {act}")


def cmd_batches(a):
    for b in store.rec_all("batches"):
        if a.all or b.get("step") not in ("live", "published", "failed"):
            print(f"{b['id']:18} {b.get('kind', 'train'):8} {b.get('step', '?'):12} integration {str(b.get('integration') or '-')[:9]} "
                  f"includes {', '.join(b.get('includes') or []) or '-'}" + (f"  exception: {str(b.get('exception'))[:80]}" if b.get("exception") else ""))


def cmd_train(a):
    from . import batches
    for line in batches.advance(_obs(), now=a.now) or []:
        print(line)


def cmd_resume(a):
    from . import batches
    print(batches.resume(a.batch))


def cmd_release_request(a):
    from . import state_dir
    from .util import write_json
    write_json(os.path.join(state_dir(), "release.request"), {"tag": a.tag, "at": iso()})
    print(f"release {a.tag} requested; the next tick makes the batch")


def cmd_events(a):
    for e in events.read(kinds=[a.kind] if a.kind else None, change=a.change, limit=a.limit):
        rest = {k: v for k, v in e.items() if k not in ("ts", "kind")}
        print(f"{local(e['ts']):18} {e['kind']:9} " + json.dumps(rest, sort_keys=True)[:200])


def cmd_recount(a):
    from . import metrics
    print(", ".join(metrics.recount("hd recount")))


def cmd_kpi(a):
    from . import kpi
    print(json.dumps(kpi.compute(), indent=1, default=str))


def main(argv=None):
    p = argparse.ArgumentParser(prog="hd", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("new"); s.add_argument("--track", required=True, choices=store.TRACKS); s.add_argument("--slug", required=True)
    s.add_argument("--title", required=True); s.add_argument("--prio", default="P2", choices=store.PRIOS); s.add_argument("--dod", action="append")
    s.add_argument("--deps"); s.add_argument("--branch"); s.add_argument("--spec"); s.add_argument("--network", action="store_true")
    s.add_argument("--local-only", action="store_true"); s.add_argument("--backlog", action="store_true"); s.add_argument("--text")
    s.add_argument("--server-dod", action="store_true"); s.set_defaults(f=cmd_new)
    s = sp.add_parser("list"); s.add_argument("--track"); s.add_argument("--stage"); s.add_argument("--all", action="store_true"); s.set_defaults(f=cmd_list)
    s = sp.add_parser("show"); s.add_argument("slug"); s.set_defaults(f=cmd_show)
    s = sp.add_parser("log"); s.add_argument("slug"); s.add_argument("message"); s.set_defaults(f=cmd_log)
    s = sp.add_parser("dod"); s.add_argument("slug"); s.add_argument("numbers", nargs="+", type=int, help="1-based items"); s.set_defaults(f=cmd_dod)
    s = sp.add_parser("note"); s.add_argument("text"); s.add_argument("--kind", default="note"); s.set_defaults(f=cmd_note)
    s = sp.add_parser("handover"); s.add_argument("slug"); s.add_argument("--branch", required=True); s.add_argument("--commit", required=True)
    s.add_argument("--evidence"); s.add_argument("--summary"); s.add_argument("--repo"); s.set_defaults(f=cmd_handover)
    s = sp.add_parser("block"); s.add_argument("slug"); s.add_argument("--by", required=True); s.add_argument("why", nargs="?"); s.set_defaults(f=cmd_block)
    s = sp.add_parser("fail"); s.add_argument("slug"); s.add_argument("why"); s.set_defaults(f=cmd_fail)
    s = sp.add_parser("hold"); s.add_argument("slug"); s.add_argument("kind", choices=["decision", "failed", "exception"]); s.add_argument("reason"); s.set_defaults(f=cmd_hold)
    s = sp.add_parser("unhold"); s.add_argument("slug"); s.add_argument("why", nargs="?"); s.set_defaults(f=cmd_unhold)
    s = sp.add_parser("gate"); s.add_argument("slug"); s.add_argument("verdict", choices=["PASS", "FAIL"]); s.add_argument("note", nargs="?"); s.set_defaults(f=cmd_gate)
    for t in tracks.every():
        t.register(sp)
    s = sp.add_parser("resolve"); s.add_argument("batch"); s.add_argument("note"); s.add_argument("--decision", action="store_true", help="nothing recorded: the user decides; no resume"); s.set_defaults(f=cmd_resolve)
    s = sp.add_parser("check"); s.add_argument("slug"); s.set_defaults(f=cmd_check)
    s = sp.add_parser("brief"); s.add_argument("slug"); s.add_argument("--stage", default="dev"); s.set_defaults(f=cmd_brief)
    s = sp.add_parser("dispatch"); s.add_argument("slug"); s.add_argument("--stage"); s.set_defaults(f=cmd_dispatch)
    sp.add_parser("lint").set_defaults(f=cmd_lint)
    s = sp.add_parser("agents"); s.add_argument("--all", action="store_true"); s.set_defaults(f=cmd_agents)
    s = sp.add_parser("run-end"); s.add_argument("name"); s.add_argument("--exit", default="ok"); s.add_argument("--turns", type=int)
    s.add_argument("--tokens", type=int); s.add_argument("--minutes", type=float); s.add_argument("--result"); s.set_defaults(f=cmd_run_end)
    s = sp.add_parser("run-stopped"); s.add_argument("name"); s.set_defaults(f=cmd_run_stopped)
    s = sp.add_parser("drive"); s.add_argument("--json", action="store_true"); s.set_defaults(f=cmd_drive)
    s = sp.add_parser("actions"); s.add_argument("--json", action="store_true"); s.set_defaults(f=cmd_actions)
    s = sp.add_parser("run-link"); s.add_argument("name"); s.add_argument("agent_id"); s.set_defaults(f=cmd_run_link)
    s = sp.add_parser("status"); s.add_argument("--json", action="store_true"); s.set_defaults(f=cmd_status)
    s = sp.add_parser("tick"); s.add_argument("--dry-run", action="store_true"); s.set_defaults(f=cmd_tick)
    s = sp.add_parser("run"); s.add_argument("--interval", type=int, default=60); s.add_argument("--once", action="store_true"); s.set_defaults(f=cmd_run)
    s = sp.add_parser("start"); s.add_argument("--interval", type=int, default=60); s.set_defaults(f=cmd_start)
    sp.add_parser("stop").set_defaults(f=cmd_stop)
    sp.add_parser("daemon-status").set_defaults(f=cmd_daemon_status)
    sp.add_parser("digest").set_defaults(f=cmd_digest)
    s = sp.add_parser("lease"); s.add_argument("action", choices=["take", "release", "reclaim", "status", "holds"])
    s.add_argument("res", nargs="?"); s.add_argument("who", nargs="?"); s.add_argument("what", nargs="?")
    s.add_argument("--pid", type=int); s.add_argument("--container")
    s.set_defaults(f=cmd_lease)
    s = sp.add_parser("batches"); s.add_argument("--all", action="store_true"); s.set_defaults(f=cmd_batches)
    s = sp.add_parser("train"); s.add_argument("--now", action="store_true"); s.set_defaults(f=cmd_train)
    s = sp.add_parser("resume"); s.add_argument("batch"); s.set_defaults(f=cmd_resume)
    s = sp.add_parser("release-request"); s.add_argument("tag"); s.set_defaults(f=cmd_release_request)
    s = sp.add_parser("events"); s.add_argument("--kind"); s.add_argument("--change"); s.add_argument("--limit", type=int, default=50); s.set_defaults(f=cmd_events)
    sp.add_parser("kpi").set_defaults(f=cmd_kpi)
    sp.add_parser("recount").set_defaults(f=cmd_recount)
    sp.add_parser("version").set_defaults(f=lambda a: print("hd 4.0"))
    a = p.parse_args(argv)
    try:
        rc = a.f(a)
    except NotImplementedError as e:
        sys.exit(f"hd: not implemented yet: {e or a.cmd}")
    return rc or 0
