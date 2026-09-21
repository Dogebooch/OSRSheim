#!/usr/bin/env python3
"""PostToolUse hook: after any edit, audit the collection log against the build. Advisory only (exit 0).

Runs `gen-collection-log.py --audit` and, when a collectible has no log row (or a logged clone is gone),
tells Claude to fix loot\\collection-log.csv and regenerate. Also flags stale generated cfgs.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, 'scripts', 'gen-collection-log.py')

try:
    sys.stdin.read()
except Exception:
    pass

msgs = []
try:
    r = subprocess.run([sys.executable, GEN, '--audit'], capture_output=True, text=True, timeout=20)
    if r.returncode != 0:
        msgs.append(r.stdout.strip().replace('\n', ' | '))
    r = subprocess.run([sys.executable, GEN, '--check'], capture_output=True, text=True, timeout=20)
    if r.returncode != 0:
        msgs.append(r.stdout.strip() + ' (run python scripts\\gen-collection-log.py)')
except Exception as e:
    msgs.append(f'collection-guard could not run: {e}')

if msgs:
    msg = 'COLLECTION LOG: ' + ' || '.join(msgs)
    print(json.dumps({
        'systemMessage': msg,
        'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext':
            msg + '. Rule: every collectible added or removed in this task gets its loot\\collection-log.csv row added or removed, then regenerate.'},
    }))
sys.exit(0)
