#!/usr/bin/env python3
r"""Live console of the dedicated host through the Pterodactyl client API.

    python scripts\tail-console.py                  last 200 lines, then follow until Ctrl-C
    python scripts\tail-console.py --duration 60    follow for 60 s, then exit
    python scripts\tail-console.py --no-follow      backlog only
    python scripts\tail-console.py --power restart  start | stop | restart | kill, then follow
    python scripts\tail-console.py --command "..."  send a console command, then follow
    python scripts\tail-console.py --state          print the power state and exit

Credentials come from <repo>\server.env (gitignored, never printed):
    PTERO_URL=https://panel.ggservers.com
    PTERO_SERVER=<server id from the dashboard>
    PTERO_API_KEY=ptlc_...        panel -> Account -> API Key
"""
import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
import websockets

ROOT = Path(__file__).resolve().parent.parent
ANSI = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')


def load_env():
    env = {}
    p = ROOT / 'server.env'
    if not p.exists():
        sys.exit(f'no {p}: create it with PTERO_URL, PTERO_SERVER, PTERO_API_KEY')
    for line in p.read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    for k in ('PTERO_URL', 'PTERO_SERVER', 'PTERO_API_KEY'):
        if not env.get(k):
            sys.exit(f'{k} missing from server.env')
    env['PTERO_URL'] = env['PTERO_URL'].rstrip('/')
    return env


class Panel:
    def __init__(self, env):
        self.url, self.sid = env['PTERO_URL'], env['PTERO_SERVER']
        self.h = {'Authorization': f"Bearer {env['PTERO_API_KEY']}",
                  'Accept': 'application/json', 'Content-Type': 'application/json'}

    def get(self, path):
        r = requests.get(f'{self.url}/api/client/servers/{self.sid}{path}', headers=self.h, timeout=20)
        r.raise_for_status()
        return r.json()

    def post(self, path, body):
        r = requests.post(f'{self.url}/api/client/servers/{self.sid}{path}', headers=self.h,
                          json=body, timeout=20)
        r.raise_for_status()
        return r

    def state(self):
        a = self.get('/resources')['attributes']
        r = a['resources']
        return (f"{a['current_state']}  mem {r['memory_bytes'] / 2**30:.2f} GiB  "
                f"cpu {r['cpu_absolute']:.0f}%  uptime {r['uptime'] / 1000:.0f}s")

    def ws_credentials(self):
        d = self.get('/websocket')['data']
        return d['token'], d['socket']


async def follow(panel, backlog, duration, power, command):
    token, socket = panel.ws_credentials()
    started = time.monotonic()
    async with websockets.connect(socket, origin=panel.url, max_size=None) as ws:
        await ws.send(json.dumps({'event': 'auth', 'args': [token]}))
        while True:
            left = None if duration is None else duration - (time.monotonic() - started)
            if left is not None and left <= 0:
                return
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=left)
            except asyncio.TimeoutError:
                return
            msg = json.loads(raw)
            ev, args = msg.get('event'), msg.get('args') or []
            if ev == 'auth success':
                if backlog:
                    await ws.send(json.dumps({'event': 'send logs', 'args': [None]}))
                if power:
                    await ws.send(json.dumps({'event': 'set state', 'args': [power]}))
                    print(f'>>> power: {power}', flush=True)
                if command:
                    await ws.send(json.dumps({'event': 'send command', 'args': [command]}))
                    print(f'>>> command: {command}', flush=True)
                if not backlog and not power and not command and duration == 0:
                    return
            elif ev == 'token expiring':
                token, _ = panel.ws_credentials()
                await ws.send(json.dumps({'event': 'auth', 'args': [token]}))
            elif ev == 'token expired':
                print('>>> token expired, reconnecting', flush=True)
                return await follow(panel, False, None if duration is None else left, None, None)
            elif ev == 'status':
                print(f'>>> status: {args[0]}', flush=True)
            elif ev in ('console output', 'daemon message', 'install output'):
                for a in args:
                    print(ANSI.sub('', a).rstrip(), flush=True)
            elif ev in ('daemon error', 'jwt error'):
                print(f'>>> {ev}: {args}', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--duration', type=float, default=None, help='seconds to follow (default: until Ctrl-C)')
    ap.add_argument('--no-follow', action='store_true', help='print the backlog and exit')
    ap.add_argument('--no-backlog', action='store_true', help='skip the stored log lines')
    ap.add_argument('--power', choices=['start', 'stop', 'restart', 'kill'])
    ap.add_argument('--command')
    ap.add_argument('--state', action='store_true')
    a = ap.parse_args()
    # Piped output defaults to cp1252 on Windows; the host log carries a BOM.
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    panel = Panel(load_env())
    if a.state:
        print(panel.state())
        return
    duration = 3 if a.no_follow else a.duration  # 3 s is enough for the backlog to arrive
    try:
        asyncio.run(follow(panel, not a.no_backlog, duration, a.power, a.command))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
