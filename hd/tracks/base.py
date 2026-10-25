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

    def settles_first(self, ch):
        """The change settles work already in front of an external party; policy `settle_first` ranks it first."""
        return False

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

    def checked_later(self, item):
        """A definition-of-done item a later step checks itself: it does not block the hand-over."""
        return False

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
    """The change's evidence dir as an absolute path: always the slug dir, where QA writes its records."""
    from .. import evidence_dir
    return os.path.join(evidence_dir(), ch["slug"])


def sync_evidence(ch):
    """Copy the files of a recorded evidence dir other than the slug dir into the slug dir (never overwriting)."""
    import shutil
    from .. import ROOT
    rec = ch.get("evidence")
    if not rec:
        return
    src = rec if os.path.isabs(rec) else os.path.join(ROOT, rec)
    dst = evidence_path(ch)
    if os.path.realpath(src) == os.path.realpath(dst) or not os.path.isdir(src):
        return
    os.makedirs(dst, exist_ok=True)
    for name in os.listdir(src):
        if not os.path.exists(os.path.join(dst, name)):
            if os.path.isdir(os.path.join(src, name)):
                shutil.copytree(os.path.join(src, name), os.path.join(dst, name))
            else:
                shutil.copy2(os.path.join(src, name), os.path.join(dst, name))
