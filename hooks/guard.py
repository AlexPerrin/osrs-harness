#!/usr/bin/env python3
"""Shim for a console started before .claude/settings.json named hook.py; deleted at the v7 cutover."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook  # noqa: E402

hook.main("PreToolUse")
