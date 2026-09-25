#!/usr/bin/env python3
r"""Post-build check: the authored configs are written correctly, not just semantically valid.

    python scripts\post-build-check.py            everything (formatting, generators, validator)
    python scripts\post-build-check.py --format   formatting and parity only, skip the validator
    python scripts\post-build-check.py --repo     check the repo alone (another session holds the profile)

Run after any authoring pass, before `sync-configs.ps1 -Push` and before a launch.

  1. Bytes    no file flips its line endings against git HEAD (.gitattributes: byte-for-byte,
              no EOL conversion, ever), new wackydb ymls match the folder's LF, no BOM,
              every authored file ends with a newline.
  2. Clones   every wackysDatabase yml parses, `name` matches the filename, clonePrefabName is
              set, m_weight is present (no m_weight = wackydb drops the file silently), names
              are unique, and every OSRS_* named in a cfg or in loot\*.csv has a yml.
  3. Tables   loot\*.csv headers, column counts, numeric ids, chance syntax, display text.
  4. KG cfgs  ONE data line per gambler profile (KG keeps only the last and drops the rest
              silently), cost and prize tokens pair up, amounts and ranges are sane, every
              OpenUI target exists, no duplicate section headers or banker entries.
  5. Sync     generated cfgs match loot\*.csv, and the repo copy matches the profile copy.
  6. Semantics  validate-configs.py.

Exit 0 = clean. Exit 1 = at least one ERROR. WARNs are advisory.
"""
import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOOT = ROOT / 'loot'
CFG = ROOT / 'config'
KG = CFG / 'Marketplace/Configs'
ITEMS = CFG / 'wackysDatabase/Items'
PROFILE = Path(os.environ.get('APPDATA', '')) / 'com.kesomannen.gale/valheim/profiles/OSRSheim/BepInEx/config'
TEXT = {'.cfg', '.csv', '.yml', '.yaml', '.json', '.txt'}
SKIP = ('wackysDatabase/Cache', 'Marketplace_Cached', 'Marketplace_KGChat', 'Marketplace/SavedData', '.bak')

REPO = '--repo' in sys.argv
errors, warns = [], []
def err(msg): errors.append(msg); print('ERROR ', msg)
def warn(msg): warns.append(msg); print('WARN  ', msg)
def ok(msg): print('ok    ', msg)


def eol(b):
    crlf = b.count(b'\r\n')
    lf = b.count(b'\n') - crlf
    if crlf and lf: return 'mixed'
    if crlf: return 'crlf'
    if lf: return 'lf'
    return 'none'


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True)


# ------------------------------------------------------------------ 1. bytes
changed = git('diff', '--name-only', 'HEAD').stdout.decode().split()
flips = 0
for rel in changed:
    p = ROOT / rel
    if not p.exists() or p.suffix not in TEXT | {'.py', '.ps1', '.md'}:
        continue
    head = git('show', f'HEAD:{rel}').stdout
    before, after = eol(head), eol(p.read_bytes())
    if before != after and 'none' not in (before, after):
        err(f'{rel}: line endings changed {before} -> {after} (.gitattributes forbids EOL conversion; '
            f'rewrite the file with its original bytes)')
        flips += 1
if not flips:
    ok(f'line endings: {len(changed)} changed file(s) keep their bytes')

untracked = git('ls-files', '-o', '--exclude-standard').stdout.decode().split()
tracked_yml = [f for f in ITEMS.glob('*.yml') if str(f.relative_to(ROOT)).replace('\\', '/') not in untracked]
folder_eol = {eol(f.read_bytes()) for f in tracked_yml} or {'lf'}
for f in ITEMS.glob('*.yml'):
    if eol(f.read_bytes()) not in folder_eol:
        err(f'{f.name}: line endings differ from the other clone ymls ({"/".join(sorted(folder_eol))})')
ok(f'wackydb ymls: {len(list(ITEMS.glob("*.yml")))} files, {"/".join(sorted(folder_eol))}')

# Mod-shipped files (EpicLoot baseconfig, Therzie translations, CLLC examples) ship without a
# trailing newline and are not ours to reformat; the rule applies to what we author.
AUTHORED = ('loot/', 'config/Marketplace/Configs/', 'config/wackysDatabase/Items/', 'config/wackysDatabase/Pieces/',
            'config/drop_that.', 'config/ItemConfig.yml', 'config/WackyMole.')
n_authored = 0
for f in [*CFG.rglob('*'), *LOOT.glob('*')]:
    rel = str(f.relative_to(ROOT)).replace('\\', '/')
    if not f.is_file() or f.suffix not in TEXT or any(s in rel for s in SKIP):
        continue
    b = f.read_bytes()
    if b.startswith(b'\xef\xbb\xbf'):
        warn(f'{rel}: UTF-8 BOM (readers here use utf-8-sig, but nothing else in the repo carries one)')
    if rel.startswith(AUTHORED):
        n_authored += 1
        if b and not b.endswith(b'\n'):
            err(f'{rel}: no trailing newline')
ok(f'byte hygiene: BOM repo-wide, trailing newline on {n_authored} authored files')

# ------------------------------------------------------------------ 2. clones
try:
    import yaml
except ImportError:
    yaml = None
clones, bad = {}, 0
for f in sorted(ITEMS.glob('*.yml')):
    text = f.read_text(encoding='utf-8-sig')
    if yaml:
        try:
            doc = yaml.safe_load(text) or {}
        except Exception as e:
            err(f'{f.name}: does not parse ({e})'); bad += 1; continue
    else:
        doc = {k: v.strip() for k, v in re.findall(r'^([A-Za-z_]+):[ \t]*(.*)$', text, re.M)}
    name = str(doc.get('name') or '').strip()
    if name != f.stem.replace('Item_', ''):
        err(f'{f.name}: name is {name!r}, expected {f.stem.replace("Item_", "")!r}'); bad += 1
    if not str(doc.get('clonePrefabName') or '').strip():
        err(f'{f.name}: no clonePrefabName'); bad += 1
    if doc.get('m_weight') in (None, ''):
        err(f'{f.name}: no m_weight (wackydb drops the file at load, silently)'); bad += 1
    if name in clones:
        err(f'{f.name}: name {name} already used by {clones[name]}'); bad += 1
    clones[name] = f.name
if not bad:
    ok(f'clone ymls: {len(clones)} parse, named and weighted')

referenced = set()
for f in [*KG.rglob('*.cfg'), *LOOT.glob('*.csv'), CFG / 'ItemConfig.yml']:
    if f.is_file():
        referenced |= set(re.findall(r'\bOSRS_[A-Za-z0-9_]+', f.read_text(encoding='utf-8-sig')))
missing = sorted(referenced - set(clones))
if missing:
    err(f'named in a cfg or table but no wackydb yml: {missing}')
else:
    ok(f'clone references: {len(referenced)} OSRS_* names all resolve')

# ------------------------------------------------------------------ 3. tables
HEADERS = {
    'classes.csv': ['class', 'valheim_kills_hr', 'osrs_kills_hr', 'members'],
    'creatures.csv': ['biome', 'creature', 'class', 'list', 'display'],
    'lists.csv': ['list', 'class', 'first_id'],
    'drops.csv': ['owner', 'item', 'min', 'max', 'chance', 'flags', 'id'],
    'collection-log.csv': ['category', 'prefab', 'display'],
}
for name, header in HEADERS.items():
    rows = (LOOT / name).read_text(encoding='utf-8').splitlines()
    if rows[0].split(',') != header:
        err(f'{name}: header is {rows[0]!r}, expected {",".join(header)}')
        continue
    for n, row in enumerate(rows[1:], 2):
        if not row.strip():
            err(f'{name}:{n}: blank line'); continue
        cells = row.split(',')
        if len(cells) != len(header):
            err(f'{name}:{n}: {len(cells)} columns, expected {len(header)}'); continue
        cells = [c.strip() for c in cells]
        if name == 'drops.csv':
            if not re.fullmatch(r'\d+(\.\d+)?|\d+/\d+', cells[4]):
                err(f'drops.csv:{n}: chance {cells[4]!r} is not a percent or a 1/x rate')
            if cells[6] and not cells[6].isdigit():
                err(f'drops.csv:{n}: id {cells[6]!r} is not a number')
            for f in cells[5].split():
                if f not in ('one-per-player', 'event') and not f.startswith(('key=', 'unique=')):
                    err(f'drops.csv:{n}: unknown flag {f!r}')
            if cells[5] == 'one-per-player' and cells[2:4] != ['1', '1']:
                err(f'drops.csv:{n}: one-per-player needs amount 1')
        if name == 'collection-log.csv' and ('|' in cells[2] or not cells[2]):
            err(f'collection-log.csv:{n}: display {cells[2]!r} is empty or contains |')
ok(f'loot tables: {len(HEADERS)} csvs, headers, columns, chances, flags and ids checked')

# ------------------------------------------------------------------ 4. KG cfgs
def sections(path):
    out, cur = {}, None
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            cur = line[1:-1].strip()
            if cur in out:
                err(f'{path.name}: duplicate section [{cur}]')
            out[cur] = []
        elif cur is not None and line and not line.startswith('#'):
            out[cur].append(line)
    return out


try:
    known = set(json.loads((ROOT / 'reference/verified-prefab-names.json').read_text(encoding='utf-8'))['items'])
except Exception as e:
    known = set(); warn(f'verified-prefab-names.json unreadable ({e}); skipping item name checks')
known |= set(clones)

gamblers = {}
for header, lines in sections(KG / 'Gamblers/osrsheim_gamblers.cfg').items():
    name = header.split('=')[0].strip()
    gamblers[name] = lines
    if '=' in header:
        queued = header.split('=', 1)[1].strip()
        if not queued.isdigit() or int(queued) < 1:
            err(f'gambler [{header}]: queued-roll count {queued!r} is not a positive number')
    if len(lines) != 1:
        err(f'gambler [{name}]: {len(lines)} data lines; KG parses only the last one and drops the rest')
        continue
    toks = [t.strip() for t in lines[0].split(',')]
    if len(toks) % 2 or len(toks) < 4:
        err(f'gambler [{name}]: {len(toks)} tokens; needs an even count of at least 4 (cost pair + one prize)')
        continue
    for i in range(0, len(toks), 2):
        item, amount = toks[i], toks[i + 1]
        if known and item not in known:
            err(f'gambler [{name}]: unknown item {item!r}')
        m = re.fullmatch(r'(\d+)(?:-(\d+))?', amount)
        if not m:
            err(f'gambler [{name}]: amount {amount!r} for {item} is not N or N-M')
        elif m.group(2) and int(m.group(2)) < int(m.group(1)):
            err(f'gambler [{name}]: range {amount} for {item} runs backwards')
        elif int(m.group(1)) < 1:
            err(f'gambler [{name}]: amount {amount} for {item} is zero')
    if i and len(lines[0]) > 400:
        warn(f'gambler [{name}]: data line is {len(lines[0])} chars; the KG parser limit is unmeasured')
ok(f'gamblers: {len(gamblers)} profiles, one data line each, {sum(len(v) for v in gamblers.values())} lines linted')

bank = sections(KG / 'Bankers/osrsheim_bank.cfg')
for name, lines in bank.items():
    dupes = {x for x in lines if lines.count(x) > 1}
    if dupes:
        err(f'banker [{name}]: duplicate entries {sorted(dupes)}')
    unknown = [x for x in lines if known and x not in known]
    if unknown:
        err(f'banker [{name}]: unknown items {unknown}')
ok(f'banker: {sum(len(v) for v in bank.values())} entries, no duplicates')

menus = {'gambler': gamblers, 'trader': sections(KG / 'Traders/osrsheim_traders.cfg'),
         'banker': bank, 'buffer': sections(KG / 'BufferProfiles/osrsheim_chapel.cfg'),
         'info': sections(KG / 'ServerInfos/osrsheim_guide.cfg')}
opens = 0
for f in KG.glob('Dialogues/*.cfg'):
    for node, lines in sections(f).items():
        for line in lines:
            m = re.search(r'Command:\s*OpenUI\s*,\s*(\w+)\s*,\s*([\w-]+)', line)
            if not m:
                continue
            opens += 1
            kind, target = m.group(1).lower(), m.group(2).strip()
            pool = menus.get(kind)
            if pool is not None and target not in {k.split('=')[0].strip() for k in pool}:
                err(f'{f.name} [{node}]: OpenUI {kind} "{target}" has no profile')
ok(f'dialogues: {opens} OpenUI targets resolve')

# ------------------------------------------------------------------ 5. sync
# every generator reads and writes the repo's config\, so these checks never touch the profile
for script, what in (('gen-loot.py', 'loot cfgs'), ('gen-collection-log.py', 'collection log'),
                     ('gen-handbook.py', 'handbook'), ('gen-npcs.py', 'npc placement')):
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / script), '--check'],
                       capture_output=True, text=True)
    (ok if r.returncode == 0 else err)(f'{what}: {r.stdout.strip() or r.stderr.strip()}')

if PROFILE.is_dir():
    drift = []
    for f in CFG.rglob('*'):
        rel = str(f.relative_to(CFG)).replace('\\', '/')
        if not f.is_file() or f.suffix not in TEXT or any(s in rel for s in SKIP):
            continue
        twin = PROFILE / rel
        if not twin.is_file() or twin.read_bytes() != f.read_bytes():
            drift.append(rel)
    if drift:
        (warn if REPO else err)(f'repo config\\ differs from the profile ({len(drift)}): {drift[:6]}'
                                f'{"..." if len(drift) > 6 else ""} - run scripts\\sync-configs.ps1 -Push')
    else:
        ok('repo config\\ matches the Gale profile byte for byte')
else:
    warn(f'no Gale profile at {PROFILE}; skipped the parity check')

# ------------------------------------------------------------------ 6. validator
if not REPO and '--format' not in sys.argv:
    print('\n--- validate-configs.py ---')
    r = subprocess.run([sys.executable, str(ROOT / 'scripts/validate-configs.py')], capture_output=True, text=True)
    tail = [l for l in r.stdout.splitlines() if l.startswith(('ERROR', 'WARN', 'SUMMARY'))]
    print('\n'.join(tail) or r.stdout.strip()[-400:])
    if r.returncode != 0:
        errors.append('validate-configs.py failed')

print(f'\nPOST-BUILD: {len(errors)} error(s), {len(warns)} warning(s)')
sys.exit(1 if errors else 0)
