---
slug: v5-docs-trim
track: harness
title: 'v5: trim agent docs to current understanding (no rule or meaning changes)'
prio: P2
role: harness-dev
stage: live
hold: null
deps: []
branch: harness/v5-docs-trim
commit: 9d3e38301926416ae27b84c26d94fbf17c6356f3
local_only: false
owner: null
instances: []
evidence: /home/alex/osrs-plugins-reverse/re/evidence/v5-docs-trim
summary: Docs trimmed to current truth; 9 v2/v3-era docs deleted; PRD renamed docs/PRD.md; role files 264-415 words; 4 new skills; 167 tests pass; hd lint reports 14 pre-existing branch-prefix problems
  on other changes (not mine)
live_commit: 9d3e38301926416ae27b84c26d94fbf17c6356f3
cost:
  runs: 1
  turns: 0
  tokens: 0
  minutes: 0
created: '2026-10-24T21:43:36Z'
updated: '2026-10-24T22:50:08Z'
---
## Change
v5: trim agent docs to current understanding (no rule or meaning changes)

## Definition of done
- [x] Delete the v2-era docs (workflow.md, harness.md, orchestrator.md, v2-shipped.md, harness-v3-handoff.md, harness-v3-problem.md, integration-pipeline.md) unless v4 ARCHITECTURE.md or the PRD still depends on them; git history keeps them
- [x] One home per fact: CLAUDE.md rules, ARCHITECTURE.md how it works, PRD intent, HANDOFF.md current state only
- [x] Role files about 400 words: goal, definition of done, hand-over command, hard nevers; procedures move to skills; nothing repeats hd brief
- [x] Prose deleted where a hook or test enforces the rule; no dates, PR numbers or incident stories in rules; no hand-kept counts or state
- [x] Every rule in the old docs is kept, moved, or listed as removed with the reason in the hand-over; tests pass

## Log
- 2026-10-24T21:43:36Z created (ready)
- 2026-10-24T21:43:36Z hold blocked: waits for the v4 rewrite (harness-dev agent a0d68621b85fcc35e) to be merged; unhold when it is
- 2026-10-24T21:44:35Z hold blocked cleared: every dep is live
- 2026-10-24T22:37:46Z USER RULE 2026-10-24: documentation does not include revision justification; it is the most concise source of truth. Remove 'why we changed it', history, dated rationale and justifying parentheticals from CLAUDE.md, docs/ARCHITECTURE.md, docs/HANDOFF.md, role files and skills; state only what is true now. Incident and root-cause records stay only in docs/ISSUES.md. Agents' definition-of-done items are ticked with hd dod. Docs live in docs/ (CLAUDE.md the only root doc); the harness stays contained in this repo.
- 2026-10-24T22:41:35Z Also record in docs/ISSUES.md (dated, short: symptom, cause, evidence, fix, how to recognise): (1) harness-track check failed a harness/<slug> change once main already contained its commit (console merged by hand before the daemon's check); closed by handing it over on main; the check should treat 'main contains the commit' as pass for harness. (2) New change files in harness/changes are untracked in the main checkout and invisible to worktrees; agents cannot tick DoD without hd dod. (3) hd worktrees (EnterWorktree) are created from origin/main, not local main: agents must git reset --hard main first. (4) The console's EnterWorktree isolates the whole session and breaks subagents' Bash; the console never enters a worktree while agents run. Keep ISSUES.md the only place for these; docs state current truth only.
- 2026-10-24T22:41:35Z ready -> dev: dispatched to hd13
- 2026-10-24T22:41:35Z run hd13 started (harness-dev, stage dev, instances none)
- 2026-10-24T22:48:26Z dod ticked: 1, 2, 3, 4, 5
- 2026-10-24T22:48:41Z handover harness/v5-docs-trim@9d3e38301: Docs trimmed to current truth; 9 v2/v3-era docs deleted; PRD renamed docs/PRD.md; role files 264-415 words; 4 new skills; 167 tests pass; hd lint reports 14 pre-existing branch-prefix problems on other changes (not mine)
- 2026-10-24T22:49:02Z dev -> checked: hand-over check PASS
- 2026-10-24T22:49:02Z ship: merged into main 6c4421e
- 2026-10-24T22:49:03Z run hd13 ended: ? turns, ? tokens, exit stopped:lingering: owner is None (change at checked)
- 2026-10-24T22:50:08Z checked -> live: observed
