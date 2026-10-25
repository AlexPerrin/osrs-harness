# Harness v7 — proposal

A summary of docs/PROBLEM.md, docs/PRD.md and docs/ARCHITECTURE.md on this branch, for review. It adds what they do not
carry: what this iteration changed, what v7 removes, the build order, the assumptions to verify and the decisions for
you. v7 is written from zero; nothing of v6 is patched. This file is deleted when v7 is live.

## 1. Problem, as first principles

Ten axioms (A1–A10): outcomes with nobody watching; agents spawned only by a console that can vanish; words are not
evidence, artifacts are; two public actions need you; upstream's rules; live means "the target contains the commit";
things that exist once; time says nothing; the platform; privacy. Eight principles follow:

| | Principle |
|---|---|
| P1 | Facts decide; an unknown fact stops the step, it is never read as false |
| P2 | Store only what cannot be derived: definitions, judgments bound to commit and base, run starts and ends |
| P3 | Every step is idempotent: "done when" plus "do" |
| P4 | Nothing depends on a process: a timer, a console that only spawns, a train that reruns from pins |
| P5 | One authority: the harness alone writes to OpenRune or releases, at the approved commit, agents denied by default |
| P6 | Cheapest check first; nothing checked twice for the same commit and base |
| P7 | Scarce things are single-flight (kernel lock) or counted (one agent number) |
| P8 | The user sees derived facts only |

Goals: client **100% of the RuneLite API** working in the app; server: the client is never blocked and every contribution
is single-purpose and settled before the next; harness: simpler and faster each iteration.

## 2. Requirements, as constraints

Seven, each derived from the principles: R1 Goals, R2 Flow, R3 Integrity, R4 Authority, R5 Recovery, R6 Economy (new:
script before agent before user, nothing twice, one agent count), R7 Visibility. Checklists live in role files and skills.

## 3. Architecture, in one sentence

**A change is a list of steps; a step is "done when this fact holds" plus an action by a script, an agent or you; a
timer-run pass does the first unmet step of every change whose dependencies are live.** Stage, dispatch, cards, alerts,
publish, release, the train and repairs are all that one shape.

| List | Steps |
|---|---|
| client change, harness change | handover → gate → merge |
| client release | review → approve → release |
| server change | handover → gate, then independently: queue (test server) and review → approve → push → pr → ci → comment → ready → merged |
| server local | handover → gate → queue |
| goal | measure (the orchestrator measures, then files changes) |

Four modules (`store`, `facts`, `steps`, `tick`) plus `cli`, three gate scripts, one hook program, one train script; nine
commands; targets code ≤ 1 500 lines, tests ≤ 800, `hd.yaml` ≤ 25.

## 4. What this iteration changed from the previous proposal

| Before | Now | Why |
|---|---|---|
| a stage state machine, a dispatch function, publish steps, release steps, healing, each its own idea | one idea: step lists; repairs are steps too | fewer concepts |
| `ghidra` and `device` locks, `hd lock` | no harness locks: Ghidra and `buildq.sh` lock themselves; you ruled out device locking | P7, your decision |
| a `hold` record (agent asks, hook writes, user removes) | `ask.json` written by the agent; a run that ended without its record is a question derived from the run | one fewer record |
| `hd dod`, `hd cost`, `hd lock`, `hd hold` (12 commands) | nine; usage is read from runs, the definition of done is judged by the gate and the reviewer | fewer commands |
| a smoke test when a base moves | removed: the gate covers the change, the measurement guards the goal | no requirement |
| dispatch by priority, dependents, age | priority, then age (your decision); a no-loop rule: same `head` and definition never dispatch twice | fewer rules |
| guard denies listed write verbs | deny by default for OpenRune: only read verbs pass | the v6 audit found allowed writes |
| `pid_alive` by pid | pid with start time | recycled pids after a WSL restart |
| three hook files and a shell parser | one `hook.py`, three events | one program |
| a measurement per base move | the orchestrator measures when no open change serves the goal | fewer device runs |
| six requirements | seven: Economy made explicit | it drove most of the cuts above |

## 5. What v7 removes from v6

| v6 | v7 |
|---|---|
| stored stage, hold, owner, booking, cost, log in the committed change file | derived from facts and records; the harness commits nothing |
| the daemon, two tickers, restarts | one timer-run pass under `flock` |
| run link/end commands, lingering runs | two hook events |
| `hd contribute` sleep-poll; a publish process | one GitHub step per pass |
| the train as a ten-step state machine, `queue.json`, `repin.json` | one script rerun from the start; `git rerere` |
| five capacity classes, lease heartbeats, instance locks | one agent count |
| 20-method track interface, three track modules | step lists; server-only code in `gates/server.py` and `steps.py` |
| six hooks, two shell parsers | one hook program |
| 32 requirements, 68-line policy | seven; `hd.yaml` ≤ 25 |
| 7 172 lines, 4 463 of tests | ≤ 1 500 and ≤ 800 |

## 6. Build order (branch `v7`, new tree; v6 stays on `main` until cutover)

1. `hook.py` live: `SubagentStart` sees the prompt (fallback: bind at stop); deny-by-default guard; `git rerere` replays
   across two clones.
2. `store`, `facts`, `steps`, `tick`, `cli`; the client and harness lists; one harness change merged and pushed by the pass.
3. The server list: `gates/server.py`, `train.sh`, publish steps, finding filing.
4. The goal list: `hd measure`, the orchestrator role, the first client measurement.
5. Fault injection per R5; delete the v6 tree, tests, policy and docs; CLAUDE.md and HANDOFF rewritten; this file deleted.
6. Cutover on your yes: stop v6, `loginctl enable-linger alex`, enable the timer, merge `v7` into `main`.

## 7. Assumptions to confirm or overrule

1. The client probe is `tools/api-probe.sh` in the client repo and prints the percentage; it may not exist yet.
2. The orchestrator files changes freely within the agent count; P0 is reserved for review fixes.
3. Ghidra's own project lock is enough: two client-devs on `native/` wait on it, nothing in the harness serialises them.
4. A publish step lags up to a minute; a run that ends without its record waits for your answer rather than retrying.
5. `git rerere` works for the integrator's resolutions.
6. Evidence lives in `~/osrs-harness/evidence/<slug>/`; CLAUDE.md still names the client checkout and is rewritten at step 5.

## 8. For your decision

1. Accept the eight principles and the seven constraints?
2. Accept step lists as the one mechanism, with no harness locks and no hold record?
3. Is the probe an existing tool, or the first thing to build for the client goal?
4. Start build step 1 now?
