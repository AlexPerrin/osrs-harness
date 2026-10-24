"""Defaults of the track interface (hd/tracks/__init__.py): a track overrides what differs."""
import os

from .. import policy


class BaseTrack:
    name = ""
    keys = ()
    records_repo = False   # `hd handover --repo` is recorded on the change (the commit lives in a dev's clone)
    CHAIN = ("backlog", "ready", "dev", "gate", "live")

    def chain(self, ch):
        return self.CHAIN

    def repo_name(self, ch):
        """The observer's name for the repo the branch lives in."""
        return "ours"

    def tip(self, ch, obs):
        repo = ch.get("repo") or self.repo_name(ch)
        return obs.branch_tip(repo, ch["branch"]), repo

    def default_repo(self):
        """Where `hd handover` looks for the commit without --repo."""
        from .. import ROOT
        return ROOT

    def open_stages(self, ch):
        """The stages in which the handed-over commit can still be replaced: a branch that moved past it re-enters at ready."""
        return ("ready", "dev", "gate")

    def moves_expected(self, ch):
        return False

    def live_target(self):
        return policy.live_target(self.name)

    def facts(self, ch, obs):
        return {}

    def waiting(self, stage, ch):
        return ""

    def executor(self, ch):
        return None

    def finding_set(self, ch):
        return []

    def reconcile(self, ctx, slug, ch):
        pass

    def ship(self, ctx, slug, ch):
        pass

    def step(self, ctx):
        pass

    def needs_you(self, ch, obs, idx):
        return []

    def check_items(self, ch, obs, ev, files):
        return []

    def brief(self, ch, stage):
        return []

    def run_valid(self, run, ch):
        return None

    def default_dod(self, spec):
        return []

    def migrate_stage(self, meta):
        """The current stage for a recorded one of a retired chain."""
        stage = meta.get("stage") or "backlog"
        return {"checked": "gate"}.get(stage, stage)

    def record_gate(self, ch, verdict, note):
        import sys
        sys.exit(f"hd: the {self.name} track has no gate record; a release gate is a batch")

    def register(self, sp):
        pass


def evidence_path(ch):
    """The change's evidence dir as an absolute path."""
    from .. import ROOT, evidence_dir
    ev = ch.get("evidence") or os.path.join(evidence_dir(), ch["slug"])
    return ev if os.path.isabs(ev) else os.path.join(ROOT, ev)
