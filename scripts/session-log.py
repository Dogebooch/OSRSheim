#!/usr/bin/env python3
r"""Real-play telemetry from the character save (.fch): snapshot before and after a session, diff into sessions.csv.

    python scripts\session-log.py snap [--char NAME | --file PATH] [--note TEXT]   copy + parse the newest save -> .cache\sessions\
    python scripts\session-log.py diff [--char NAME] [--note TEXT]   last two snaps -> one row in reference\sessions.csv
    python scripts\session-log.py show [--char NAME | --file PATH] [--json]   parsed save: stats, skills, coins, recipes

Snap with the game closed, or after a logout (Valheim writes the .fch on logout and on world save).
Character files: Steam cloud userdata\*\892970\remote\characters, then LocalLow\IronGate\Valheim\characters_local.
No game logging needed. `console` lists commands used between snaps: those rows are not real play. Format: PlayerProfile.LoadPlayerFromDisk and Player.Load (decompiled 1.0.15, profile v46,
player data v33, item v109). Stats row 1 is the all-time total (row 0 unused, rows 3+ per achievement difficulty).
Mod skills (Smoothbrain SkillManager) are saved as SkillType = abs(StableHash(name)); names resolved from MOD_SKILLS
(Smoothbrain Cooking and Farming reuse vanilla 105 and 106).
"""
import argparse
import csv
import glob
import io
import json
import os
import shutil
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAPS = ROOT / '.cache' / 'sessions'
OUT = ROOT / 'reference' / 'sessions.csv'
CHAR_DIRS = [*glob.glob(r'C:\Program Files (x86)\Steam\userdata\*\892970\remote\characters'),
             str(Path(os.environ.get('USERPROFILE', '')) / 'AppData/LocalLow/IronGate/Valheim/characters_local')]

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
    out.update({k: tot[k] for k in ('world_keys', 'crafted', 'pickables', 'food', 'pieces', 'commands')})
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
    return out


def xp_total(level, acc):
    """Cumulative XP: rate-model xp_to_reach + progress into the current level (Skills.GetNextLevelRequirement)."""
    L = int(level)
    return sum(0.5 * (k + 1) ** 1.5 + 0.5 for k in range(L)) + acc


def find_char(name):
    files = [Path(d) / f for d in CHAR_DIRS if Path(d).is_dir() for f in os.listdir(d) if f.endswith('.fch')]
    if name:
        files = [f for f in files if f.stem.lower() == name.lower() or f.stem.lower().endswith('_' + name.lower())]
    if not files:
        sys.exit(f'no .fch for {name or "any character"} in {CHAR_DIRS}')
    return max(files, key=lambda f: f.stat().st_mtime)


def bosses(d):
    return sorted({k.split()[0] for k in d['world_keys'] if k.startswith('defeated_')})


def played_s(s):
    return s['stats'].get('TimeInBase', 0) + s['stats'].get('TimeOutOfBase', 0)


def cmd_snap(a):
    src = Path(a.file) if a.file else find_char(a.char)
    d = parse(src)
    d['snapped'] = datetime.now().isoformat(timespec='seconds')
    d['save_mtime'] = datetime.fromtimestamp(src.stat().st_mtime).isoformat(timespec='seconds')
    d['note'] = a.note or ''
    SNAPS.mkdir(parents=True, exist_ok=True)
    stem = f"{d['name']}-{datetime.now():%Y%m%d-%H%M%S}"
    shutil.copy2(src, SNAPS / f'{stem}.fch')
    (SNAPS / f'{stem}.json').write_text(json.dumps(d, indent=1), encoding='utf-8')
    print(f"snap {stem}: {src} (saved {d['save_mtime']}), played {played_s(d) / 3600:.2f} h, "
          f"{len(d['skills'])} skills, {d['coins']} coins")


def cmd_diff(a):
    snaps = sorted(SNAPS.glob('*.json'), key=lambda f: f.stat().st_mtime)
    if a.char:
        snaps = [f for f in snaps if json.loads(f.read_text(encoding='utf-8'))['name'].lower() == a.char.lower()]
    if len(snaps) < 2:
        sys.exit('need two snaps (snap before and after the session)')
    s0, s1 = (json.loads(f.read_text(encoding='utf-8')) for f in snaps[-2:])
    if s0['name'] != s1['name']:
        sys.exit(f"last two snaps are different characters: {s0['name']} / {s1['name']}")
    h = (played_s(s1) - played_s(s0)) / 3600
    if h <= 0:
        sys.exit('no played time between the snaps (was the save written? log out first)')
    row = {'date': s1['snapped'][:10], 'char': s1['name'], 'hours': round(h, 2), 'note': a.note or s1['note']}
    for col, keys in RATES:
        dv = sum(s1['stats'].get(k, 0) - s0['stats'].get(k, 0) for k in keys)
        row[f'{col}_per_h'] = round(dv / h / (1000 if col.endswith('_km') else 1), 2)
    row['coins_per_h'] = round((s1['coins'] - s0['coins']) / h)
    row['new_recipes'] = len(set(s1['recipes']) - set(s0['recipes']))
    row['bosses'] = ' '.join(bosses(s1))
    cmds = sorted(k for k, v in s1['commands'].items() if v > s0['commands'].get(k, 0))
    row['console'] = ' '.join(cmds) if cmds else ('cheats' if s1['used_cheats'] and not s0['used_cheats'] else '')
    for sk, v in sorted(s1['skills'].items()):
        dxp = v['xp'] - s0['skills'].get(sk, {'xp': 0})['xp']
        if dxp > 0.01:
            row[f'xp_per_h.{sk}'] = round(dxp / h, 1)
            row[f'level.{sk}'] = round(v['level'], 1)
    rows = list(csv.DictReader(OUT.open(encoding='utf-8'))) if OUT.exists() else []
    rows.append(row)
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with OUT.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, cols, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
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
    for sk, v in sorted(d['skills'].items(), key=lambda kv: -kv[1]['level']):
        print(f"  {sk:16} {v['level']:6.1f}  xp {v['xp']:9.0f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    for n in ('snap', 'diff', 'show'):
        s = sub.add_parser(n)
        s.add_argument('--char')
        if n != 'show':
            s.add_argument('--note')
    sub.choices['show'].add_argument('--file')
    sub.choices['snap'].add_argument('--file', help='a specific .fch instead of the newest save')
    sub.choices['show'].add_argument('--json', action='store_true')
    a = ap.parse_args()
    {'snap': cmd_snap, 'diff': cmd_diff, 'show': cmd_show}[a.cmd](a)


if __name__ == '__main__':
    main()
