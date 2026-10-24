"""The harness track: this repo. A change is live when this repo's `main` contains its commit; the daemon merges a
`harness/<slug>` branch into main locally (never pushed). Branches and the target are read in this repo (observer repo
`harness`); a change handed over on `main` itself passes while main contains the commit."""
from .target import TargetTrack


class HarnessTrack(TargetTrack):
    name = "harness"

    def repo_name(self, ch):
        return "harness"

    def default_repo(self):
        from .. import HD_HOME
        return HD_HOME


TRACK = HarnessTrack()
