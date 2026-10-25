# Requirements

What a solution to docs/PROBLEM.md must satisfy. Each requirement has an id (R-n) that code and tests cite, is
testable, and serves a goal: **U** unattended, **H** heals, **L** legible, **P** product rule. A *fact* is read from git,
GitHub, docker, the process table, or a record written by its owner through a checked `hd` command. The mechanism for
each is in docs/ARCHITECTURE.md.

| Id | Requirement | Goal |
|---|---|---|
| R1 | **State is derived.** Stage, liveness, dispatch, cards, questions, alerts and each goal's progress are computed from facts on every read. Stored: definitions (committed), records, locks, the train, the event log. State and evidence are never committed; the harness commits only the merge of a harness change into `main`. | U L |
| R2 | **One owner per record, bound to a sha.** Dev: hand-over. QA: verdict. User: approval and answers. Hooks: run start, end, usage. A moved head voids the records about the old sha. An incomplete record is refused. | U |
| R3 | **Progress is the next unmet step.** Every action is idempotent and tests its own result first, so a re-run resumes. No decision reads the clock; a subprocess timeout is only a backstop for a hung tool. | U |
| R4 | **A run is alive iff it has no end record and its console is alive.** Hooks write start, end and token usage; the model records neither. A dead console ends its runs, frees their locks and makes their changes dispatchable. A run that stops without the record its change needs is blocked at stop; if it stops anyway (error, limit) its last message becomes a hold. | U H |
| R5 | **Only two actions need the user:** a write to OpenRune (open a PR, push to its head, comment, ready, draft) and a client release. Each runs only at a sha with an approval record, recorded by `hd approve` after the user's yes in chat, and only by the harness's own step, never an agent or the console. If CI is not green the sequence stops before the comment. No approval is offered before the verdict passed at that sha. The card shows exact commands, full text, every check line and finding. | P |
| R6 | **Owned by nothing alive means removed.** Each tick ends runs of dead consoles, reclaims locks of dead holders, removes containers, clones, worktrees and images with no live owner (keeping the live and rollback images), and reruns a train whose process died. Each repair is one event. What only the user can fix (Docker down, BlueStacks absent, `gh` unauthenticated, usage limit) is an alert, never a retry loop. | H |
| R7 | **Scarce things are locked or counted.** One train at a time. `ghidra` and `device` are locks bound to a run and free when it is not alive. Alive agents are bounded by one number. Client instances are the agent's own. | U |
| R8 | **Every write is an event; `hd` shows facts.** `events.jsonl` is append-only UTC and records records, runs with usage, locks, train and publish steps, repairs and denials. Times shown in US Eastern. A question an agent cannot answer is a hold with the question; the user is notified once per new card or question. | L |
| R9 | **A goal is a committed definition with a metric command and a target.** The command prints one number; `hd` shows it against the target for every open goal. Below target, the orchestrator role is dispatched; it reads the metric and the gap and files changes (with deps across tracks), writes no code, and files nothing beyond the free agent capacity. A met goal stays open as a guard: a metric that drops below target is a gap again. The client goal's metric is the share of RuneLite API interface methods a probe confirms working in the Android app. | U L |

Product rules are not harness requirements; agents get them from their role file and brief: the server QA checklist and
accuracy source order (skills `server-track`, `accuracy-check`), client hand-over contents and release gate
(`client-track`, `network-qa`), privacy and process hygiene (CLAUDE.md shared rules, enforced by the guard hook).

## Acceptance

1. A night with no user message in which the orchestrator filed changes toward an open goal, they were dispatched,
   handed over, trained, deployed and merged, the goal's metric rose, and the user returned to cards only.
2. Each fault repaired within a tick: console killed mid-run; tick killed mid-train; a lock whose holder is dead; an
   orphan container or clone; an approval given and the console killed before the publish finished (it completes).
3. A harness code change merged into `main` runs on the next tick without a restart.
4. No prompt reached the user for anything but R5 actions and R8 questions.
5. Non-test code ≤ 1 800 lines, tests ≤ 1 000, `hd.yaml` ≤ 30, every `hd` command has a caller.
