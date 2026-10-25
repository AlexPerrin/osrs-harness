---
slug: hd-measure-numeric
track: harness
kind: change
title: hd measure stores the value as a number, so the measure step can compare it
  with the target
priority: P1
deps: []
created: '2026-10-25T13:57:59Z'
goal: client-api
---
## Change
`hd measure` saves argparse's string (hd/cli.py:161, `{"value": a.value, ...}`) while the goal's target is the YAML int
(harness/goals/client-api.md `target: 100`). Once no change serves the goal, `_measure_done` (hd/steps.py:419,
`(m.get("value") or 0) >= goal["target"]`) evaluates `'76.3' >= 100` and raises TypeError, so `hd`/`hd tick` fail on
the first real measurement. tests/test_hd.py:28 saves an int directly and :38 checks only the base, so the suite
misses it. Parse the value as a number in `hd measure` (refuse a non-number) and store it as one.

## Definition of done
- A test runs `cli.main(["measure", "client-api", "42.5", "--evidence", rep])` and asserts the stored value is the
  number 42.5 and that the measure step then reports not done (below target) without raising; a second asserts
  `hd measure client-api abc ...` is refused and stores nothing.
- `python3 -m unittest discover -s tests` passes.
