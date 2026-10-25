"""The server track (OpenRune fork, contributed upstream). Two independent outputs per change: the test server runs it
through the integration train (the core's batches.py, fed here), and the contribution upstream:

    backlog -> ready -> dev -> gate -> contribute -> review -> merged        (local/*: ... gate -> live)

  dev          one agent; `hd handover` runs the hand-over check and refuses an incomplete one
  gate         handed over; server-qa aggregates every check onto QA's record (qa.py), `hd gate-ci` runs the scratch
               merge and fork CI (gateci.py); the change waits for the record at its commit
  contribute   the record exists: the approval card (cards.py) waits for the user's yes, bound to the commit
  review       `hd contribute` ran (contribute.py): the PR is ready with the commit in its head; maintainer findings
               are filed once each as review-fix changes (review.py)
  merged       the PR is merged, or upstream main contains the commit
`live_commit` (the test server runs the commit) is observed separately and never gates the contribution. The only gate
is the user's approval; QA's findings set no hold and book no dev. GitHub is read through `github.py` only.
Settings: policy `tracks.server` (reviewers, ci_equivalence). Heavy modules are imported where used: the
hooks import this package on every command."""
import os

from ... import evidence_dir, events, store
from ...util import same_commit
from ..base import BaseTrack
from . import qa

FULL = ("backlog", "ready", "dev", "gate", "contribute", "review", "merged")
LOCAL = ("backlog", "ready", "dev", "gate", "live")
LABELS = {"gate": "QA's aggregate (server-qa)", "contribute": "the user's approval (hd contribute)", "review": "the maintainers"}


def _pr_has(pr, commit, obs):
    head = str(pr.get("head") or "")
    return bool(head) and (same_commit(head, commit) or obs.contains("fork", head, commit) is True)


class ServerTrack(BaseTrack):
    name = "server"
    keys = ("upstream_pr", "finding", "review_seen")
    records_repo = True

    def chain(self, ch):
        return LOCAL if ch.get("local_only") else FULL

    def repo_name(self, ch):
        return "fork"

    def open_stages(self, ch):
        return ("ready", "dev", "gate", "contribute")

    def default_repo(self):
        from ... import fork_clone
        return fork_clone()

    def migrate_stage(self, meta):
        """The retired chain (checked, gated, published, and `live` before the contribution): checked and live -> gate."""
        stage = meta.get("stage") or "backlog"
        if stage == "live" and not meta.get("local_only"):
            return "gate"
        return {"checked": "gate", "gated": "contribute", "published": "review"}.get(stage, stage)

    def default_dod(self, spec):
        return ["accuracy spec (accuracy*.md in the evidence dir; accuracy-check: sources, RSProx comparison, caveats)",
                "change built and checked in game on the branch server (evidence in re/evidence/<slug>/)",
                "one change only, branch off upstream main (no stacking); the diff self-checked against upstream AGENTS.md and "
                "CONTRIBUTING (no added comments or tests)",
                "PR text in the evidence dir (pr-title.txt, pr-body.md; pr-text-review)"]

    # --- facts --------------------------------------------------------------------------------------------------------

    def live_fact(self, ch, obs):
        """(met, why): the integration pin is the commit and the live server's integration contains it (live.json)."""
        branch, commit = ch["branch"], ch["commit"]
        lv = obs.live() or {}
        pin = obs.pin(branch)
        integ = lv.get("integration")
        if integ is None:
            return None, "live.json missing: nothing deployed by the daemon yet"
        if not pin or not same_commit(pin, commit):
            return False, f"integration pin is {pin[:9] if pin else 'absent'}, not {commit[:9]} (next train)"
        c = obs.contains("fork", integ, commit)
        return c, (f"live integration {integ[:9]} {'carries' if c else 'lacks'} {commit[:9]}" if c is not None
                   else "could not read the live integration commit")

    def facts(self, ch, obs):
        commit = ch["commit"]
        tip, where = self.tip(ch, obs)
        out = {"tip": (tip, f"{where}/{ch['branch']} at {tip[:9]}" if tip else f"{where}/{ch['branch']} not found"),
               "live": self.live_fact(ch, obs)}
        if ch.get("local_only"):
            return out
        pr = obs.upstream_pr(ch.get("upstream_pr") or ch["branch"])
        if pr is None:
            out["review"] = (None, "could not read the upstream PR")
        elif not pr:
            out["review"] = (False, "no upstream PR")
        elif pr.get("merged"):
            out["review"] = (True, f"upstream PR #{pr['number']} merged")
        elif pr.get("state") != "open":
            out["review"] = (False, f"upstream PR #{pr['number']} is {pr.get('state')}")
        elif pr.get("draft"):
            out["review"] = (False, f"upstream PR #{pr['number']} is a draft")
        elif not _pr_has(pr, commit, obs):
            out["review"] = (False, f"upstream PR #{pr['number']} head {str(pr.get('head'))[:9]} lacks {commit[:9]}")
        else:
            out["review"] = (True, f"upstream PR #{pr['number']} ready for review at {commit[:9]}")
        verdict, findings = qa.gate_state(ch)
        done = out["review"][0] is True   # contributed before QA's record existed (an older flow): nothing to approve
        out["contribute"] = (verdict is not None or done,
                             f"QA record at the commit ({verdict}, {len(findings)} finding(s))" if verdict
                             else "the PR is already ready at the commit" if done else f"no QA record at {commit[:9]}")
        if pr and pr.get("merged"):
            out["merged"] = (True, f"upstream PR #{pr['number']} merged")
        else:
            m = obs.contains("upstream", "main", commit)
            out["merged"] = (m, "upstream main contains the commit" if m else "not merged upstream yet" if m is not None
                             else "could not read upstream main")
        return out

    def waiting(self, stage, ch):
        return LABELS.get(stage, "")

    def executor(self, ch):
        """`gate`: the QA aggregate, for a handed-over change that is not local-only, not held, with no record at its commit."""
        if ch.stage == "gate" and not ch.get("local_only") and not ch.hold and qa.gate_state(ch)[0] is None:
            return "gate"
        return None

    def finding_set(self, ch):
        verdict, findings = qa.gate_state(ch)
        return list(findings if verdict == "FAIL" else []) + ([f"finding:{ch['finding']}"] if ch.get("finding") else [])

    def settles_first(self, ch):
        """A review-fix change settles a maintainer's finding on a PR that is open."""
        return bool(ch.get("finding"))

    # --- tick hooks ---------------------------------------------------------------------------------------------------

    def reconcile(self, ctx, slug, ch):
        """`live_commit` follows the test server; the upstream stage is untouched."""
        if ch.get("local_only") or not ch.get("commit") or ctx.dry_run:
            return
        met, why = self.live_fact(ch, ctx.obs)
        if met and ch.get("live_commit") != ch["commit"]:
            ch["live_commit"] = ch["commit"]
            store.add_log(ch, f"live on the test server: {why}")
            store.save(ch)
            events.emit("stage", change=slug, **{"from": ch.stage, "to": "live"}, commit=ch["commit"], why=why)
            ctx.refresh(slug)
            ctx.act(f"{slug}: live on the test server")

    def ship(self, ctx, slug, ch):
        """The train takes what the fork has: a handed-over, unheld change whose commit is the tip of its fork branch."""
        if ch.stage not in ("gate", "contribute", "review") or ch.hold:
            return
        if ctx.obs.branch_tip("fork", ch.get("branch")) != ch.get("commit"):
            return
        if ctx.obs.pin(ch.get("branch")) == ch.get("commit"):
            return   # integration already carries this commit: no train
        if ctx.dry_run:
            ctx.act(f"{slug}: would join the train queue [dry run]")
            return
        from ... import batches
        if batches.enqueue(ch):
            ctx.act(f"{slug}: queued for the next train")

    def step(self, ctx):
        if ctx.dry_run:
            return
        from . import review
        for slug in review.file(ctx.idx, ctx.obs):
            ctx.act(f"{slug}: maintainer finding filed")
        ctx.refresh()

    def needs_you(self, ch, obs, idx):
        from . import cards
        out = []
        if ch.get("finding") and ch.get("upstream_pr") and ch.stage in ("ready", "dev", "gate", "contribute"):
            card = cards.draft(ch, obs)
            if card:
                out.append(card)
        if ch.stage == "contribute" and ch.get("commit") and not ch.hold and qa.gate_state(ch)[0]:
            out.append(cards.contribution(ch, obs))
        return out

    # --- hand-over, briefs, runs --------------------------------------------------------------------------------------

    def check_items(self, ch, obs, ev, files):
        out = []
        ok = lambda t: out.append((True, t))
        fail = lambda t: out.append((False, t))
        branch, commit = ch["branch"], ch["commit"]
        if files:
            ok(f"evidence dir {ev} ({len(files)} files)")
        else:
            fail(f"evidence dir {ev} missing or empty")
        repo = ch.get("repo")
        tip = obs.branch_tip(repo or "fork", branch)
        where = repo or "the fork"
        if tip is None:
            fail(f"no branch {branch} in {where}")
        elif tip != commit:
            fail(f"{branch} in {where} is at {tip[:9]}, not {commit[:9]}")
        else:
            ok(f"{branch} in {where} is at the commit")
        local = branch.startswith("local/") or ch.get("local_only")
        spec = [f for f in files if f.startswith("accuracy") and f.endswith(".md")]
        found = next((n for n in (ch.get("spec"), branch.split("/", 1)[-1], ch["slug"])
                      if n and obs.docs_file(f"accuracy/{n}.md") is not None), None)
        if spec or found:
            ok("accuracy spec " + (spec[0] if spec else f"accuracy/{found}.md on docs"))
        elif local:
            ok("local/* branch: no accuracy spec needed (never upstream)")
        else:
            fail(f"no accuracy spec ({ev}/accuracy*.md, or accuracy/{ch.get('spec') or branch.split('/', 1)[-1]}.md on docs)")
        if local:
            ok("local/* branch: no PR text needed")
        else:
            slug = branch.split("/", 1)[-1]
            title = "pr-title.txt" in files or obs.docs_file(f"pr-texts/{slug}.title") is not None
            body = "pr-body.md" in files or obs.docs_file(f"pr-texts/{slug}.upstream.body") is not None
            (ok if title and body else fail)("PR text present" if title and body
                                             else f"PR text missing ({ev}/pr-title.txt and pr-body.md, or pr-texts/{slug}.* on docs)")
        return out

    def brief(self, ch, stage):
        slug, branch = ch["slug"], ch.get("branch") or "<branch>"
        from ...agents import HD
        if stage == "dev":
            lines = ["QA then aggregates its checks of the exact commit onto the user's approval card. Definition of done, always (BR-C3): the accuracy spec (accuracy*.md) and the PR text (pr-title.txt, "
                     "pr-body.md) in the evidence dir; one change only, off current upstream main; the diff self-checked "
                     "against upstream AGENTS.md and CONTRIBUTING before the hand-over (no added comments, no tests unless "
                     "a rule has several cases or a reviewer asked). A review fix commits on top of the PR head and "
                     "replies to the finding in pr-comment.md."]
            verdict, findings = qa.gate_state(ch)
            if verdict == "FAIL":
                lines += ["QA findings at your head (fix all of them; the fix is a new commit on the SAME branch, BR-C2):"] + \
                    [f"  - {f}" for f in findings]
            return lines
        ev = os.path.join(evidence_dir(), slug)
        return [f"Stage `gate` (QA aggregate): check `{branch}` at exactly `{ch.get('commit')}` and collect EVERY finding "
                "before you report: they go on the user's approval card, which is the only gate. A finding blocks and "
                "re-dispatches nothing; the user decides.",
                f"  1. `{HD} gate-ci {slug}`: the commit (read from the dev's clone {ch.get('repo') or '(the fork clone)'}) merged "
                "with current upstream main in a scratch clone, pushed to the fork's gate/<slug> branch, CI observed, the diff "
                f"scanned; the result lands in {ev}/gate-ci.json (findings included). It resumes when re-run.",
                "  2. accuracy against the spec and sources, formatting (spotless) of the scratch merge, scope (one change, no "
                "stacking, no test file, no docs of ours), upstream AGENTS.md and CONTRIBUTING style (no added comments or "
                "tests), the PR text, gameval ids, and the change in game on your own client.",
                f"  3. write {ev}/gate.md (the role file has the format): the commit line, a `- Tests: <modules>; CI run <id>` line, one `- accuracy|ci|format|scope|style|"
                "text|ingame: PASS|FAIL|N/A reason` line each, `## Gate: **PASS|FAIL**` (PASS only with no failed check), "
                "`## Findings` listing all of them, evidence links.",
                f"  4. `{HD} gate {slug} PASS|FAIL \"note\"`: it checks the record against the commit and the CI result. "
                "You never write the code you check."]

    def run_valid(self, run, ch):
        """Why a QA run no longer applies: the change left `gate`, its commit moved, or the record exists."""
        if ch.stage != "gate":
            return f"change at {ch.stage}"
        if run.get("commit") and not same_commit(run["commit"], ch.get("commit")):
            return f"commit moved to {str(ch.get('commit'))[:9]}"
        if qa.gate_state(ch)[0] or ch.hold:
            return "gate recorded" if not ch.hold else f"hold {ch.hold}"
        return None

    def record_gate(self, ch, verdict, note):
        """`hd gate`: accept QA's record for `verdict` at the change's commit, or say why not; no stage, no hold."""
        import sys
        text = qa._read(qa.record_path(ch))
        problems = qa.record_problems(text, ch.get("commit") or "", verdict, qa.read_ci(ch))
        if problems:
            sys.exit(f"hd: the gate record cannot stand for {verdict} at {str(ch.get('commit'))[:9]}:\n  - " + "\n  - ".join(problems))
        findings = qa.findings_of(text)
        store.add_log(ch, f"QA aggregate {verdict} at {str(ch['commit'])[:9]} ({len(findings)} finding(s)): {note or ''}")
        events.emit("gate", change=ch["slug"], commit=ch["commit"], result=verdict, findings=len(findings))
        ch["owner"] = None
        store.save(ch)

    # --- commands -----------------------------------------------------------------------------------------------------

    def register(self, sp):
        s = sp.add_parser("gate-ci")
        s.add_argument("slug")
        s.add_argument("--no-wait", action="store_true")
        s.set_defaults(f=self.cmd_gate_ci)
        s = sp.add_parser("contribute")
        s.add_argument("slug")
        s.add_argument("--approved", required=True, help="the commit the user approved in chat")
        s.add_argument("--no-wait", action="store_true")
        s.set_defaults(f=self.cmd_contribute)

    def _run(self, a, fn, **kw):
        import sys
        from .. import Observer
        from . import contribute, gateci
        if not store.exists(a.slug):
            sys.exit(f"hd: no change {a.slug}")
        ch = store.load(a.slug)
        rc, lines = fn(ch, Observer(), **kw)
        print("\n".join(lines))
        return rc

    def cmd_gate_ci(self, a):
        from . import gateci
        return self._run(a, gateci.run, wait=not a.no_wait)

    def cmd_contribute(self, a):
        from . import contribute
        return self._run(a, lambda ch, obs, **kw: contribute.run(ch, obs, a.approved, **kw), wait=not a.no_wait)


TRACK = ServerTrack()
