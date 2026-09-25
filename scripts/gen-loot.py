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
flags: one-per-player (amount 1 items only), key=<global key>, event (raid creatures only:
       ConditionCreatureStates = Event, Drop That DLL: MonsterAI.IsEventCreature),
       unique=<EpicLoot legendary ID>: rolled by EpicLoot, not Drop That, as that legendary (beam +
       inventory highlight). Creature rows only, amount 1, no one-per-player (EpicLoot rolls once per kill).
       Drop That item modifiers never apply to creature drops in this stack, so this is the only route.
       skill=<SkillType>: ConditionKilledBySkillType, the killing hit's weapon skill (Drop That 3.1.5,
       decompiled). Fire, poison and spirit land as DoT ticks with skill None, so a burn or poison kill
       never matches. A misspelled value makes Drop That drop the condition (the entry turns
       unconditional), so values are checked against SKILL_TYPES. Not with unique= or one-per-player.
id: blank = next free (100+ creatures, first_id+ lists); set it to pin a slot (uniques 102, pets 103).
Coins purses above 100 are split into <=100 chunks: extras at 106+ (creatures) / 130+ (lists).
Writes drop_that.character_drop.cfg, drop_that.character_drop_list.shared_tables.cfg and the unique
tables in EpicLoot\baseconfig\loottables.json (tables whose Loot is an OSRS_ item; owners lose RefObject).
"""
import csv
import json
import os
import sys
from pathlib import Path

from main_guard import require_current

ROOT = Path(__file__).resolve().parent.parent
LOOT = ROOT / 'loot'
CFG = ROOT / 'config'
MAIN = 'drop_that.character_drop.cfg'
LISTS = 'drop_that.character_drop_list.shared_tables.cfg'
EL_TABLES = 'EpicLoot/baseconfig/loottables.json'
EL_LEGENDARIES = 'EpicLoot/baseconfig/legendaries.json'
CHUNK = 100
CREATURE_BASE, CREATURE_OVERFLOW, LIST_OVERFLOW = 100, 106, 130
NUMERIC = {'AmountMin', 'AmountMax', 'ChanceToDrop'}
# Skills.SkillType names Drop That's ConditionKilledBySkillType parses (case-insensitive Enum.TryParse)
SKILL_TYPES = {'Swords', 'Knives', 'Clubs', 'Polearms', 'Spears', 'Blocking', 'Axes', 'Bows', 'ElementalMagic',
               'BloodMagic', 'Unarmed', 'Pickaxes', 'WoodCutting', 'Crossbows'}
FLAGS = {'one-per-player', 'event'}
FLAG_PREFIXES = ('key=', 'unique=', 'skill=')


def flag_errors(flags):
    """Problems with one drops.csv flags cell (a set of tokens); shared with post-build-check.py."""
    errs = [f'unknown flag {f}' for f in sorted(flags) if f not in FLAGS and not f.startswith(FLAG_PREFIXES)]
    for f in flags:
        if f.startswith('skill=') and f[6:] not in SKILL_TYPES:
            errs.append(f'skill={f[6:]} is not a weapon SkillType (Drop That would drop the condition)')
    if any(f.startswith('skill=') for f in flags) and (
            'one-per-player' in flags or any(f.startswith('unique=') for f in flags)):
        errs.append('skill= rules out one-per-player and unique=')
    return errs


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
    """Return (id, item, lo, hi, chance, one_per_player, key, unique, event, skill) rows for one owner, sorted by ID."""
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
        unique = next((f[7:] for f in flags if f.startswith('unique=')), None)
        event = 'event' in flags
        skill = next((f[6:] for f in flags if f.startswith('skill=')), None)
        bad = flag_errors(flags)
        if bad:
            fail(f'{owner} {item}: ' + '; '.join(bad))
        if not 1 <= lo <= hi:
            fail(f'{owner} {item}: bad amount {lo}-{hi}')
        if one and (hi != 1 or item == 'Coins'):
            fail(f'{owner} {item}: one-per-player forces amount 1; never on a purse')
        if unique and (hi != 1 or one):
            fail(f'{owner} {item}: unique forces amount 1 and rules out one-per-player')
        p = chance(r['chance'], mult, mode)
        if hi > CHUNK and item != 'Coins':
            fail(f'{owner} {item}: max {hi} above the {CHUNK} per-entry cap (only Coins split)')
        parts = chunks(lo, hi)
        out.append((idx, item, parts[0][0], parts[0][1], p, one, key, unique, event, skill))
        for lo2, hi2 in parts[1:]:
            out.append((overflow, item, lo2, hi2, p, one, key, unique, event, skill))
            overflow += 1
    return sorted(out)


def entry_text(owner, e):
    idx, item, lo, hi, p, one, key, unique, event, skill = e
    if unique:
        return ''
    lines = [f'[{owner}.{idx}]', f'PrefabName = {item}', f'AmountMin = {lo}', f'AmountMax = {hi}',
             f'ChanceToDrop = {fmt(p)}', 'ScaleByLevel = false', 'ConditionNotCreatureStates = Tamed']
    if one:
        lines.append('DropOnePerPlayer = true')
    if key:
        lines.append(f'ConditionGlobalKeys = {key}')
    if event:
        lines.append('ConditionCreatureStates = Event')
    if skill:
        lines.append(f'ConditionKilledBySkillType = {skill}')
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
    uniques = []
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
        uniques += [(name, e[1], e[4], e[7]) for e in es if e[7]]
    listtxt = [head, f'# class multipliers: {mults}\n\n']
    for l in lists:
        rows = drops.get(l['list'], [])
        if not rows:
            fail(f'list {l["list"]} has no rows in drops.csv')
        if any('unique=' in r['flags'] for r in rows):
            fail(f'list {l["list"]}: unique= is creature-only (EpicLoot tables are per creature)')
        for k in classes:
            if not any(c['list'] == l['list'] and c['class'] == k for c in creatures):
                continue
            name = variant({'list': l['list'], 'class': k}, list_class)
            listtxt.append(f'# ---- {name} ({k}) ----\n\n')
            es = entries(name, rows, int(l['first_id']), LIST_OVERFLOW, classes[k], mode)
            listtxt += [entry_text(name, e) for e in es]
    return ''.join(main), ''.join(listtxt), el_tables(uniques)


def el_tables(uniques):
    """Rewrite loottables.json: drop old OSRS_ tables, add one standalone Legendary table per unique row.
    A RefObject table is an alias of its tier (AddLootTable), so owners are detached from theirs.
    Level 4 LeveledLoot covers CLLC levels above 3; levels 1-3 read the top-level Drops/Loot."""
    text = on_disk(EL_TABLES)
    if not text:
        fail(f'{EL_TABLES} missing from config\\')
    data = json.loads(text)
    legs = json.loads(on_disk(EL_LEGENDARIES))['LegendaryItems']
    for owner, item, p, lid in uniques:
        if not any(x['ID'] == lid for x in legs):
            fail(f'{owner} {item}: unique={lid} is not in {EL_LEGENDARIES}')
    owners = {u[0] for u in uniques}
    kept = []
    for t in data['LootTables']:
        if any(str(d.get('Item', '')).startswith('OSRS_') for d in t.get('Loot') or []):
            continue
        if t['Object'] in owners:
            t['RefObject'] = None
        kept.append(t)
    for owner, item, p, lid in uniques:
        drops = [[0.0, round(100.0 - p, 7)], [1.0, round(p, 7)]]
        loot = [{'Item': item, 'Weight': 1.0, 'Rarity': [0.0, 0.0, 0.0, 1.0, 0.0, 0.0]}]
        kept.append({'Object': owner, 'RefObject': None, 'Drops': drops, 'Loot': loot,
                     'LeveledLoot': [{'Level': 4, 'Drops': drops, 'Loot': loot}]})
    data['LootTables'] = kept
    return json.dumps(data, indent=2).replace('\n', '\r\n')


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
    return p.read_bytes().decode('utf-8-sig') if p.exists() else ''


def el_diff(new):
    old = on_disk(EL_TABLES)
    if old == new:
        return []
    key = lambda t: json.dumps(t, sort_keys=True)
    a = {key(t) for t in json.loads(old)['LootTables']} if old else set()
    b = {key(t) for t in json.loads(new)['LootTables']}
    return ([f'- {EL_TABLES} {s[:160]}' for s in sorted(a - b)] +
            [f'+ {EL_TABLES} {s[:160]}' for s in sorted(b - a)] or [f'~ {EL_TABLES} formatting only'])


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
        cur_main, cur_lists, cur_el = generate('literal' if m == 'literal' else 'time')
        d = diff(on_disk(MAIN), cur_main) + diff(on_disk(LISTS), cur_lists) + el_diff(cur_el)
        print(f'{len(d)} difference(s) between loot\\*.csv and the cfgs on disk')
        sys.exit(1 if d else 0)
    new_main, new_lists, new_el = generate(mode, marker)
    if '--diff' in args:
        for line in diff(on_disk(MAIN), new_main) + diff(on_disk(LISTS), new_lists) + el_diff(new_el):
            print(line)
        return
    require_current(LOOT, __file__)
    (CFG / MAIN).write_text(new_main, encoding='utf-8')
    (CFG / LISTS).write_text(new_lists, encoding='utf-8')
    (CFG / EL_TABLES).write_bytes(new_el.encode('utf-8'))
    print(f'wrote {MAIN} ({new_main.count(chr(10) + "[")} sections) and {LISTS} '
          f'({new_lists.count(chr(10) + "[")} sections), mode = {mode if not marker else "marker"}')
    if mode != 'time' or marker:
        print('test mode: run gen-loot.py with no flags before a real session')


if __name__ == '__main__':
    main()
