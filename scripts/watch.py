#!/usr/bin/env python3
r"""Background watcher: records play sessions and keeps a status file Claude reads at every session start.

    pythonw scripts\watch.py run       the loop (the logon task from watch-install.ps1 starts it; one instance)
    python scripts\watch.py status     print the status (refreshes it when the watcher is not running)
    python scripts\watch.py hook       SessionStart hook (.claude\settings.json): status lines for Claude, always exit 0
    python scripts\watch.py decline    this PC does not want the watcher; the hook stops asking

Every 15 s: is valheim.exe running (tasklist). Nothing heavy runs while the game is up.
  game exit      session-log.py auto (snap each changed save, one row per character into .cache\sessions\<char>.csv),
                 then LogOutput.log -> BepInEx\Logs\LogOutput-<stamp>.log (last 20 kept, as launch-modded.ps1 does)
  game start     a toast when the status needs action (profile behind main, pre-flight errors)
  every 30 min   with the game closed: git fetch origin main; post-build-check.py when HEAD or the profile changed;
                 unpublished session rows. Result: <main checkout>\.cache\watch\status.json (+ watch.log).
Changes nothing in the repo, the profile or the host: sync, publish and commits stay with Claude + the user.
Idle cost: one pythonw process (~20 MB), a tasklist call every 15 s.
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
PROFILE = Path(os.environ.get('APPDATA', '')) / 'com.kesomannen.gale/valheim/profiles/OSRSheim/BepInEx'
TASK = 'OSRSheim watcher'
PY = Path(sys.executable).with_name('python.exe')                     # not pythonw: child output is captured
POLL_S, REFRESH_S, HEARTBEAT_S, STALE_S = 15, 1800, 300, 1200


def sh(*cmd, cwd=None, timeout=120):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=timeout, creationflags=NO_WINDOW)
        return r.returncode, r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return -1, str(e)


def main_root():
    rc, common = sh('git', '-C', str(ROOT), 'rev-parse', '--path-format=absolute', '--git-common-dir')
    return Path(common).parent if rc == 0 and common else ROOT


MAIN = main_root()
DIR = MAIN / '.cache' / 'watch'
STATUS, LOG, LOCK, DECLINED = DIR / 'status.json', DIR / 'watch.log', DIR / 'watch.lock', DIR / 'declined'


def log(msg):
    DIR.mkdir(parents=True, exist_ok=True)
    if LOG.exists() and LOG.stat().st_size > 1_000_000:
        LOG.replace(LOG.with_suffix('.log.1'))
    with LOG.open('a', encoding='utf-8') as f:
        f.write(f'{datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n')


def load_status():
    try:
        return json.loads(STATUS.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def save_status(st):
    DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATUS.with_suffix('.tmp')
    tmp.write_text(json.dumps(st, indent=1), encoding='utf-8')
    tmp.replace(STATUS)


def game_running():
    rc, out = sh('tasklist', '/FI', 'IMAGENAME eq valheim.exe', '/NH', '/FO', 'CSV', timeout=20)
    return rc == 0 and 'valheim.exe' in out.lower()


def session_log():
    spec = importlib.util.spec_from_file_location('session_log', SCRIPTS / 'session-log.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def record_sessions():
    """session-log auto; stdout goes to watch.log. Returns the new rows."""
    import contextlib
    import io
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rows = session_log().auto()
    except (SystemExit, Exception) as e:
        rows = []
        buf.write(f'session-log failed: {e!r}\n')
    for line in buf.getvalue().splitlines():
        log(line)
    return rows


def rotate_log():
    src = PROFILE / 'LogOutput.log'
    if not src.exists():
        return
    dst_dir = PROFILE / 'Logs'
    dst_dir.mkdir(exist_ok=True)
    stamp = datetime.fromtimestamp(src.stat().st_mtime).strftime('%Y%m%d-%H%M%S')
    try:
        src.replace(dst_dir / f'LogOutput-{stamp}.log')
    except OSError as e:
        log(f'log rotation skipped: {e}')
        return
    for old in sorted(dst_dir.glob('LogOutput-*.log'), key=lambda f: f.stat().st_mtime, reverse=True)[20:]:
        old.unlink(missing_ok=True)


def unpublished():
    """Rows in the local session log that origin/main's reference\\sessions\\ does not have yet."""
    n = {}
    for f in (MAIN / '.cache' / 'sessions').glob('*.csv'):
        local = len(f.read_text(encoding='utf-8').splitlines()) - 1
        rc, pub = sh('git', '-C', str(MAIN), 'show', f'origin/main:reference/sessions/{f.name}')
        have = len(pub.splitlines()) - 1 if rc == 0 else 0
        if local > have:
            n[f.stem] = local - have
    return n


def refresh(st, fetch=True):
    if fetch:
        sh('git', '-C', str(MAIN), 'fetch', '-q', 'origin', 'main', timeout=60)
    _, branch = sh('git', '-C', str(MAIN), 'rev-parse', '--abbrev-ref', 'HEAD')
    _, head = sh('git', '-C', str(MAIN), 'rev-parse', 'HEAD')
    _, behind = sh('git', '-C', str(MAIN), 'rev-list', '--count', 'HEAD..origin/main')
    _, cfg = sh('git', '-C', str(MAIN), 'log', '--oneline', 'HEAD..origin/main', '--', 'config', 'loot')
    prof = PROFILE / 'config'
    newest = max((f.stat().st_mtime for f in prof.rglob('*') if f.is_file()), default=0) if prof.is_dir() else 0
    sig = f'{head}:{newest:.0f}'
    if sig != st.get('preflight_sig'):
        rc, out = sh(str(PY), str(MAIN / 'scripts' / 'post-build-check.py'), cwd=str(MAIN), timeout=300)
        errs = [l for l in out.splitlines() if l.startswith('ERROR')]
        st.update(preflight_sig=sig, preflight_rc=rc, preflight_errors=errs[:8], preflight_error_count=len(errs),
                  preflight_at=datetime.now().isoformat(timespec='seconds'))
        log(f'post-build-check exit {rc}, {len(errs)} ERROR line(s)')
    st.update(main_branch=branch, behind_main=int(behind or 0), config_commits_behind=len(cfg.splitlines()) if cfg else 0,
              unpublished_rows=unpublished(), refreshed=datetime.now().isoformat(timespec='seconds'))
    return st


def needs_action(st):
    """Lines that need the user or Claude, empty when all is well."""
    out = []
    if st.get('main_branch') not in (None, 'main'):
        out.append(f"main checkout is on {st['main_branch']}, not main")
    if st.get('behind_main'):
        n = st.get('config_commits_behind', 0)
        out.append(f"main checkout is {st['behind_main']} commit(s) behind origin/main: git pull"
                   + (f', then sync-configs.ps1 -Push ({n} touch config/loot)' if n else ''))
    if st.get('preflight_rc'):
        out.append(f"post-build-check: {st.get('preflight_error_count')} ERROR(s): " + ' | '.join(
            e.removeprefix('ERROR').strip()[:110] for e in st.get('preflight_errors', [])[:3]))
    if st.get('unpublished_rows'):
        out.append('session rows not in the repo yet: ' + ', '.join(f'{k} {v}' for k, v in st['unpublished_rows'].items())
                   + ' (session-log.py publish in a branch, then PR)')
    return out


def toast(title, text):
    title, text = (x.replace("'", '`') for x in (title, text))
    ps = ("[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]"
          " > $null; $x = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent("
          "[Windows.UI.Notifications.ToastTemplateType]::ToastText02); $t = $x.GetElementsByTagName('text');"
          f" $t.Item(0).AppendChild($x.CreateTextNode('{title}')) > $null;"
          f" $t.Item(1).AppendChild($x.CreateTextNode('{text[:200]}')) > $null;"
          " [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("
          "'{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe')"
          ".Show([Windows.UI.Notifications.ToastNotification]::new($x))")
    sh('powershell.exe', '-NoProfile', '-NonInteractive', '-Command', ps, timeout=30)


def cmd_run(_):
    DIR.mkdir(parents=True, exist_ok=True)
    try:
        import msvcrt
        lock = LOCK.open('w')
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        return 0                                                          # another watcher holds the lock
    log(f'watcher start (pid {os.getpid()}, repo {MAIN})')
    st = load_status()
    st.update(pid=os.getpid(), started=datetime.now().isoformat(timespec='seconds'))
    running = game_running()
    if not running:
        record_sessions()                                                 # baseline snaps / anything missed
        st = refresh(st)
    last_refresh = time.time()
    last_beat = 0.0
    while True:
        try:
            now = game_running()
            if now and not running:
                log('game start')
                st['game_started'] = datetime.now().isoformat(timespec='seconds')
                todo = needs_action(st)
                if todo:
                    toast('OSRSheim: ask Claude before playing', todo[0])
            elif running and not now:
                log('game exit')
                time.sleep(20)                                            # let the save and log flush
                rows = record_sessions()
                rotate_log()
                st['game_exited'] = datetime.now().isoformat(timespec='seconds')
                st['last_sessions'] = ([{k: r[k] for k in ('date', 'char', 'hours', 'console')} for r in rows]
                                       or st.get('last_sessions', []))
                st = refresh(st)
                last_refresh = time.time()
            elif not now and time.time() - last_refresh > REFRESH_S:
                st = refresh(st)
                last_refresh = time.time()
            running = now
            st['game_running'] = running
            if time.time() - last_beat > HEARTBEAT_S or 'heartbeat' not in st:
                st['heartbeat'] = datetime.now().isoformat(timespec='seconds')
                last_beat = time.time()
            save_status(st)
        except Exception as e:                                            # the loop must survive anything
            log(f'error: {e!r}')
        time.sleep(POLL_S)


def alive(st):
    try:
        return (datetime.now() - datetime.fromisoformat(st['heartbeat'])).total_seconds() < STALE_S
    except (KeyError, ValueError):
        return False


def cmd_status(_):
    st = load_status()
    if not alive(st):
        st = refresh(st, fetch=True)
        save_status(st)
        print('watcher: not running (status refreshed now)')
    else:
        print(f"watcher: running (pid {st.get('pid')}), game {'running' if st.get('game_running') else 'closed'}")
    for r in st.get('last_sessions', []):
        print(f"last session: {r['date']} {r['char']} {r['hours']} h" + (f" console {r['console']}" if r['console'] else ''))
    todo = needs_action(st)
    print('\n'.join(f'- {t}' for t in todo) if todo else 'nothing needs action')


def cmd_hook(_):
    try:
        st = load_status()
        if not STATUS.exists():
            if not DECLINED.exists():
                print('OSRSheim watcher is not set up on this PC. Ask the user once whether to install it: it records '
                      'each play session from the character save for the balance sim and tells Claude at session start '
                      'when the profile is behind main or the pre-flight fails. It never syncs, commits or touches the '
                      'profile. Setup and requirements: header of scripts\\watch-install.ps1. '
                      'Yes: follow it. No: run `python scripts\\watch.py decline`.')
            return 0
        lines = []
        if not alive(st):
            lines.append(f"watcher not running (last heartbeat {st.get('heartbeat', 'never')}): "
                         'powershell -ExecutionPolicy Bypass -File scripts\\watch-install.ps1 restarts it')
        lines += needs_action(st)
        for r in st.get('last_sessions', []):
            lines.append(f"last session recorded: {r['date']} {r['char']} {r['hours']} h"
                         + (' (console use, not real play)' if r['console'] else ''))
        if lines:
            print(f"OSRSheim watcher status ({st.get('refreshed', '?')}); offer the user each fix, never apply one "
                  'unasked:\n' + '\n'.join(f'- {l}' for l in lines))
    except Exception as e:                                                # a hook must never block a session
        print(f'OSRSheim watcher hook error: {e!r}')
    return 0


def cmd_decline(_):
    DIR.mkdir(parents=True, exist_ok=True)
    DECLINED.write_text(datetime.now().isoformat(timespec='seconds'), encoding='utf-8')
    print(f'declined; delete {DECLINED} to be asked again')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['run', 'status', 'hook', 'decline'])
    a = ap.parse_args()
    return {'run': cmd_run, 'status': cmd_status, 'hook': cmd_hook, 'decline': cmd_decline}[a.cmd](a) or 0


if __name__ == '__main__':
    sys.exit(main())
