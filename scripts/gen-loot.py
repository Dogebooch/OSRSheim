#!/usr/bin/env python3
r"""Generate the Drop That loot cfgs from loot\*.csv. Never edit the cfgs by hand.

    python scripts\gen-loot.py                 write both cfgs (time-normalized preset)
    python scripts\gen-loot.py --diff          print what would change, write nothing
    python scripts\gen-loot.py --check         exit 0 = cfgs match the tables, 1 = stale, 2 = test mode on disk
    python scripts\gen-loot.py --literal       OSRS fractions as-is (every class multiplier = 1)
    python scripts\gen-loot.py --wiring        every ChanceToDrop = 100: spawn 3, kill, watch each entry fire
    python scripts\gen-loot.py --marker Greydwarf Flint   add a 100% x1 kill counter to one creature
    --allow-behind   write even when origin/main has newer loot\ or gen-loot.py (refused otherwise)

Tables in loot\:
  classes.csv    class, valheim_kills_hr, osrs_kills_hr   multiplier = osrs / valheim
  creatures.csv  biome, creature, class, list             output order; one UseDropList per creature
  lists.csv      list, class, first_id                    Gem lists 110+, Rare lists 120+
                 a creature of another class gets a copy at its own multiplier (GemTableTier3Roamer)
  drops.csv      owner, item, min, max, chance, flags, id owner = creature or list; rows in ID order
chance "30" = flat percent. chance "1/256" = OSRS rate x the owner's class multiplier, capped at 100.
flags: one-per-player (amount 1 items only), key=<global key>.
id: blank = next free (100+ creatures, first_id+ lists); set it to pin a slot (uniques 102, pets 103).
Coins purses above 100 are split into <=100 chunks: extras at 106+ (creatures) / 130+ (lists).
Writes drop_that.character_drop.cfg and drop_that.character_drop_list.shared_tables.cfg to the profile.
"""
import csv
import os
import sys
from pathlib import Path

from main_guard import require_current

ROOT = Path(__file__).resolve().parent.parent
LOOT = ROOT / 'loot'
CFG = Path(os.environ['APPDATA']) / 'com.kesomannen.gale/valheim/profiles/OSRSheim/BepInEx/config'
MAIN = 'drop_that.character_drop.cfg'
LISTS = 'drop_that.character_drop_list.shared_tables.cfg'
CHUNK = 100
CREATURE_BASE, CREATURE_OVERFLOW, LIST_OVERFLOW = 100, 106, 130
NUMERIC = {'AmountMin', 'AmountMax', 'ChanceToDrop'}


def fail(msg):
    print('ERROR', msg)
    sys.exit(1)


def read_csv(name):
    with open(LOOT / name, newline='', encoding='utf-8') as f:
        rows = []
        for row in csv.DictReader(f):
            row = {k: (v or '').strip() for k, v in row.items()}
            first = next(iter(row.values()))
            if first and not first.startswith('#'):
                rows.append(row)
        return rows


def fmt(x):
    s = f'{x:.7f}'.rstrip('0').rstrip('.')
    return s or '0'


def chunks(lo, hi):
    n = -(-hi // CHUNK)
    return [(lo // n + (i < lo % n), hi // n + (i < hi % n)) for i in range(n)]


def load(mode, marker):
    classes = {}
    for r in read_csv('classes.csv'):
        v, o = float(r['valheim_kills_hr']), float(r['osrs_kills_hr'])
        if v <= 0 or o <= 0:
            fail(f'classes.csv {r["class"]}: kills/hr must be > 0')
        classes[r['class']] = 1.0 if mode == 'literal' else o / v
    creatures = read_csv('creatures.csv')
    lists = read_csv('lists.csv')
    drops = {}
    for r in read_csv('drops.csv'):
        drops.setdefault(r['owner'], []).append(r)
    if marker:
        creature, item = marker
        if creature not in {c['creature'] for c in creatures}:
            fail(f'--marker: {creature} is not in creatures.csv')
        drops.setdefault(creature, []).append(
            {'owner': creature, 'item': item, 'min': '1', 'max': '1', 'chance': '100', 'flags': '', 'id': ''})
    owners = {}
    seen = set()
    for c in creatures:
        if c['creature'] in seen:
            fail(f'creatures.csv: {c["creature"]} listed twice')
        seen.add(c['creature'])
        owners[c['creature']] = c
    for l in lists:
        if l['list'] in owners:
            fail(f'lists.csv: {l["list"]} clashes with a creature name')
        owners[l['list']] = l
    for c in creatures:
        if c['class'] not in classes:
            fail(f'creatures.csv {c["creature"]}: unknown class {c["class"]}')
        if c['list'] and c['list'] not in {l['list'] for l in lists}:
            fail(f'creatures.csv {c["creature"]}: unknown list {c["list"]}')
    for l in lists:
        if l['class'] not in classes:
            fail(f'lists.csv {l["list"]}: unknown class {l["class"]}')
    for owner in drops:
        if owner not in owners:
            fail(f'drops.csv: owner {owner} is in neither creatures.csv nor lists.csv')
    return classes, creatures, lists, drops


def chance(text, mult, mode):
    if mode == 'wiring':
        return 100.0
    if '/' in text:
        num, den = text.split('/', 1)
        p = 100.0 * float(num) / float(den) * mult
    else:
        p = float(text)
    if p <= 0:
        fail(f'chance {text!r} is not positive')
    return min(p, 100.0)


def entries(owner, rows, base, overflow, mult, mode):
    """Return (id, item, lo, hi, chance, one_per_player, key) rows for one owner, sorted by ID."""
    ids, nxt = [], base
    for r in rows:
        idx = int(r['id']) if r.get('id') else nxt
        if idx < base or idx in ids:
            fail(f'{owner} {r["item"]}: id {idx} is below {base} or already used')
        ids.append(idx)
        nxt = max(nxt, idx) + 1
    overflow = max(overflow, nxt)
    out = []
    for idx, r in zip(ids, rows):
        item = r['item']
        lo, hi = int(r['min']), int(r['max'])
        flags = set(r['flags'].split())
        one = 'one-per-player' in flags
        key = next((f[4:] for f in flags if f.startswith('key=')), None)
        bad = flags - {'one-per-player'} - {f for f in flags if f.startswith('key=')}
        if bad:
            fail(f'{owner} {item}: unknown flags {sorted(bad)}')
        if not 1 <= lo <= hi:
            fail(f'{owner} {item}: bad amount {lo}-{hi}')
        if one and (hi != 1 or item == 'Coins'):
            fail(f'{owner} {item}: one-per-player forces amount 1; never on a purse')
        p = chance(r['chance'], mult, mode)
        if hi > CHUNK and item != 'Coins':
            fail(f'{owner} {item}: max {hi} above the {CHUNK} per-entry cap (only Coins split)')
        parts = chunks(lo, hi)
        out.append((idx, item, parts[0][0], parts[0][1], p, one, key))
        for lo2, hi2 in parts[1:]:
            out.append((overflow, item, lo2, hi2, p, one, key))
            overflow += 1
    return sorted(out)


def entry_text(owner, e):
    idx, item, lo, hi, p, one, key = e
    lines = [f'[{owner}.{idx}]', f'PrefabName = {item}', f'AmountMin = {lo}', f'AmountMax = {hi}',
             f'ChanceToDrop = {fmt(p)}', 'ScaleByLevel = false']
    if one:
        lines.append('DropOnePerPlayer = true')
    if key:
        lines.append(f'ConditionGlobalKeys = {key}')
    return '\n'.join(lines) + '\n\n'


def variant(c, list_class):
    """Shared lists roll at the creature's class; the list's own class keeps the plain name."""
    if c['class'] == list_class[c['list']]:
        return c['list']
    return c['list'] + c['class'].capitalize()


def generate(mode='time', marker=None):
    classes, creatures, lists, drops = load(mode, marker)
    list_class = {l['list']: l['class'] for l in lists}
    label = mode if not marker else f'marker {marker[0]} {marker[1]}'
    head = (f'# GENERATED by scripts\\gen-loot.py from loot\\*.csv. Edit the tables and regenerate.\n'
            f'# mode = {label}\n')
    mults = ' '.join(f'{k} x{fmt(v)}' for k, v in classes.items())
    main = [head, f'# class multipliers: {mults}\n\n']
    biome = None
    for c in creatures:
        name = c['creature']
        if c['biome'] != biome:
            biome = c['biome']
            main.append(f'# ===== {biome} =====\n\n')
        if c['list']:
            main.append(f'[{name}]\nUseDropList = {variant(c, list_class)}\n\n')
        rows = drops.get(name, [])
        es = entries(name, rows, CREATURE_BASE, CREATURE_OVERFLOW, classes[c['class']], mode)
        if c['list'] and any(e[0] >= 110 for e in es):
            fail(f'{name}: per-creature IDs reach 110+ and would collide with list {c["list"]}')
        main += [entry_text(name, e) for e in es]
    listtxt = [head, f'# class multipliers: {mults}\n\n']
    for l in lists:
        rows = drops.get(l['list'], [])
        if not rows:
            fail(f'list {l["list"]} has no rows in drops.csv')
        for k in classes:
            if not any(c['list'] == l['list'] and c['class'] == k for c in creatures):
                continue
            name = variant({'list': l['list'], 'class': k}, list_class)
            listtxt.append(f'# ---- {name} ({k}) ----\n\n')
            es = entries(name, rows, int(l['first_id']), LIST_OVERFLOW, classes[k], mode)
            listtxt += [entry_text(name, e) for e in es]
    return ''.join(main), ''.join(listtxt)


def parse(text):
    secs, cur = {}, None
    for raw in text.splitlines():
        s = raw.strip()
        if s.startswith('['):
            cur = secs.setdefault(s.strip('[]'), {})
        elif '=' in s and cur is not None and not s.startswith('#'):
            k, v = s.split('=', 1)
            k, v = k.strip(), v.strip()
            cur[k] = float(v) if k == 'ChanceToDrop' else int(v) if k in NUMERIC else v
    return secs


def diff(old, new):
    a, b = parse(old), parse(new)
    out = []
    for sec in list(a) + [s for s in b if s not in a]:
        if sec not in b:
            out.append(f'- [{sec}]')
        elif sec not in a:
            out.append(f'+ [{sec}] ' + ' '.join(f'{k}={v}' for k, v in b[sec].items()))
        else:
            for k in set(a[sec]) | set(b[sec]):
                if a[sec].get(k) != b[sec].get(k):
                    out.append(f'~ [{sec}] {k}: {a[sec].get(k)} -> {b[sec].get(k)}')
    return out


def on_disk(name):
    p = CFG / name
    return p.read_text(encoding='utf-8-sig') if p.exists() else ''


def disk_mode():
    lines = on_disk(MAIN).splitlines()
    return lines[1][len('# mode = '):] if len(lines) > 1 and lines[1].startswith('# mode = ') else 'hand-authored'


def main():
    args = sys.argv[1:]
    mode = 'time'
    marker = None
    if '--literal' in args:
        mode = 'literal'
    if '--wiring' in args:
        mode = 'wiring'
    if '--marker' in args:
        i = args.index('--marker')
        marker = (args[i + 1], args[i + 2])
    if '--check' in args:
        m = disk_mode()
        if m.startswith('wiring') or m.startswith('marker'):
            print(f'loot cfgs are in {m} mode: regenerate with gen-loot.py before a real session')
            sys.exit(2)
        cur_main, cur_lists = generate('literal' if m == 'literal' else 'time')
        d = diff(on_disk(MAIN), cur_main) + diff(on_disk(LISTS), cur_lists)
        print(f'{len(d)} difference(s) between loot\\*.csv and the cfgs on disk')
        sys.exit(1 if d else 0)
    new_main, new_lists = generate(mode, marker)
    if '--diff' in args:
        for line in diff(on_disk(MAIN), new_main) + diff(on_disk(LISTS), new_lists):
            print(line)
        return
    require_current(LOOT, __file__)
    (CFG / MAIN).write_text(new_main, encoding='utf-8')
    (CFG / LISTS).write_text(new_lists, encoding='utf-8')
    print(f'wrote {MAIN} ({new_main.count(chr(10) + "[")} sections) and {LISTS} '
          f'({new_lists.count(chr(10) + "[")} sections), mode = {mode if not marker else "marker"}')
    if mode != 'time' or marker:
        print('test mode: run gen-loot.py with no flags before a real session')


if __name__ == '__main__':
    main()
