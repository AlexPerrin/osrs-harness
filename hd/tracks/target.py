"""The shared shape of the client and harness tracks: a change is done when its live target (client: `master` of the
client repo; harness: `main` of this repo, policy `live_target`) contains the commit. The daemon merges a handed-over
change into the target (`hd/ship.py`); a change handed over on the target itself needs only the target to contain it.

Hand-over check (beyond the common items): the branch is at the commit, the commit is not on the target yet, and, unless
the change is docs-only (every file since the merge base is *.md), evidence in the evidence dir; the client track adds
its build evidence (`build_evidence`)."""
import fnmatch

from .. import policy, ship
from .base import BaseTrack


class TargetTrack(BaseTrack):
    def repo_name(self, ch):
        return "ours"

    def moves_expected(self, ch):
        return ch.get("branch") == self.live_target()

    def facts(self, ch, obs):
        commit = ch.get("commit")
        tip, where = self.tip(ch, obs)
        out = {"tip": (tip, f"{where}/{ch['branch']} at {tip[:9]}" if tip else f"{where}/{ch['branch']} not found")}
        target = self.live_target()
        met = obs.contains(self.repo_name(ch), target, commit)
        out["live"] = (met, f"{target} {'contains' if met else 'does not contain'} {commit[:9]}" if met is not None
                       else f"could not read {target}")
        return out

    def waiting(self, stage, ch):
        return f"the merge into {self.live_target()}" if stage == "gate" else ""

    def ship(self, ctx, slug, ch):
        from .. import events, store
        if ch.stage != "gate" or ch.hold:
            return
        if ctx.dry_run:
            ctx.act(f"{slug}: would merge into {self.live_target()} [dry run]")
            return
        ok, msg = ship.merge_to_master(ch)
        store.add_log(ch, f"ship: {msg}")
        if not ok:
            store.set_hold(ch, "exception", f"ship: {msg}")
            events.emit("hold", change=slug, hold="exception", reason=msg)
        store.save(ch)
        ctx.refresh(slug)
        ctx.act(f"{slug}: {msg}")

    def check_items(self, ch, obs, ev, files):
        out = []
        ok = lambda t: out.append((True, t))
        fail = lambda t: out.append((False, t))
        branch, commit = ch["branch"], ch["commit"]
        repo, target = self.repo_name(ch), self.live_target()
        tip = obs.branch_tip(repo, branch)
        if tip is None:
            fail(f"no local branch {branch}")
        elif self.moves_expected(ch):
            held = obs.contains(repo, branch, commit)
            (ok if held else fail)(f"{branch} contains the commit" if held else f"{branch} does not contain {commit[:9]}")
        elif tip != commit:
            fail(f"branch {branch} is at {tip[:9]}, not {commit[:9]}")
        else:
            ok("branch is at the commit")
        on_target = obs.contains(repo, target, commit)
        if on_target and self.moves_expected(ch):
            ok(f"commit already on {target} (handed over on {target}; the daemon has nothing to merge)")
        elif on_target:
            fail(f"commit already on {target}")
        elif on_target is False:
            ok(f"not yet on {target}")
        else:
            fail(f"could not read {target}")
        mb = obs.merge_base(repo, target, commit)
        changed = obs.changed_files(repo, mb, commit) if mb else None
        if bool(changed) and all(f.endswith(".md") for f in changed):
            ok(f"docs-only change ({len(changed)} markdown files): no build or device evidence needed")
            return out
        if files:
            ok(f"evidence dir {ev} ({len(files)} files)")
        else:
            fail(f"evidence dir {ev} missing or empty")
        out += self.build_evidence(ch, obs, ev, files)
        return out

    def build_evidence(self, ch, obs, ev, files):
        return []


def match(name, pattern):
    return fnmatch.fnmatch(name, pattern)
