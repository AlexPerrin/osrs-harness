"""The hand-over check: run by `hd handover` itself, which refuses an incomplete hand-over (nothing is recorded, the
dev fixes the items in its own run). Deterministic, on evidence that exists; it checks the claims a hand-over makes,
never the feature (the gate does that). Every item is (ok, text); the hand-over stands when all are ok.

Every track: branch and commit set; definition of done all ticked; then the track's own items
(`track.check_items`, hd/tracks/): where the commit lives, the evidence dir and what it must hold."""
import os

from . import evidence_dir, tracks


def items(ch, obs):
    out = []
    branch, commit = ch.get("branch"), ch.get("commit")
    if not (branch and commit):
        return [(False, "branch or commit missing")]
    out.append((True, f"branch {branch} at {commit[:9]}"))
    unticked = ch.dod_unticked()
    out.append((False, f"definition of done has {len(unticked)} unticked item(s)") if unticked
               else (True, "definition of done ticked"))
    ev = ch.get("evidence") or os.path.join(evidence_dir(), ch["slug"])
    return out + tracks.of(ch).check_items(ch, obs, ev, obs.evidence_files(ev))


def run(ch, obs):
    """(passed, items): passed is True when every item is ok."""
    its = items(ch, obs)
    return all(o for o, _ in its), its


def render(ch, its):
    lines = [f"check {ch['slug']} ({ch.get('track')}) {ch.get('branch')}@{str(ch.get('commit') or '')[:9]}"]
    for o, t in its:
        lines.append(f"  {'OK  ' if o else 'FAIL'} {t}")
    fails = sum(1 for o, _ in its if not o)
    lines.append(f"FAIL ({fails})" if fails else "PASS")
    return "\n".join(lines)
