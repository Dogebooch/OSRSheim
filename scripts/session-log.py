#!/usr/bin/env python3
r"""Real-play telemetry from the character save (.fch). `watch.py` runs `auto` after every game exit.

    python scripts\session-log.py auto [--note TEXT]     snap every save changed since its last snap; diff each
    python scripts\session-log.py publish                copy the session logs (own + host-pulled) into reference\sessions\ (commit it)
    python scripts\session-log.py snap [--char NAME | --file PATH] [--note TEXT]   one snap by hand
    python scripts\session-log.py diff [--char NAME] [--note TEXT]   last two snaps of a character -> one row
    python scripts\session-log.py show [--char NAME | --file PATH] [--json]   parsed save: stats, skills, coins, recipes

Snaps, and the complete local session log <char>.csv, live in the MAIN checkout's .cache\sessions\ (shared by
worktrees). One row = the play between two snaps (TimeInBase + TimeOutOfBase), so a session the watcher missed is
folded into the next row, never lost. `hours` is active play: watch.py's away time (game not focused, or no input
for 2 min: pause menu, notes, Claude) between the two saves is cut and shown as `away_h`. `console` lists commands used between the snaps: those rows are not real play.
<char>.jsonl holds one detail line per row: kills per enemy, pickups per item, new player keys, KG quests finished
(`[MPASN]questCD=<uid>`, named from the quest cfgs) and KG custom values (`kgMarketplaceValue@<name>`) moved.
Published and shared rows are named <steam account id>-<char> (local for characters_local).
Character files: Steam cloud <SteamPath>\userdata\*\892970\remote\characters, then
LocalLow\IronGate\Valheim\characters_local.
Format: PlayerProfile.LoadPlayerFromDisk and Player.Load (decompiled 1.0.15; profile v38+, player data v29+).
Stats row 1 is the all-time total. Mod skills (Smoothbrain SkillManager) are saved as abs(StableHash(name)),
resolved from MOD_SKILLS (Smoothbrain Cooking and Farming reuse vanilla 105 and 106).
"""
import argparse
import csv
import glob
import io
import json
import os
import shutil
import struct
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)


def main_root():
    """The main checkout: worktrees share its .cache, so snaps and the local session log live in one place."""
    try:
        common = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--path-format=absolute', '--git-common-dir'],
                                capture_output=True, text=True, creationflags=NO_WINDOW).stdout.strip()
        return Path(common).parent if common else ROOT
    except OSError:
        return ROOT


def steam_dir():
    """Steam's install folder from the registry (it can be on any drive), else the default."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam') as k:
            return Path(winreg.QueryValueEx(k, 'SteamPath')[0])
    except (ImportError, OSError):
        return Path(r'C:\Program Files (x86)\Steam')


MAIN = main_root()
SNAPS = MAIN / '.cache' / 'sessions'                   # snaps + <char>.csv/.jsonl, the complete local session log
AWAY = MAIN / '.cache' / 'watch' / 'away.csv'           # watch.py: pause menu, alt-tab, no input; not played
HOST_ROWS = MAIN / '.cache' / 'host' / 'sessions'      # other PCs' rows, pulled by host-data.py
PUB = ROOT / 'reference' / 'sessions'                  # committed copy (publish)
STEAM = steam_dir()
CHAR_DIRS = [*glob.glob(str(STEAM / 'userdata' / '*' / '892970' / 'remote' / 'characters')),
             str(Path(os.environ.get('USERPROFILE', '')) / 'AppData/LocalLow/IronGate/Valheim/characters_local')]
QUESTS = ROOT / 'config' / 'Marketplace' / 'Configs' / 'Quests'
QUEST_DONE, KG_VALUE = '[MPASN]questCD=', 'kgMarketplaceValue@'   # KG 10.0.1 Player.m_customData keys

STATS = ('Deaths CraftsOrUpgrades Builds Jumps Cheats EnemyHits EnemyKills EnemyKillsLastHits PlayerHits PlayerKills '
         'HitsTakenEnemies HitsTakenPlayers ItemsPickedUp Crafts Upgrades PortalsUsed DistanceTraveled DistanceWalk '
         'DistanceRun DistanceSail DistanceAir TimeInBase TimeOutOfBase Sleep ItemStandUses ArmorStandUses WorldLoads '
         'TreeChops Tree TreeTier0 TreeTier1 TreeTier2 TreeTier3 TreeTier4 TreeTier5 LogChops Logs MineHits Mines '
         'MineTier0 MineTier1 MineTier2 MineTier3 MineTier4 MineTier5 RavenHits RavenTalk RavenAppear CreatureTamed '
         'FoodEaten SkeletonSummons ArrowsShot TombstonesOpenedOwn TombstonesOpenedOther TombstonesFit DeathByUndefined '
         'DeathByEnemyHit DeathByPlayerHit DeathByFall DeathByDrowning DeathByBurning DeathByFreezing DeathByPoisoned '
         'DeathBySmoke DeathByWater DeathByEdgeOfWorld DeathByImpact DeathByCart DeathByTree DeathBySelf '
         'DeathByStructural DeathByTurret DeathByBoat DeathByStalagtite DoorsOpened DoorsClosed BeesHarvested '
         'SapHarvested TurretAmmoAdded TurretTrophySet TrapArmed TrapTriggered PlaceStacks PortalDungeonIn '
         'PortalDungeonOut BossKills BossLastHits SetGuardianPower SetPowerEikthyr SetPowerElder SetPowerBonemass '
         'SetPowerModer SetPowerYagluth SetPowerQueen SetPowerAshlands SetPowerDeepNorth UseGuardianPower '
         'UsePowerEikthyr UsePowerElder UsePowerBonemass UsePowerModer UsePowerYagluth UsePowerQueen UsePowerAshlands '
         'UsePowerDeepNorth DeathByCatapult DeathByCinderFire DeathByAshlandsOcean DeathByIncinerator CraftFood '
         'CraftFoodBonus CraftGrill CraftGrillBurnt CraftGrillBonus CraftWeapon CraftArmor CraftTrinket CraftAmmo '
         'CraftTorch CraftBait CraftOther HarvestCrop HarvestBerry HarvestMushroom HarvestVine HarvestBonus '
         'ConsecutiveDaysSurvived ConsecutiveDaysSurvivedMax MaxBuildingHeight MaxBuildingHeightWorld MaxComfort '
         'TreasureBuriedFound TreasureDungeonFound TreasureLocationFound LeviathanSink LavaLeviathanSink ExploreNorth '
         'ExploreSouth ExploreEast ExploreWest ExploreNorthNoMap ExploreSouthNoMap ExploreEastNoMap ExploreWestNoMap '
         'BossKillMultiplayer BossKillSolo VillagePointsMax DeepestDungeon DistanceSailHelm PlayerSpawn '
         'DeathByTreeTier0 DeathByTreeTier1 DeathByTreeTier2 DeathByTreeTier3 DeathByTreeTier4 DeathByTreeTier5 '
         'FishHooked FishLost FishCaught FishCaughtTier0 FishCaughtTier1 FishCaughtTier2 FishCaughtTier3 '
         'FishCaughtTier4 FishCaughtTier5 FishCaughtTier6 BuiltPieces BuiltPiecesNoDebt BuildPiecesRemoved '
         'BuildClusterMisc BuildClusterCrafting BuildClusterBuilding BuildClusterFloor BuildClusterWall '
         'BuildClusterRoof BuildClusterArchitecture BuildClusterFurniture BuildClusterLighting BuildClusterDecor '
         'BuildClusterStorage BuildClusterTransport BuildClusterFood BuildClusterMeads BuildClusterFeasts '
         'BuildClusterDefense BuildClusterStacks BuildClusterStairs BuildClusterDoors BuildClusterSeasonal '
         'TamedPetting TamedCommand TreeFir TreeOak TreePine TreeAshlands TreeYggdrasilShoot TreeSwamp TreeBeech '
         'TreeBirch TreeSnowFir TreeSnowPine DeathByDrawBridge DeathByAshlandsLava').split()
VANILLA_SKILLS = {1: 'Swords', 2: 'Knives', 3: 'Clubs', 4: 'Polearms', 5: 'Spears', 6: 'Blocking', 7: 'Axes', 8: 'Bows',
                  9: 'ElementalMagic', 10: 'BloodMagic', 11: 'Unarmed', 12: 'Pickaxes', 13: 'WoodCutting',
                  14: 'Crossbows', 100: 'Jump', 101: 'Sneak', 102: 'Run', 103: 'Swim', 104: 'Fishing', 105: 'Cooking',
                  106: 'Farming', 107: 'Crafting', 108: 'Dodge', 110: 'Ride'}
MOD_SKILLS = ['Mining', 'Lumberjacking', 'Building', 'Blacksmithing', 'Exploration', 'Sailing',
              'Evasion', 'Foraging', 'Ranching', 'Tenacity', 'Vitality', 'Alchemy', 'Wizardry', 'Pack Horse',
              'Hunting', 'Magic', 'Sorcery', 'Warfare', 'Blood Magic', 'Elemental Magic']
# per-hour columns: (name, stats keys summed)
RATES = [('kills', ['EnemyKills']), ('deaths', ['Deaths']), ('boss_kills', ['BossKills']),
         ('hits_dealt', ['EnemyHits']), ('hits_taken', ['HitsTakenEnemies']), ('crafts', ['Crafts']),
         ('upgrades', ['Upgrades']), ('builds', ['Builds']), ('trees', ['Tree']), ('mines', ['Mines']),
         ('crops', ['HarvestCrop']), ('fish', ['FishCaught']), ('food_eaten', ['FoodEaten']),
         ('portals', ['PortalsUsed']), ('sail_km', ['DistanceSail']), ('walk_km', ['DistanceWalk', 'DistanceRun'])]


def stable_hash(s):
    """Valheim StringExtensionMethods.GetStableHashCode, int32."""
    def i32(x):
        return (x + 2**31) % 2**32 - 2**31
    a = b = 5381
    i = 0
    while i < len(s) and s[i] != '\0':
        a = i32(((a << 5) + a) ^ ord(s[i]))
        if i == len(s) - 1 or s[i + 1] == '\0':
            break
        b = i32(((b << 5) + b) ^ ord(s[i + 1]))
        i += 2
    return i32(a + b * 1566083941)


SKILL_NAMES = {**{abs(stable_hash(n)): n for n in MOD_SKILLS}, **VANILLA_SKILLS}


class Pkg:
    def __init__(self, data):
        self.b = io.BytesIO(data)

    def _u(self, fmt, n):
        return struct.unpack('<' + fmt, self.b.read(n))[0]

    def int(self): return self._u('i', 4)
    def ushort(self): return self._u('H', 2)
    def long(self): return self._u('q', 8)
    def single(self): return self._u('f', 4)
    def byte(self): return self.b.read(1)[0]
    def bool(self): return self.byte() != 0
    def vec3(self): return struct.unpack('<3f', self.b.read(12))
    def bytes_(self): return self.b.read(self.int())

    def string(self):                                     # .NET BinaryReader: 7-bit length prefix, UTF-8
        n = shift = 0
        while True:
            c = self.byte()
            n |= (c & 0x7F) << shift
            shift += 7
            if not c & 0x80:
                break
        return self.b.read(n).decode('utf-8')

    def num_items(self):
        n = self.byte()
        return ((n & 0x7F) << 8) | self.byte() if n & 0x80 else n

    def sdict(self):
        return {self.string(): self.single() for _ in range(self.int())}


def parse(path):
    raw = Path(path).read_bytes()
    n = struct.unpack('<i', raw[:4])[0]
    p = Pkg(raw[4:4 + n])
    ver = p.int()
    if ver < 38:
        sys.exit(f'{path}: profile version {ver}; only 38+ is parsed')
    out = {'file': str(path), 'profile_version': ver}
    tot = {k: {} for k in ('world_keys', 'crafted', 'pickables', 'food', 'pieces', 'commands', 'worlds', 'pickups')}
    tot['enemies'] = [{}]
    if ver >= 46 or ver == 44:
        nstat, rows = p.int(), p.int()
        per = []
        for _ in range(rows):
            st = {(STATS[j] if j < len(STATS) else f'stat{j}'): p.single() for j in range(nstat)}
            extra = {'worlds': p.sdict(), 'world_keys': p.sdict(), 'commands': p.sdict()}
            extra['enemies'] = [p.sdict() for _ in range(p.int())]
            for k in ('pickups', 'crafted', 'pickables', 'food', 'pieces'):
                extra[k] = p.sdict()
            per.append((st, extra))
        out['stats'], tot = per[1] if len(per) > 1 else per[0]
    else:                                                                 # Stats2 (38-45): one row, dicts later
        out['stats'] = {(STATS[j] if j < len(STATS) else f'stat{j}'): p.single() for j in range(p.int())}
    p.bool()                                                              # first spawn
    for _ in range(p.int()):                                              # per-world spawn/logout/death/home + map
        p.long(); p.bool(); p.vec3(); p.bool(); p.vec3(); p.bool(); p.vec3(); p.vec3()
        if p.bool():
            p.bytes_()
    out['name'], out['player_id'], _ = p.string(), p.long(), p.string()
    out['used_cheats'] = p.bool()
    out['created'] = datetime.fromtimestamp(p.long(), timezone.utc).date().isoformat()
    if ver < 46 and ver != 44:
        tot['worlds'], tot['world_keys'], tot['commands'] = p.sdict(), p.sdict(), p.sdict()
        if ver >= 42:
            tot['enemies'], tot['pickups'], tot['crafted'] = [p.sdict()], p.sdict(), p.sdict()
    out.update({k: tot[k] for k in ('world_keys', 'crafted', 'pickables', 'food', 'pieces', 'commands', 'pickups')})
    out['kills'] = tot['enemies'][0] if tot['enemies'] else {}
    if not p.bool():
        return out
    q = Pkg(p.bytes_())
    pv = q.int()
    if pv < 29:
        sys.exit(f'{path}: player data version {pv}; only 29+ is parsed')
    q.single(); q.single(); q.single(); q.single()                        # max hp, hp, stamina, time since death
    out['guardian_power'] = q.string(); q.single()
    iv = q.int()
    inv = {}
    if iv >= 108:
        for _ in range(q.ushort()):
            q.int(); q.byte(); q.byte(); q.byte()
            flags = q.byte()
            if flags & 4:
                q.ushort()
            stack = q.ushort() if flags & 8 else 1
            if flags & 0x10:
                q.int()
            if flags & 0x20:
                q.long(); q.string()
            h = q.int() if flags & 0x40 else 0
            for _ in range(q.num_items() if flags & 0x80 else 0):
                q.string(); q.string()
            if iv >= 109:
                q.byte()
            inv[h] = inv.get(h, 0) + stack
    else:                                                                 # Inventory.LoadOld
        for _ in range(q.int()):
            name, stack = q.string(), q.int()
            q.single(); q.int(); q.int(); q.bool()                        # durability, grid x y, equipped
            if iv >= 101:
                q.int()
            if iv >= 102:
                q.int()
            if iv >= 103:
                q.long(); q.string()
            if iv >= 104:
                for _ in range(q.int()):
                    q.string(); q.string()
            if iv >= 105:
                q.int()
            if iv >= 106:
                q.bool()
            if iv == 107:
                q.bool()
            h = stable_hash(name)
            inv[h] = inv.get(h, 0) + stack
    out['coins'] = inv.get(stable_hash('Coins'), 0)
    out['inventory_hashes'] = {str(k): v for k, v in inv.items()}
    out['recipes'] = sorted(q.string() for _ in range(q.int()))
    out['stations'] = {q.string(): q.int() for _ in range(q.int())}
    out['materials'] = sorted(q.string() for _ in range(q.int()))
    for _ in range(q.int()):
        q.string()                                                        # tutorials
    out['uniques'] = sorted(q.string() for _ in range(q.int()))
    out['trophies'] = sorted(q.string() for _ in range(q.int()))
    out['biomes'] = sorted((q.string() if pv >= 33 else str(q.int())) for _ in range(q.int()))
    for _ in range(q.int()):
        q.string(); q.string()                                            # known texts
    q.string(); q.string(); q.vec3(); q.vec3(); q.int()                   # beard, hair, colours, model
    out['foods'] = []
    for _ in range(q.int()):
        out['foods'].append(q.string())
        q.single()                                                        # time left
    q.int()                                                               # Skills version
    skills = {}
    for _ in range(q.int()):
        t, lvl, acc = q.int(), q.single(), q.single()
        skills[SKILL_NAMES.get(t, f'skill{t}')] = {'level': lvl, 'acc': acc, 'xp': xp_total(lvl, acc)}
    out['skills'] = skills
    try:                                                                  # Player.m_customData: KG quests/values, EpicLoot
        out['custom'] = {q.string(): q.string() for _ in range(q.int())}
    except Exception:                                                     # an unknown tail drops only this block
        out['custom'] = None
    return out


def xp_total(level, acc):
    """Cumulative XP: rate-model xp_to_reach + progress into the current level (Skills.GetNextLevelRequirement)."""
    L = int(level)
    return sum(0.5 * (k + 1) ** 1.5 + 0.5 for k in range(L)) + acc


def char_files():
    """Newest save per character: {name: path}; skips *_backup_* copies and .old files."""
    found = {}
    for d in CHAR_DIRS:
        for f in (Path(d).glob('*.fch') if Path(d).is_dir() else []):
            if '_backup_' in f.stem:
                continue
            k = f.stem.lower().split('_')[-1]                               # Steam_<id>_name -> name
            if k not in found or f.stat().st_mtime > found[k].stat().st_mtime:
                found[k] = f
    return found


def find_char(name):
    files = char_files()
    if name:
        files = {k: v for k, v in files.items() if k == name.lower()}
    if not files:
        sys.exit(f'no .fch for {name or "any character"} in {CHAR_DIRS}')
    return max(files.values(), key=lambda f: f.stat().st_mtime)


def bosses(d):
    return sorted({k.split()[0] for k in d['world_keys'] if k.startswith('defeated_')})


def played_s(s):
    return s['stats'].get('TimeInBase', 0) + s['stats'].get('TimeOutOfBase', 0)


def snaps_of(char):
    """Snap json files of one character, oldest first."""
    return sorted(SNAPS.glob(f'{char}-*.json'), key=lambda f: f.name)


def account_id(path):
    """Steam account id of a save (its userdata\\<id> folder); 'local' for characters_local."""
    parts = Path(path).parts
    low = [p.lower() for p in parts]
    return parts[low.index('userdata') + 1] if 'userdata' in low else 'local'


def shared_name(char):
    """<account>-<char>: the name a character's rows are published and shared under (no clash across PCs)."""
    snaps = snaps_of(char)
    d = json.loads(snaps[-1].read_text(encoding='utf-8')) if snaps else {}
    return f"{d.get('account') or (account_id(d['file']) if 'file' in d else 'local')}-{char}"


def row_files(own_only=False):
    """[(shared name, path)] of the session logs: this PC's (.cache/sessions) and, unless own_only, the rows other
    PCs shared through the host (.cache/host/sessions, already named <account>-<char>)."""
    out = {}
    for f in [*SNAPS.glob('*.csv'), *SNAPS.glob('*.jsonl')]:
        out[shared_name(f.stem) + f.suffix] = f
    if not own_only:
        for f in [*HOST_ROWS.glob('*.csv'), *HOST_ROWS.glob('*.jsonl')]:
            out.setdefault(f.name, f)                                    # this PC's own copy wins
    return sorted(out.items())


def quest_names():
    """KG quest uid (the number in `[MPASN]questCD=<uid>`) -> quest id: stable hash of the cfg header's id,
    spaces removed and lowercased (`[id = Tag]` headers hash the id only)."""
    names = {}
    for f in QUESTS.glob('*.cfg'):
        for line in f.read_text(encoding='utf-8', errors='replace').splitlines():
            if line.startswith('[') and ']' in line:
                qid = line[1:line.index(']')].split('=')[0].replace(' ', '').lower()
                names[str(stable_hash(qid))] = qid
    return names


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def gains(a, b):
    """Per-key increase from stats dict a to b; keys that did not rise are dropped."""
    out = {}
    for k, v in b.items():
        d = v - a.get(k, 0)
        if d > 0:
            out[k] = int(d) if d == int(d) else round(d, 2)
    return out


def snap(src, note=''):
    src = Path(src)
    d = parse(src)
    d['char'] = src.stem.lower().split('_')[-1]
    d['account'] = account_id(src)
    d['snapped'] = datetime.now().isoformat(timespec='seconds')
    d['save_mtime'] = datetime.fromtimestamp(src.stat().st_mtime).isoformat(timespec='seconds')
    d['note'] = note
    SNAPS.mkdir(parents=True, exist_ok=True)
    stem = f"{d['char']}-{datetime.now():%Y%m%d-%H%M%S}"
    shutil.copy2(src, SNAPS / f'{stem}.fch')
    (SNAPS / f'{stem}.json').write_text(json.dumps(d, indent=1), encoding='utf-8')
    print(f"snap {stem}: {src} (saved {d['save_mtime']}), played {played_s(d) / 3600:.2f} h, "
          f"{len(d['skills'])} skills, {d['coins']} coins")
    return d


def away_s(t0, t1):
    """Seconds away (watch.py Presence: game not focused, or no input) between two save times."""
    if not (t0 and t1 and AWAY.exists()):
        return 0.0
    a, b = datetime.fromisoformat(t0), datetime.fromisoformat(t1)
    return sum(max(0.0, (min(datetime.fromisoformat(r['end']), b) - max(datetime.fromisoformat(r['start']), a))
                   .total_seconds()) for r in csv.DictReader(AWAY.open(encoding='utf-8')))


def diff(char, note=''):
    """Last two snaps of a character -> one row appended to .cache/sessions/<char>.csv and one detail line to
    <char>.jsonl. None if no play between."""
    snaps = snaps_of(char)
    if len(snaps) < 2:
        return None
    s0, s1 = (json.loads(f.read_text(encoding='utf-8')) for f in snaps[-2:])
    played = (played_s(s1) - played_s(s0)) / 3600
    if played <= 0:
        return None
    away = min(away_s(s0.get('save_mtime'), s1.get('save_mtime')) / 3600, played)
    h = max(played - away, 1 / 60)                          # active hours: every per-hour rate uses them
    both = [k for k in ('pickups', 'custom') if s0.get(k) is not None and s1.get(k) is not None]   # older snaps lack them
    picks = gains(s0['pickups'], s1['pickups']) if 'pickups' in both else {}
    c0, c1 = (s0['custom'], s1['custom']) if 'custom' in both else ({}, {})
    names = quest_names()
    quests = sorted(names.get(k[len(QUEST_DONE):], k[len(QUEST_DONE):]) for k, v in c1.items()
                    if k.startswith(QUEST_DONE) and (k not in c0 or num(v) > num(c0[k])))   # new, or a repeat
    values = {k[len(KG_VALUE):]: num(c1.get(k)) - num(c0.get(k)) for k in {*c0, *c1}
              if k.startswith(KG_VALUE) and num(c1.get(k)) != num(c0.get(k))}
    row = {'date': s1['snapped'][:10], 'char': s1['name'], 'hours': round(h, 2), 'away_h': round(away, 2),
           'note': note or s1['note']}
    for col, keys in RATES:
        dv = sum(s1['stats'].get(k, 0) - s0['stats'].get(k, 0) for k in keys)
        row[f'{col}_per_h'] = round(dv / h / (1000 if col.endswith('_km') else 1), 2)
    row['coins_per_h'] = round((s1['coins'] - s0['coins']) / h)
    row['coins_picked_per_h'] = round(picks.get('$item_coins', 0) / h)   # purses and ground coins; banking can't hide them
    row['quests_done'] = len(quests)
    row['new_recipes'] = len(set(s1['recipes']) - set(s0['recipes']))
    row['bosses'] = ' '.join(bosses(s1))
    cmds = sorted(k for k, v in s1['commands'].items()        # `test` only turns on logging: still real play
                  if v > s0['commands'].get(k, 0) and k != 'test')
    row['console'] = ' '.join(cmds) if cmds else ('cheats' if s1['used_cheats'] and not s0['used_cheats'] else '')
    for sk, v in sorted(s1['skills'].items()):
        dxp = v['xp'] - s0['skills'].get(sk, {'xp': 0})['xp']
        if dxp > 0.01:
            row[f'xp_per_h.{sk}'] = round(dxp / h, 1)
            row[f'level.{sk}'] = round(v['level'], 1)
    out = SNAPS / f'{char}.csv'
    rows = list(csv.DictReader(out.open(encoding='utf-8'))) if out.exists() else []
    rows.append(row)
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with out.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, cols, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    detail = {k: row[k] for k in ('date', 'char', 'hours', 'console')}
    detail.update(quests=quests, values={k: int(v) if v == int(v) else round(v, 2) for k, v in sorted(values.items())},
                  new_keys=sorted(set(s1.get('uniques', [])) - set(s0.get('uniques', []))),
                  kills=gains(s0.get('kills', {}), s1.get('kills', {})), pickups=picks)
    with (SNAPS / f'{char}.jsonl').open('a', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(detail, ensure_ascii=False) + '\n')
    return row


def auto(note=''):
    """Snap every character whose save changed since its last snap; diff those with an earlier snap."""
    rows = []
    for char, f in sorted(char_files().items()):
        prev = snaps_of(char)
        mtime = datetime.fromtimestamp(f.stat().st_mtime).isoformat(timespec='seconds')
        if prev and json.loads(prev[-1].read_text(encoding='utf-8'))['save_mtime'] >= mtime:
            continue
        try:
            snap(f, note)
        except (SystemExit, Exception) as e:                             # one unreadable save must not stop the rest
            print(f'skip {f}: {e}')
            continue
        if prev and (row := diff(char, note)):
            rows.append(row)
            print(f"session {row['char']}: {row['hours']} h" + (f" (console: {row['console']})" if row['console'] else ''))
    return rows


def publish():
    """Copy every session log (row_files: own + shared through the host) to reference/sessions/ for a commit."""
    PUB.mkdir(parents=True, exist_ok=True)
    n = 0
    for name, f in row_files():
        dst = PUB / name
        if not dst.exists() or dst.read_bytes() != f.read_bytes():
            shutil.copyfile(f, dst)
            n += 1
            print(f'{f} -> {dst}')
    print(f'{n} file(s) updated')


def cmd_snap(a):
    snap(Path(a.file) if a.file else find_char(a.char), a.note or '')


def cmd_diff(a):
    last = max(SNAPS.glob('*.json'), key=lambda f: f.stat().st_mtime, default=None)
    char = a.char.lower() if a.char else last and json.loads(last.read_text(encoding='utf-8'))['char']
    row = diff(char, a.note or '') if char else None
    if not row:
        sys.exit('no played time between the last two snaps (log out first so the save is written)')
    for k, v in row.items():
        print(f'{k:28} {v}')


def cmd_show(a):
    d = parse(a.file or find_char(a.char))
    if a.json:
        print(json.dumps(d, indent=1))
        return
    s = d['stats']
    print(f"{d['name']} (profile v{d['profile_version']}, created {d['created']}, cheats {d['used_cheats']}): "
          f"played {played_s(d) / 3600:.1f} h, {d['coins']} coins, {len(d['recipes'])} recipes, "
          f"{len(d['trophies'])} trophies")
    for col, keys in RATES:
        print(f"  {col:12} {sum(s.get(k, 0) for k in keys) / (1000 if col.endswith('_km') else 1):12.0f}")
    print('  bosses:', ' '.join(bosses(d)) or '-')
    top = sorted(d['kills'].items(), key=lambda kv: -kv[1])[:8]
    print('  top kills:', ', '.join(f'{k.removeprefix("$enemy_")} {v:.0f}' for k, v in top))
    c = d['custom'] or {}
    vals = ', '.join(f'{k[len(KG_VALUE):]} {v}' for k, v in sorted(c.items()) if k.startswith(KG_VALUE))
    print(f'  KG: {sum(k.startswith(QUEST_DONE) for k in c)} quests finished' + (f'; {vals}' if vals else ''))
    for sk, v in sorted(d['skills'].items(), key=lambda kv: -kv[1]['level']):
        print(f"  {sk:16} {v['level']:6.1f}  xp {v['xp']:9.0f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    for n in ('snap', 'diff', 'show', 'auto', 'publish'):
        s = sub.add_parser(n)
        if n in ('snap', 'diff', 'show'):
            s.add_argument('--char')
        if n in ('snap', 'diff', 'auto'):
            s.add_argument('--note')
    sub.choices['show'].add_argument('--file')
    sub.choices['snap'].add_argument('--file', help='a specific .fch instead of the newest save')
    sub.choices['show'].add_argument('--json', action='store_true')
    a = ap.parse_args()
    {'snap': cmd_snap, 'diff': cmd_diff, 'show': cmd_show, 'auto': lambda a: auto(a.note or ''),
     'publish': lambda a: publish()}[a.cmd](a)


if __name__ == '__main__':
    main()
