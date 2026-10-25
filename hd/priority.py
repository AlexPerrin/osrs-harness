"""Cross-track priority (BR-C5), recomputed from facts every tick, never stored. One order for every track:

  1. a change that settles work already in front of an external party (the track says so: `settles_first`) outranks
     the rest while policy `settle_first` is true
  2. effective priority: the highest priority (lowest P-number) of the change itself and of every unfinished change that
     lists it as a dep while it is not live (`hd block --by` adds the edge); transitive
  3. age (created)"""
from . import policy, tracks


def dependents(slug, idx):
    """The unfinished changes that name `slug` in their deps."""
    return [d for d in idx.values() if slug in (d.get("deps") or []) and d.stage != d.terminal]


def effective(ch, idx, _path=()):
    """The priority order number (lower first) of `ch`: its own, or that of the changes waiting on it."""
    best = policy.prio_order(ch.get("prio"))
    if ch.reached("live") or ch["slug"] in _path:
        return best
    for d in dependents(ch["slug"], idx):
        best = min(best, effective(d, idx, _path + (ch["slug"],)))
    return best


def rank(ch, idx):
    settle = policy.get().get("settle_first") and tracks.of(ch).settles_first(ch)
    return (0 if settle else 1, effective(ch, idx), ch.get("created") or "")
