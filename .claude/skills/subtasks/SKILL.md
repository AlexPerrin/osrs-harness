---
name: subtasks
description: "How a dev or QA agent hands read-heavy lookups to read-only subtasks and keeps only the conclusion. Use before searching RSProx transcripts, logs, wiki or cache sweeps, decompiled code or CI logs."
---
# Subtasks

Hand read-heavy lookups to a subtask (the Agent tool; `Explore` for searches, `general-purpose` for multi-step digging)
and keep only its conclusion: RSProx transcript searches (`re/ref/rsprox/`), server or client logs, wiki and cache
sweeps, decompiled code, CI logs. Give it the question, where to look and the answer format (e.g. "ticks, packets and
quoted lines for NPC 731's dialogue in recordings 1718 and 1619-1622").

Subtasks only read and summarise: they take no locks and do not build, edit, commit or push. Anything a gate or record
cites you check yourself at the source (file and line, recording and tick) before you write it down.
