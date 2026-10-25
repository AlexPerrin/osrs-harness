# Requirements

What a solution to docs/PROBLEM.md must satisfy, in outcomes. Each requirement has an id (R-n) that code and tests cite
and is testable. docs/ARCHITECTURE.md is the mechanism that meets each.

| Id | Requirement |
|---|---|
| R1 **Goals** | Every goal's progress is measured, and work is chosen to close the gap to its target. A met goal stays measured. |
| R2 **Flow** | A defined change reaches its live target with no person involved, once the changes it depends on are live. |
| R3 **Integrity** | Only what has been checked ships: what was checked and approved is exactly what ships. A claim counts only if it can be verified; what an agent says counts for nothing. |
| R4 **Authority** | Only a write to OpenRune and a client release need the user, and nothing else can do either. |
| R5 **Recovery** | Any failure is repaired without the user. Only what they alone can fix is raised, once. |
| R6 **Visibility** | The user can see at any time what is running, what waits for them, each goal's progress and what happened. |

Constraint: nothing contacts Jagex; the user's own RuneLite and the tester account are never touched. Product rules
(QA checklist, accuracy sources, hand-over contents, release gate) are in the role files and skills, not here.

## Acceptance

1. **R1** The client goal's metric is printed against its target; below target, changes toward it are filed; after a night
   of merges the metric has risen.
2. **R2** A change with a live dependency goes from defined to live, on each track, with no message from the user.
3. **R3** A commit changed after its check or approval does not ship; a claim with no verifiable record is refused.
4. **R4** No agent or console action writes to OpenRune or publishes a release; the same action succeeds after the user's
   yes.
5. **R5** Each fault is repaired within one tick with no user action: console killed mid-run, tick killed mid-train, a
   lock whose holder is dead, an orphan container or clone, a user's yes recorded and the console killed before the
   publish finished (it completes). Docker down raises one alert.
6. **R6** `hd` lists the agents to spawn, the cards and questions waiting, the alerts, what is running and each goal's
   metric, and nothing else.
