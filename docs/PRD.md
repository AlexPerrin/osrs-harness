# Requirements

What a solution to docs/PROBLEM.md must satisfy. Each requirement has a stable id (R-n) that code and tests cite, is
testable, and traces to a goal: **U** unattended, **H** heals, **L** legible, **P** product rule. "Fact" means
something read from git, GitHub, docker, the process table, or a record written by its owner through a checked `hd`
command. docs/ARCHITECTURE.md names the mechanism that meets each.

## Facts, not records of records

| Id | Requirement | Goal |
|---|---|---|
| R1 | No stage, status or liveness is stored. Each is derived on every read from facts. The only stored things are definitions, the records of R3, locks, train and publish records, and the event log. | U H |
| R2 | No decision uses elapsed time. A step ends on its result or on the fact that the result cannot come (process exited, container exited, run ended). A subprocess timeout exists only as a backstop for a hung tool and is never read as a verdict. | U |
| R3 | One owner per record: dev → hand-over; QA → verdict; user → approval, answer; hooks → run start, run end, usage; train and publish processes → their steps. A record is bound to the commit it is about; a moved head voids it. | U |
| R4 | A change's definition (`harness/changes/<slug>.md`: slug, track, kind, title, priority, deps, branch when it differs from the rule, PR and finding ids, the spec, the definition of done) is committed. Nothing under `harness/state/` or `evidence/` is committed. The harness commits nothing of its own except the merge of a harness change into `main`. | L |
| R5 | Evidence lives in this repo at `evidence/<slug>/` (git-ignored). The client and server repos hold code and releases only. | L |

## Runs

| Id | Requirement | Goal |
|---|---|---|
| R6 | A run exists from the hook that sees the subagent start to the hook that sees it stop. Start records agent id, role, change, head and the console's pid; stop records exit, last message and token usage summed from the subagent transcript. The model never records either. | U L |
| R7 | A run is alive iff it has no end record and its console pid is alive. A dead console ends all its runs (`console-died`), frees their locks and makes their changes dispatchable again. | H |
| R8 | A run cannot stop with its change needing a record it did not write (hand-over, verdict, resolution, or a question); the stop hook blocks. A run that stops anyway (max turns, error) puts a hold on its change carrying its last message; the change is not dispatched again until the hold is answered. | U |
| R9 | Dispatch is a pure function of facts: candidates in priority (P0 first) then age order, minus changes with an alive run or a hold, up to the free slots of every capacity class the role uses. Nothing is booked ahead; the list is recomputed on every call. | U |
| R10 | A role's brief is generated from the definition and the stage; rules reach agents only through the role file and the brief. Roles: `client-dev`, `client-qa`, `server-dev`, `server-qa`, `integrator`, `harness-dev`. | U |

## The user

| Id | Requirement | Goal |
|---|---|---|
| R11 | Exactly two kinds of action need the user: an action on an OpenRune PR (open, push to its head, comment, ready, draft) and a client release (tag, publish). Fork, local and harness actions need none. | P |
| R12 | An approval is `hd approve <slug> <sha>`, recorded after the user's yes in chat. The tick performs the action as one resumable sequence of observed steps, never the console. If CI does not go green the sequence stops before the comment and the card says so. | U P |
| R13 | No approval is offered before the verdict passed at the same sha. The card shows the exact commands, the full text to be posted, every check line and finding, the diff range and caveats; never a summary. The user's no or silence changes nothing. When GitHub shows the action done, the card is gone. | P L |
| R14 | A question an agent cannot answer is a hold with the question; `hd` lists it; the console asks in chat and records the answer with `hd answer`. The user is notified once per new card or question. | L |
| R15 | `hd` shows, from facts and nothing of its own: spawns, cards, questions, alerts, alive runs and trains, each change's state per target. Times shown in US Eastern, stored in UTC. | L |

## Locks and capacity

| Id | Requirement | Goal |
|---|---|---|
| R16 | A lock exists for `integration`, `live-server` and `ghidra` only; it is bound to a run or a pid and is free the moment that holder is not alive. Tools that drive a locked resource refuse without it. | H |
| R17 | Capacity classes (`agent`, `build`, `image`, `client`, `device`) are counted from alive runs and alive trains only. Client instances are not locked: each agent starts its own and stops it. | U |

## Server track

| Id | Requirement | Goal |
|---|---|---|
| R18 | A dev's output is the fork ref `dev/<slug>`. The public branch (`content/<slug>`, `fix/<slug>`, the PR head) is moved only by an approved publish, fast-forward or merge, never force. `local/<slug>` ends at the test server and is never published. | P |
| R19 | A hand-over on the fork starts a train (one at a time): pin every handed-over head, rebuild `integration` in recorded order with recorded conflict resolutions, gate, image (`COPY --from` the live image's keys, hash checked, boot checked), deploy with rollback tag and automatic rollback on container exit. A step failure books one integrator; its resolution resumes the train from the pins. | U H |
| R20 | QA's verdict covers, at the exact commit on a scratch merge with current upstream `main`: accuracy against the spec, fork CI and Formatting green, one change, upstream AGENTS.md, CONTRIBUTING and PR template read live, PR text (template checkboxes verbatim, no deferral wording, no stacking, no tests unless a rule has several cases or a reviewer asked), gameval ids, in game on its own client. Dev and QA run locally only the touched modules' tests; the full suite is the fork CI run. A red check is a FAIL line on the card, never a hold. | P |
| R21 | When upstream `main` moves, the fork's `main` fast-forwards, merged branches drop and a train runs. When upstream `main` contains a change's commit, the change is done. | U |
| R22 | A maintainer comment or review on an open PR newer than its ready time, by anyone but the fork owner or a bot, is filed once by the tick as a P0 change on the same branch, keyed by its id. Moving the PR to draft is an R11 action. | P |
| R23 | Behaviour matches the official game: RSProx recordings over wiki over cache; every divergence is a caveat in the spec and the PR text. | P |

## Client and harness tracks

| Id | Requirement | Goal |
|---|---|---|
| R24 | Client hand-over needs the repack log (7 `telemetry:` lines), device evidence (logcat or data-tool dump) and, when networking changes, a network QA record; a docs-only change needs no build evidence. The tick merges into `master` and pushes. Any new outbound host is a FAIL. | P |
| R25 | A release is a change of kind `release` created on the user's request, on `master` at one sha: its dev role is `client-qa` (install, hooks, Network QA), its publish needs the user's yes (R11); the tick tags and publishes the gate's single APK with its notices. Autonomous versions are the next `0.1.x`; `0.2`/`1.0` are the user's call. | P |
| R26 | A harness change is merged into `main` by the tick (`--no-ff`) and pushed; the next tick runs the new code. A harness change needs a test per requirement it touches. A major revision is merged only after the user's yes. | U |

## Healing and hygiene

| Id | Requirement | Goal |
|---|---|---|
| R27 | The tick is started by a systemd user timer every minute and by every run end; it is never restarted by hand; two ticks never run at once. | H |
| R28 | Each tick: ends runs of dead consoles, reclaims locks of dead holders, removes containers, clones, worktrees and images owned by nothing alive (keeping the live and rollback images), books an integrator for a train whose process died without a final step, re-pins on upstream movement. Each repair is one event. | H |
| R29 | What only the user can fix (Docker engine down, BlueStacks absent, `gh` unauthenticated, the usage limit) is an alert in `hd`, never a retry loop. | L |
| R30 | `events.jsonl` is append-only, UTC, and records every record written, run start and end with usage, lock event, train and publish step, repair and denial. `hd cost` reports tokens per change and role from run records. | L |

## Guards

| Id | Requirement | Goal |
|---|---|---|
| R31 | One guard hook, one table: agents and the console are denied every write to OpenRune and every deploy or docker write on the live stack; a fork push is allowed only to the role's refs; the publish process alone writes to OpenRune, and only with an approval record at that sha. Targets are resolved (remote URL, ref), never matched as words. Every denial is an event. | P |
| R32 | Only processes the harness started are stopped. Every APK passes the telemetry patch. No client contacts Jagex. The user's RuneLite and the tester account are never touched. Agents read game state through the data tools, not screenshots; keep temp files under their own scratch dir; report a denied action, never work around it. | P |

## Acceptance

1. A night with no user message in which changes were dispatched, handed over, trained, deployed and merged, and the
   user returned to cards only.
2. Each fault repaired within one tick with no user action: the console killed mid-run; the tick killed mid-train; a lock
   whose pid is dead; an orphan `qa-*` container; a clone of an ended run; an approval given and the console killed
   before the publish finished (the publish completes).
3. A harness code change merged into `main` runs on the next tick without a restart.
4. No prompt reached the user for anything but R11 actions and R14 questions.
5. Non-test code ≤ 2 500 lines, tests ≤ 1 500, configuration ≤ 40 lines, no `hd` command without a caller.
