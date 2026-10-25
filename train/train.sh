#!/usr/bin/env bash
# train/train.sh: the one long process (ARCHITECTURE 7), started by the pass, rerun from the start after any stop.
#   rebuild  `integration` = upstream main + every pinned branch (the fork's scripts/build-integration.sh on
#            local/integration-tools; git rerere replays recorded resolutions), pushed to the fork with a lease
#   gate     qa.sh clone + qa.sh gate of the integration commit
#   image    train/image.sh: the deploy image, keys from the live image only, boot checked
#   deploy   train/deploy.sh: rollback tag, compose up, "Server ready in" or roll back; then live.json
# train.json: {pid, start, step, tools, integration, failed_step, detail, ended}. A fault the integrator must resolve
# sets failed_step (the pass lists the integrator while the tools branch has not moved); any other stop only sets
# ended, and the pass starts the train again. One at a time: flock on the integration dir.
# Env: HD_STATE (required), HD_FORK (~/src/OpenRune-Server), HD_WORK (~/src/openrune-work), HD_QA_SH.
set -uo pipefail
STATE=${HD_STATE:?HD_STATE}
FORK=${HD_FORK:-$HOME/src/OpenRune-Server}
WORK=${HD_WORK:-$HOME/src/openrune-work}
QA=${HD_QA_SH:-$WORK/server-tools/upstream/qa/qa.sh}
HERE=$(cd "$(dirname "$0")" && pwd)
BUILD=$WORK/integration/build
TOOLS=local/integration-tools
mkdir -p "$WORK/integration"
exec 9>"$WORK/integration/.lock"
flock -n 9 || exit 0

j() { python3 -I -c '
import json, os, sys
p = sys.argv[1]
try:
    d = json.load(open(p))
except Exception:
    d = {}
for kv in sys.argv[2:]:
    k, v = kv.split("=", 1)
    d[k] = None if v == "null" else v
json.dump(d, open(p + ".tmp", "w"), indent=1, sort_keys=True)
os.replace(p + ".tmp", p)' "$STATE/train.json" "$@"; }
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
fail() { j failed_step="$1" detail="$2" ended="$(now)"; echo "train: $1 failed: $2" >&2; exit 1; }
stop() { j detail="$1" ended="$(now)"; echo "train: stopped: $1" >&2; exit 1; }
tail_of() { tail -n 15 "$1" 2>/dev/null | tr '\n' ' ' | cut -c1-1500; }

start=$(python3 -I -c "print(open('/proc/$$/stat').read().rsplit(')',1)[1].split()[19])")
rm -f "$STATE/train.json"
j pid="$$" start="$start" step=rebuild failed_step=null ended=null detail= integration=
git -C "$FORK" fetch -q --prune fork || stop "fetch of the fork failed"
git -C "$FORK" fetch -q origin main || stop "fetch of upstream main failed"
tools=$(git -C "$FORK" rev-parse "fork/$TOOLS") || stop "no fork/$TOOLS"
lease=$(git -C "$FORK" rev-parse -q --verify fork/integration || true)
j tools="$tools"

# rebuild
if [ ! -d "$BUILD/.git" ] && [ ! -f "$BUILD/.git" ]; then
    git -C "$FORK" worktree add -q --detach "$BUILD" origin/main || stop "cannot add the build worktree"
fi
git -C "$BUILD" merge --abort >/dev/null 2>&1 || true
git -C "$BUILD" reset -q --hard && git -C "$BUILD" checkout -q --detach origin/main || stop "cannot reset the build worktree"
script=$(mktemp)
git -C "$FORK" show "$tools:scripts/build-integration.sh" > "$script" || stop "no build-integration.sh on $TOOLS"
# build-integration.sh merges <remote>/main and the pinned <remote>/<branch> refs: fork/main must be upstream main.
git -C "$FORK" push -q fork origin/main:refs/heads/main 2>/dev/null || true
log=$STATE/train-rebuild.log
if ! (cd "$BUILD" && sh "$script" fork) >"$log" 2>&1; then
    rm -f "$script"
    fail rebuild "build-integration: $(tail_of "$log")"
fi
rm -f "$script"
sha=$(git -C "$BUILD" rev-parse HEAD)
j integration="$sha" step=gate
if [ -n "$lease" ]; then
    git -C "$BUILD" push -q "--force-with-lease=integration:$lease" fork "HEAD:refs/heads/integration" || stop "lease push of integration refused"
else
    git -C "$BUILD" push -q fork "HEAD:refs/heads/integration" || stop "push of integration refused"
fi

# gate
export QA_ROOT=$WORK/qa
dir=$QA_ROOT/integration-${sha:0:9}
[ -d "$dir" ] || "$QA" clone integration "$sha" >"$STATE/train-gate.log" 2>&1 || fail gate "qa.sh clone: $(tail_of "$STATE/train-gate.log")"
"$QA" gate "$dir" >>"$STATE/train-gate.log" 2>&1
grep -q 'rc=0$' "$dir.logs/summary" 2>/dev/null || fail gate "qa.sh gate: $(tail -n1 "$dir.logs/summary" 2>/dev/null) $(tail_of "$STATE/train-gate.log")"
j step=image

# image
HD_STATE_DIR=$STATE "$HERE/image.sh" "$dir" "$sha" >"$STATE/train-image.log" 2>&1 || fail image "image.sh: $(tail_of "$STATE/train-image.log")"
j step=deploy

# deploy
HD_STATE_DIR=$STATE "$HERE/deploy.sh" "$sha" >"$STATE/train-deploy.log" 2>&1 || fail deploy "deploy.sh: $(tail_of "$STATE/train-deploy.log")"
python3 -I - "$STATE" "$sha" "$(git -C "$FORK" rev-parse origin/main)" <<'EOF'
import json, sys
state, sha, main = sys.argv[1:4]
dep = json.load(open(f"{state}/deploys/{sha[:7]}.json"))
json.dump({"integration": sha, "image": dep["image"], "rollback": dep["rollback_tag"], "upstream_main": main,
           "since": dep.get("since")}, open(f"{state}/live.json", "w"), indent=1, sort_keys=True)
EOF
j step=done ended="$(now)"
echo "train: live $sha"
