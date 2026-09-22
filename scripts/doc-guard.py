#!/usr/bin/env python3
"""PostToolUse hook: flags doc bloat in the OSRSheim root. Advisory only (exit 0)."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIMITS = {"CLAUDE.md": 3500, "STATE.md": 3000, "AGENTS.md": 800}
ALLOWED = set(LIMITS) | {"RESEARCH.md"}  # RESEARCH.md is uncapped

try:
    sys.stdin.read()  # payload not needed; every edit triggers a full scan
except Exception:
    pass

problems = []
for name in sorted(os.listdir(ROOT)):
    if not name.lower().endswith(".md"):
        continue
    size = os.path.getsize(os.path.join(ROOT, name))
    if name not in ALLOWED:
        problems.append(f"{name}: not one of the four allowed docs (move to archive/ or fold into RESEARCH.md)")
    elif name in LIMITS and size > LIMITS[name]:
        problems.append(f"{name}: {size} bytes > {LIMITS[name]} cap; prune in place before adding")

if problems:
    msg = "DOC GUARD: " + " | ".join(problems)
    print(json.dumps({
        "systemMessage": msg,
        "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg + ". Rule: less is more; edit in line, delete what is done."},
    }))
sys.exit(0)
