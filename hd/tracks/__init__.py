"""The tracks (client, server, harness) behind one narrow interface. The core (store, stages, tick, agents, actions,
drive, cli, batches) orchestrates between them: changes, deps and priority, capacity, dispatch, holds, run bookkeeping,
the console driver. Everything a track does by itself lives in its module and is reached only through
`tracks.of(change)` / `tracks.get(name)`; the core never imports a track's internals.

  client    hd/tracks/client.py     master contains the commit (evidence checks); releases stay in the core for now
  harness   hd/tracks/harness.py    this repo's main contains the commit
  server    hd/tracks/server/       dev -> QA aggregate -> approval -> contribution -> review -> merged: the PR bucket and
                                    its GitHub observer, the CI-equivalence table, QA's record, the approval card,
                                    `hd contribute`, the maintainer-finding filer, the scratch-branch gate CI, the hook
                                    logic; settings in policy `tracks.server`
Settings of a track live in its own policy section (`tracks.<name>`).

A track is an object with these methods (defaults in `base.BaseTrack`):
  chain(ch)                 the stages the change moves through, `backlog ... terminal`
  tip(ch, obs)              (branch tip, where it was read): where the change's commit lives
  open_stages(ch)           the stages in which the handed-over commit can still be replaced (BR-C2)
  moves_expected(ch)        the branch tip moving on is normal (a change handed over on its live target)
  facts(ch, obs)            {stage: (met True|False|None, why)} for the stages after `gate`, plus `live` and `tip`
  waiting(stage, ch)        the words for what the change waits on at `stage`
  executor(ch)              `gate` when the track's verifier must run now, else None (the core books `dev`)
  finding_set(ch)           the findings a dev run would be given (part of the no-loop booking key)
  reconcile(ctx, slug, ch)  per change, each tick, after the stage is derived
  ship(ctx, slug, ch)       per handed-over change, each tick: the track's merge or queue step
  step(ctx)                 once per tick: the track's own work (findings, ...)
  needs_you(ch, obs, idx)   the track's items for the user: cards with exact commands, from observed facts alone
  check_items(ch, obs, ev, files)  [(ok, text)] the hand-over check items beyond the common ones
  brief(ch, stage)          lines the agent's brief adds for `dev` or `gate`
  run_valid(run, ch)        why a booked run no longer applies (None while it does)
  default_dod(spec)         the definition of done `hd new --server-dod` writes
  migrate_stage(meta)       the current stage for a recorded one of a retired chain
  record_gate(ch, verdict, note)  `hd gate`: accept the track's verifier record, or exit with why
  records_repo              `hd handover --repo` is kept on the change
  register(subparsers)      the track's own `hd` subcommands
  keys                      front-matter keys the track adds to a change

`tracks.Observer` and `tracks.FakeObserver` are the core observers with the tracks' observation mixins; the core
constructs only these.
"""
import importlib

NAMES = ("client", "harness", "server")
_cache = {}


def get(name):
    name = name if name in NAMES else "client"
    if name not in _cache:
        _cache[name] = importlib.import_module(f"{__name__}.{name}").TRACK
    return _cache[name]


def of(ch):
    return get((ch.get("track") if hasattr(ch, "get") else ch) or "client")


def every():
    return [get(n) for n in NAMES]


def extra_keys():
    return tuple(k for t in every() for k in t.keys)


def __getattr__(name):
    """`Observer` / `FakeObserver`: composed on first use (the server track's GitHub mixin needs the core observer)."""
    if name in ("Observer", "FakeObserver"):
        from .. import observe
        from .server.github import FakeGitHub, GitHub
        cls = type("Observer", (observe.Observer, GitHub), {}) if name == "Observer" else \
            type("FakeObserver", (observe.FakeObserver, FakeGitHub), {})
        globals()[name] = cls
        return cls
    raise AttributeError(name)
