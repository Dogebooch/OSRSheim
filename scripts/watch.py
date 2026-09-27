#!/usr/bin/env python3
r"""Background watcher: records play sessions and keeps a status file Claude reads at every session start.

    pythonw scripts\watch.py run       the loop (the logon task from watch-install.ps1 starts it; one instance)
    python scripts\watch.py status     print the status (refreshes it when the watcher is not running)
    python scripts\watch.py hook       SessionStart hook (.claude\settings.json): status lines for Claude, always exit 0
    python scripts\watch.py decline    this PC does not want the watcher; the hook stops asking
    python scripts\watch.py findings   screenshots and new error types not yet handled (the hook sums them up)
    python scripts\watch.py ack        mark those findings handled

Every 15 s: is valheim.exe running (tasklist). Nothing heavy runs while the game is up.
  game exit      (two empty polls in a row) session-log.py auto (snap each changed save, one row per character into
                 .cache\sessions\<char>.csv + a detail line in <char>.jsonl); the game report: screenshots taken since
                 game start (Steam F12, Game Bar Win+Alt+PrtScn) and error types the client log never showed before;
                 then LogOutput.log -> BepInEx\Logs\LogOutput-<stamp>.log (last 20 kept, as launch-modded.ps1 does);
                 then host-data.py sync (server logs, KG trade/bank lines, GG pull and session-row exchange)
  game start     a toast when something breaks a session (checkout off main or behind it, pre-flight errors)
  every 30 min   with the game closed: git fetch origin main; post-build-check.py when HEAD or the profile changed;
                 unpublished session rows. Every 6 h: host-data.py sync.
                 Result: <main checkout>\.cache\watch\status.json (+ watch.log).
Changes nothing in the repo or the profile; on the host it writes only osrsheim-data/sessions/ (host-data.py).
Sync, publish and commits stay with Claude + the user. session-log.py and host-data.py load fresh at every use;
a changed watch.py needs a restart (the hook says so).
Idle cost: one pythonw process (~20 MB), a tasklist call every 15 s.
"""
import argparse
import hashlib
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
POLL_S, REFRESH_S, HEARTBEAT_S, STALE_S, SYNC_S = 15, 1800, 300, 1200, 6 * 3600


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
STATUS, LOG, LOCK, DECLINED, ACKED = (DIR / 'status.json', DIR / 'watch.log', DIR / 'watch.lock', DIR / 'declined',
                                      DIR / 'acked')
KEEP_FINDINGS_DAYS, MAX_FINDINGS = 30, 60


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


def script(name):
    """A sibling script, loaded fresh at every use: a pulled change applies without restarting the watcher."""
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), SCRIPTS / f'{name}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def code_hash():
    """The main checkout's watch.py; the running loop keeps the code it started with."""
    try:
        return hashlib.sha1((MAIN / 'scripts' / 'watch.py').read_bytes()).hexdigest()[:12]
    except OSError:
        return ''


def record_sessions():
    """session-log auto; stdout goes to watch.log. Returns the new rows."""
    import contextlib
    import io
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rows = script('session-log').auto()
    except (SystemExit, Exception) as e:
        rows = []
        buf.write(f'session-log failed: {e!r}\n')
    for line in buf.getvalue().splitlines():
        log(line)
    return rows


def rotate_log():
    """LogOutput.log -> BepInEx\\Logs\\LogOutput-<stamp>.log (last 20 kept). Returns the archive name or ''."""
    src = PROFILE / 'LogOutput.log'
    if not src.exists():
        return ''
    dst_dir = PROFILE / 'Logs'
    dst_dir.mkdir(exist_ok=True)
    dst = dst_dir / f"LogOutput-{datetime.fromtimestamp(src.stat().st_mtime):%Y%m%d-%H%M%S}.log"
    try:
        src.replace(dst)
    except OSError as e:
        log(f'log rotation skipped: {e}')
        return ''
    for old in sorted(dst_dir.glob('LogOutput-*.log'), key=lambda f: f.stat().st_mtime, reverse=True)[20:]:
        old.unlink(missing_ok=True)
    return dst.name


def now_iso():
    return datetime.now().isoformat(timespec='seconds')


def screenshots(since, steam):
    """Screenshots/clips saved since the game started: Steam F12 (userdata\\<id>\\760\\...), Game Bar Win+Alt+PrtScn."""
    t0 = datetime.fromisoformat(since).timestamp() if since else time.time() - 86400
    found = [*steam.glob('userdata/*/760/remote/892970/screenshots/*.jpg'),
             *(Path.home() / 'Videos' / 'Captures').glob('Valheim*')]
    return sorted(str(f) for f in found if f.stat().st_mtime >= t0)


def game_report(st):
    """Findings of the game that just ended: its screenshots and the error types the client log never showed before
    (host-data.py's signatures and seen-set). Runs before rotate_log()."""
    out = []
    try:
        sl, hd = script('session-log'), script('host-data')
        out += [{'at': now_iso(), 'kind': 'screenshot', 'source': 'client', 'text': f}
                for f in screenshots(st.get('game_started'), sl.STEAM)]
        src = PROFILE / 'LogOutput.log'
        sigs = hd.error_signatures(src.read_text(encoding='utf-8', errors='replace')) if src.exists() else {}
        out += [{'at': now_iso(), 'kind': 'error', 'source': 'client', 'text': k, 'n': n}
                for k, n in hd.unseen('client', sigs)]
    except Exception as e:
        log(f'game report failed: {e!r}')
    return out


def host_sync(st):
    """host-data.py sync -> st['server'] + findings (new server error types, an oversized host log). Never raises."""
    try:
        s = script('host-data').sync()
    except Exception as e:
        s = {'at': now_iso(), 'error': f'{type(e).__name__}: {e}'[:200]}
    st['server'] = s
    items = []
    for src, r in s.get('sources', {}).items():
        items += [{'at': s['at'], 'kind': 'error', 'source': src, 'text': k, 'n': n} for k, n in r.get('new_errors', [])]
        if r.get('big'):
            items.append({'at': s['at'], 'kind': 'big log', 'source': src, 'text': r['big']})
    add_findings(st, items)
    log('host-data sync: ' + (s['error'] if s.get('error') else ', '.join(
        f'{k} {len(s[k])}' for k in ('pulled', 'pushed', 'rows_in') if s.get(k)) or 'ok')
        + (f', {sum(1 for i in items if i["kind"] == "error")} new error type(s)' if items else ''))
    return st


def add_findings(st, items):
    """Append to the rolling findings list (30 days, 60 items); a repeated 'big log' is kept once."""
    have = {(f['kind'], f['source'], f['text']) for f in st.get('findings', []) if f['kind'] == 'big log'}
    keep = [f for f in st.get('findings', []) + [i for i in items if (i['kind'], i['source'], i['text']) not in have]
            if (datetime.now() - datetime.fromisoformat(f['at'])).days < KEEP_FINDINGS_DAYS]
    st['findings'] = keep[-MAX_FINDINGS:]


def acked():
    try:
        return ACKED.read_text(encoding='utf-8').strip()
    except OSError:
        return ''


def open_findings(st):
    """Findings newer than the last `watch.py ack`."""
    a = acked()
    return [f for f in st.get('findings', []) if f['at'] > a]


def unpublished():
    """Session-log rows (own + shared through the host) that origin/main's reference\\sessions\\ does not have yet."""
    n = {}
    try:
        files = script('session-log').row_files()
    except (SystemExit, Exception):
        return n
    for name, f in files:
        if not name.endswith('.csv'):
            continue
        local = len(f.read_text(encoding='utf-8').splitlines()) - 1
        rc, pub = sh('git', '-C', str(MAIN), 'show', f'origin/main:reference/sessions/{name}')
        have = len(pub.splitlines()) - 1 if rc == 0 else 0
        if local > have:
            n[name[:-4]] = local - have
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


def needs_action(st, toast_only=False):
    """Lines that need the user or Claude, empty when all is well. toast_only: just what breaks a session."""
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
    if toast_only:
        return out
    if st.get('unpublished_rows'):
        out.append('session rows not in the repo yet: ' + ', '.join(f'{k} {v}' for k, v in st['unpublished_rows'].items())
                   + ' (session-log.py publish in a branch, then PR)')
    if st.get('code') and alive(st) and st['code'] != code_hash():
        out.append('the watcher runs an older watch.py: powershell -ExecutionPolicy Bypass -File '
                   'scripts\\watch-install.ps1 (main checkout) restarts it')
    if (st.get('server') or {}).get('error'):
        out.append(f"host-data sync failed at {st['server']['at']}: {st['server']['error'][:160]}")
    found = open_findings(st)
    if found:
        shots = [f for f in found if f['kind'] == 'screenshot']
        errs = [f for f in found if f['kind'] == 'error']
        parts = [f'{len(shots)} screenshot(s): ask Doug what went wrong, then read the log around that time'] if shots else []
        if errs:
            by = {}
            for f in errs:
                by[f['source']] = by.get(f['source'], 0) + 1
            parts.append(f"{len(errs)} new error type(s) ({', '.join(f'{s} {n}' for s, n in by.items())}), "
                         f"e.g. {errs[0]['text'][:90]}")
        parts += [f"{f['source']} {f['text']}: rename that log at the next server stop"
                  for f in found if f['kind'] == 'big log']
        out.append(f"findings since {acked() or 'install'}: " + '; '.join(parts)
                   + '. List: python scripts\\watch.py findings; handled: python scripts\\watch.py ack')
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
    st.update(pid=os.getpid(), started=now_iso(), code=code_hash())
    running = game_running()
    if not running:
        record_sessions()                                                 # baseline snaps / anything missed
        st = host_sync(refresh(st))
    last_refresh = last_sync = time.time()
    last_beat = 0.0
    empty = 0                                                             # polls in a row without valheim.exe
    while True:
        try:
            seen = game_running()
            empty = 0 if seen else empty + 1
            now = seen or (running and empty < 2)                         # exit only after two empty polls
            if now and not running:
                log('game start')
                st['game_started'] = now_iso()
                todo = needs_action(st, toast_only=True)
                if todo:
                    toast('OSRSheim: ask Claude before playing', todo[0])
            elif running and not now:
                log('game exit')
                time.sleep(20)                                            # let the save and log flush
                rows = record_sessions()
                found = game_report(st)
                st['last_game'] = {'started': st.get('game_started'), 'exited': now_iso(), 'log': rotate_log(),
                                   'screenshots': sum(f['kind'] == 'screenshot' for f in found),
                                   'new_error_types': sum(f['kind'] == 'error' for f in found)}
                add_findings(st, found)
                log(f"game report: {st['last_game']['screenshots']} screenshot(s), "
                    f"{st['last_game']['new_error_types']} new error type(s), log {st['last_game']['log'] or '-'}")
                st['game_exited'] = st['last_game']['exited']
                st['last_sessions'] = ([{k: r[k] for k in ('date', 'char', 'hours', 'console')} for r in rows]
                                       or st.get('last_sessions', []))
                st = host_sync(refresh(st))
                last_refresh = last_sync = time.time()
            elif not now and time.time() - last_refresh > REFRESH_S:
                st = refresh(st)
                last_refresh = time.time()
                if time.time() - last_sync > SYNC_S:
                    st = host_sync(st)
                    last_sync = time.time()
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
                      'each play session from the character save for the balance sim, notes screenshots and new error '
                      'types for Claude, and tells Claude at session start when the profile is behind main or the '
                      'pre-flight fails. It never syncs configs, commits or touches the profile; with a GG key in '
                      'server.env it shares session rows through osrsheim-data/ on the host. Setup and requirements: '
                      'header of scripts\\watch-install.ps1. Yes: follow it. No: run `python scripts\\watch.py decline`.')
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


def cmd_findings(_):
    st = load_status()
    found = open_findings(st)
    lg = st.get('last_game') or {}
    if lg:
        print(f"last game {lg.get('started')} - {lg.get('exited')}: client log BepInEx\\Logs\\{lg.get('log') or '?'}")
    for f in found:
        print(f"{f['at']}  {f['kind']:10} {f['source']:12} " + (f"x{f['n']:<5} " if 'n' in f else '') + f['text'])
    print(f'{len(found)} finding(s) since {acked() or "install"}')


def cmd_ack(_):
    DIR.mkdir(parents=True, exist_ok=True)
    ACKED.write_text(now_iso(), encoding='utf-8')                       # the loop never writes this file
    print(f'findings up to now marked handled ({ACKED})')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['run', 'status', 'hook', 'decline', 'findings', 'ack'])
    a = ap.parse_args()
    return {'run': cmd_run, 'status': cmd_status, 'hook': cmd_hook, 'decline': cmd_decline, 'findings': cmd_findings,
            'ack': cmd_ack}[a.cmd](a) or 0


if __name__ == '__main__':
    sys.exit(main())
