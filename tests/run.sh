#!/usr/bin/env bash
# The harness tests (hd core, batches, hooks, live rules). No network, no devices; temp repos and stores only.
#   tools/harness/tests/run.sh [unittest args]
cd "$(dirname "$0")/../../.." && exec python3 -m unittest discover -s tools/harness/tests -v "$@"
