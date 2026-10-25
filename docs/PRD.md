# Requirements

The constraints every solution to docs/PROBLEM.md must satisfy, each derived from its principles. Code and tests cite the
ids. docs/ARCHITECTURE.md is the mechanism that meets each.

| Id | Constraint | From |
|---|---|---|
| R1 **Goals** | Each goal's progress is measured by its command, and work is chosen to close the gap to its target. A met goal stays measured. | P1 P8 |
| R2 **Flow** | A defined change reaches its live target with no person involved once the changes it depends on are live. | P3 P4 |
| R3 **Integrity** | What ships is exactly what was checked and approved: a judgment is bound to a commit and base, void when either moves. A claim with no verifiable record counts for nothing. An unknown fact stops a step. | P1 P2 |
| R4 **Authority** | Only a write to OpenRune and a client release need the user; nothing but the harness can do either, and only at the approved commit. | P5 |
| R5 **Recovery** | Any failure is repaired in one pass with no user action. Only what the user alone can fix is raised, once. Nothing is decided from elapsed time. | P3 P4 P1 |
| R6 **Economy** | A script runs before an agent, an agent before the user; nothing is checked twice for the same commit and base; agents are bounded by one count. | P6 P7 |
| R7 **Visibility** | The user can see at any time what runs, what waits for them, each goal's progress and what happened, all derived from facts. | P8 |

Constraints that need no mechanism: nothing contacts Jagex; the user's own RuneLite and the tester account are never
touched (A10). Product rules (QA checklists, accuracy sources, hand-over contents, the release gate) live in the role files
and skills, where agents read them.

## Acceptance

1. **R1** The client goal's metric is shown against its target; below target, changes toward it are filed; after a night of
   merges the metric has risen.
2. **R2** A change with a live dependency goes from defined to live on each track with no message from the user.
3. **R3** A commit changed after its check or approval does not ship; a hand-over with no evidence is refused; a failed
   fetch leaves every change where it was.
4. **R4** No agent or console command writes to OpenRune or publishes a release; the same action succeeds after the user's
   yes, at that commit only.
5. **R5** Each fault is repaired in one pass: console killed mid-run, pass killed mid-train, orphan container or clone, a
   yes recorded and the console killed before the publish finished (it completes). Docker down raises one alert.
6. **R6** The same commit and base never run a gate, a review or a measurement twice; no more than the configured agents
   are listed.
7. **R7** `hd` lists the agents to spawn, the cards and questions waiting, the alerts, what runs and each goal's metric,
   and nothing else.
