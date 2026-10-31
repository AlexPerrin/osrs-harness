---
name: accuracy-check
description: "Write or check a server feature's accuracy spec against OSRS sources (RSProx recordings and the wiki, cache and Mod posts first, then LostCity), and check behaviour against it. Use before coding a server feature, before handing it over (the dev's check), and in QA's aggregate."
---
# Accuracy check

The spec is `accuracy.md` in the change's evidence dir `~/osrs-harness/evidence/<slug>/`. Look sources up with the
`osrs-mcp` MCP (`wiki_search`, `wiki_page`, `wiki_npc_spawns`, `cache_search`; load with ToolSearch).

## Sources, in order
RSProx recordings and the wiki (with the cache and Mod posts) are the baseline together; LostCity comes only after
them. Where a recording and the wiki disagree, cite both and follow the newer (a recording's revision against the
wiki's update history); either one beats LostCity.
1. **RSProx recordings of the official game**: community captures from rsprox.net, for anything they show (anims,
   spot anims, sounds, messages, dialogue order, varps, interfaces, tick timings). The index, search,
   transcribe method and coverage are in `references/rsprox.md` on the fork's `docs` branch; the recordings and
   transcripts stay local under `re/ref/rsprox/` (git-ignored). They may contain other players' names and chat:
   never commit, quote or upload them; cite only recording ids and the packets you checked. We never record the
   official game ourselves. See "RSProx comparison" in both procedures below.
2. **OSRS Wiki** (pages, transcripts, update history), the **cache** (osrs-mcp `cache_search`, gamevals) and **Mod
   posts**. A rule cites a recording or one of these, or it's a guess.
3. **Reference implementations**, read-only clones in `re/ref/` (refresh with `git -C re/ref/<repo> pull`), for logic
   the wiki doesn't spell out: tick timings, dialogue flow and branches, state machines, edge cases (interrupted
   dialogue, full inventory, logout mid-event). They are evidence for a guess, never a source for a rule:
   - `re/ref/Content/scripts` (LostCity, MIT): RuneScript content of 2004 RuneScape (quests incl. mcannon, doric,
     gobdip, hetty, cook, the macro/random events, skills, shops). Jagex's script style, so timings and flows are
     often close to the original, but it's **pre-OSRS**: OSRS has changed much since (reworks, new dialogue,
     QoL). Check the OSRS Wiki's history for the mechanic before trusting it. Engine: `re/ref/Engine-TS` (MIT).
   - `re/ref/project-gielinor-rust-server` (ISC, OSRS 239.1): young and unverified, and its own
     SOURCE_PROVENANCE.md leaves open questions about derived code. Its Wiki-research issues can point to sources;
     its code is a last resort.
   Read for behaviour, never copy code or text into our branches (different languages anyway; licences and
   provenance differ). In the spec, say "per LostCity <file>" next to a guess so QA can check it; the PR's Data
   sources may name LostCity as a reference only when a rule followed it.
4. The RuneLite plugins that read the mechanic (what they parse is what the client expects).

## Writing the spec (server-dev)
1. What upstream already has: `gh pr list -R OpenRune/OpenRune-Server --search <topic>`, issues, recent `main`.
2. Each mechanic: its source (wiki page and section, cache entry, Mod post), the planned behaviour.
3. Caveats and guesses, each marked.
4. **RSProx comparison** (required for new content): search rsprox.net for recordings of the
   mechanic (`references/rsprox.md` on the fork's docs: search by NPC/LOC/INTERFACE id and by TEXT/MESSAGE_GAME;
   quest varps alone match only recordings that change them), transcribe them locally, and note per rule what the
   recording shows (anims, spot anims, sounds, messages, dialogue order, varps per stage, interfaces, tick timings).
   If none exists, say so in the spec; it stays a guess.
5. The tests, one per rule (only where AGENTS.md wants them).
6. The PR split and `Depends:` (skill `server-track`, "Changes for upstream").

## Checking (server-dev before hand-over; server-qa independently in its aggregate)
1. Re-read each source yourself; don't rely on the spec's quotes.
2. **Compare against the RSProx recordings** listed in the spec or `references/rsprox.md` (transcripts under
   `re/ref/rsprox/txt/`, notes under `re/ref/rsprox/notes/`): each recorded detail that the branch implements must
   match, or be fixed, or be a caveat. Record the comparison in the hand-over or QA's record (recording ids, revision, which rules
   matched or diverged; no player names or chat). Tick the PR template's rsprox item only when this was done.
3. Check the branch's behaviour (tests, in-game) against each rule.
4. Every gameplay-visible divergence is either fixed or listed in the PR's Caveats.

A passing check is what the PR template's "Matches the OSRS wiki" item means: nothing found differs from the official
game. A difference is fixed, never recorded: no `docs/quirks.md` entries in our changes; one the server cannot fix is an
`hd ask`. A rule with no official data at all (the wiki names it but no cache, recording or transcript bounds it) is
not a difference: implement the best reconstruction (an open reconstruction such as LostCity's tables, or the game's map)
and name it in the PR notes as unsourced; it does not block the wiki item.

## Report
Per rule: matches, diverges (with the evidence), or a guess. Then the caveats the PR must list.
