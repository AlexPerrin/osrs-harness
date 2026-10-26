"""The one mechanism (ARCHITECTURE 1, 3): a change is a list of steps; a step is "done when this fact holds" plus an
action by a script, an agent or the user. Pure over the pass context `Ctx` (config, facts, definitions, records), apart
from the script actions, which run commands and return a detail line.

  Ctx(cfg, F)                      one pass: facts memoised, definitions loaded
  lists(ctx, ch)                   the step lists of a change or goal (a server change has two)
  head / base / live / done        the containment facts of A6
  next_steps(ctx)                  [(ch, step, actor)] the first unmet step of every list whose deps are live
  dispatch(ctx)                    [(ch, step, role, name)] the agents to spawn, within the agent count (R6)
  questions(ctx) / cards(ctx)      what waits for the user (R7)
  brief(ctx, ch, step, name)       the agent's prompt
"""
import os
import re
import shutil
import tempfile

from . import store
from .facts import sh

AUTHOR = "Alex Perrin <44126061+AlexPerrin@users.noreply.github.com>"
TRAILER = "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
MARK = "<!-- hd:{} -->"
WAIT = "wait"


class Ctx:
    def __init__(self, cfg, F):
        self.cfg, self.F = cfg, F
        self.changes = store.changes()
        self.goals = store.goals()
        self.by_slug = {c["slug"]: c for c in self.changes}
        self.runs = store.runs()
        self._memo = {}

    def m(self, key, f):
        if key not in self._memo:
            self._memo[key] = f()
        return self._memo[key]

    def track(self, ch):
        return self.cfg["tracks"][ch["track"]]

    def repo(self, ch):
        return {"client": self.cfg["paths"]["client"], "server": self.cfg["paths"]["fork"]}.get(ch["track"], store.HD_HOME)

    def rec(self, ch, kind):
        return store.record(ch["slug"], kind)


def evidence(ch):
    return os.path.join(store.HD_HOME, "evidence", ch["slug"])


def public_branch(ch):
    return ch.get("branch") or f"content/{ch['slug']}"


# --- the facts of A6 --------------------------------------------------------------------------------------------------

def head(ctx, ch):
    """The change's commit: its dev ref; a release's is the client's live tip; None when unknown."""
    if ch.get("kind") == "release":
        return base(ctx, ch)
    ref = ctx.track(ch)["head"].replace("<slug>", ch["slug"])
    return ctx.m(("head", ch["slug"]), lambda: ctx.F.rev(ctx.repo(ch), ref))


def base(ctx, ch):
    return ctx.m(("base", ch["track"]), lambda: ctx.F.rev(ctx.repo(ch), ctx.track(ch)["base"]))


def live(ctx, ch):
    h = head(ctx, ch)
    if not h:
        return h
    if ch.get("kind") == "release":
        r = ctx.F.release(ch["version"])
        return None if r is None else bool(r)
    if ch["track"] == "server":
        integ = (store.read("live.json") or {}).get("integration")
        return False if not integ else ctx.F.contains(ctx.repo(ch), integ, h)
    return ctx.F.contains(ctx.repo(ch), ctx.track(ch)["base"], h)


def done(ctx, ch):
    if ch["track"] == "server" and ch.get("kind") == "change":
        h = head(ctx, ch)
        if not h:
            return h
        pr = _pr(ctx, ch)
        return bool(pr) and pr["state"] == "merged" or ctx.F.contains(ctx.repo(ch), ctx.track(ch)["base"], h)
    return live(ctx, ch)


def deps_live(ctx, ch):
    for d in ch.get("deps") or []:
        dep = ctx.by_slug.get(d)
        if dep is None or live(ctx, dep) is not True:
            return False
    return True


# --- steps ------------------------------------------------------------------------------------------------------------

class Step:
    """`done(ctx, ch)` -> True | False | None; `actor(ctx, ch)` -> 'script' | 'user' | 'wait' | a role; `do(ctx, ch)` runs
    the script action and returns a detail line, or the line of what an agent owes."""
    def __init__(self, name, done, actor, do=None):
        self.name, self._done, self._actor, self._do = name, done, actor, do

    def done(self, ctx, ch):
        return self._done(ctx, ch)

    def actor(self, ctx, ch):
        return self._actor(ctx, ch) if callable(self._actor) else self._actor

    def do(self, ctx, ch):
        return self._do(ctx, ch) if self._do else ""


def _dev(ctx, ch):
    return ctx.track(ch)["dev"]


def _owner(ctx):
    return ctx.cfg["repos"]["fork"].split("/")[0].lower()


def _reviewer(ctx, ch):
    return ctx.track(ch).get("reviewer")


def _handover_done(ctx, ch):
    h = head(ctx, ch)
    return None if h is None else store.valid(ctx.rec(ch, "handover"), h)


def _gate_rec(ctx, ch):
    g = ctx.rec(ch, "gate")
    return g if store.valid(g, head(ctx, ch), base(ctx, ch)) else None


def _gate_done(ctx, ch):
    if head(ctx, ch) is None or base(ctx, ch) is None:
        return None
    g = _gate_rec(ctx, ch)
    return bool(g) and g.get("ok") is True


def _gate_actor(ctx, ch):
    g = _gate_rec(ctx, ch)
    return _dev(ctx, ch) if g and g.get("ok") is False else "script"


def _run_gate(ctx, ch):
    """gates/<track>.py <slug> <head> <base> <evidence>: exit 0 ok, 1 fail, 2 pending; stdout is the detail."""
    h, b = head(ctx, ch), base(ctx, ch)
    r = sh(["python3", os.path.join(store.HD_HOME, "gates", f"{ch['track']}.py"), ch["slug"], h, b, evidence(ch)],
           env={"HD_STATE": store.state_dir(), "HD_CONFIG": os.environ.get("HD_CONFIG", "")})
    if r is None:
        return "gate: could not run"
    detail = (r.stdout + r.stderr).strip()[-2000:]
    ok = {0: True, 1: False}.get(r.returncode)
    rec = {"head": h, "base": b, "ok": ok, "detail": detail}
    if {k: (ctx.rec(ch, "gate") or {}).get(k) for k in rec} != rec:   # a pending gate is not re-recorded every pass
        store.save_record(ch["slug"], "gate", rec)
    return f"gate {'ok' if ok else 'FAIL' if ok is False else 'pending'}: {detail.splitlines()[-1] if detail else ''}"


def _merge_done(ctx, ch):
    return live(ctx, ch)


def _merge_conflict(ctx, ch):
    s = ctx.rec(ch, "step") or {}
    return s.get("step") == "merge" and s.get("head") == head(ctx, ch) and (s.get("detail") or "").startswith("merge: conflict")


def _merge_actor(ctx, ch):
    return _dev(ctx, ch) if _merge_conflict(ctx, ch) else "script"


def _merge(ctx, ch):
    """Merge the head into the target branch in the checkout and push (client: master -> origin/main)."""
    repo, F, h = ctx.repo(ch), ctx.F, head(ctx, ch)
    target = ctx.track(ch)["base"].split("/")[-1]
    local = ctx.track(ch).get("checkout_branch", target)
    if (F.git(repo, "branch", "--show-current") or sh(["false"])).stdout.strip() != local:
        return f"merge: {repo} is not on {local}; nothing done"
    if F.git(repo, "status", "--porcelain", "--untracked-files=no").stdout.strip():
        return f"merge: {repo} has uncommitted changes; nothing done"
    msg = f"Merge {ch['slug']} ({h[:9]}): {ch.get('title', '')}\n\n{TRAILER}"
    r = F.git(repo, "merge", "--no-ff", "--no-edit", "-m", msg, h)
    if r.returncode != 0:
        F.git(repo, "merge", "--abort")
        return f"merge: conflict: {r.stdout[-300:]}"
    F.git(repo, "commit", "--amend", "--no-edit", "-q", f"--author={AUTHOR}")
    remote = ctx.track(ch).get("remote")
    if remote:
        p = F.git(repo, "push", "-q", remote, f"{local}:{target}")
        if p.returncode != 0:
            return f"merged, push failed: {p.stderr[-300:]}"
    return f"merged {h[:9]} into {target}"


# server: the test server

def train_state():
    return store.read("train.json") or {}


def _train_alive(ctx):
    t = train_state()
    return bool(t.get("pid")) and not t.get("ended") and ctx.F.alive(t["pid"], t.get("start"))


PASS_PIN = re.compile(r"integration: pin \S+ at [0-9a-f]{9}")   # server.pin's own subject


def _train_failed(ctx):
    """The train stopped on a fault the integrator must resolve, and the tools branch has not moved since."""
    t = train_state()
    if not t.get("failed_step") or _train_alive(ctx):
        return False
    tools = ctx.F.rev(ctx.cfg["paths"]["fork"], "fork/local/integration-tools")
    if tools is None or not t.get("tools"):
        return False
    if tools == t["tools"]:
        return True
    log = ctx.F.git(ctx.cfg["paths"]["fork"], "log", "--format=%s", f"{t['tools']}..{tools}")   # the pass's own pins resolve nothing
    subjects = log.stdout.splitlines() if log is not None and log.returncode == 0 else []
    return bool(subjects) and all(PASS_PIN.fullmatch(s) for s in subjects)   # an integrator's re-pin says why: a resolution


def _queue_actor(ctx, ch):
    return "integrator" if _train_failed(ctx) else "script"


def _queue(ctx, ch):
    """Pin the head on the tools branch (idempotent) and start the train when none is alive."""
    if ctx.rec(ch, "ask"):
        return "queue: the change has a question; not pinned"
    from . import server
    out = server.pin(ctx, ch)
    if _train_alive(ctx):
        return out + "; train running"
    if _train_failed(ctx) or any(r.get("role") == "integrator" for r in alive_runs(ctx)):   # the integrator works in the build worktree
        return out + "; train failed, waiting for the integrator"
    return out + "; " + server.start_train(ctx)


# server: upstream

def _verdict_rec(ctx, ch):
    v = ctx.rec(ch, "verdict")
    return v if store.valid(v, head(ctx, ch)) else None


def _review_done(ctx, ch):
    if head(ctx, ch) is None:
        return None
    v = _verdict_rec(ctx, ch)
    return bool(v) and v.get("pass") is True


def _review_actor(ctx, ch):
    v = _verdict_rec(ctx, ch)
    return _dev(ctx, ch) if v and v.get("pass") is False else _reviewer(ctx, ch)


def _approve_done(ctx, ch):
    h = head(ctx, ch)
    return None if h is None else store.valid(ctx.rec(ch, "approval"), h)


def _pushed(ctx, ch):
    return ctx.F.contains(ctx.cfg["paths"]["fork"], f"fork/{public_branch(ch)}", head(ctx, ch))


def _push(ctx, ch):
    r = ctx.F.git(ctx.cfg["paths"]["fork"], "push", "-q", "fork", f"{head(ctx, ch)}:refs/heads/{public_branch(ch)}")
    return "pushed" if r is not None and r.returncode == 0 else f"push failed: {(r.stderr if r else '')[-300:]}"


def _pr(ctx, ch):
    return ctx.m(("pr", public_branch(ch)), lambda: ctx.F.pr(public_branch(ch)))


def _pr_done(ctx, ch):
    pr = _pr(ctx, ch)
    return None if pr is None else bool(pr) and pr["state"] in ("open", "merged")


def _texts(ch):
    out = {}
    for key, name in (("title", "pr-title.txt"), ("body", "pr-body.md"), ("comment", "pr-comment.md")):
        try:
            with open(os.path.join(evidence(ch), name)) as f:
                out[key] = f.read().strip()
        except OSError:
            out[key] = ""
    return out


def _pr_actor(ctx, ch):
    t = _texts(ch)
    return "script" if t["title"] and t["body"] else _dev(ctx, ch)


def _open_pr(ctx, ch):
    t = _texts(ch)
    if not (t["title"] and t["body"]):
        return "pr: pr-title.txt or pr-body.md missing in the evidence dir"
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(t["body"] + "\n")
    owner = ctx.cfg["repos"]["fork"].split("/")[0]
    r = sh(["gh", "pr", "create", "-R", ctx.cfg["repos"]["upstream"], "--draft", "--base", "main", "--head",
            f"{owner}:{public_branch(ch)}", "--title", t["title"], "--body-file", f.name])
    os.unlink(f.name)
    return f"pr opened: {r.stdout.strip()}" if r is not None and r.returncode == 0 else f"pr failed: {(r.stderr if r else '')[-300:]}"


def _ci_state(ctx, ch):
    pr = _pr(ctx, ch)
    if not pr:
        return None
    h = head(ctx, ch)
    if pr.get("head") and pr["head"] != h and ctx.F.contains(ctx.cfg["paths"]["fork"], pr["head"], h):
        return "success"   # the PR moved on past this head (a finding's commit): its CI is that change's step
    return ctx.F.pr_checks(pr["number"], h)


def _ci_done(ctx, ch):
    s = _ci_state(ctx, ch)
    return None if s is None else s == "success"


def _ci_actor(ctx, ch):
    return _dev(ctx, ch) if _ci_state(ctx, ch) == "failure" else WAIT


def _comments(ctx, ch):
    pr = _pr(ctx, ch)
    return None if not pr else ctx.m(("comments", pr["number"]), lambda: ctx.F.pr_comments(pr["number"]))


def _ours_at_head(ctx, ch):
    """Our comments that name the head, newest last."""
    cs = _comments(ctx, ch) or []
    h, owner = head(ctx, ch), _owner(ctx)
    marks = (MARK.format(h[:12]), f"<!-- hd-contribute:{h[:12]} -->", h[:9]) if h else ()   # v6 wrote the sha in prose
    return [c for c in cs if (c["author"] or "").lower() == owner and any(m in c["body"] for m in marks)]


def _norm(text):
    return "\n".join(l.rstrip() for l in re.sub(r"<!-- hd:\w+ -->", "", text.replace("\r\n", "\n")).strip().splitlines())


def _comment_done(ctx, ch):
    """Done when one of our comments names the head (every PR has one before it is marked for review, the user's rule)
    and, when pr-comment.md is prepared, says what it says (an edited pr-comment.md is edited in place)."""
    if _comments(ctx, ch) is None:
        return None
    if not head(ctx, ch):
        return False
    ours, want = _ours_at_head(ctx, ch), _texts(ch)["comment"]
    return bool(ours) and (not want or _norm(ours[-1]["body"]) == _norm(want))


def _comment_actor(ctx, ch):
    return "script" if _texts(ch)["comment"] else _dev(ctx, ch)


GQL_EDIT = "mutation($id:ID!,$b:String!){updateIssueComment(input:{id:$id,body:$b}){issueComment{id}}}"


def _comment(ctx, ch):
    t = _texts(ch)
    body = (t["comment"] or f"Updated to {head(ctx, ch)[:9]}.") + "\n\n" + MARK.format(head(ctx, ch)[:12]) + "\n"
    ours = _ours_at_head(ctx, ch)
    if ours:   # our comment at this head exists: edit it in place (GraphQL takes the node id gh reports)
        r = sh(["gh", "api", "graphql", "-f", "query=" + GQL_EDIT, "-f", f"id={ours[-1]['id']}", "-f", f"b={body}"])
        return "comment edited" if r is not None and r.returncode == 0 else f"comment edit failed: {(r.stderr if r else '')[-300:]}"
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(body)
    r = sh(["gh", "pr", "comment", str(_pr(ctx, ch)["number"]), "-R", ctx.cfg["repos"]["upstream"], "--body-file", f.name])
    os.unlink(f.name)
    return "commented" if r is not None and r.returncode == 0 else f"comment failed: {(r.stderr if r else '')[-300:]}"


def _title_done(ctx, ch):
    pr, want = _pr(ctx, ch), _texts(ch)["title"]
    return None if pr is None else bool(pr) and (not want or pr.get("title") == want)


def _title(ctx, ch):
    pr = _pr(ctx, ch)   # REST: `gh pr edit` fails on repos that still list classic projects
    r = sh(["gh", "api", "-X", "PATCH", f"repos/{ctx.cfg['repos']['upstream']}/pulls/{pr['number']}", "-f", f"title={_texts(ch)['title']}"])
    return "title set" if r is not None and r.returncode == 0 else f"title failed: {(r.stderr if r else '')[-300:]}"


def _unanswered(ctx, ch):
    """The findings filed on this PR whose answer is not yet pushed, commented and complete: planned work the
    maintainers can see."""
    pr = _pr(ctx, ch)
    if not pr:
        return []
    return [c for c in ctx.changes if c.get("finding") and c.get("pr") == pr["number"] and c["slug"] != ch["slug"]
            and not (_handover_done(ctx, c) and _pushed(ctx, c) and _comment_done(ctx, c) and not _incomplete(c))]


def _incomplete(ch):
    """What keeps the PR text from saying "mergeable": an unticked checklist item or a Not done list (the user's rule:
    nothing deferred, every template check true)."""
    import re as _re
    t = _texts(ch)
    text = t["comment"] if "## Checklist" in t["comment"] else t["body"]
    out = []
    m = _re.search(r"^## Checklist\s*$(.*?)(?=^## |\Z)", text, _re.M | _re.S)
    out += [f"unticked: {l.strip()[6:]}" for l in (m.group(1).splitlines() if m else []) if l.strip().startswith("- [ ]")]
    if _re.search(r"^\s*Not done\b", text, _re.M):
        out.append("a Not done list")
    return out


def _fix_in_progress(ctx, ch):
    """A dev run is alive on a change for this PR, or a dev ref holds commits the PR head does not (the user: a PR is a
    draft while a fix is in progress)."""
    pr = _pr(ctx, ch)
    if not pr:
        return False
    mine = [c for c in ctx.changes if c["track"] == "server" and public_branch(c) == public_branch(ch)]
    devs = {ctx.track(c)["dev"] for c in mine}
    if any(r.get("change") in {c["slug"] for c in mine} and r.get("role") in devs for r in alive_runs(ctx)):
        return True
    for c in mine:
        h = head(ctx, c)
        if h and pr.get("head") and h != pr["head"] and ctx.F.contains(ctx.cfg["paths"]["fork"], pr["head"], h) is False:
            return True
    return False


def _blocked(ctx, ch):
    """What puts a PR back to draft: a step before ready is open (a failed review, a new head), a finding is unanswered,
    or a fix is in progress."""
    before = UPSTREAM[:UPSTREAM.index(READY)]
    return not all(s.done(ctx, ch) is True for s in before) or bool(_unanswered(ctx, ch)) or _fix_in_progress(ctx, ch)


def _may_be_ready(ctx, ch):
    return not _blocked(ctx, ch) and not _incomplete(ch)


def _ready_done(ctx, ch):
    """Draft while blocked; ready only when also complete. An incomplete text keeps a draft PR in draft but does not
    pull a ready one back (the user exempted #354 and #355): either way it is the dev's step."""
    pr = _pr(ctx, ch)
    if pr is None:
        return None
    if not pr:
        return False
    blocked = _blocked(ctx, ch)
    return (pr["draft"] and blocked) or (not pr["draft"] and not blocked and not _incomplete(ch))


def _ready_actor(ctx, ch):
    return _dev(ctx, ch) if not _blocked(ctx, ch) and _incomplete(ch) else "script"


def _ready(ctx, ch):
    undo = _blocked(ctx, ch)
    r = sh(["gh", "pr", "ready", str(_pr(ctx, ch)["number"]), "-R", ctx.cfg["repos"]["upstream"]] + (["--undo"] if undo else []))
    if r is None or r.returncode != 0:
        return f"ready failed: {(r.stderr if r else '')[-300:]}"
    return "drafted: not mergeable yet (" + "; ".join(_incomplete(ch) or ["a step before ready, or a finding, is open"]) + ")" if undo else "ready"


def _merged_done(ctx, ch):
    return done(ctx, ch)


# client release

def _release_done(ctx, ch):
    return live(ctx, ch)


def _release(ctx, ch):
    ev = evidence(ch)
    apk = os.path.join(ev, "osrs-runelite.apk")
    if not os.path.isfile(apk):
        return "release: no osrs-runelite.apk in the evidence dir"
    notices = os.path.join(ev, "THIRD_PARTY_NOTICES.md")
    args = ["gh", "release", "create", ch["version"], "-R", ctx.cfg["repos"]["client"], "--target", head(ctx, ch),
            "--title", ch["version"], "--notes", ch.get("title", ch["version"]), apk]
    if os.path.isfile(notices):
        args.append(notices)
    r = sh(args)
    return f"released {ch['version']}" if r is not None and r.returncode == 0 else f"release failed: {(r.stderr if r else '')[-300:]}"


# goals

def _serving(ctx, goal):
    return [c for c in ctx.changes if c.get("goal") == goal["slug"] and done(ctx, c) is not True]


def _measure_done(ctx, goal):
    if _serving(ctx, goal):
        return True
    track = {"slug": goal["slug"], "track": goal["track"]}
    b = base(ctx, track)
    if b is None:
        return None
    m = ctx.rec(goal, "measure")
    return bool(m) and m.get("base") == b and (m.get("value") or 0) >= goal["target"]


HANDOVER = Step("handover", _handover_done, _dev)
GATE = Step("gate", _gate_done, _gate_actor, _run_gate)
MERGE = Step("merge", _merge_done, _merge_actor, _merge)
QUEUE = Step("queue", live, _queue_actor, _queue)
REVIEW = Step("review", _review_done, _review_actor)
APPROVE = Step("approve", _approve_done, "user")
PUSH = Step("push", _pushed, "script", _push)
PR = Step("pr", _pr_done, _pr_actor, _open_pr)
TITLE = Step("title", _title_done, "script", _title)
CI = Step("ci", _ci_done, _ci_actor)
COMMENT = Step("comment", _comment_done, _comment_actor, _comment)
READY = Step("ready", _ready_done, _ready_actor, _ready)
MERGED = Step("merged", _merged_done, WAIT)
RELEASE = Step("release", _release_done, "script", _release)
MEASURE = Step("measure", _measure_done, "orchestrator")

UPSTREAM = [HANDOVER, GATE, REVIEW, APPROVE, PUSH, PR, TITLE, CI, COMMENT, READY, MERGED]


def lists(ctx, ch):
    if "target" in ch:
        return [[MEASURE]]
    if ch.get("kind") == "release":
        return [[REVIEW, APPROVE, RELEASE]]
    if ch["track"] != "server":
        return [[HANDOVER, GATE, MERGE]]
    if ch.get("kind") == "local":
        return [[HANDOVER, GATE, QUEUE]]
    return [[HANDOVER, GATE, QUEUE], UPSTREAM]


def first_unmet(ctx, ch, steps):
    """(step, done) of the first step not True; None when every step is done. An unknown (None) stops the list."""
    for s in steps:
        d = s.done(ctx, ch)
        if d is not True:
            return s, d
    return None


def stage(ctx, ch):
    """The names of the first unmet step of each list ('done' when all are met, '?' when a fact is unknown)."""
    out = []
    for steps in lists(ctx, ch):
        u = first_unmet(ctx, ch, steps)
        out.append("done" if u is None else u[0].name if u[1] is False else f"{u[0].name}?")
    return out


def next_steps(ctx):
    """[(ch, step)] for every list whose first unmet step is known and whose deps are live; one entry per step."""
    out, seen = [], set()
    for ch in ctx.goals + ctx.changes:
        try:
            if "target" not in ch and (not deps_live(ctx, ch) or done(ctx, ch) is True):   # a done change has no step left
                continue
            for steps in lists(ctx, ch):
                u = first_unmet(ctx, ch, steps)
                if u and u[1] is False and (ch["slug"], u[0].name) not in seen:
                    seen.add((ch["slug"], u[0].name))
                    out.append((ch, u[0]))
        except Exception as e:   # one change's bad fact stops that change, not the pass
            store.event("error", change=ch["slug"], detail=repr(e)[:300])
    return out


# --- the agents (R6) ------------------------------------------------------------------------------------------------

def alive_runs(ctx):
    return [r for r in ctx.runs if not r.get("ended")]


def _last_run(ctx, slug, role):
    rs = [r for r in ctx.runs if r.get("change") == slug and r.get("role") == role and r.get("ended")]
    return max(rs, key=lambda r: r.get("ended")) if rs else None


def _repeat(ctx, ch, step, role):
    """The ended run of this role that worked on the same input: head, definition and step (a hand-over at X and a gate
    fix at X are different inputs)."""
    last = _last_run(ctx, ch["slug"], role)
    if last and last.get("reason") == "console-died":   # the agent did not fail: the console under it exited
        return None
    same = last and last.get("head") == run_head(ctx, ch, step) and last.get("def_hash") == ch["hash"] \
        and (last.get("step") or step.name) == step.name
    return last if same else None


def run_head(ctx, ch, step):
    """The input a run works on: the change's head, or the failed train's tools commit for the integrator."""
    return train_state().get("tools") if step is QUEUE else head(ctx, ch)


def _order(ch):
    return (ch.get("priority", "P2"), ch.get("created") or "", ch["slug"])


def dispatch(ctx):
    """[(ch, step, role, name)] in priority then age, while alive runs are fewer than the agent count. A change with a
    question or an alive run is skipped; a role whose last run ended on the same head and definition is not re-run
    (that run is a question, see `questions`)."""
    busy = {r.get("change") for r in alive_runs(ctx)}
    free = ctx.cfg.get("agents", 3) - len(alive_runs(ctx))
    single = {r.get("role") for r in alive_runs(ctx)} & {"integrator"}   # one train, so one integrator at a time
    out = []
    for ch, step in sorted(next_steps(ctx), key=lambda x: _order(x[0])):
        role = step.actor(ctx, ch)
        if role in ("script", "user", WAIT) or ch["slug"] in busy or ctx.rec(ch, "ask") or role in single:
            continue
        if role == "integrator":
            single.add(role)
        if _repeat(ctx, ch, step, role):
            continue
        if free <= 0:
            break
        free -= 1
        busy.add(ch["slug"])   # one run per change, also within this pass (a server change has two lists)
        n = max([int(r["name"].rsplit("-", 1)[1]) for r in ctx.runs if r.get("change") == ch["slug"]
                 and r["name"].rsplit("-", 1)[-1].isdigit()] or [0]) + 1   # next free number: a skipped spawn leaves a gap
        out.append((ch, step, role, f"{ch['slug']}-{n}"))
    return out


def questions(ctx):
    """[(slug, text)]: what agents asked, and runs that ended without their record on an input that has not changed."""
    out = []
    for ch in ctx.goals + ctx.changes:
        a = ctx.rec(ch, "ask")
        if a:
            out.append((ch["slug"], a.get("question", "") + ("  options: " + ", ".join(a["options"]) if a.get("options") else "")))
    for ch, step in next_steps(ctx):
        role = step.actor(ctx, ch)
        if role in ("script", "user", WAIT) or ctx.rec(ch, "ask"):
            continue
        last = _repeat(ctx, ch, step, role)
        if last:
            out.append((ch["slug"], f"run {last['name']} ({role}) ended without its record on the same input: "
                                    f"{(last.get('last') or '')[-300:]}  answer with `hd answer {ch['slug']} \"...\"`"))
    return out


def cards(ctx):
    """[(slug, text)]: each approval the user can give now, with everything the decision needs."""
    out = []
    for ch, step in next_steps(ctx):
        if step is not APPROVE:
            continue
        h, v, t = head(ctx, ch), ctx.rec(ch, "verdict") or {}, _texts(ch)
        lines = [f"## {ch['slug']}: {ch.get('title', '')}", f"head {h}  base {base(ctx, ch)}  evidence {evidence(ch)}",
                 "verdict PASS: " + "; ".join(v.get("findings") or ["no findings"]),
                 "gate: " + ((ctx.rec(ch, "gate") or {}).get("detail") or "-").splitlines()[-1]]
        if ch.get("kind") == "release":
            lines += [f"release {ch['version']} at {h}", f"then: hd approve {ch['slug']} {h}"]
        else:
            pr = _pr(ctx, ch) or {}
            lines += [f"branch {public_branch(ch)}" + (f", PR #{pr['number']}" if pr else ", new draft PR"),
                      f"### title\n{t['title']}", f"### body\n{t['body']}", f"### comment\n{t['comment']}",
                      f"then: hd approve {ch['slug']} {h}  (push, PR, CI green, comment, ready: one step per pass)"]
        out.append((ch["slug"], "\n".join(lines)))
    return out


def brief(ctx, ch, step, name):
    """The agent's prompt: the change, the step's task, the facts and the records it needs, the record it owes."""
    h, b = head(ctx, ch), base(ctx, ch)
    role = step.actor(ctx, ch)
    lines = [f"Harness change `{ch['slug']}` run `{name}` head `{run_head(ctx, ch, step) or ''}` def `{ch['hash']}` step `{step.name}`", "",
             f"# {ch.get('title', ch['slug'])}",
             f"track {ch['track']}  kind {ch.get('kind', 'change')}  priority {ch.get('priority')}  head {h or '-'}  base {b or '-'}",
             f"definition {ch['path']}  evidence {evidence(ch)}", "", ch.get("body", "").strip(), ""]
    g, v = ctx.rec(ch, "gate"), ctx.rec(ch, "verdict")
    if step is GATE and g:
        lines += ["## The gate failed at this head", g.get("detail", ""), ""]
    if step is REVIEW and v and v.get("pass") is False and role == _dev(ctx, ch):
        lines += ["## The review failed at this head"] + [f"- {f}" for f in v.get("findings") or []] + [""]
    if step is CI and role == _dev(ctx, ch):
        lines += ["## Upstream CI failed at this head", f"PR #{(_pr(ctx, ch) or {}).get('number')}", ""]
    if step is MERGE and role == _dev(ctx, ch):
        lines += [f"## The merge into {ctx.track(ch)['base']} conflicted at this head",
                  (ctx.rec(ch, "step") or {}).get("detail", ""), "Merge the current base into your branch and resolve.", ""]
    if step is READY and role == _dev(ctx, ch):
        lines += ["## Not mergeable yet: the PR text is incomplete"] + [f"- {x}" for x in _incomplete(ch)] + \
                 ["Finish the work or take it out of scope; tick only what is true; no Not done list.", ""]
    if step in (PR, COMMENT) and role == _dev(ctx, ch):
        lines += ["## Missing PR text in the evidence dir",
                  "pr-title.txt and pr-body.md" if step is PR else "pr-comment.md: what changed for the maintainers since their last look", ""]
    if step is QUEUE:
        t = train_state()
        lines += [f"## The train failed at `{t.get('failed_step')}` (tools {str(t.get('tools'))[:9]})", t.get("detail", ""), ""]
    owed = {HANDOVER: f"hd handover {ch['slug']} <sha> --summary \"...\"", REVIEW: f"hd verdict {ch['slug']} {h} PASS|FAIL [findings...]",
            MEASURE: f"hd measure {ch['slug']} <value> --evidence <report>, then `hd new` for each change that closes a gap",
            QUEUE: "a resolution pushed to fork local/integration-tools (a recorded rr-cache or a dropped branch, with `hd ask` on it)"}
    if step in (GATE, CI, MERGE) or (step in (REVIEW, READY) and role == _dev(ctx, ch)):
        owed[step] = f"a new commit on the dev ref, then hd handover {ch['slug']} <sha>"
    if step in (PR, COMMENT):
        owed[step] = f"the PR text in the evidence dir, then hd handover {ch['slug']} {h}"
    lines += [f"## You owe\n{owed.get(step, 'the record of your role')}; or `hd ask {ch['slug']} \"<question>\"` when you cannot."]
    return "\n".join(lines)


def clear_evidence_tmp(path):
    shutil.rmtree(path, ignore_errors=True)
