---
slug: server-clan-channels
track: server
kind: change
title: 'Clans: the server sends no clan channel or clan settings state'
priority: P2
deps:
- server-friends-chat-clan-channels
created: '2026-10-31T03:20:17Z'
---
Split from server-friends-chat-clan-channels (the user, 2026-10-31: friends chat first, clans second, one change per PR, for upstream; #73 is months old: supersede it or open our PR over it). Blocks the client-api probe's clan rows (clan.ClanSettings 4, ClanChannel 3, ClanChannelMember 3, ClanMember 3; client change client-api-probe-reach).

Expected (official): a clan member gets CLANSETTINGS_FULL and CLANCHANNEL_FULL for their clan (and the guest clan when they join one), with deltas on change. Minimum to unblock the client: one clan whose settings and channel list the tester. Build on the friends chat change's chat-channel tab.
