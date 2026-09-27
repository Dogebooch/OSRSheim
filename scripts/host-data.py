#!/usr/bin/env python3
r"""Server-side play data for the watcher: a dedicated server's logs, KG's trade/bank log, shared session rows.

    python scripts\host-data.py sync      GG pull + push this PC's rows + report (what watch.py runs)
    python scripts\host-data.py report    new error types and trade/bank lines since the last check (advances it)
    python scripts\host-data.py pull      GG only: mirror the host files into <main>\.cache\host\
    python scripts\host-data.py push      GG only: upload this PC's session rows to the host

Settings: <main checkout>\server.env (gitignored, never printed); every key optional:
    SERVER_DIR=<a dedicated server folder on this PC>    default: Steam's Valheim Dedicated Server app folder, when
                                                          BepInEx runs there; its files are read in place
    PTERO_URL / PTERO_SERVER / PTERO_API_KEY              the GG host through the Pterodactyl client API; a
                                                          subuser key needs file.read, file.read-content, file.create
Sources: the profile's own Marketplace\Logger.log (KG runs its server half there in -Solo play), the local dedicated
server, the GG mirror (BepInEx/LogOutput.log, Marketplace/Logger.log, SavedData/DB.db copied unparsed; downloaded
whole when the listed size changes, since the panel has no ranged reads).
Reports read only the complete lines added since the last check (.cache\host\offsets.json; the first check reads the
whole file), so no timestamps are parsed (host logs use the host's clock and date format). Error lines fold into
signatures (digits masked, plus the
first stack frame); only signatures never seen before (.cache\watch\seen_errors.json) are reported. KG lines count
as this PC's when they carry one of its SteamID64s: [Trader] <char> (<id>) ..., [Banker] Player User ID: <id> ...
Writes to the host only under osrsheim-data/sessions/: this PC's <account>-<char>.csv/.jsonl when they changed; the
other PCs' copies land in .cache\host\sessions\ (session-log.py publish includes them).
Standard library only: the watcher runs this under pythonw with no packages.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
PROFILE = Path(os.environ.get('APPDATA', '')) / 'com.kesomannen.gale/valheim/profiles/OSRSheim/BepInEx'
PTERO = ('PTERO_URL', 'PTERO_SERVER', 'PTERO_API_KEY')
HOST_FILES = {'LogOutput.log': 'BepInEx/LogOutput.log', 'Logger.log': 'BepInEx/config/Marketplace/Logger.log',
              'DB.db': 'BepInEx/config/Marketplace/SavedData/DB.db'}
ROWS_DIR = 'osrsheim-data/sessions'                    # the only place this script writes on the host
STEAM64 = 76561197960265728                            # SteamID64 = this + the userdata account id
BIG = 50_000_000                                       # warn: the host log appends forever and pulls are whole files
MASK = re.compile(r'\d+')


def main_root():
    try:
        common = subprocess.run(['git', '-C', str(SCRIPTS.parent), 'rev-parse', '--path-format=absolute',
                                 '--git-common-dir'], capture_output=True, text=True, creationflags=NO_WINDOW).stdout.strip()
        return Path(common).parent if common else SCRIPTS.parent
    except OSError:
        return SCRIPTS.parent


MAIN = main_root()
CACHE = MAIN / '.cache' / 'host'
OFFSETS, PULLED, PUSHED = CACHE / 'offsets.json', CACHE / 'pulled.json', CACHE / 'pushed.json'
SEEN = MAIN / '.cache' / 'watch' / 'seen_errors.json'


def load(p):
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def save(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix('.tmp')
    tmp.write_text(json.dumps(d, indent=1), encoding='utf-8')
    tmp.replace(p)


def session_log():
    spec = importlib.util.spec_from_file_location('session_log', SCRIPTS / 'session-log.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_env():
    """<main>\\server.env as a dict; {} when missing. Values are never printed."""
    env = {}
    try:
        for line in (MAIN / 'server.env').read_text(encoding='utf-8-sig').splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return env


def gg(env):
    return all(env.get(k) for k in PTERO)


class Panel:
    """Pterodactyl client API, file endpoints only (tail-console.py has the console side)."""

    def __init__(self, env):
        self.base = f"{env['PTERO_URL'].rstrip('/')}/api/client/servers/{env['PTERO_SERVER']}"
        self.key = env['PTERO_API_KEY']

    def _open(self, path, data=None, ctype='application/json'):
        req = urllib.request.Request(self.base + path, data=data, method='GET' if data is None else 'POST',
                                     headers={'Authorization': f'Bearer {self.key}', 'Accept': 'application/json',
                                              'Content-Type': ctype, 'User-Agent': 'osrsheim-host-data'})
        return urllib.request.urlopen(req, timeout=30)

    def files(self, folder):
        """{name: [size, modified_at]} of the files in a host folder; {} when it doesn't exist."""
        try:
            with self._open('/files/list?directory=' + urllib.parse.quote(folder)) as r:
                items = [d['attributes'] for d in json.load(r)['data']]
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {}
            raise
        return {a['name']: [a['size'], a['modified_at']] for a in items if a['is_file']}

    def download(self, path, dest):
        """Whole file through the signed Wings URL, into a .part file first."""
        with self._open('/files/download?file=' + urllib.parse.quote(path)) as r:
            url = json.load(r)['attributes']['url']
        dest.parent.mkdir(parents=True, exist_ok=True)
        part = dest.with_name(dest.name + '.part')
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'osrsheim-host-data'}),
                                    timeout=60) as r, part.open('wb') as f:
            shutil.copyfileobj(r, f, 1 << 20)
        part.replace(dest)

    def write(self, path, data):
        """Raw body -> host file (the panel creates missing folders)."""
        with self._open('/files/write?file=' + urllib.parse.quote(path), data=data, ctype='text/plain'):
            pass


def pull(panel):
    """Mirror HOST_FILES whose listed size or time changed; a file that shrank keeps its old copy. Returns names."""
    state, got = load(PULLED), []
    for name, remote in HOST_FILES.items():
        folder, fname = remote.rsplit('/', 1)
        meta = panel.files(folder).get(fname)
        dest = CACHE / name
        if not meta or (state.get(name) == meta and dest.exists()):
            continue
        if dest.exists() and meta[0] < dest.stat().st_size:
            dest.replace(dest.with_name(f'{dest.stem}-{datetime.now():%Y%m%d-%H%M%S}{dest.suffix}'))
        panel.download(remote, dest)
        state[name] = meta
        got.append(name)
    save(PULLED, state)
    return got


def push(panel, sl=None):
    """Upload this PC's own session rows whose content changed. Returns names."""
    sl = sl or session_log()
    state, sent = load(PUSHED), []
    for name, f in sl.row_files(own_only=True):
        data = f.read_bytes()
        h = hashlib.sha1(data).hexdigest()
        if state.get(name) != h:
            panel.write(f'{ROWS_DIR}/{name}', data)
            state[name] = h
            sent.append(name)
    save(PUSHED, state)
    return sent


def pull_rows(panel, sl=None):
    """Download the other PCs' session rows into .cache\\host\\sessions\\. Returns names."""
    sl = sl or session_log()
    own = {n for n, _ in sl.row_files(own_only=True)}
    state, got = load(PULLED), []
    for name, meta in panel.files(ROWS_DIR).items():
        if name in own or state.get('rows/' + name) == meta:
            continue
        panel.download(f'{ROWS_DIR}/{name}', sl.HOST_ROWS / name)
        state['rows/' + name] = meta
        got.append(name)
    save(PULLED, state)
    return got


def local_server(env, sl=None):
    """BepInEx folder of a modded dedicated server on this PC: SERVER_DIR, else Steam's own Valheim Dedicated
    Server app folder when BepInEx runs there. None when neither has a log."""
    steam = (sl or session_log()).STEAM
    for d in ([Path(env['SERVER_DIR'])] if env.get('SERVER_DIR') else []) + [
            steam / 'steamapps' / 'common' / 'Valheim dedicated server']:
        if (d / 'BepInEx' / 'LogOutput.log').is_file():
            return d / 'BepInEx'
    return None


def sources(env, sl=None):
    """[(source name, {file: local path})] to read: in place, or the GG mirror. Names never hold a path."""
    out = [('profile', {'Logger.log': PROFILE / 'config' / 'Marketplace' / 'Logger.log'})]
    d = local_server(env, sl)
    if d:
        out.append(('local server', {'LogOutput.log': d / 'LogOutput.log',
                                     'Logger.log': d / 'config' / 'Marketplace' / 'Logger.log'}))
    if gg(env):
        out.append(('host', {'LogOutput.log': CACHE / 'LogOutput.log', 'Logger.log': CACHE / 'Logger.log'}))
    return out


def new_text(key, path):
    """Complete lines added since the last check (all of it on the first check); a shrunk file is read from the start."""
    offs = load(OFFSETS)
    size = path.stat().st_size
    start = offs.get(key, 0)
    if start > size:
        start = 0
    with path.open('rb') as f:
        f.seek(start)
        data = f.read(size - start)
    end = data.rfind(b'\n') + 1
    offs[key] = start + end
    save(OFFSETS, offs)
    return data[:end].decode('utf-8', 'replace')


def error_signatures(text):
    """Counter of error signatures: '[Error'/'[Fatal' log lines, or log lines naming an Exception, with digits
    masked, plus the first stack frame when one follows."""
    sigs = Counter()
    lines = text.splitlines()
    for i, line in enumerate(lines):
        s = line.strip()
        if not s.startswith('[') or not (s.startswith(('[Error', '[Fatal')) or 'Exception' in s):
            continue
        frame = ''
        for nxt in lines[i + 1:i + 4]:
            t = nxt.strip()
            if t in ('', 'Stack trace:'):
                continue
            frame = '' if t.startswith('[') else t
            break
        sigs[MASK.sub('#', s)[:160] + (' | ' + MASK.sub('#', frame)[:100] if frame else '')] += 1
    return sigs


def unseen(source, sigs):
    """[(signature, count)] this source never showed before, most frequent first; they count as seen from now on."""
    seen = load(SEEN)
    mine = seen.setdefault(source, {})
    new = [(k, n) for k, n in sigs.most_common() if k not in mine]
    if new:
        today = datetime.now().date().isoformat()
        mine.update({k: today for k, _ in new})
        save(SEEN, seen)
    return new


def steam_ids(sl=None):
    """SteamID64s of the Steam accounts on this PC (userdata\\<account id>)."""
    steam = (sl or session_log()).STEAM
    return {str(STEAM64 + int(d.name)) for d in steam.glob('userdata/*') if d.name.isdigit()}


def report(env=None, sl=None):
    """{source: {...}}: new error types of its LogOutput.log; this PC's [Trader]/[Banker] lines and all of them."""
    env = read_env() if env is None else env
    ids = steam_ids(sl)
    out = {}
    for name, files in sources(env, sl):
        r = {}
        for key, path in files.items():
            if not path.is_file():
                continue
            first = f'{name}:{key}' not in load(OFFSETS)
            text = new_text(f'{name}:{key}', path)
            if key == 'LogOutput.log':
                new = unseen(name, error_signatures(text))
                if new:
                    r['new_errors'] = [[k, n] for k, n in new]
            else:
                kg = [l for l in text.splitlines() if '[Trader]' in l or '[Banker]' in l]
                mine = [l for l in kg if any(i in l for i in ids)]
                if kg:
                    r.update(trades=sum('[Trader]' in l for l in mine), bank=sum('[Banker]' in l for l in mine),
                             kg_lines_all=len(kg))
            if first:
                r['first_check'] = True
            if path.stat().st_size > BIG:
                r['big'] = f'{key} {path.stat().st_size / 1e6:.0f} MB'
        if r:
            out[name] = r
    return out


def sync():
    """What the watcher runs: GG pull + row exchange (when PTERO_* is set), then the report of every source."""
    env = read_env()
    st = {'at': datetime.now().isoformat(timespec='seconds')}
    sl = session_log()
    if gg(env):
        try:
            panel = Panel(env)
            st.update(pulled=pull(panel), pushed=push(panel, sl), rows_in=pull_rows(panel, sl))
        except Exception as e:                                            # report, never raise into the watcher
            st['error'] = f'{type(e).__name__}: {e}'[:200]
    st['sources'] = report(env, sl)
    return st


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['sync', 'report', 'pull', 'push'])
    a = ap.parse_args()
    env = read_env()
    if a.cmd in ('pull', 'push') and not gg(env):
        sys.exit(f'{MAIN / "server.env"} has no {", ".join(PTERO)}: GG pulls are off on this PC')
    if a.cmd == 'pull':
        print(json.dumps({'pulled': pull(Panel(env)), 'rows_in': pull_rows(Panel(env))}, indent=1))
    elif a.cmd == 'push':
        print(json.dumps({'pushed': push(Panel(env))}, indent=1))
    else:
        print(json.dumps(sync() if a.cmd == 'sync' else report(env), indent=1, ensure_ascii=False))


if __name__ == '__main__':
    sys.exit(main())
