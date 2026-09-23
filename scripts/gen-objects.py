#!/usr/bin/env python3
r"""Generate drop_that.drop_table.cfg from loot\objects.csv. Never edit the cfg by hand.

    python scripts\gen-objects.py              write the cfg (rates solved against the dump)
    python scripts\gen-objects.py --diff       print what would change, write nothing
    python scripts\gen-objects.py --check      exit 0 = cfg matches the table, 1 = stale
    python scripts\gen-objects.py --rates      print the solved rate table, write nothing
    python scripts\gen-objects.py --wiring     every entry at a winning weight: chop/mine once, watch it fire

Table in loot\:
  objects.csv   group, object, item, min, max, target, note

Drop That's DropTable module has no per-entry chance: an entry's Weight is its share of a
fixed number of picks (DropMin..DropMax), so rarity only exists relative to the vanilla
entries already on the table. This script reads those vanilla numbers out of
BepInEx\Debug\drop_that.drop_table.prefabs.txt and solves for the weight:

    P = DropChance * mean over N in DropMin..DropMax of [ 1 - (1 - w/(W+w))^N ]

target "1/5000" = that probability per destruction. "w=30" pins a literal weight for entries
that are not rate-driven. Two guards, both of which the hand-authored file tripped:
  - vanilla total weight 0 means there is no denominator and the entry fires at 100%. ERROR.
  - an entry taking more than MAX_SHARE of the picks is stealing vanilla yield. ERROR.

Writes to the Gale profile, like gen-loot.py; run scripts\sync-configs.ps1 -Pull to stage it.
"""
import csv
import os
import re
import sys
from pathlib import Path

from main_guard import require_current

ROOT = Path(__file__).resolve().parent.parent
LOOT = ROOT / 'loot'
PROFILE = Path(os.environ['APPDATA']) / 'com.kesomannen.gale/valheim/profiles/OSRSheim/BepInEx'
CFG = PROFILE / 'config'
DUMP = PROFILE / 'Debug/drop_that.drop_table.prefabs.txt'
OUT = 'drop_that.drop_table.cfg'
FIRST_ID = 100
MAX_SHARE = 0.01
WIRING_WEIGHT = 10000.0


def fail(msg):
    print('ERROR', msg)
    sys.exit(1)


def read_dump():
    """base prefab -> vanilla table numbers, from Drop That's own prefab dump."""
    if not DUMP.exists():
        fail(f'missing dump {DUMP} - load a world once with the Drop That dump flags on')
    tables, entries, cur, src, cursrc = {}, {}, None, {}, None
    for line in DUMP.read_text(encoding='utf-8-sig').splitlines():
        m = re.match(r'^## DropTable Source: (\S+)', line)
        if m:
            cursrc = m.group(1).rstrip(';')
            continue
        m = re.match(r'^\[([^\]]+)\]', line)
        if m:
            cur = m.group(1)
            if '.' in cur:
                entries[cur] = {}
            else:
                tables[cur] = {}
                src[cur] = cursrc
            continue
        if cur and '=' in line:
            k, v = line.split('=', 1)
            (entries if '.' in cur else tables)[cur][k.strip()] = v.strip()
    out = {}
    for base, head in tables.items():
        ents = [(v.get('PrefabName'), float(v.get('Weight', 0)))
                for k, v in entries.items() if k.rsplit('.', 1)[0] == base]
        out[base] = {
            'W': sum(w for _, w in ents),
            'lo': int(head.get('DropMin', 1)),
            'hi': int(head.get('DropMax', 1)),
            'dc': float(head.get('DropChance', 100)) / 100.0,
            'once': head.get('DropOnlyOnce') == 'True',
            'ents': ents,
            'src': src.get(base, '?'),
        }
    return out


def chance(w, t):
    """P(at least one) per destruction, for an added entry of weight w."""
    if w <= 0:
        return 0.0
    p = w / (t['W'] + w)
    ns = range(t['lo'], t['hi'] + 1)
    return t['dc'] * sum(1 - (1 - p) ** n for n in ns) / len(list(ns))


def solve(t, target):
    lo, hi = 0.0, max(t['W'], 1.0)
    while chance(hi, t) < target:
        hi *= 2
        if hi > 1e9:
            return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if chance(mid, t) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def parse_target(text):
    """'1/5000' or '0.02%' -> probability; 'w=30' -> ('literal', 30.0)."""
    text = text.strip()
    if text.startswith('w='):
        return ('literal', float(text[2:]))
    if text.endswith('%'):
        return ('rate', float(text[:-1]) / 100.0)
    if '/' in text:
        a, b = text.split('/', 1)
        return ('rate', float(a) / float(b))
    return ('rate', float(text))


def rows():
    with open(LOOT / 'objects.csv', newline='', encoding='utf-8') as f:
        out = []
        for n, row in enumerate(csv.DictReader(f), start=2):
            if not row.get('object') or row['object'].lstrip().startswith('#'):
                continue
            row['_line'] = n
            out.append(row)
    return out


def build(wiring=False):
    dump = read_dump()
    solved, order = [], []
    for row in rows():
        obj, item, line = row['object'].strip(), row['item'].strip(), row['_line']
        t = dump.get(obj)
        if t is None:
            fail(f'objects.csv line {line}: object {obj!r} is not in the prefabs dump')
        kind, value = parse_target(row['target'])
        if wiring:
            w, target = WIRING_WEIGHT, None
        elif kind == 'literal':
            w, target = value, None
        else:
            target = value
            if t['W'] <= 0:
                fail(f'objects.csv line {line}: {obj} has no vanilla drop entries (total weight 0), '
                     f'so any weight fires at 100%. Pick a table with vanilla drops.')
            w = solve(t, target)
            if w is None:
                fail(f'objects.csv line {line}: cannot reach {row["target"]} on {obj}')
            share = w / (t['W'] + w)
            if share > MAX_SHARE:
                fail(f'objects.csv line {line}: {item} on {obj} would take {share:.1%} of the picks '
                     f'(cap {MAX_SHARE:.0%}); it would eat vanilla yield')
        if obj not in order:
            order.append(obj)
        solved.append((obj, item, row, w, target, t))

    lines = [
        '# OSRSheim object/skilling drops. GENERATED by scripts\\gen-objects.py from',
        '# loot\\objects.csv - do not edit by hand, your edit will be overwritten.',
        '#',
        '# Weight is a share of the table\'s picks, not a chance. Each weight below was solved',
        '# against the vanilla numbers in BepInEx\\Debug\\drop_that.drop_table.prefabs.txt, quoted',
        '# per table as: vanilla total weight W, DropChance, DropMin-DropMax picks.',
        '#',
        '# Woodcutting hangs on TreeBase (one roll per tree felled), not on the *_log tables:',
        '# most log tables are empty in vanilla, so any entry added to one fires at 100%.',
    ]
    if wiring:
        lines += ['#', '# *** WIRING MODE: every entry is at a winning weight. NOT a shipping config. ***']
    for obj in order:
        t = dump[obj]
        mine = [s for s in solved if s[0] == obj]
        ent = ', '.join(f'{n}:{w:g}' for n, w in t['ents']) or 'none'
        lines += [
            '',
            f'# ---- {obj} ({t["src"]}) ----',
            f'# vanilla: W={t["W"]:g}, DropChance={t["dc"] * 100:g}%, picks {t["lo"]}-{t["hi"]}'
            + (', DropOnlyOnce' if t['once'] else '') + f' | {ent}',
        ]
        for i, (_, item, row, w, target, _t) in enumerate(mine):
            note = row.get('note', '').strip()
            # Comments go on their own line: Drop That reads the whole right-hand side of
            # "Weight =" as the value, so a trailing "# ..." would not parse as a float.
            rate = f'{row["target"]} per destruction' if target else 'literal weight'
            lines += ['', f'# {item}: {rate}' + (f'; {note}' if note else '')]
            if not target:
                # Literal weights are deliberate and can be common. Mark them so validate-configs.py's rate cap skips them on purpose
                # rather than by accident.
                lines.append(f'# rate-exempt: authored weight, not solved from a target')
            lines += [
                f'[{obj}.{FIRST_ID + i}]',
                f'PrefabName = {item}',
                'Weight = ' + f'{w:.8f}'.rstrip('0').rstrip('.'),
                f'AmountMin = {row["min"].strip()}',
                f'AmountMax = {row["max"].strip()}',
            ]
    return '\n'.join(lines) + '\n', solved


def print_rates(solved):
    print('%-26s %-20s %9s %10s %9s %8s' % ('object', 'item', 'weight', 'target', 'actual', 'share'))
    for obj, item, row, w, target, t in solved:
        got = chance(w, t)
        print('%-26s %-20s %9.6f %10s %8.4f%% %7.3f%%' % (
            obj, item, w, row['target'], got * 100, w / (t['W'] + w) * 100))


def main():
    args = sys.argv[1:]
    text, solved = build(wiring='--wiring' in args)
    if '--rates' in args:
        print_rates(solved)
        return
    path = CFG / OUT
    old = path.read_text(encoding='utf-8-sig') if path.exists() else ''
    if '--check' in args:
        if old.replace('\r\n', '\n') != text:
            print(f'{OUT} differs from loot\\objects.csv')
            sys.exit(1)
        print(f'{OUT} matches loot\\objects.csv')
        return
    if '--diff' in args:
        import difflib
        d = list(difflib.unified_diff(old.replace('\r\n', '\n').splitlines(), text.splitlines(),
                                      OUT + ' (on disk)', OUT + ' (from objects.csv)', lineterm=''))
        print('\n'.join(d) if d else 'no change')
        return
    require_current(LOOT, __file__)
    # newline='' keeps the LF endings the repo stores (.gitattributes: "* -text",
    # no EOL conversion ever); text mode would rewrite them to CRLF on Windows.
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(text)
    n = len({s[0] for s in solved})
    print(f'wrote {path} ({len(solved)} entries across {n} objects)')


if __name__ == '__main__':
    main()
