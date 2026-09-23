#!/usr/bin/env python3
r"""Read a Valheim 1.0 world save (chunked format, world version 41) offline. Read-only.

    python scripts\world-scan.py <world folder> locations [--match a,b] [--near x,z,r]
                                 every generated location instance: name, x, y, z, placed
    python scripts\world-scan.py <world folder> sites [--kaupang x,z]
                                 candidate anchor per waystone node (ANCHORS), >= 500 m from Kaupang (default spawn)
    python scripts\world-scan.py <world folder> npcs     every KG MarketPlaceNPC: position, type, name, profile,
                                 dialogue, show condition; compared with reference\npc-layout.csv
    python scripts\world-scan.py <world folder> names <dir>...   add location names found in <dir> files to
                                 reference\location-names.txt (names are stored as hashes in the save)

<world folder> holds _main.<n>.db2 and *.chunk (count-world.py has the layout). Copy it first if a server
has it open. Locations: _main.<n>.db2 is a 16-byte header then a gzip stream; inside it the location list is
int count + count x {int name hash, float x, y, z, byte placed}. Positions are the world-gen placement,
y = terrain height there.
"""
import csv
import importlib.util
import math
import os
import re
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAMES = ROOT / 'reference/location-names.txt'
LAYOUT = ROOT / 'reference/npc-layout.csv'

spec = importlib.util.spec_from_file_location('count_world', ROOT / 'scripts/count-world.py')
cw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cw)
H = cw.stable_hash
NPC = H('MarketPlaceNPC')
KG_STRINGS = ['KGnpcNameOverride', 'KGnpcProfile', 'KGnpcDialogue', 'KGnpcShowCondition', 'KGnpcModelOverride']
KG_INTS = ['KGmarketNPC']
TYPES = ['None', 'Trader', 'Info', 'Teleporter', 'Feedback', 'Banker', 'Gambler', 'Quests', 'Buffer',
         'Transmog', 'Marketplace', 'Mail']


def main_file(folder):
    files = sorted(Path(folder).glob('_main.*.db2'), key=lambda p: p.stat().st_mtime)
    if not files:
        sys.exit(f'no _main.*.db2 in {folder}')
    b = files[-1].read_bytes()
    i = b.find(b'\x1f\x8b\x08')
    return zlib.decompressobj(31).decompress(b[i:])


def locations(folder):
    """[(name hash, x, y, z, placed)] found by shape: a count followed by that many 17-byte records."""
    u = main_file(folder)
    for p in range(0, len(u) - 4):
        n = struct.unpack_from('<i', u, p)[0]
        if not 100 < n < 500000 or p + 4 + 17 * n > len(u):
            continue
        recs = [struct.unpack_from('<ifffB', u, p + 4 + 17 * k) for k in range(min(n, 64))]
        if all(f in (0, 1) and all(math.isfinite(c) and abs(c) < 20000 for c in (x, y, z))
               for _, x, y, z, f in recs):
            return [struct.unpack_from('<ifffB', u, p + 4 + 17 * k) for k in range(n)]
    sys.exit('location list not found in the main file')


def name_map():
    return {H(n): n for n in NAMES.read_text(encoding='utf-8').split()} if NAMES.exists() else {}


def cmd_locations(folder, args):
    names = name_map()
    match = args[args.index('--match') + 1].lower().split(',') if '--match' in args else None
    near = [float(v) for v in args[args.index('--near') + 1].split(',')] if '--near' in args else None
    rows = []
    for h, x, y, z, f in locations(folder):
        name = names.get(h, f'#{h}')
        if match and not any(m in name.lower() for m in match):
            continue
        d = math.hypot(x - near[0], z - near[1]) if near else 0
        if near and d > near[2]:
            continue
        rows.append((d, name, x, y, z, f))
    rows.sort()
    for d, name, x, y, z, f in rows:
        print(f'{name:36s} {x:8.0f} {y:6.1f} {z:8.0f}  {"placed" if f else "-":6s}' + (f'  {d:5.0f} m' if near else ''))
    print(f'{len(rows)} locations')


# waystone node -> anchor location types (osrsheim_teleports.cfg placement rules), preferred first
ANCHORS = {
    'meadows': ['MWL_MeadowsTavern1', 'MWL_Tavern1', 'WoodVillage1', 'WoodVillage2', 'Eikthyrnir'],
    'blackforest': ['GDKing', 'Crypt4', 'Crypt3', 'Crypt2'],
    'swamp': ['SunkenCrypt4', 'Bonemass'],
    'mountain': ['Dragonqueen'],
    'plains': ['MWL_FulingVillage1', 'MWL_FulingVillage2', 'GoblinCamp2', 'GoblinKing'],
    'mistlands': ['Mistlands_Harbour1', 'Mistlands_Excavation1', 'Mistlands_DvergrBossEntrance1'],
    'ashlands': ['FortressRuins', 'CharredFortress', 'FaderLocation'],
    'deepnorth': ['NorthVillage', 'DN_Bossroom'],
}


def cmd_sites(folder, args):
    """Nearest anchors per waystone node that clear the 500 m rule from Kaupang (default: the spawn)."""
    names = name_map()
    locs = [(names.get(h, ''), x, y, z) for h, x, y, z, _ in locations(folder)]
    if '--kaupang' in args:
        kx, kz = (float(v) for v in args[args.index('--kaupang') + 1].split(','))
    else:
        kx, _, kz = next((x, y, z) for n, x, y, z in locs if n == 'StartTemple')
    print(f'Kaupang at {kx:.0f}, {kz:.0f}; stones need >= 500 m from it')
    for node, types in ANCHORS.items():
        hits = sorted((math.hypot(x - kx, z - kz), n, x, y, z) for n, x, y, z in locs
                      if n in types and math.hypot(x - kx, z - kz) >= 500)
        best = sorted(hits, key=lambda h: (types.index(h[1]) > 0, h[0]))[:3] if hits else []
        for d, n, x, y, z in sorted(best):
            print(f'  {node:12s} {n:32s} {x:7.0f} {y:6.1f} {z:7.0f}  {d:5.0f} m')
        if not best:
            print(f'  {node:12s} no anchor of {types}')


def read_zdo_full(r):
    """Like count-world.read_zdo, also returning the int and string fields."""
    flags = r.take('<H')
    if flags & 0x2000:
        x, z = r.take('<hh')
        pos = (float(x), None, float(z))
    else:
        pos = r.take('<fff')
    prefab = r.take('<i')
    if flags & 0x1000:
        v = r.take('<H')
        if not v & 0x8000:
            r.take('<H')
    ints, strings = {}, {}
    if flags & 0xFF:
        if flags & 0x01:
            r.take('<Bi')
        for bit, size in ((0x02, 4), (0x04, 12), (0x08, 16), (0x10, 4), (0x20, 8)):
            if flags & bit:
                for _ in range(r.num_items()):
                    k = r.take('<i')
                    if bit == 0x10:
                        ints[k] = r.take('<i')
                    else:
                        r.p += size
        if flags & 0x40:
            for _ in range(r.num_items()):
                k = r.take('<i')
                strings[k] = r.string().decode('utf-8', 'replace')
        if flags & 0x80:
            for _ in range(r.num_items()):
                r.take('<i')
                size = r.take('<i')
                r.p += size
    return prefab, pos, ints, strings


def cmd_npcs(folder):
    found = []
    for f in sorted(Path(folder).glob('*.chunk')):
        r = cw.Reader(f.read_bytes())
        if r.take('<h') != 41:
            continue
        for _ in range(r.take('<i')):
            prefab, pos, ints, strings = read_zdo_full(r)
            if prefab == NPC:
                s = {k: strings.get(H(k), '') for k in KG_STRINGS}
                t = ints.get(H('KGmarketNPC'), 0)
                found.append((pos, TYPES[t] if 0 <= t < len(TYPES) else t, s))
    with open(LAYOUT, newline='', encoding='utf-8') as fh:
        want = [r for r in csv.DictReader(fh) if all(r[c] for c in 'xyz')]
    for pos, t, s in sorted(found, key=lambda v: v[2]['KGnpcNameOverride']):
        y = '?' if pos[1] is None else f'{pos[1]:.0f}'
        print(f"{s['KGnpcNameOverride'] or '(unnamed)':24s} {pos[0]:7.0f} {y:>5s} {pos[2]:7.0f}  {t:11s} "
              f"{s['KGnpcProfile']:18s} {s['KGnpcDialogue']:16s} {s['KGnpcShowCondition'][:40]}")
    missing = [r for r in want if not any(math.hypot(p[0] - int(r['x']), p[2] - int(r['z'])) < 2 for p, _, _ in found)]
    print(f'{len(found)} MarketPlaceNPC in the save; layout rows with coordinates: {len(want)}, not found: {len(missing)}')
    for r in missing:
        print(f"  missing {r['npc']} @ {r['node']} ({r['x']}, {r['z']})")
    sys.exit(1 if missing else 0)


def cmd_names(folder, dirs):
    want = {h for h, *_ in locations(folder)}
    known = name_map()
    tok = re.compile(rb'[A-Za-z][A-Za-z0-9_\-]{2,60}')
    for d in dirs:
        for dp, _, fs in os.walk(d):
            for fn in fs:
                try:
                    b = open(os.path.join(dp, fn), 'rb').read()
                except OSError:
                    continue
                for m in set(tok.findall(b)) | {x.replace(b'\0', b'') for x in re.findall(rb'(?:[A-Za-z0-9_]\0){3,60}', b)}:
                    h = H(m.decode('latin1'))
                    if h in want and h not in known:
                        known[h] = m.decode('latin1')
    NAMES.write_text('\n'.join(sorted(set(known.values()))) + '\n', encoding='utf-8', newline='\n')
    print(f'{len(want & set(known))} of {len(want)} location types named; {NAMES.name} has {len(known)} names')


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit(__doc__)
    folder, cmd, rest = a[0], a[1], a[2:]
    if cmd == 'locations':
        cmd_locations(folder, rest)
    elif cmd == 'sites':
        cmd_sites(folder, rest)
    elif cmd == 'npcs':
        cmd_npcs(folder)
    elif cmd == 'names' and rest:
        cmd_names(folder, rest)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
