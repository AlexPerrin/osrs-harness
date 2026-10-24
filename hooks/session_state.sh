#!/usr/bin/env bash
# SessionStart hook (matcher "compact"): after a compaction, print the state the console works from, so it
# is rebuilt from disk rather than from the summary (docs/ARCHITECTURE.md). Read-only, and
# short: the harness status, runs, instances and the build queue, with pointers to the STATE docs instead of
# their text (read them when a task needs them).
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" || exit 0
echo "# State after compaction (tools/hooks/session_state.sh)"
echo; echo "## Harness"; python3 ~/osrs-harness/hd.py status 2>&1
echo; echo "## This repo"; git log --oneline -5
echo; echo "Read when needed: docs/client-state.md,"
echo "the fork's STATE.md (git -C ~/src/OpenRune-Server show fork/docs:STATE.md), `hd drive` for what needs the console."
exit 0
