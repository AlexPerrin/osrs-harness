#!/usr/bin/env bash
# MCP stdio server for OpenRune-Developer-Tools in the isolated desktop RuneLite on Windows (see
# bench/multiclient/desktop_devtools_mcp.py). Register: {"command": "<repo>/bench/multiclient/desktop-devtools-mcp.sh"}.
exec python3 -I "$(dirname "$(readlink -f "$0")")/desktop_devtools_mcp.py" "$@"
