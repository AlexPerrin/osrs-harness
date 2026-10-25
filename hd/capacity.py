"""Capacity classes (BR-R5): the machine budget as data. Policy `capacity` names each class and its slots; a role
declares the classes it uses (`agents.roles.<role>.uses`), a batch step likewise (`batches.uses.<step>`). Dispatch books
a run only while every class the role uses has a free slot; the wait is for a slot, never for a lock. Usage is counted
from facts: runs not ended and batches at a step that uses a class."""
import collections

from . import policy


def limits():
    return policy.get().get("capacity", {})


def used(running, open_batches=()):
    """{class: slots in use} by the running agents and the batches at a step that uses a class."""
    n = collections.Counter()
    for r in running:
        n.update(policy.role(r["role"]).get("uses", []))
    steps = policy.get().get("batches", {}).get("uses", {})
    for b in open_batches:
        n.update(steps.get(b.get("step"), []))
    return n


def full(role, running, open_batches=()):
    """The first class `role` uses that has no free slot, or None when the role fits."""
    n, cap = used(running, open_batches), limits()
    return next((c for c in policy.role(role).get("uses", []) if n[c] >= cap[c]), None)
