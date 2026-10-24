"""The client track: RuneLite plugins in the official Android app. A change is live when the client repo's `master`
contains its commit. Build evidence at hand-over (policy `evidence`): a repack log with the policy's `telemetry:` lines,
device evidence (a logcat extract or a data-tool dump), and a `netqa*.md` record when the change touches networking.
The release flow (batches of live changes, the release gate and tag) is still the core's (batches.py, actions.py)."""
import os
import re

from .. import ROOT, policy
from .target import TargetTrack, match


class ClientTrack(TargetTrack):
    name = "client"

    def build_evidence(self, ch, obs, ev, files):
        out = []
        ok = lambda t: out.append((True, t))
        fail = lambda t: out.append((False, t))
        pol = policy.get().get("evidence", {})
        evp = ev if os.path.isabs(ev) else os.path.join(ROOT, ev)
        logs = [f for f in files if re.match(r"repack.*\.log$|.*repack.*\.txt$", f)]
        if logs:
            text = obs.read_file(os.path.join(evp, logs[0])) or ""
            n = len(re.findall(r"^telemetry:", text, re.M))
            want = int(pol.get("client_repack_telemetry_lines", 7))
            (ok if n == want else fail)(f"repack log {logs[0]}: {n} telemetry lines" + ("" if n == want else f", not {want}"))
        else:
            fail(f"no repack log in {ev} (copy the build's repack output there as repack.log)")
        pats = pol.get("client_device_evidence", ["*logcat*.txt"])
        hits = [f for p in pats for f in files if match(f, p)]
        (ok if hits else fail)("device evidence present: " + ", ".join(hits[:3]) if hits
                               else f"no device evidence ({', '.join(pats)}) in {ev}")
        if ch.get("network"):
            nq = [f for f in files if match(f, pol.get("client_network_report", "netqa*.md"))]
            (ok if nq else fail)("Network QA report present" if nq else f"network: true but {ev} has no netqa*.md")
        return out


TRACK = ClientTrack()
