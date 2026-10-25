"""QA's aggregate of a server change: a local record in the change's evidence dir, bound to the commit (BR-S7).

`gate.md` (the record, written by server-qa) and `gate-ci.json` (`hd gate-ci`'s result for the scratch merge):

    # Gate: <branch>
    - Branch: `<branch>`
    - Commit: `<full sha>`
    - Tests: <modules whose tests ran>; CI run <id of the fork CI run covering the full suite>
    ## Gate: **PASS**|**FAIL**       PASS only with no failed check and no finding
    ## Checks                          one `- <check>: PASS|FAIL|N/A <note>` line each of REQUIRED_CHECKS
    ## Findings                        every finding, or `- none`

The record decides nothing by itself: its verdict and findings go on the user's approval card. `hd gate` accepts it
only when `record_problems` is empty; a new commit voids it (the commit is the key)."""
import json
import os
import re

from ...util import same_commit
from ..base import evidence_path

RECORD_FILE = "gate.md"
CI_FILE = "gate-ci.json"
RECORD_COMMIT = re.compile(r"^- Commit: `([0-9a-f]{7,40})`", re.M)
RECORD_TESTS = re.compile(r"^- Tests: (\S.*)$", re.M)
RECORD_VERDICT = re.compile(r"^## Gate: \*\*(PASS|FAIL)\*\*", re.M)
RECORD_CHECK = re.compile(r"^- (accuracy|ci|format|scope|style|text|ingame): (PASS|FAIL|N/A)\b(.*)$", re.M)
REQUIRED_CHECKS = ("accuracy", "ci", "format", "scope", "style", "text", "ingame")


def _read(p):
    try:
        with open(p, errors="replace") as f:
            return f.read()
    except OSError:
        return None


def record_path(ch):
    return os.path.join(evidence_path(ch), RECORD_FILE)


def findings_of(text):
    """The bullets under `## Findings` of a record."""
    out, inside = [], False
    for line in (text or "").splitlines():
        if line.startswith("## "):
            inside = line.strip().lower() == "## findings"
        elif inside and line.startswith("- ") and line[2:].strip().lower() not in ("none", "(none)"):
            out.append(line[2:].strip())
    return out


def parse_record(text):
    """{commit, tests, verdict, checks: {name: (result, note)}, findings} of a record text, or None without a commit line."""
    mc = RECORD_COMMIT.search(text or "")
    if not mc:
        return None
    mv = RECORD_VERDICT.search(text)
    mt = RECORD_TESTS.search(text)
    return {"commit": mc.group(1), "tests": mt.group(1).strip() if mt else None, "verdict": mv.group(1) if mv else None,
            "checks": {m.group(1): (m.group(2), m.group(3).strip(" :-")) for m in RECORD_CHECK.finditer(text)},
            "findings": findings_of(text)}


def read_record(ch):
    return parse_record(_read(record_path(ch)))


def read_ci(ch):
    """`gate-ci.json` ({commit, upstream_main, scratch, result, url, findings}) or {}."""
    try:
        return json.loads(_read(os.path.join(evidence_path(ch), CI_FILE)) or "{}")
    except ValueError:
        return {}


def gate_state(ch):
    """(verdict, findings) of the record at the change's commit: ('PASS'|'FAIL', [...]), or (None, []) when no record is
    bound to this commit."""
    rec = read_record(ch)
    if not rec or not same_commit(rec["commit"], ch.get("commit")):
        return None, []
    return rec["verdict"], rec["findings"]


def record_problems(text, commit, verdict, ci=None):
    """Why a record cannot stand for `verdict` at `commit` (the `hd gate` check): every item at once."""
    rec = parse_record(text)
    if not rec:
        return [f"no gate record with a `- Commit:` line at {RECORD_FILE}"]
    out = []
    if not same_commit(rec["commit"], commit):
        out.append(f"the record is for {rec['commit'][:9]}, the change is at {commit[:9]}")
    if rec["verdict"] != verdict:
        out.append(f"the record's verdict line is {rec['verdict'] or 'missing'}, not {verdict}")
    if not rec["tests"]:
        out.append("no `- Tests: <modules>; CI run <id>` line (the modules whose tests ran, the CI run covering the full suite)")
    missing = [c for c in REQUIRED_CHECKS if c not in rec["checks"]]
    if missing:
        out.append("missing check lines: " + ", ".join(f"`- {c}: PASS|FAIL|N/A reason`" for c in missing))
    failed = [c for c, (r, _) in rec["checks"].items() if r == "FAIL"]
    if verdict == "PASS":
        if failed:
            out.append("PASS with failed checks: " + ", ".join(failed))
        if rec["findings"]:
            out.append(f"PASS with {len(rec['findings'])} finding(s)")
        if not ((ci or {}).get("result") == "success" and same_commit((ci or {}).get("commit"), commit)):
            out.append(f"no green CI result for this commit in {CI_FILE} (run `hd gate-ci <slug>`)")
    elif not rec["findings"]:
        out.append("FAIL without a finding under `## Findings`")
    return out
