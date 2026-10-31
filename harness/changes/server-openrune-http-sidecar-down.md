---
slug: server-openrune-http-sidecar-down
track: server
kind: local
title: 'Test server: the jav_config/LOCAL_AUTH HTTP sidecars crash-loop, so no Android
  client can reach the login screen'
priority: P1
deps: []
created: '2026-10-31T01:50:37Z'
---
Repro (2026-10-30 21:43-21:55 EDT): docker ps shows osrs-openrune Up, but osrs-openrune-http and osrs-openrune-http-desktop 'Restarting (2)' (RestartCount 25+). docker logs osrs-openrune-http repeats: '/app/docker-entrypoint.sh: 6: OPENRS2_CACHE_ID: cache missing and OPENRS2_CACHE_ID not set'. Their compose working_dir label is /home/alex/osrs-plugins-reverse/openrune, a directory that no longer exists (train/deploy.sh only ups 'openrune' with --no-deps from server-tools, so the sidecars are never recreated). curl http://127.0.0.1:8080/jav_config.ws -> no response. Effect: a repack (OPENRUNE=1 LOCAL_AUTH=1) on Agent_Phone starts the host (host ready; 3 plugins) but the game stays in GameStateChanged UNKNOWN and never shows the login screen (evidence/client-docs-no-bluestacks/logcat-host.txt, plugin-test.log). Expected: the 8080 sidecar (jav_config, world list, LOCAL_AUTH provider) and 8082 desktop sidecar serving, as before.
