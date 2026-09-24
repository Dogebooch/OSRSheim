#!/usr/bin/env python3
r"""Whole-run balance simulator (#81 budget): hours -> activities -> XP -> gates -> combat -> drops -> coins -> unlocks.

    python scripts\sim-run.py                            default scenario, summary tables
    python scripts\sim-run.py run [--profile balanced|fighter|skiller] [--mode mixed|together|split|solo]
                                  [--runs 400] [--seed 1] [--out sim-out\<label>] [--set key=value ...]
    python scripts\sim-run.py validate                   reproduce the measured and modelled checks; exit 1 on a failure
    python scripts\sim-run.py sensitivity [--runs 150]   x0.5 / x1.5 on every guessed input -> tornado.csv
    python scripts\sim-run.py inputs                     parse counts, every guessed input and its source

Reads the repo only (no game, no network): the SHIPPED loot (config\drop_that.character_drop*.cfg, EpicLoot tables),
WIRSL gates, KG quests / contracts / gamblers / traders, loot\*.csv, reference\game-data\, reference\measured.csv,
reference\sim-profiles.csv (behaviour inputs, one source per row; rows whose source starts with "guess" are what
`sensitivity` varies) and reference\vanilla-drops.csv (trophy and summon-item chances, kirilloid). Action rates and
kill mechanics come from rate-model.py (imported, not re-derived). Writes only --out (default sim-out\, gitignored).

Model, per player, Monte Carlo (one block = one activity inside one session):
  phases       rate-model BUDGET hours per biome (#81); each boss dies at the end of its phase, its key opens the next
  sessions     lognormal(session.hours, session.cv); activity shares ~ Dirichlet(kappa x share.*); errands first
  kills        Poisson(min(engaged, supply / players sharing it) x h); supply = loot\classes.csv; camp mix = the
               biome's SpawnArea weights (game-data), roam mix = vanilla world-spawn supply, elite = class elite
  loot         every shipped Drop That entry per kill: coins as a compound-binomial normal, the rest Poisson
               thinning; EpicLoot uniques per kill; vanilla trophies per kill; level-3 superiors on revisits
  xp           weapon: hits/kill (rate-model kill_sim) x 1.5 x step x Global; Mining / Lumberjacking: rate-model;
               Smoothbrain per action (mod sources): Cooking 5/cook, Farming 1/plant, Building 1/piece,
               Blacksmithing 15/craft + 75 first craft, Exploration 0.075/map pixel, Sailing 0.5/s at the helm,
               x each cfg factor; Fishing from the reeling rate x SkillGainModifier Fishing 3
  levels       0.5(L+1)^1.5 + 0.5 XP per level; gate crossing times interpolated inside a block
  gate slack   biome entry of the gated item (EpicLoot ItemsByBoss, else the tier ladder) - crossing time
  combat index (TTK / TTD) OSRSheim / (TTK / TTD) vanilla; vanilla = rate-model ladder skill, 10% 1-star, 1% 2-star
  cadence      salience tiers S1 (gem, trophy, curio) S2 (riddle-stone, key half, necklace, superior, bounty, Rare
               magic) S3 (elite unique, T4 stone, riddle cosmetic, keel, oath cape, Epic magic) S4 (boss unique,
               pet, Legendary magic, skillcape); per session P(>=1), gaps, longest drought, closed-form check
"""
import argparse
import bisect
import csv
import importlib.util
import json
import math
import random
import re
import statistics
import sys
import time
from collections import Counter, defaultdict, namedtuple
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
CFG = ROOT / 'config'
KG = CFG / 'Marketplace' / 'Configs'
REF = ROOT / 'reference'
sys.path.insert(0, str(SCRIPTS))


def sibling(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), SCRIPTS / f'{name}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RM = sibling('rate-model')
GL = sibling('gen-loot')

PHASES = [(b, float(h)) for b, h in RM.BUDGET]
BIOMES = [b for b, _ in PHASES]
START, END = {}, {}
_t = 0.0
for _b, _h in PHASES:
    START[_b], END[_b] = _t, _t + _h
    _t += _h
RUN_H = _t
CSV_BIOME = {'Meadows': 'Meadows', 'Black Forest': 'BlackForest', 'Swamp': 'Swamp', 'Ocean': 'Mountain',
             'Mountain': 'Mountain', 'Plains': 'Plains', 'Mistlands': 'Mistlands', 'Ashlands': 'AshLands',
             'Deep North': 'DeepNorth'}
BOSS = dict(zip(BIOMES, ['Eikthyr', 'gd_king', 'Bonemass', 'Dragon', 'GoblinKing', 'SeekerQueen', 'Fader',
                         'FrozenKing_p3']))
KEY = dict(zip(BIOMES, ['defeated_eikthyr', 'defeated_gdking', 'defeated_bonemass', 'defeated_dragon',
                        'defeated_goblinking', 'defeated_queen', 'defeated_fader', 'defeated_frozenking_p3']))
BIOME_OF_KEY = {v: k for k, v in KEY.items()}
# a summon's offering: item and vanilla count (the Seeress sells these per item)
OFFERING = {'Eikthyr': ('TrophyDeer', 2), 'gd_king': ('AncientSeed', 3), 'Bonemass': ('WitheredBone', 10),
          'GoblinKing': ('GoblinTotem', 5)}
BIT = {'Meadows': 1, 'Swamp': 2, 'Mountain': 4, 'BlackForest': 8, 'Plains': 16, 'AshLands': 32, 'DeepNorth': 64,
       'Mistlands': 512}
ACTS = ['camp', 'roam', 'elite', 'boss', 'deaths', 'mine', 'chop', 'farm', 'craft', 'build', 'sail', 'fish',
        'errands', 'other']
FIGHT = ('camp', 'roam', 'elite')
CAMP_SPAWNERS = {'BlackForest': ['Spawner_GreydwarfNest'], 'Swamp': ['Spawner_DraugrPile', 'BonePileSpawner_swamp'],
                 'AshLands': ['Spawner_CharredStone_Elite', 'Spawner_CharredCross'], 'DeepNorth': ['Spawner_Hole']}
WEAPON = {b: (w, q) for b, w, _, q, _ in RM.LADDER}           # the #83 ladder's sword per biome
REP_MOB = {b: m for b, _, m, _, _ in RM.LADDER}
MINE = {'Meadows': 'rock4_copper_frac', 'BlackForest': 'rock4_copper_frac', 'Swamp': 'mudpile_frac'}
PICKS = [(40, 'PickaxeBlackMetal'), (20, 'PickaxeIron'), (10, 'PickaxeBronze'), (0, 'PickaxeAntler')]
AXES = [(50, 'AxeJotunBane'), (40, 'AxeBlackMetal'), (20, 'AxeIron'), (15, 'AxeBronze'), (0, 'AxeFlint')]
CHOP_OBJ = {'Meadows': 'Beech1', 'BlackForest': 'FirTree', 'Swamp': 'SwampTree1_log', 'Mountain': 'SnowFirTree',
            'Plains': 'Birch1', 'Mistlands': 'YggaShoot1', 'AshLands': 'AshlandsTree3', 'DeepNorth': 'SnowFirTree'}
MINE_OBJ = {'Meadows': 'rock4_copper_frac', 'BlackForest': 'rock4_copper_frac', 'Swamp': 'mudpile_frac',
            'Mountain': 'silvervein_frac', 'Plains': 'MineRock_Obsidian', 'Mistlands': 'silvervein_frac',
            'AshLands': 'silvervein_frac', 'DeepNorth': 'silvervein_frac'}
ARMOR = {'Meadows': ['HelmetLeather', 'ArmorLeatherChest', 'ArmorLeatherLegs'],
         'BlackForest': ['HelmetBronze', 'ArmorBronzeChest', 'ArmorBronzeLegs'],
         'Swamp': ['HelmetIron', 'ArmorIronChest', 'ArmorIronLegs'],
         'Mountain': ['HelmetDrake', 'ArmorWolfChest', 'ArmorWolfLegs'],
         'Plains': ['HelmetPadded', 'ArmorPaddedCuirass', 'ArmorPaddedGreaves'],
         'Mistlands': ['HelmetCarapace', 'ArmorCarapaceChest', 'ArmorCarapaceLegs'],
         'AshLands': ['HelmetFlametal', 'ArmorFlametalChest', 'ArmorFlametalLegs'],
         'DeepNorth': ['HelmetDNHeavy', 'ArmorDeepNorthHeavyChest', 'ArmorDeepNorthHeavylegs']}
FOODS = {'Meadows': ['CookedMeat', 'CookedDeerMeat', 'NeckTailGrilled'],
         'BlackForest': ['DeerStew', 'MinceMeatSauce', 'CookedMeat'],
         'Swamp': ['Sausages', 'BlackSoup', 'DeerStew'],
         'Mountain': ['WolfMeatSkewer', 'Sausages', 'BlackSoup'],
         'Plains': ['SerpentStew', 'LoxPie', 'FishWraps'],
         'Mistlands': ['MisthareSupreme', 'MeatPlatter', 'HoneyGlazedChicken'],
         'AshLands': ['PiquantPie', 'MashedMeat', 'FierySvinstew'],
         'DeepNorth': ['SealSoup', 'MooseKebab', 'SmokedMooseMeat']}
SHIELD = {'Meadows': 'ShieldWood', 'BlackForest': 'ShieldBronzeBuckler', 'Swamp': 'ShieldBanded',
          'Mountain': 'ShieldSilver', 'Plains': 'ShieldBlackmetal', 'Mistlands': 'ShieldCarapace',
          'AshLands': 'ShieldFlametal', 'DeepNorth': 'ShieldFlametal'}
GEMS = {'Amber', 'AmberPearl', 'Ruby', 'Crystal', 'Chain', 'SilverNecklace'}
SUMMON = {'AncientSeed', 'GoblinTotem', 'WitheredBone', 'DragonEgg'}
STEP = {'Swords': 1.0, 'Clubs': 1.0, 'Bows': 1.5, 'ElementalMagic': 1.0}   # m_increseStep (game-data player.json)
TIER_NAME = {1: 'S1', 2: 'S2', 3: 'S3', 4: 'S4'}
RARITY_TIER = [1, 2, 3, 4, 4, 4]           # EpicLoot Magic, Rare, Epic, Legendary, Mythic, Ancient -> salience
CASKETS = (('riddle_simple', 'OSRS_RiddleStoneT1'), ('riddle_cryptic', 'OSRS_RiddleStoneT2'),
           ('riddle_elaborate', 'OSRS_RiddleStoneT3'), ('riddle_master', 'OSRS_RiddleStoneT4'),
           ('crystal_chest', 'OSRS_CrystalKey'))
CUM = [RM.xp_to_reach(L) for L in range(101)]
INF = float('inf')

Entry = namedtuple('Entry', 'item lo hi p one keys lmin lmax biomes', defaults=((),))
TRACKED = {'Swords', 'Bows', 'Clubs', 'ElementalMagic', 'Blocking', 'Mining', 'Lumberjacking', 'Farming', 'Alchemy',
           'Cooking', 'Blacksmithing', 'Building', 'Sailing', 'Exploration', 'Fishing', 'Evasion', 'Foraging', 'Ranching'}
DROP_BIOME = {'Meadows': 'Meadows', 'Blackforest': 'BlackForest', 'BlackForest': 'BlackForest', 'Swamp': 'Swamp',
              'Mountain': 'Mountain', 'Plains': 'Plains', 'Mistlands': 'Mistlands', 'AshLands': 'AshLands',
              'Ashlands': 'AshLands', 'DeepNorth': 'DeepNorth'}


def read(path):
    return Path(path).read_text(encoding='utf-8-sig')


def level_of(xp):
    return min(100, bisect.bisect_right(CUM, xp) - 1)


def poisson(rng, lam):
    if lam <= 0:
        return 0
    if lam > 30:
        return max(0, int(round(rng.gauss(lam, math.sqrt(lam)))))
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p < L:
            return k
        k += 1


def dirichlet(rng, means, kappa):
    g = {k: rng.gammavariate(max(v * kappa, 1e-6), 1.0) if v > 0 else 0.0 for k, v in means.items()}
    s = sum(g.values()) or 1.0
    return {k: v / s for k, v in g.items()}


def pct(xs, q):
    xs = sorted(x for x in xs if x == x)
    if not xs:
        return float('nan')
    i = (len(xs) - 1) * q
    lo = int(i)
    return xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (i - lo)


# ---------- behaviour inputs (reference\sim-profiles.csv) ----------
class Params:
    def __init__(self, path=REF / 'sim-profiles.csv'):
        self.rows = {}
        for r in csv.DictReader(open(path, encoding='utf-8')):
            if r['profile'] and not r['profile'].startswith('#'):
                self.rows[(r['profile'], r['phase'], r['key'])] = (float(r['value']), r['source'])
        self.scale, self.override = {}, {}

    def get(self, key, profile='*', phase='*', default=None):
        if key in self.override:
            return self.override[key]
        for p, ph in ((profile, phase), (profile, '*'), ('*', phase), ('*', '*')):
            if (p, ph, key) in self.rows:
                return self.rows[(p, ph, key)][0] * self.scale.get(key, 1.0)
        if default is None:
            raise KeyError(key)
        return default

    def shares(self, profile, phase):
        s = {a: self.get(f'share.{a}', profile, phase, 0.0) for a in ACTS if a != 'other'}
        s['other'] = max(0.0, 1.0 - sum(s.values()))
        tot = sum(s.values())
        return {a: v / tot for a, v in s.items()}

    def guesses(self):
        return sorted({k for (_, _, k), (_, src) in self.rows.items() if src.startswith('guess')})


# ---------- the shipped loot ----------
def _entry(kv):
    keys = tuple(k.strip() for k in str(kv.get('ConditionGlobalKeys', '')).split(',') if k.strip())
    biomes = tuple(DROP_BIOME.get(b.strip(), b.strip()) for b in str(kv.get('ConditionBiomes', '')).split(',') if b.strip())
    return Entry(kv['PrefabName'], int(kv.get('AmountMin', 1)), int(kv.get('AmountMax', 1)),
                 float(kv.get('ChanceToDrop', 100)) / 100.0, str(kv.get('DropOnePerPlayer', 'false')).lower() == 'true',
                 keys, int(str(kv.get('ConditionMinLevel', '-1'))), int(str(kv.get('ConditionMaxLevel', '-1'))), biomes)


def load_drops():
    lists = defaultdict(list)
    for sec, kv in GL.parse(read(CFG / GL.LISTS)).items():
        if 'PrefabName' in kv:
            lists[sec.rsplit('.', 1)[0]].append(_entry(kv))
    table = defaultdict(list)
    for name in (GL.MAIN, 'drop_that.character_drop.osrsheim_superiors.cfg'):
        for sec, kv in GL.parse(read(CFG / name)).items():
            if 'PrefabName' in kv:
                table[sec.rsplit('.', 1)[0]].append(_entry(kv))
            elif 'UseDropList' in kv:
                table[sec].extend(lists[kv['UseDropList']])
    return table


SUFFIX = re.compile(r'_(sleeping|noarcher|NoArcher|NonSleeping|Meadows|Swamps|Mountains|DeepNorth|Ranged|cave|'
                    r'DualWield)$')


def base_name(c):
    prev = None
    while c != prev:
        prev, c = c, SUFFIX.sub('', c)
    return c


class World:
    """Everything static: parsed configs, derived tables, memoised curves."""

    def __init__(self, params):
        self.P = params
        self.drops = load_drops()
        self.vanilla = defaultdict(list)
        for r in csv.DictReader(open(REF / 'vanilla-drops.csv', encoding='utf-8')):
            self.vanilla[r['creature']].append(Entry(r['item'], int(r['min']), int(r['max']), float(r['chance']),
                                                     False, (), -1, -1))
        self.el_tables = RM.el('loottables.json')['LootTables']
        self.uniques = {}
        for t in self.el_tables:
            loot = t.get('Loot') or []
            if loot and str(loot[0].get('Item', '')).startswith('OSRS_'):
                d = t.get('Drops') or []
                w = sum(x[1] for x in d)
                self.uniques[t['Object']] = (loot[0]['Item'], sum(x[1] for x in d if x[0] >= 1) / w if w else 0.0)
        self.creatures = {r['creature']: r for r in GL.read_csv('creatures.csv')}
        self.kph = {r['class']: float(r['valheim_kills_hr']) for r in GL.read_csv('classes.csv')}
        boss_objs = set(BOSS.values())
        self.boss_uniques = {v[0] for k, v in self.uniques.items() if k in boss_objs}
        self.elite_uniques = {v[0] for k, v in self.uniques.items() if k not in boss_objs}
        self.log_rows = [r for r in GL.read_csv('collection-log.csv')]
        self.log_items = {r['prefab'] for r in self.log_rows}
        self.adv = RM.el('adventuredata.json')
        self.map_refresh_h = self.adv['TreasureMap']['RefreshInterval'] * RM.CAL['day_s'] / 3600
        self.map_info = {x['Biome']: x for x in self.adv['TreasureMap']['BiomeInfo']}
        self.bounties = defaultdict(list)
        for x in self.adv['Bounties']['Targets']:
            self.bounties[x['Biome']].append(x)
        self.prices = self.load_prices()
        self.gamblers = self.load_gamblers()
        self.quests = load_quests()
        self.gates = self.load_gates()
        smith = read(CFG / 'org.bepinex.plugins.blacksmithing.cfg')
        self.smith_bonus, self.smith_factor = (
            float(re.search(rf'^{k}\s*=\s*([\d.]+)', smith, re.M).group(1))
            for k in ('First Craft Bonus', 'Skill Experience Gain Factor'))
        # natural stars: CLLC Custom difficulty, world-level-0 row (every row is the same); other difficulties: none
        cllc = read(CFG / 'org.bepinex.plugins.creaturelevelcontrol.cfg')
        row = re.search(r'^Chances for stars at world level 0 \(percent\) = (.*)$', cllc, re.M)
        custom = re.search(r'^Difficulty = Custom', cllc, re.M)
        ch = [float(x) / 100 for x in row.group(1).split(',')] if custom and row else [0.0, 0.0]
        self.star1, self.star2 = ch[0], ch[1]
        self.objects = self.load_objects()
        self.sup_rows = [s for s in RM.spawn_that_rows('spawn_that.world_spawners_advanced.cfg').values()
                         if str(s.get('LevelMin')) == '3' and s.get('Enabled', 'true') == 'true']
        self.sup_hr = {id(s): RM.world_spawn_hr(s)[2] for s in self.sup_rows}
        self._killable = {}
        self._compiled, self._hits, self._mix = {}, {}, {}
        self._mining, self._chop = {}, {}

    # --- traders and gamblers ---
    def load_prices(self):
        sell, buy, cur = {}, {}, None
        for raw in read(KG / 'Traders' / 'osrsheim_traders.cfg').splitlines():
            s = raw.strip()
            if not s or s.startswith('#'):
                continue
            if s.startswith('['):
                cur = s.strip('[]').split('=')[0].strip()
                continue
            parts = [x.strip() for x in s.split(',')]
            if len(parts) >= 4 and '=' not in s:
                try:
                    a, n, b, m = parts[0], float(parts[1]), parts[2], float(parts[3])
                except ValueError:
                    continue
                if b == 'Coins' and cur in ('general_store', 'gem_trader'):
                    sell[a] = max(sell.get(a, 0), m / n)
                elif a == 'Coins':
                    buy.setdefault(b, n / m)
        return {'sell': sell, 'buy': buy}

    def load_gamblers(self):
        out, cur = {}, None
        for raw in read(KG / 'Gamblers' / 'osrsheim_gamblers.cfg').splitlines():
            s = raw.strip()
            if not s or s.startswith('#'):
                continue
            if s.startswith('['):
                cur = s.strip('[]').split('=')[0].strip()
                continue
            parts = [x.strip() for x in s.split(',')]
            prizes = []
            for i in range(2, len(parts) - 1, 2):
                lo, _, hi = parts[i + 1].partition('-')
                prizes.append((parts[i], int(lo), int(hi or lo)))
            out[cur] = {'cost': (parts[0], int(parts[1])), 'prizes': prizes}
        return out

    # --- gates ---
    def load_gates(self):
        biome_of = {}
        info = json.load(open(CFG / 'EpicLoot' / 'baseconfig' / 'iteminfo.json', encoding='utf-8-sig'))['ItemInfo']
        for grp in info:
            for key, items in (grp.get('ItemsByBoss') or {}).items():
                for it in items:
                    biome_of.setdefault(it, BIOME_OF_KEY.get(key, 'Meadows'))
        for c, (item, _) in self.uniques.items():            # a rare belongs where it drops (the dropper's biome)
            b = CSV_BIOME.get(self.creatures.get(c, {}).get('biome', ''))
            if self.creatures.get(c, {}).get('biome') == 'Bosses':
                b = next(bb for bb, o in BOSS.items() if o == c)
            if b:
                biome_of[item] = b
        ladder = [(15, 'BlackForest'), (20, 'Swamp'), (30, 'Mountain'), (40, 'Plains'), (50, 'Mistlands'),
                  (60, 'AshLands'), (70, 'DeepNorth')]
        gates, cur = [], None
        for raw in read(CFG / 'WackyMole.ItemRequiresSkillLevel.yml').splitlines():
            s = raw.strip()
            if s.startswith('- PrefabName:'):
                cur = {'prefab': s.split(':', 1)[1].strip(), 'reqs': []}
                gates.append(cur)
            elif s.startswith('- Skill:') and cur is not None:
                cur['reqs'].append({'skill': s.split(':', 1)[1].strip()})
            elif cur is not None and cur['reqs'] and ':' in s:
                k, v = (x.strip() for x in s.split(':', 1))
                if k in ('Level', 'BlockCraft', 'BlockEquip'):
                    cur['reqs'][-1][k] = v
        out = []
        for g in gates:
            for r in g['reqs']:
                lvl = int(float(r.get('Level', 0)))
                if lvl >= 100 or lvl <= 0:
                    continue
                b = biome_of.get(g['prefab'])
                if not b:
                    m = re.match(r'FishingBait(\w+)', g['prefab'])
                    b = {'Forest': 'BlackForest', 'Ocean': 'Mountain', 'Cave': 'Mountain', 'Mistlands': 'Mistlands',
                         'Ashlands': 'AshLands', 'DeepNorth': 'DeepNorth', 'Swamp': 'Swamp',
                         'Plains': 'Plains'}.get(m.group(1)) if m else None
                if not b:
                    b = next((bb for L, bb in reversed(ladder) if lvl >= L), 'Meadows')
                out.append((g['prefab'], r['skill'], lvl, r.get('BlockCraft') == 'true', r.get('BlockEquip') == 'true', b))
        return out

    # --- skilling objects (loot\objects.csv, targets solved by rate-model objects) ---
    def load_objects(self):
        out = defaultdict(list)
        for r in GL.read_csv('objects.csv'):
            m = re.search(r'rate-model ([\d.]+)/hr x yield ([\d.]+)', r.get('note', ''))
            t = r['target']
            if not m or not t.startswith('1/'):
                continue
            out[r['object']].append((r['item'], float(m.group(1)), float(m.group(2)) / float(t[2:])))
        return out

    # --- kill mixes ---
    def mix(self, biome, act):
        k = (biome, act)
        if k in self._mix:
            return self._mix[k]
        mem = {c: r for c, r in self.creatures.items() if CSV_BIOME.get(r['biome']) == biome and r['biome'] != 'Ocean'}
        if act == 'camp':
            mix = Counter()
            for sp in CAMP_SPAWNERS.get(biome, []):
                pre = [(p['m_prefab'].lstrip('@'), p['m_weight']) for p in RM.SPAWN['SpawnArea'][sp]['m_prefabs']
                       if p.get('m_prefab')]
                tot = sum(w for _, w in pre)
                for c, w in pre:
                    mix[c] += w / tot / len(CAMP_SPAWNERS[biome])
            supply = self.kph['camped']
        elif act == 'roam':
            sup = Counter()
            for lst in RM.SPAWN['SpawnSystemList'].values():
                for sp in lst.get('m_spawners', []):
                    if sp.get('m_enabled') and sp.get('m_spawnInterval') and sp.get('m_biome', 0) & BIT[biome] \
                            and not sp.get('m_requiredGlobalKey'):
                        g = (sp['m_groupSizeMin'] + sp['m_groupSizeMax']) / 2
                        sup[(sp.get('m_prefab') or '').lstrip('@')] += 3600 / sp['m_spawnInterval'] * sp['m_spawnChance'] / 100 * g
            # camped-class mobs also world-spawn (Black Forest Greydwarf 128/hr raw, Swamp Draugr); roaming meets
            # those at the world rate, not the nest rate
            cand = {c: r for c, r in mem.items() if r['class'] in ('roamer', 'world', 'camped')}
            mix = Counter({c: sup.get(c, 0.0) for c in cand if sup.get(c, 0.0) > 0})
            if not mix:
                mix = Counter({c: 1.0 for c in cand if cand[c]['class'] != 'camped'})
            tot = sum(mix.values())
            mix = Counter({c: v / tot for c, v in mix.items()})
            supply = sum(v * self.kph['world' if cand[c]['class'] == 'camped' else cand[c]['class']]
                         for c, v in mix.items())
        else:
            cand = [c for c, r in mem.items() if r['class'] in ('elite',) and 'sleeping' not in c.lower()]
            if not cand:
                cand = [c for c, r in mem.items() if r['class'] == 'nest']
            mix = Counter({c: 1.0 / len(cand) for c in cand}) if cand else Counter()
            supply = self.kph['elite']
        self._mix[k] = (dict(mix), supply)
        return self._mix[k]

    # --- weapon curves (rate-model kill_sim) ---
    def hits(self, biome, mob, level, weapon=None):
        """Mean hits per kill with the biome's ladder weapon (or `weapon`), interpolated on a 10-level grid."""
        w, q = weapon or WEAPON[biome]
        cr = RM.CREATURES.get(mob) or RM.CREATURES.get(base_name(mob)) or RM.CREATURES[REP_MOB[biome]]
        key = (w, q, cr.get('m_name', mob), mob if mob in RM.CREATURES else REP_MOB[biome])
        if key not in self._hits:
            it = RM.ITEMS[w]
            times = RM.combo(it) or [1.0]
            self._hits[key] = [RM.kill_sim(it, cr, L, q, times, n=250, seed=7) for L in range(0, 101, 10)]
        g = self._hits[key]
        i = min(9, int(level // 10))
        return g[i] + (g[i + 1] - g[i]) * (level - 10 * i) / 10

    def swing_rate(self, biome, level, weapon=None):
        it = RM.ITEMS[(weapon or WEAPON[biome])[0]]
        times = RM.combo(it) or [1.0]
        cost = it['m_attack']['m_attackStamina'] * (1 - 0.33 * level / 100)
        return RM.sustained(sum(times) / len(times), cost, 120.0)[0]

    def ttk(self, biome, mob, level, hp_mult=1.0, weapon=None):
        return (self.hits(biome, mob, level, weapon) * hp_mult / RM.CAL['melee_hit']
                / self.swing_rate(biome, level, weapon))

    # --- compiled loot per (creature, keys, level) ---
    def compiled(self, creature, keys, level=1, biome=None):
        k = (creature, keys, level, biome)
        if k in self._compiled:
            return self._compiled[k]
        coin_mu = coin_var = 0.0
        rare = []
        ents = list(self.drops.get(creature, []))
        ents += self.vanilla.get(creature) or self.vanilla.get(base_name(creature), [])
        if creature in self.uniques:
            item, p = self.uniques[creature]
            ents.append(Entry(item, 1, 1, p, False, (), -1, -1))
        for e in ents:
            if e.keys and not any(x in keys for x in e.keys):
                continue
            if (e.lmin > 0 and level < e.lmin) or (e.lmax > 0 and level > e.lmax):
                continue
            if e.biomes and biome not in e.biomes:
                continue
            if e.item == 'Coins':
                m = (e.lo + e.hi) / 2
                ex2 = ((e.hi - e.lo + 1) ** 2 - 1) / 12 + m * m
                coin_mu += e.p * m
                coin_var += e.p * ex2 - (e.p * m) ** 2
            elif e.item in GEMS or e.item in self.log_items or e.item.startswith(('OSRS_', 'Trophy')) or e.item in SUMMON:
                rare.append(e)
        cum, tot = [], 0.0
        for e in rare:
            tot += e.p
            cum.append(tot)
        self._compiled[k] = (coin_mu, coin_var, rare, cum, tot)
        return self._compiled[k]

    def mining_xp_hr(self, level):
        L = int(level // 10) * 10
        if L not in self._mining:
            tool = next(t for g, t in PICKS if L >= g)
            r = RM.mining(tool, 'rock4_copper_frac', L, 1, 120.0, None, L)
            self._mining[L] = r.get('Mining xp/hr >=', 0) if 'error' not in r else 0.0
        return self._mining[L]

    def chop_xp_hr(self, level):
        L = int(level // 10) * 10
        if L not in self._chop:
            tool = next(t for g, t in AXES if L >= g)
            r = RM.trees(tool, 'FirTree', L, 1, 120.0, None, True, 0)
            self._chop[L] = r.get('Lumberjacking xp/hr', 0) if 'error' not in r else 0.0
        return self._chop[L]

    def item_tier(self, item):
        if item in self.boss_uniques or item.startswith('OSRS_Pet') or item == 'OSRS_JalNibRek':
            return 4
        if item in self.elite_uniques or item == 'OSRS_RiddleStoneT4' or item.startswith(
                ('OSRS_Cloak', 'OSRS_Crown', 'OSRS_OathCape', 'OSRS_Keel')):
            return 3
        if item.startswith(('OSRS_RiddleStone', 'OSRS_LoopHalf', 'OSRS_ToothHalf', 'OSRS_CrystalKey')) \
                or item == 'SilverNecklace':
            return 2
        if item in GEMS or item.startswith(('Trophy', 'OSRS_Geode', 'OSRS_Burl')):
            return 1
        return 0


# ---------- KG quests (story, free, oaths, contracts) ----------
Quest = namedtuple('Quest', 'qid file tag type targets coins items skill_exp cooldown keys prereq pkeys')


def load_quests():
    out = []
    for path in sorted((KG / 'Quests').glob('osrsheim_quests_*.cfg')):
        block = None
        for raw in read(path).splitlines() + ['[__end__]']:
            s = raw.strip()
            if s.startswith('['):
                if block and len(block['lines']) >= 6:
                    out.append(_quest(path.stem, block))
                head = s.strip('[]')
                qid, _, tag = head.partition('=')
                block = {'qid': qid.strip(), 'tag': tag.strip(), 'lines': []}
            elif block is not None and s and not s.startswith('#'):
                block['lines'].append(s)
    return out


def _quest(stem, b):
    L = b['lines']
    typ, target, rewards, cooldown = L[0], L[3], L[4], L[5]
    cond = L[6] if len(L) > 6 else ''
    targets = []
    for t in target.split('|'):
        parts = [x.strip() for x in t.split(',')]
        if parts and parts[0]:
            n = int(float(parts[1])) if len(parts) > 1 and re.match(r'^[\d.]+$', parts[1]) else 1
            stars = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
            targets.append((parts[0], n, stars))
    coins, items, sx = 0, [], []
    for r in rewards.split('|'):
        k, _, v = r.partition(':')
        parts = [x.strip() for x in v.split(',')]
        if k.strip() == 'Item' and len(parts) >= 2:
            if parts[0] == 'Coins':
                coins += int(float(parts[1]))
            else:
                items.append((parts[0], int(float(parts[1]))))
        elif k.strip() == 'Skill_EXP' and len(parts) >= 2:
            sx.append((parts[0], float(parts[1])))
    cd = cooldown.strip()
    cd_h = float(cd[:-1]) / 3600 if cd.endswith('s') else float(cd or 0) * RM.CAL['day_s'] / 3600
    keys = tuple(re.findall(r'GlobalKey,\s*(\w+)', cond))
    prereq = tuple(re.findall(r'QuestFinished,\s*(\w+)', cond))
    pkeys = tuple(re.findall(r'HasPlayerKey,\s*(\w+)', cond))
    return Quest(b['qid'], stem, b['tag'], typ, targets, coins, items, sx, cd_h, keys, prereq, pkeys)


# ---------- one simulated run ----------
class Player:
    def __init__(self, idx):
        self.idx = idx
        self.xp = Counter()
        self.cross = defaultdict(lambda: [INF] * 101)
        for s in ('Swords', 'Bows', 'Clubs', 'ElementalMagic', 'Blocking', 'Mining', 'Lumberjacking', 'Farming',
                  'Alchemy', 'Cooking', 'Blacksmithing', 'Building', 'Sailing', 'Exploration', 'Fishing', 'Evasion',
                  'Foraging', 'Ranching'):
            self.cross[s][0] = 0.0
        self.coins = 0.0
        self.flow = Counter()           # coin income / sinks by source
        self.has = Counter()            # items held (collectibles not sold)
        self.got = {}                   # item -> first time obtained
        self.lit = {}                   # collection-log prefab -> time lit
        self.events = []                # (t, tier, what)
        self.kills = Counter()          # creature -> kills credited (quests / contracts)
        self.done = {}                  # quest id -> completion time
        self.pkeys = set()
        self.magic = Counter()
        self.explored = 0.0
        self.sessions = []
        self.contracts = {}             # qid -> kills at accept
        self.map_due = 0.0
        self.balance = []               # (t, coins) at each town round

    def level(self, skill):
        return level_of(self.xp[skill])

    def add_xp(self, skill, amount, t0, t1, events=True):
        if amount <= 0:
            return
        x0 = self.xp[skill]
        x1 = x0 + amount
        L0, L1 = level_of(x0), level_of(x1)
        cr = self.cross[skill]
        for L in range(L0 + 1, L1 + 1):
            f = (CUM[L] - x0) / (x1 - x0)
            cr[L] = t0 + f * (t1 - t0)
            if events:
                self.events.append((cr[L], 1, f'lvl {skill} {L}'))
        self.xp[skill] = x1

    def gain(self, item, n, t, W, tier=None):
        if n <= 0:
            return
        self.has[item] += n
        if item not in self.got:
            self.got[item] = t
        tr = W.item_tier(item) if tier is None else tier
        if tr:
            self.events.append((t, tr, item))


class Run:
    def __init__(self, W, profile, mode, seed, n_players=2):
        self.W, self.P = W, W.P
        self.profile, self.mode = profile, mode
        self.rng = random.Random(seed)
        self.n = 1 if mode == 'solo' else n_players
        self.players = [Player(i) for i in range(self.n)]
        self.keys = set()
        self.unlocks = []               # (t, label)
        self.boss_kills = Counter()

    def p(self, key, phase='*', default=None):
        return self.P.get(key, self.profile, phase, default)

    # ----- loot -----
    def roll(self, creature, n_kills, keys, level, t0, h, owners, biome=None):
        """Roll the shipped loot of n_kills of one creature; coins and items go to owners (split evenly)."""
        W, rng = self.W, self.rng
        if n_kills <= 0:
            return
        mu, var, rare, cum, tot = W.compiled(creature, keys, level, biome)
        if mu > 0:
            coins = max(0.0, rng.gauss(n_kills * mu, math.sqrt(max(n_kills * var, 0.0))))
            for pl in owners:
                pl.coins += coins / len(owners)
                pl.flow['in: creature purses'] += coins / len(owners)
        if tot <= 0:
            return
        for _ in range(poisson(rng, n_kills * tot)):
            e = rare[bisect.bisect_left(cum, rng.random() * tot)]
            t = t0 + rng.random() * h
            amt = rng.randint(e.lo, e.hi)
            if e.one:
                for pl in owners:
                    pl.gain(e.item, amt, t, W)
            else:
                rng.choice(owners).gain(e.item, amt, t, W)

    def magic_roll(self, obj, level, t, owner):
        items, mix = RM.el_roll(self.W.el_tables, obj, level)
        if items <= 0 or self.rng.random() >= items:
            return
        r = self.rng.random() * items
        acc = 0.0
        for i, v in enumerate(mix):
            acc += v
            if r <= acc:
                owner.magic[i] += 1
                owner.events.append((t, RARITY_TIER[i], f'magic {i}'))
                return

    # ----- one fight block -----
    def fight(self, biome, act, h, t0, pls, keys, revisit=False):
        W = self.W
        mix, supply = W.mix(biome, act)
        if not mix or h <= 0:
            return
        hp_mult = 1 + 0.4 * (len(pls) - 1)       # CLLC HP increase per player in multiplayer = 40
        hp_mult *= 1 + W.star1 + 2 * W.star2     # natural stars: +100% HP per star
        lvl = statistics.mean(pl.level('Swords') for pl in pls)
        ttk = sum(w * W.ttk(biome, c, lvl, hp_mult) for c, w in mix.items())
        engaged = 3600.0 / (ttk / len(pls) + RM.CAL['engage_s'])
        rate = min(supply * self.p(f'kph_scale.{act}', biome, 1.0), engaged)
        kills = {c: poisson(self.rng, rate * w * h) for c, w in mix.items()}
        for c, n in kills.items():
            self.roll(c, n, keys, 1, t0, h, pls, biome)
            for pl in pls:
                pl.kills[c] += n
        total = sum(kills.values())
        # natural two-stars roll the EpicLoot level-3 table like superiors do
        for c, n in kills.items():
            k = poisson(self.rng, n * W.star2)
            for _ in range(k):
                self.magic_roll(c, 3, t0 + self.rng.random() * h, self.rng.choice(pls))
            for pl in pls:                             # two-star contracts accept these too (Kill level >= 3)
                pl.kills['*' + c] += k
        # weapon, blocking, evasion XP (each player lands 1/len(pls) of the hits)
        for pl in pls:
            hits = sum(n * W.hits(biome, c, pl.level('Swords')) for c, n in kills.items()) * hp_mult / len(pls)
            base = hits * 1.5 * RM.GAIN_GLOBAL
            for s in ('Swords', 'Bows', 'Clubs', 'ElementalMagic'):
                share = self.p(f'weapon.{s}', biome, 0.0)
                pl.add_xp(s, base * share * STEP[s], t0, t0 + h)
            pl.add_xp('Blocking', total / len(pls) * self.p('rate.blocks_per_kill') * 0.5 * RM.GAIN_GLOBAL, t0, t0 + h)
            pl.add_xp('Evasion', h * self.p('rate.dodges_per_fight_hour') * 0.5, t0, t0 + h)
            if act == 'roam':
                pl.add_xp('Foraging', h * self.p('rate.forage_picks_per_roam_hour') * 0.5, t0, t0 + h)
            buy = self.p('rule.buy_supplies_share') * self.p('rule.supply_coins_per_fight_hour', biome) * h
            pl.coins -= buy
            pl.flow['out: supplies'] += buy
        # superiors on revisits (level 3, key set)
        if revisit:
            for s in W.sup_rows:
                if s.get('Biomes') != biome:
                    continue
                lam = W.sup_hr[id(s)] * h
                for _ in range(poisson(self.rng, lam)):
                    t = t0 + self.rng.random() * h
                    owner = self.rng.choice(pls)
                    self.roll(s['PrefabName'], 1, keys, 3, t, 0.0, pls, biome)
                    self.magic_roll(s['PrefabName'], 3, t, owner)
                    for pl in pls:
                        pl.events.append((t, 2, f'superior {s["PrefabName"]}'))
                        pl.kills['*' + s['PrefabName']] += 1

    # ----- a session -----
    def session(self, idx_phase, t0, hours, pls):
        biome = BIOMES[idx_phase]
        W, rng = self.W, self.rng
        keys = frozenset(self.keys)
        shares = dirichlet(rng, self.P.shares(self.profile, biome), self.p('kappa'))
        self.errands(idx_phase, t0, pls)
        t = t0
        for act in [a for a in ACTS if a != 'errands']:
            h = shares[act] * hours
            if h <= 0:
                continue
            if act in FIGHT:
                rev = self.p('rate.revisit_share') if idx_phase > 0 else 0.0
                h_rev = h * rev
                if h_rev > 0:
                    old = BIOMES[rng.randrange(idx_phase)]
                    self.fight(old, act if W.mix(old, act)[0] else 'roam', h_rev, t, pls, keys, revisit=True)
                self.fight(biome, act, h - h_rev, t + h_rev, pls, keys)
            elif act == 'mine' and idx_phase > 0:
                for pl in pls:
                    xph = W.mining_xp_hr(pl.level('Mining'))
                    pl.add_xp('Mining', xph * h, t, t + h)
                    self.objects(pl, MINE_OBJ[biome], h, t)
            elif act == 'chop':
                for pl in pls:
                    pl.add_xp('Lumberjacking', W.chop_xp_hr(pl.level('Lumberjacking')) * h, t, t + h)
                    self.objects(pl, CHOP_OBJ[biome], h, t)
            elif act == 'build':
                for pl in pls:
                    pl.add_xp('Building', h * self.p('rate.pieces_per_build_hour') * 0.5, t, t + h)
            elif act == 'sail':
                for pl in pls:
                    pl.add_xp('Sailing', h * self.p('rate.helm_share_of_sail') * 3600 * 0.5 * 0.5 / len(pls), t, t + h)
                    room = self.p('rate.explore_px_world') * self.p('rate.explore_share_max') - pl.explored
                    px = max(0.0, min(room, h * self.p('rate.explore_px_per_hour')))
                    pl.explored += px
                    pl.add_xp('Exploration', px * 0.075 * 0.5, t, t + h)
            elif act == 'fish':
                for pl in pls:
                    pl.add_xp('Fishing', h * self.p('rate.fish_xp_per_hour'), t, t + h)
            elif act == 'boss':
                pass                                        # boss kills happen at the phase end
            t += h
        # continuous: food, meads, smithing, farming cycles over the whole session
        for pl in pls:
            sgm = self.p('xp.cookfarm_sgm')
            cooks = hours * (self.p('rate.food_items_per_hour') + self.p('rate.meads_per_hour'))
            pl.add_xp('Cooking', cooks * 5 * 0.5 * sgm, t0, t0 + hours)
            self.farm(pl, biome, idx_phase, hours, shares['farm'] * hours, t0, keys)
            self.smith(pl, biome, idx_phase, hours, t0)
        return t0 + hours

    def objects(self, pl, obj, h, t0):
        for item, per_hr, p_evt in self.W.objects.get(obj, []):
            for _ in range(poisson(self.rng, per_hr * h * p_evt)):
                pl.gain(item, 1, t0 + self.rng.random() * h, self.W)

    def farm(self, pl, biome, idx_phase, hours, hands_on, t0, keys):
        if hands_on <= 0:
            return
        F = pl.level('Farming')
        cycle_h = 4500 / (1 + 2 * F / 100) / 3600 + 0.05
        per_cycle_h = self.p('rate.plants_per_cycle') * self.p('rate.plant_handson_s') / 3600
        cycles = min(hours / cycle_h, hands_on / per_cycle_h)
        plants = cycles * self.p('rate.plants_per_cycle')
        sgm = self.p('xp.cookfarm_sgm')
        pl.add_xp('Farming', plants * 1 * 0.5 * sgm, t0, t0 + hours)
        crops = plants * (1 + F / 100)
        stone = 3.0 if pl.level('Alchemy') >= 50 else 1.0                 # Philosopher's Stone, gated at Alchemy 50
        pl.add_xp('Alchemy', crops * 0.4286 * stone, t0, t0 + hours)      # 3649 XP / 8514 crop units (check-alchemy-balance)
        # herb contracts (cooldown 1 day ~ 0.5 h real): one per ~50 crops of an open crop
        herbs = [q for q in self.W.quests if q.file.endswith('slayer') and q.type == 'Harvest'
                 and all(k in keys for k in q.keys)]
        n = int(cycles * min(len(herbs), self.p('rate.plants_per_cycle') // 50 + (self.rng.random() < 0.2)))
        for _ in range(n):
            q = self.rng.choice(herbs)
            pl.coins += q.coins
            pl.flow['in: herb contracts'] += q.coins
            for s, v in q.skill_exp:
                pl.add_xp(s, v * self.p('xp.quest_skill_exp_factor'), t0, t0 + hours, events=False)

    def smith(self, pl, biome, idx_phase, hours, t0):
        frac = hours / dict(PHASES)[biome]
        new = self.p('rate.smith_new_items', biome) * frac
        crafts = self.p('rate.smith_crafts', biome) * frac
        # repeats per item stay under the cfg's reduction threshold (5), so no reduction is modelled
        pl.add_xp('Blacksmithing', (new * self.W.smith_bonus + crafts * 15) * self.W.smith_factor, t0, t0 + hours)

    # ----- errands: town round at session start -----
    def errands(self, idx_phase, t, pls):
        W, rng = self.W, self.rng
        biome = BIOMES[idx_phase]
        keys = self.keys
        for pl in pls:
            # light the collection log for everything held (partner hand-over when rule.pass_to_log)
            held = set(i for i, n in pl.has.items() if n > 0)
            if self.p('rule.pass_to_log') and len(pls) > 1:
                for o in pls:
                    held |= set(o.got)
            for item in held & W.log_items:
                if item not in pl.lit:
                    pl.lit[item] = t
            for prefab, skill, lvl, _, _, _ in W.jewellery:
                if prefab not in pl.lit and pl.cross[skill][lvl] <= t and pl.got:
                    pl.lit[prefab] = t
                    pl.gain(prefab, 1, t, W, tier=0)
            # open caskets / forge keys / crystal chest
            self.caskets(pl, t)
            pl.balance.append((t, pl.coins))
            # sell gems, curios and duplicate trophies (keep one of each collectible)
            for item in list(pl.has):
                keep = 1 if item in W.log_items else 0
                price = W.prices['sell'].get(item, 35 if item in ('OSRS_Geode', 'OSRS_Burl') else 0)
                if price and pl.has[item] > keep and (item in GEMS or item.startswith(('Trophy', 'OSRS_Geode', 'OSRS_Burl'))):
                    n = pl.has[item] - keep
                    pl.has[item] = keep
                    pl.coins += n * price
                    pl.flow['in: trader sales'] += n * price
            # waystone fee (oath network)
            tier = sum(1 for b in BIOMES if f'oath_{b.lower()}' in pl.pkeys)
            if tier:
                fee = [25, 50, 100, 150, 200, 300, 400, 500][tier - 1] * self.p('rule.trips_per_session')
                pl.coins -= fee
                pl.flow['out: waystones'] += fee
            # treasure map (frontier biome), one per refresh
            info = W.map_info.get(biome)
            if self.p('rule.maps') and info and t >= pl.map_due and pl.coins >= info['Cost']:
                pl.map_due = t + W.map_refresh_h
                pl.coins += info['Coins'] - info['Cost']
                pl.flow['in: treasure maps (net)'] += info['Coins'] - info['Cost']
                self.magic_roll(f'TreasureMapChest_{biome}', 1, t + 0.5, pl)
            # bounty (previous biome's, unlocked by its boss)
            if idx_phase > 0 and rng.random() < self.p('rule.bounties_per_session'):
                bb = BIOMES[idx_phase - 1]
                opts = W.bounties.get(bb)
                if opts:
                    x = rng.choice(opts)
                    pl.coins += x['RewardCoins']
                    pl.flow['in: bounties'] += x['RewardCoins']
                    pl.events.append((t + 1.0, 2, f'bounty {bb}'))
                    self.roll(x['TargetID'], 1, frozenset(keys), 3, t + 1.0, 0.0, [pl], bb)
                    self.magic_roll(x['TargetID'], 3, t + 1.0, pl)
            # skillcapes at 100
            if self.p('rule.capes'):
                for s in list(pl.xp):
                    cape = f'OSRS_Cape{s}'
                    if pl.level(s) >= 100 and not pl.has.get(cape) and pl.coins >= 5000:
                        pl.coins -= 5000
                        pl.flow['out: skillcapes'] += 5000
                        pl.gain(cape, 1, t, W, tier=4)
            # gambling above the reserve
            g = self.p('rule.gamble_share')
            if g > 0 and pl.coins > self.p('rule.coin_reserve'):
                stake = (pl.coins - self.p('rule.coin_reserve')) * g
                pl.coins -= stake * 0.28                      # dice 30% / poker 25% edge (gambler cfg EV)
                pl.flow['out: gambling (EV loss)'] += stake * 0.28
        self.quests(idx_phase, t, pls)
        self.contracts(idx_phase, t, pls)

    def caskets(self, pl, t):
        """Forge key halves at Gullveig, open every riddle-stone and crystal key at the Gambler (uniform prize slots).
        The player is in town, so anything a log row wants is shown to Halla before it is spent."""
        W, rng = self.W, self.rng
        while min(pl.has['OSRS_LoopHalfKey'], pl.has['OSRS_ToothHalfKey']) > 0:
            for half in ('OSRS_LoopHalfKey', 'OSRS_ToothHalfKey'):
                pl.has[half] -= 1
                if half in W.log_items:
                    pl.lit.setdefault(half, t)
            pl.gain('OSRS_CrystalKey', 1, t, W)
        for _ in range(5):                                    # a prize can be the next tier's stone
            for prof, item in CASKETS:
                g = W.gamblers.get(prof)
                while g and pl.has[item] > 0:
                    if item in W.log_items:
                        pl.lit.setdefault(item, t)
                    pl.has[item] -= 1
                    prize, lo, hi = rng.choice(g['prizes'])
                    n = rng.randint(lo, hi)
                    pl.flow[f'opened: {prof}'] += 1
                    if prize == 'Coins':
                        pl.coins += n
                        pl.flow[f'in: {prof}'] += n
                    elif prize in GEMS:
                        v = n * W.prices['sell'].get(prize, 0)
                        pl.coins += v
                        pl.flow[f'in: {prof}'] += v
                        pl.got.setdefault(prize, t)
                        if prize in W.log_items:
                            pl.lit.setdefault(prize, t)
                        pl.events.append((t, 2 if prize == 'SilverNecklace' else 1, f'{prof}: {prize}'))
                    elif prize != 'Stone':
                        pl.gain(prize, n, t, W)
                        if prize in W.log_items:
                            pl.lit.setdefault(prize, t)

    # ----- one-time quests (story, free, oaths) -----
    def quests(self, idx_phase, t, pls):
        W, rng = self.W, self.rng
        for pl in pls:
            for q in W.quests:
                if q.file.endswith('slayer') or q.file.endswith('collection_log') or q.qid in pl.done:
                    continue
                if not all(k in self.keys for k in q.keys) or not all(x in pl.done for x in q.prereq) \
                        or not all(k in pl.pkeys for k in q.pkeys):
                    continue
                ok = True
                for name, n, _ in q.targets:
                    if q.type == 'Kill':
                        base = q.qid + ':' + name
                        if base not in pl.contracts:
                            pl.contracts[base] = pl.kills[name]
                            ok = False                                # opened now; counts from here
                        # targeted hunting: a quest target the mixes rarely supply is hunted on purpose
                        ok &= (pl.kills[name] - pl.contracts[base] >= n) or rng.random() < 0.35
                    elif q.type == 'Collect':
                        if name in W.log_items or name.startswith('Trophy'):
                            ok &= pl.got.get(name, INF) <= t
                        else:
                            ok &= rng.random() < 0.6
                    elif q.type == 'Craft':
                        g = next((gg for gg in W.gates if gg[0] == name), None)
                        ok &= g is None or g[1] not in TRACKED or pl.level(g[1]) >= g[2]
                    elif q.type == 'Harvest':
                        ok &= rng.random() < 0.5
                if not ok:
                    continue
                pl.done[q.qid] = t
                pl.coins += q.coins
                src = 'oaths' if q.file.endswith('oaths') else 'story quests'
                pl.flow[f'in: {src}'] += q.coins
                for item, n in q.items:
                    if item.startswith('OSRS_') or item in W.log_items:
                        pl.gain(item, n, t, W)
                for s, v in q.skill_exp:
                    pl.add_xp(s, v * self.p('xp.quest_skill_exp_factor'), t, t + 0.01, events=False)
                if q.qid.endswith('_seal') and q.file.endswith('oaths'):
                    b = q.qid[len('oath_'):-len('_seal')]
                    pl.pkeys.add(f'oath_{b}')
                    pl.events.append((t, 3, f'oath {b}'))
                    self.unlocks.append((t, f'oath {b}: waystone + sworn perks'))

    def _killable(self, idx_phase):
        if idx_phase in self.W._killable:
            return self.W._killable[idx_phase]
        out = set()
        for b in BIOMES[:idx_phase + 1]:
            for act in FIGHT:
                out |= set(self.W.mix(b, act)[0])
        self.W._killable[idx_phase] = out | {BOSS[b] for b in BIOMES[:idx_phase]}
        return self.W._killable[idx_phase]

    # ----- hunt contracts (Huntmaster, autocomplete, repeatable) -----
    def contracts(self, idx_phase, t, pls):
        W = self.W
        for pl in pls:
            # complete what was accepted last trip
            for qid, base in list(pl.contracts.items()):
                if not qid.startswith('slayer:'):
                    continue
                q = W.contract_by_id[qid[len('slayer:'):]]
                name, n, stars = q.targets[0]
                key = ('*' + name) if stars else name
                if pl.kills[key] - base >= n:
                    del pl.contracts[qid]
                    pl.coins += q.coins                        # each player holds their own instance
                    pl.flow['in: hunt contracts'] += q.coins
                    for item, k in q.items:
                        pl.gain(item, k, t, W)
                    pl.events.append((t, 1, f'contract {q.qid}'))
                elif self.rng.random() < self.p('rule.skip_share'):
                    del pl.contracts[qid]
                    fee = q.coins / 3
                    pl.coins -= fee
                    pl.flow['out: contract skips'] += fee
            # accept up to 7 open contracts whose target lives in the current or a cleared biome (one Huntmaster
            # round per session with probability rule.trips_per_session)
            if self.rng.random() >= self.p('rule.trips_per_session'):
                continue
            live = sum(1 for k in pl.contracts if k.startswith('slayer:'))
            killable = self._killable(idx_phase)
            for q in W.contracts:
                if live >= 7:
                    break
                if f'slayer:{q.qid}' in pl.contracts or not all(k in self.keys for k in q.keys):
                    continue
                name, n, stars = q.targets[0]
                if stars and name not in killable and name not in {s['PrefabName'] for s in W.sup_rows}:
                    continue
                if not stars and name not in killable:
                    continue
                pl.contracts[f'slayer:{q.qid}'] = pl.kills[('*' + name) if stars else name]
                live += 1

    # ----- the run -----
    def boss_kill(self, idx_phase, t):
        biome = BIOMES[idx_phase]
        b = BOSS[biome]
        pls = self.players
        extra = int(self.p('rule.boss_extra', biome))
        for k in range(1 + extra):
            # the last boss's repeat kills land inside the run, not after RUN_H
            tt = t + (k - extra * (idx_phase == len(BIOMES) - 1)) * self.p('rate.boss_fight_h')
            self.roll(b, 1, frozenset(self.keys), 1, tt, 0.0, pls, biome)
            self.boss_kills[b] += 1
            for pl in pls:
                pl.kills[b] += 1
            if k:
                # Seeress offerings (vanilla summon counts); unsold bosses' items are gathered, not bought
                item, n = OFFERING.get(b, (None, 0))
                cost = n * self.W.prices['buy'].get(item, 0)
                for pl in pls:
                    pl.coins -= cost / len(pls)
                    pl.flow['out: boss offerings'] += cost / len(pls)
        self.keys.add(KEY[biome])
        self.unlocks.append((t, f'{biome} boss: {KEY[biome]} opens the next biome, quests, contracts, trader pages'))

    def simulate(self):
        rng = self.rng
        together = self.p('together')
        for i, (biome, hours) in enumerate(PHASES):
            self.unlocks.append((START[biome], f'enter {biome}'))
            t = START[biome]
            end = END[biome]
            while t < end - 1e-9:
                mu, cv = self.p('session.hours'), self.p('session.cv')
                s2 = math.log(1 + cv * cv)
                h = min(end - t, rng.lognormvariate(math.log(mu) - s2 / 2, math.sqrt(s2)))
                if end - t - h < 0.3:
                    h = end - t
                if self.n > 1 and (self.mode == 'together' or (self.mode == 'mixed' and rng.random() < together)):
                    self.session(i, t, h, self.players)
                    for pl in self.players:
                        pl.sessions.append((t, t + h))
                else:
                    for pl in self.players:
                        self.session(i, t, h, [pl])
                        pl.sessions.append((t, t + h))
                t += h
            self.boss_kill(i, end)
            for pl in self.players:
                pl.add_xp('Ranching', self.p('rate.ranching_xp_per_phase') * 0.5, START[biome], end, events=False)
        self.errands(len(PHASES) - 1, RUN_H, self.players)
        return self


def build_contract_index(W):
    jew = {r['prefab'] for r in W.log_rows if r['category'] == 'Jewellery'}
    W.jewellery = [g for g in W.gates if g[0] in jew]
    W.contracts = sorted((q for q in W.quests if q.file.endswith('slayer') and q.type == 'Kill'), key=lambda q: -q.coins)
    W.contract_by_id = {q.qid: q for q in W.contracts}


# ---------- metrics ----------
def gate_slack(W, runs):
    """Per gate: median crossing time vs the item's biome entry, over every player of every run."""
    rows = []
    seen = set()
    for prefab, skill, lvl, craft, equip, biome in W.gates:
        if (prefab, skill) in seen:
            continue
        seen.add((prefab, skill))
        xs = [r.players[i].cross[skill][lvl] for r in runs for i in range(r.n) if skill in r.players[i].cross]
        if not xs:
            continue
        need = START[biome]
        cross = pct(xs, 0.5)
        rows.append({'prefab': prefab, 'skill': skill, 'level': lvl, 'biome': biome, 'need_h': need,
                     'cross_p10': pct(xs, 0.1), 'cross_p50': cross, 'cross_p90': pct(xs, 0.9),
                     'slack_h': need - cross if cross < INF else -INF,
                     'P_ready_at_entry': sum(x <= need for x in xs) / len(xs)})
    return rows


def cadence(runs, min_tier):
    per_session, gaps, droughts, rates = [], [], [], []
    for r in runs:
        for pl in r.players:
            ts = sorted(t for t, tr, _ in pl.events if tr >= min_tier)
            sess = pl.sessions
            j = 0
            for a, b in sess:
                while j < len(ts) and ts[j] < a:
                    j += 1
                per_session.append(1 if j < len(ts) and ts[j] < b else 0)
            gaps += [b - a for a, b in zip(ts, ts[1:])]
            bounds = [0.0] + ts + [RUN_H]
            droughts.append(max(b - a for a, b in zip(bounds, bounds[1:])))
            rates.append(len(ts) / RUN_H)
    lam = statistics.mean(rates) if rates else 0.0
    sh = statistics.mean(b - a for r in runs for pl in r.players for a, b in pl.sessions)
    return {'tier': f'S{min_tier}+', 'per_hour': lam, 'P_session_sim': statistics.mean(per_session),
            'P_session_closed': 1 - math.exp(-lam * sh), 'gap_p50': pct(gaps, 0.5), 'gap_p90': pct(gaps, 0.9),
            'gap_p99': pct(gaps, 0.99), 'drought_p50': pct(droughts, 0.5), 'drought_p90': pct(droughts, 0.9)}


def phase_cadence(runs, min_tier):
    out = []
    for b in BIOMES:
        per, cnt = [], []
        for r in runs:
            for pl in r.players:
                ts = [t for t, tr, _ in pl.events if tr >= min_tier and START[b] <= t < END[b]]
                cnt.append(len(ts))
                for a, bb in pl.sessions:
                    if START[b] <= a < END[b]:
                        per.append(any(a <= t < bb for t in ts))
        out.append({'biome': b, 'tier': f'S{min_tier}+', 'per_hour': statistics.mean(cnt) / dict(PHASES)[b],
                    'P_session': statistics.mean(per) if per else float('nan')})
    return out


def summarize(W, runs):
    S = {}
    skills = ['Swords', 'Bows', 'ElementalMagic', 'Blocking', 'Blacksmithing', 'Mining', 'Lumberjacking', 'Farming',
              'Alchemy', 'Cooking', 'Building', 'Sailing', 'Exploration', 'Fishing', 'Evasion', 'Foraging']
    lv = []
    for b in BIOMES + ['end']:
        t = END[b] if b != 'end' else RUN_H
        row = {'at': f'end of {b}' if b != 'end' else 'run end', 't_h': t}
        for s in skills:
            xs = [sum(1 for L in range(1, 101) if pl.cross[s][L] <= t) for r in runs for pl in r.players]
            row[s] = pct(xs, 0.5)
        lv.append(row)
    S['levels'] = lv
    S['levels_ts'] = []
    for t in [x * 7.5 for x in range(int(RUN_H / 7.5) + 1)]:
        row = {'t_h': t}
        for s in skills:
            row[s] = pct([sum(1 for L in range(1, 101) if pl.cross[s][L] <= t) for r in runs for pl in r.players], 0.5)
        S['levels_ts'].append(row)
    S['hours_to'] = []
    for s in skills:
        row = {'skill': s}
        for L in (20, 40, 50, 70, 100):
            xs = [pl.cross[s][L] for r in runs for pl in r.players]
            row[f'h_to_{L}'] = pct(xs, 0.5)
        S['hours_to'].append(row)
    S['gates'] = gate_slack(W, runs)
    S['cadence'] = [cadence(runs, k) for k in (2, 3, 4)]
    S['phase_cadence'] = [x for k in (2, 3) for x in phase_cadence(runs, k)]
    flows = defaultdict(list)
    for r in runs:
        for pl in r.players:
            for k, v in pl.flow.items():
                flows[k].append(v)
    n = sum(r.n for r in runs)
    S['coins'] = sorted(({'flow': k, 'mean': sum(v) / n} for k, v in flows.items()), key=lambda x: -abs(x['mean']))
    S['coin_end'] = pct([pl.coins for r in runs for pl in r.players], 0.5)
    S['coins_ts'] = []
    for b in BIOMES:
        xs = [next((c for t, c in reversed(pl.balance) if t <= END[b]), 0.0) for r in runs for pl in r.players]
        S['coins_ts'].append({'at': f'end of {b}', 't_h': END[b], 'p10': pct(xs, 0.1), 'p50': pct(xs, 0.5),
                              'p90': pct(xs, 0.9)})
    # collection log
    rows = W.log_rows
    lit = defaultdict(list)
    for r in runs:
        for pl in r.players:
            for row in rows:
                lit[row['prefab']].append(pl.lit.get(row['prefab'], INF))
    cats = defaultdict(lambda: [0, 0.0])
    for row in rows:
        xs = lit[row['prefab']]
        p = sum(x <= RUN_H for x in xs) / len(xs)
        cats[row['category']][0] += 1
        cats[row['category']][1] += p
    S['log'] = [{'category': c, 'rows': v[0], 'lit_mean': v[1], 'share': v[1] / v[0]} for c, v in cats.items()]
    S['log_total'] = sum(v[1] for v in cats.values()) / len(rows)
    S['log_items'] = {row['prefab']: sum(x <= RUN_H for x in lit[row['prefab']]) / len(lit[row['prefab']]) for row in rows}
    # notable items per run
    cnt = defaultdict(list)
    for r in runs:
        for pl in r.players:
            c = Counter(what for _, tr, what in pl.events if tr >= 2 and not what.startswith('lvl'))
            for k in set(c) | set(cnt):
                cnt[k].append(c.get(k, 0))
    S['items'] = sorted(({'item': k, 'per_run': sum(v) / n, 'P_any': sum(1 for x in v if x) / n}
                         for k, v in cnt.items()), key=lambda x: -x['per_run'])
    S['magic'] = {i: sum(pl.magic[i] for r in runs for pl in r.players) / n for i in range(6)}
    S['boss_kills'] = {k: v / len(runs) for k, v in sum((r.boss_kills for r in runs), Counter()).items()}
    S['kills_per_h'] = pct([sum(v for k, v in pl.kills.items() if not k.startswith('*')) / RUN_H
                            for r in runs for pl in r.players], 0.5)
    # unlock density (one player's view, dedup 0.25 h)
    dens = []
    for b in BIOMES:
        gaps_all, n_ev = [], []
        for r in runs:
            pl = r.players[0]
            ev = [t for t, _ in r.unlocks]
            for prefab, skill, lvl, craft, equip, gb in W.gates:
                c = pl.cross[skill][lvl] if skill in pl.cross else INF
                ev.append(max(START[gb], c))
            ev = sorted(t for t in ev if START[b] <= t < END[b])
            ded = []
            for t in ev:
                if not ded or t - ded[-1] > 0.25:
                    ded.append(t)
            bounds = [START[b]] + ded + [END[b]]
            gaps_all.append(max(y - x for x, y in zip(bounds, bounds[1:])))
            n_ev.append(len(ded))
        dens.append({'biome': b, 'unlocks': statistics.mean(n_ev), 'hours_per_unlock': dict(PHASES)[b] / max(1e-9, statistics.mean(n_ev)),
                     'longest_gap_p50': pct(gaps_all, 0.5)})
    S['density'] = dens
    return S


def combat_index(W, S, P, profile):
    """(TTK/TTD) OSRSheim / vanilla at each biome entry, representative mob; >1 = harder than vanilla.
    OSRSheim: median Swords / Cooking at entry, the best ladder sword the Swords gate allows (a wall drops a tier),
    CLLC's natural stars (cfg), prayer uptime. Vanilla: the same play at 1x XP over 1/3 of the hours (2/3 of the XP, the #83 rule),
    10% 1-star (2x HP, 1.5x dmg) and 1% 2-star, no Cooking bonus, no prayers, no gates."""
    lv = {row['at']: row for row in S['levels']}
    s1, s2 = P.get('combat.vanilla_star1'), P.get('combat.vanilla_star2')
    gate = {g[0]: g[2] for g in W.gates if g[1] == 'Swords'}
    agate = {g[0]: g[2] for g in W.gates if g[1] == 'Blacksmithing'}
    rows = []
    for i, b in enumerate(BIOMES):
        prev = lv[f'end of {BIOMES[i - 1]}'] if i else {'Swords': 0, 'Cooking': 0, 'Blacksmithing': 0}
        L_o = prev['Swords']
        L_v = level_of(CUM[int(L_o)] * 2 / 3)
        wb = next((BIOMES[j] for j in range(i, -1, -1) if L_o >= gate.get(WEAPON[BIOMES[j]][0], 0)), BIOMES[0])
        mob = REP_MOB[b]
        cr = RM.CREATURES[mob]
        hp_v, dm_v = 1 + s1 + 2 * s2, 1 + 0.5 * s1 + s2
        hp_o, dm_o = 1 + W.star1 + 2 * W.star2, 1 + 0.5 * W.star1 + W.star2
        ttk_o = W.ttk(b, mob, L_o, hp_o, WEAPON[wb])
        ttk_v = W.ttk(b, mob, L_v) * hp_v
        atk = [RM.ITEMS[x.lstrip('@')] for x in (cr.get('m_defaultItems') or []) + (cr.get('m_randomWeapon') or [])
               if x.lstrip('@') in RM.ITEMS]
        dmg = statistics.mean(sum(v for k, v in (a.get('m_damages') or {}).items() if k not in ('m_chop', 'm_pickaxe'))
                              for a in atk if a.get('m_damages')) if atk else 30.0
        def armor_of(bb):
            return sum(RM.ITEMS[a].get('m_armor', 0) + 2 * RM.ITEMS[a].get('m_armorPerLevel', 0)
                       for a in ARMOR[bb] if a in RM.ITEMS)
        bs = prev.get('Blacksmithing', 0)
        ab = next((BIOMES[j] for j in range(i, -1, -1)
                   if all(bs >= agate.get(a, 0) for a in ARMOR[BIOMES[j]])), BIOMES[0])
        armor, armor_v = armor_of(ab), armor_of(b)
        food = sum(RM.ITEMS[f].get('m_food', 0) for f in FOODS[b] if f in RM.ITEMS)

        def ttd(dmg, cook, dr, arm):
            d = dmg - arm if arm < dmg / 2 else dmg * dmg / (4 * arm)          # Valheim armor rule
            return (25 + food * (1 + 0.3 * cook / 100)) / max(0.1, d * (1 - dr) / P.get('combat.atk_interval_s'))

        up = P.get('combat.prayer_uptime')
        ttd_o, ttd_o0 = ttd(dmg * dm_o, prev['Cooking'], 0.15 * up, armor), ttd(dmg * dm_o, prev['Cooking'], 0.0, armor)
        ttd_v = ttd(dmg * dm_v, 0, 0.0, armor_v)
        base = (ttk_o / ttd_o0) / (ttk_v / ttd_v)
        rows.append({'biome': b, 'mob': mob, 'swords_osrsheim': L_o, 'swords_vanilla_same_play': L_v,
                     'sword_used': WEAPON[wb][0], 'armor_set': ab, 'armor': armor, 'armor_vanilla': armor_v, 'food_hp': food,
                     'index_no_prayer': base, 'index_prayer': (ttk_o / (1 + 0.10 * up) / ttd_o) / (ttk_v / ttd_v),
                     'x_stars': hp_o * dm_o / (hp_v * dm_v), 'x_cooking': 1 / (1 + 0.3 * prev['Cooking'] / 100)})
    return rows


def unique_timing(W, runs):
    """Rares rule 1: does each unique drop before its skill gate is reached?"""
    gate = {g[0]: (g[1], g[2]) for g in W.gates}
    rows = []
    for obj, (item, p) in sorted(W.uniques.items(), key=lambda x: x[1][0]):
        if item in {r['item'] for r in rows}:
            continue
        g = gate.get(item)
        got = [pl.got.get(item, INF) for r in runs for pl in r.players]
        before = [pl.got.get(item, INF) < (pl.cross[g[0]][g[1]] if g and g[0] in pl.cross else INF)
                  for r in runs for pl in r.players] if g else []
        rows.append({'item': item, 'dropper': obj, 'p_kill': p, 'gate': f'{g[0]} {g[1]}' if g else '-',
                     'P_by_run_end': sum(x <= RUN_H for x in got) / len(got),
                     'first_drop_p50_h': pct([x for x in got if x < INF], 0.5),
                     'P_before_gate': sum(before) / len(before) if before else float('nan')})
    return rows


# ---------- output ----------
def fmt(v):
    if isinstance(v, float):
        if v == INF or v == -INF:
            return 'inf' if v > 0 else '-inf'
        if v != v:
            return '-'
        return f'{v:.3g}' if abs(v) < 100 else f'{v:.0f}'
    return str(v)


def table(title, rows, keys=None):
    rows = [r for r in rows if r]
    if not rows:
        return
    keys = keys or list(dict.fromkeys(k for r in rows for k in r))
    w = {k: max(len(k), *(len(fmt(r.get(k, ''))) for r in rows)) for k in keys}
    print(f'== {title}')
    print('  '.join(k.ljust(w[k]) for k in keys))
    for r in rows:
        print('  '.join(fmt(r.get(k, '')).ljust(w[k]) for k in keys))
    print()


def write_csv(path, rows):
    rows = [r for r in rows if r]
    if not rows:
        return
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, keys, lineterminator='\n')
        w.writeheader()
        for r in rows:
            w.writerow({k: fmt(v) if isinstance(v, float) else v for k, v in r.items()})


def gate_rollup(gates):
    out = defaultdict(lambda: {'gates': 0, 'invisible (>5 h early)': 0, 'felt (within 5 h)': 0, 'wall (>5 h late)': 0,
                               'never by run end': 0, 'slack_p50_h': []})
    for g in gates:
        o = out[g['skill']]
        o['gates'] += 1
        s = g['slack_h']
        if s == -INF:
            o['never by run end'] += 1
        elif s > 5:
            o['invisible (>5 h early)'] += 1
        elif s >= -5:
            o['felt (within 5 h)'] += 1
        else:
            o['wall (>5 h late)'] += 1
        if s != -INF:
            o['slack_p50_h'].append(s)
    rows = []
    for k, o in sorted(out.items(), key=lambda x: -x[1]['gates']):
        o = dict(o)
        o['slack_p50_h'] = pct(o['slack_p50_h'], 0.5) if o['slack_p50_h'] else float('nan')
        rows.append({'skill': k, **o})
    return rows


_WORLD = {}


def world(P):
    if 'w' not in _WORLD:
        _WORLD['w'] = World(P)
        build_contract_index(_WORLD['w'])
    _WORLD['w'].P = P
    return _WORLD['w']


def run_scenario(P, profile, mode, runs, seed):
    W = world(P)
    t = time.time()
    rs = [Run(W, profile, mode, seed * 100003 + i).simulate() for i in range(runs)]
    S = summarize(W, rs)
    S['combat'] = combat_index(W, S, P, profile)
    S['uniques'] = unique_timing(W, rs)
    S['meta'] = {'profile': profile, 'mode': mode, 'runs': runs, 'seed': seed, 'seconds': round(time.time() - t, 1)}
    return W, rs, S


def report(S, out=None):
    table('median skill level at each phase end', S['levels'])
    table('gates by skill (median over players and runs)', gate_rollup(S['gates']))
    table('play hours to reach a level (median; inf = not in the run)', S['hours_to'])
    table('reward cadence, whole run', S['cadence'])
    table('reward cadence by biome', S['phase_cadence'])
    table('combat index vs vanilla at biome entry (>1 = harder than vanilla)', S['combat'])
    table('uniques: odds and timing per player (Rares rule 1)', S['uniques'])
    table('coin flows per player (mean over the run)', S['coins'])
    table('coins held at each phase end (per player)', S['coins_ts'])
    print(f"coins held at run end (median per player): {S['coin_end']:.0f}\n")
    table('collection log at run end (per player)', S['log'])
    print(f"collection log lit at run end: {S['log_total']:.0%}\n")
    table('notable drops per player-run (S2+)', S['items'][:30])
    table('unlock density by biome', S['density'])
    print('magic items per player-run by rarity:', {k: round(v, 2) for k, v in S['magic'].items()})
    print('boss kills per run:', S['boss_kills'], '\n', S['meta'])
    if out:
        out = Path(out)
        out.mkdir(parents=True, exist_ok=True)
        write_csv(out / 'levels.csv', S['levels'])
        write_csv(out / 'hours_to.csv', S['hours_to'])
        write_csv(out / 'levels_ts.csv', S['levels_ts'])
        write_csv(out / 'gate_slack.csv', S['gates'])
        write_csv(out / 'gates_by_skill.csv', gate_rollup(S['gates']))
        write_csv(out / 'cadence.csv', S['cadence'] + S['phase_cadence'])
        write_csv(out / 'combat_index.csv', S['combat'])
        write_csv(out / 'uniques.csv', S['uniques'])
        write_csv(out / 'coins.csv', S['coins'])
        write_csv(out / 'coins_ts.csv', S['coins_ts'])
        write_csv(out / 'collection_log.csv', S['log'])
        write_csv(out / 'loot_items.csv', S['items'])
        write_csv(out / 'density.csv', S['density'])
        json.dump({k: v for k, v in S.items() if k in ('meta', 'magic', 'boss_kills', 'coin_end', 'log_total',
                                                       'log_items', 'kills_per_h')}, open(out / 'summary.json', 'w'), indent=1)


# ---------- modes ----------
def cmd_inputs(P):
    W = World(P)
    build_contract_index(W)
    print(f'creatures with loot {len(W.drops)}, vanilla drop rows {sum(len(v) for v in W.vanilla.values())}, '
          f'uniques {len(W.uniques)}, gates {len(W.gates)}, quests {len(W.quests)} '
          f'(contracts {len(W.contracts)}), gamblers {len(W.gamblers)}, objects {len(W.objects)}, '
          f'log rows {len(W.log_rows)}, superior rows {len(W.sup_rows)}')
    rows = [{'key': k, 'source': src, 'value': v, 'profile': p, 'phase': ph}
            for (p, ph, k), (v, src) in sorted(P.rows.items()) if src.startswith('guess')]
    table('guessed inputs (sensitivity varies these)', rows)


def cmd_validate(P):
    fails = []

    def check(name, ok, detail):
        print(f"{'ok  ' if ok else 'FAIL'}  {name}: {detail}")
        if not ok:
            fails.append(name)

    M = RM.MEAS
    # 1. measured.csv hits per kill through rate-model kill_sim, with each row's own backstab / chain setup (#67)
    for key, backstab, chain in (('hits.Boar.Club.0', 0.2, 0.0), ('hits.Neck.Club.0', 0.8, 0.0),
                                 ('hits.Greydwarf.Club.0', 0.6, 0.0), ('hits.Greydwarf.SwordBronze.0', 0.0, 1.0),
                                 ('hits.Greydwarf_Elite.SwordBronze.0', 0.0, 1.0),
                                 ('hits.Greydwarf_Shaman.SwordBronze.0', 0.0, 1.0)):
        _, mob, tool, lvl = key.split('.')
        old = dict(RM.CAL)
        RM.CAL['backstab'], RM.CAL['chain_carry'] = backstab, chain
        it = RM.ITEMS[tool]
        model = RM.kill_sim(it, RM.CREATURES[mob], int(lvl), 1, RM.combo(it) or [1.0])
        RM.CAL.update(old)
        check(key, abs(model / M[key] - 1) <= 0.12, f'measured {M[key]} model {model:.2f}')
    for key, tool, tree, lvl in (('rate.Beech1.AxeStone.8', 'AxeStone', 'Beech1', 8),
                                 ('rate.Beech1.AxeStone.80', 'AxeStone', 'Beech1', 80)):
        r = RM.trees(tool, tree, lvl, 1, 75.0, None, True, 0)
        check(key, abs(r['trees/hr'] / M[key] - 1) <= 0.25, f"measured {M[key]} model {r['trees/hr']}")
    r = RM.mining('PickaxeIron', 'rock4_copper_frac', 21, 1, 99.0, None, 10)   # Calib: Pickaxes ~10 (#67: 0.384 swings/s)
    check('hits.rock4_copper_frac.PickaxeIron.21', abs(r['swings/node'] / M['hits.rock4_copper_frac.PickaxeIron.21'] - 1)
          <= 0.10, f"measured {M['hits.rock4_copper_frac.PickaxeIron.21']} model {r['swings/node']}")
    # 2. nest replay
    W = World(P)
    build_contract_index(W)
    mix, supply = W.mix('BlackForest', 'camp')
    ttk = sum(w * W.ttk('BlackForest', c, 0) for c, w in mix.items())
    engaged = 3600 / (ttk + RM.CAL['engage_s'])
    check('nest replay (#67 26 kills / 291 s = 321/hr)', 0.8 <= 321.6 / min(supply, engaged) <= 1.05,
          f'model min(supply {supply:.0f}, engaged {engaged:.0f}); mix {({k: round(v, 3) for k, v in mix.items()})}')
    # 3. wolf walk coins
    mu, var, *_ = W.compiled('Wolf', frozenset(), 1)
    exp15 = 15 * mu
    sd = math.sqrt(15 * var)
    z = (242 - exp15) / sd if sd else 0
    z42 = (42 - exp15) / sd if sd else 0
    print(f"info  wolf walk (#70): 15 kills -> expected {exp15:.0f} coins (sd {sd:.0f}); 242 held includes 200 from "
          f"`spawn Coins 200` 27 min earlier (log 2026-09-23 14:38), so ~42 looted (z {z42:.1f}, not {z:.1f})")
    # 4. ladder (#83): our weapon XP per kill vs rate-model's
    lad = RM.ladder(0.25, 100, 120.0)
    xp = 0.0
    ok = True
    for (b, h), row in zip(PHASES, lad):
        L = level_of(xp)
        ok &= abs(L - row['OSRSheim entry']) <= 2
        per_kill = W.hits(b, REP_MOB[b], max(L, 1)) * 1.5 * RM.GAIN_GLOBAL
        xp += per_kill * 100 * h * 0.25
    check('#83 ladder entry levels (+-2)', ok, f"rate-model {[r['OSRSheim entry'] for r in lad[:-1]]}")
    # 5. #84 mining gate XP and 6. #19 alchemy
    xs = [CUM[10], CUM[20], CUM[40]]
    check('#84 Mining XP to 10/20/40 = 76/390/2107', [round(x) for x in xs] == [76, 390, 2107], f'{[round(x) for x in xs]}')
    crops = CUM[50] / (0.4286 * 3)
    check('#19 Alchemy 50 = 2,838 crop units with the stone', abs(crops - 2838) <= 3, f'{crops:.0f} (no stone: {CUM[50] / 0.4286:.0f})')
    # 7. parser: shipped cfg chances vs gen-loot from the csv tables
    classes, creatures, lists, drops = GL.load('time', None)
    diffs = 0
    for c in creatures:
        for rr in drops.get(c['creature'], []):
            if 'unique=' in rr['flags'] or rr['item'] == 'Coins':
                continue
            want = GL.chance(rr['chance'], classes[c['class']], 'time') / 100
            have = [e.p for e in W.drops.get(c['creature'], []) if e.item == rr['item']]
            if not any(abs(h - want) < 1e-6 for h in have):
                diffs += 1
    check('shipped cfg = gen-loot(csv) chances', diffs == 0, f'{diffs} differing creature rows')
    # 8. cross-model: magic items (rate-model magic) - chest + superior streams
    mag = RM.magic()
    check('rate-model magic() runs', mag[-1]['items'] > 0, f"{mag[-1]['items']} items/run (frontier maps, revisit 0.1)")
    # 9. real play: reference\sessions\*.csv rows (no console use) vs the default scenario, per phase; a check from 10 h a phase
    sessions_vs_sim(P, check)
    print(f"\n{len(fails)} failure(s)")
    return 1 if fails else 0


def sessions_vs_sim(P, check, min_h=10.0, paths=None):
    rows = [r for f in (paths or sorted((REF / 'sessions').glob('*.csv'))) for r in csv.DictReader(open(f, encoding='utf-8'))]
    rows = [r for r in rows if not r.get('console') and float(r['hours']) >= 0.25]
    if not rows:
        print('info  reference/sessions/: no real-play rows yet (watch.py records them; session-log.py publish)')
        return
    by = defaultdict(list)
    for r in rows:
        by[BIOMES[min(len(BIOME_OF_KEY.keys() & set(r['bosses'].split())), len(BIOMES) - 1)]].append(r)
    _, _, S = run_scenario(P, 'balanced', 'mixed', 40, 1)
    lv = {row['at']: row for row in S['levels']}
    for b, rs in by.items():
        h = sum(float(r['hours']) for r in rs)
        i = BIOMES.index(b)
        prev = lv[f'end of {BIOMES[i - 1]}'] if i else None
        for col in ['kills_per_h'] + sorted({k for r in rs for k in r if k.startswith('xp_per_h.')}):
            real = sum(float(r.get(col) or 0) * float(r['hours']) for r in rs) / h
            if col == 'kills_per_h':
                sim = S['kills_per_h']
            else:
                sk = col.split('.', 1)[1]
                if sk not in lv[f'end of {b}']:
                    continue
                sim = (CUM[int(lv[f'end of {b}'][sk])] - CUM[int(prev[sk]) if prev else 0]) / (END[b] - START[b])
            ratio = real / sim if sim else INF
            detail = f"{b} {h:.1f} h real {real:.1f} sim {sim:.1f}{' (whole run)' if col == 'kills_per_h' else ''} (x{ratio:.2f})"
            if h >= min_h:
                check(f'sessions {col}', 0.5 <= ratio <= 2, detail)
            else:
                print(f'info  sessions {col}: {detail}; check from {min_h:.0f} h')


SENS_KEYS = ('share.camp', 'share.roam', 'share.elite', 'share.mine', 'share.chop', 'share.farm', 'share.craft',
             'session.hours', 'together', 'weapon.Swords', 'kph_scale.roam', 'kph_scale.elite', 'rate.blocks_per_kill',
             'rate.smith_new_items', 'rate.smith_crafts', 'rate.fish_xp_per_hour', 'rate.revisit_share',
             'rule.bounties_per_session', 'rule.skip_share', 'xp.cookfarm_sgm', 'xp.quest_skill_exp_factor')
SENS_METRICS = ('log_total', 'coin_end', 'S2_P_session', 'S3_P_session', 'swords_walls', 'bsmith_never',
                'blocking_walls', 'swords_end_Plains', 'bsmith_end_Plains', 'alchemy_end_Plains')


def metrics_of(S):
    lv = {r['at']: r for r in S['levels']}
    items = {r['item']: r for r in S['items']}
    bu = [r['P_any'] for k, r in items.items() if k in {'OSRS_GracefulCape', 'OSRS_DragonAxe', 'OSRS_DraugrVisage',
                                                        'OSRS_DragonfireShield', 'OSRS_BandosGodsword', 'OSRS_AbyssalWhip',
                                                        'OSRS_InfernalCape', 'OSRS_ScytheOfVitur'}]
    g = {r['skill']: r for r in gate_rollup(S['gates'])}
    return {'log_total': S['log_total'], 'coin_end': S['coin_end'],
            'S2_P_session': S['cadence'][0]['P_session_sim'], 'S3_P_session': S['cadence'][1]['P_session_sim'],
            'swords_walls': g['Swords']['wall (>5 h late)'] + g['Swords']['never by run end'],
            'bsmith_never': g['Blacksmithing']['never by run end'],
            'blocking_walls': g['Blocking']['wall (>5 h late)'] + g['Blocking']['never by run end'],
            'swords_end_Plains': lv['end of Plains']['Swords'], 'bsmith_end_Plains': lv['end of Plains']['Blacksmithing'],
            'alchemy_end_Plains': lv['end of Plains']['Alchemy'], 'boss_unique_P': 1 - math.prod(1 - x for x in bu) if bu else 0.0}


def cmd_sensitivity(P, runs, seed, out, keys=None):
    _, _, base = run_scenario(P, 'balanced', 'mixed', runs, seed)
    m0 = metrics_of(base)
    rows = []
    for key in keys or SENS_KEYS:
        for f in (0.5, 1.5):
            P.scale = {key: f}
            _, _, S = run_scenario(P, 'balanced', 'mixed', runs, seed)
            m = metrics_of(S)
            for k in SENS_METRICS:
                rows.append({'param': key, 'factor': f, 'metric': k, 'base': m0[k], 'value': m[k],
                             'delta': m[k] - m0[k]})
            print(f'{key} x{f}: ' + ', '.join(f'{k} {m[k]:.3g}' for k in SENS_METRICS), flush=True)
        P.scale = {}
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)
        write_csv(Path(out) / (f'tornado-{keys[0]}.csv' if keys else 'tornado.csv'), rows)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('mode', nargs='?', default='run', choices=['run', 'validate', 'sensitivity', 'inputs'])
    ap.add_argument('--profile', default='balanced')
    ap.add_argument('--mode', dest='play', default='mixed', choices=['mixed', 'together', 'split', 'solo'])
    ap.add_argument('--runs', type=int, default=None)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--out', default=None)
    ap.add_argument('--set', action='append', default=[], help='key=value override of a sim-profiles.csv key')
    ap.add_argument('--keys', default=None, help='sensitivity: comma-separated subset of the guessed inputs')
    a = ap.parse_args()
    P = Params()
    for kv in a.set:
        k, v = kv.split('=', 1)
        P.override[k.strip()] = float(v)
    if a.mode == 'inputs':
        return cmd_inputs(P)
    if a.mode == 'validate':
        return cmd_validate(P)
    if a.mode == 'sensitivity':
        cmd_sensitivity(P, a.runs or 150, a.seed, a.out or str(ROOT / 'sim-out' / 'sensitivity'),
                        a.keys.split(',') if a.keys else None)
        return 0
    _, _, S = run_scenario(P, a.profile, a.play, a.runs or 400, a.seed)
    report(S, a.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
