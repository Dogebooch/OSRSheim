"""Refuse a profile write from a checkout that is behind origin/main on its inputs.

The Gale profile is shared by every worktree, so a generator run from a stale branch
regresses the live cfgs. Generators call require_current(<their inputs>) before writing.
--allow-behind skips the refusal.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FLAG = '--allow-behind'


def git(*args):
    return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True, timeout=30)


def require_current(*paths):
    rel = [Path(p).resolve().relative_to(ROOT).as_posix() for p in paths]
    try:
        fetched = git('fetch', '-q', 'origin', 'main').returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        fetched = False
    try:
        r = git('log', '--oneline', 'HEAD..origin/main', '--', *rel)
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f'WARN   cannot compare with origin/main ({e}); writing anyway')
        return
    if r.returncode != 0:
        print(f'WARN   cannot compare with origin/main ({r.stderr.strip()}); writing anyway')
        return
    if not fetched:
        print('WARN   git fetch failed; compared with the last fetched origin/main')
    behind = r.stdout.strip().splitlines()
    if not behind:
        return
    if FLAG in sys.argv:
        print(f'WARN   {len(behind)} commit(s) on origin/main touch {", ".join(rel)}; writing anyway ({FLAG})')
        return
    print(f'ERROR  this checkout is behind origin/main on {", ".join(rel)}; writing would regress the shared profile:')
    for line in behind[:10]:
        print('         ', line)
    print(f'       git merge origin/main, then re-run. {FLAG} overrides.')
    sys.exit(1)
