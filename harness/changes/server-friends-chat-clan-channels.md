---
slug: server-friends-chat-clan-channels
track: server
kind: change
title: 'Friends chat and clan channels: the server sends no friends chat, clan channel
  or clan settings state'
priority: P2
deps: []
created: '2026-10-25T20:31:36Z'
goal: client-api
---
Blocks the client-api probe's social rows (clan.ClanSettings 4, ClanChannel 3, ClanChannelMember 3, ClanMember 3, FriendsChatManager 4, FriendsChatMember 2; client change client-api-probe-reach), which stay unreached because the client never holds a friends chat or clan.

Repro on the test server: log in the tester, open the chat-channel tab and join a friends chat (or any clan): no channel state arrives, Client.getFriendsChatManager()/getClanChannel()/getClanSettings() stay null in the Android host (the host already decodes them: host ChatChannels). Source: the fork has no sender of rsprot's UPDATE_FRIENDCHAT_CHANNEL_FULL_V2/SINGLEUSER, CLANCHANNEL_FULL/DELTA or CLANSETTINGS_FULL/DELTA (grep -r 'ClanChannelFull|ClanSettingsFull|UpdateFriendChatChannel' finds none) and no friends chat or clan content.

Expected (official): joining a friends chat sends the channel (owner, name, kick rank, members with world and rank); a clan member gets CLANSETTINGS_FULL and CLANCHANNEL_FULL for their clan (and the guest clan when they join one). Minimum to unblock the client: a joinable friends chat with the joining player as a member, and one clan whose settings and channel list the tester.
