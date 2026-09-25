"""Apply the reviewed superior balance profile; preserve originals beside each config.

    python scripts\\update-superiors.py            production rates
    python scripts\\update-superiors.py --wiring   500-507 at 100% per 60 s check (in-game test; validator errors until a plain run)

Vanilla SpawnSystem rolls min(MaxSpawned, elapsed / SpawnInterval) times when a player's zone updates;
a zone never visited, or not visited for MaxSpawned x SpawnInterval, gets MaxSpawned rolls.
Rates: rate-model.py roamers (CAL stale_zones_hr).
"""
import os
import re
import shutil
import sys
from pathlib import Path

from main_guard import require_current

CFG = Path(__file__).resolve().parent.parent / 'config'
# 500-507 production rate: ~0.12 superiors/hr per biome at CAL stale_zones_hr 40 (10 rolls each).
SPAWN_INTERVAL, SPAWN_CHANCE, MAX_SPAWNED = 900, 0.03, 10
WIRING_INTERVAL, WIRING_CHANCE = 60, 100
# 510 troll ~0.6/hr of Meadows night (1 roll per stale zone); 511 scouts ~0.6 groups/hr of BF night (3 rolls).
ROAMER_CHANCE = {510: 1.4, 511: 0.5}
# Superior identity: Spawn That TemplateId on 500-507, Drop That ConditionTemplateId on their loot, so
# natural two-stars (CLLC Custom 9/1) never drop superior loot.
TEMPLATE = 'osrsheim_superior'
# 510 wandering troll: its purse keys on this template, so a Black Forest troll led into Meadows pays nothing.
WANDERER = 'osrsheim_wanderer'
# Vanilla m_minAltitude of the same prefab's world spawner (Spawn That default -1000 spawns under water).
ALTITUDE_MIN = {500: 0, 501: 0, 502: -1.5, 503: 0, 504: 0, 505: 0, 506: 1, 507: 0, 510: 0, 511: 0}
# Station names: EpicLoot's recipe/station tables and the verified Wizardry roster.
ANCHOR_LIST = ['forge', 'blackforge', 'piece_stonecutter', 'piece_artisanstation',
               'WizardTable_TW', 'ArcaneAnvil_TW', 'WeavingLoom_TW', 'PotionCauldron_TW']
ANCHORS = ', '.join(ANCHOR_LIST)
# 510 fires at defeated_eikthyr, when a Meadows base has a workbench and no forge.
EARLY_ANCHORS = ', '.join(ANCHOR_LIST[:2] + ['piece_workbench'] + ANCHOR_LIST[2:])
EARLY_ANCHOR_IDS = {510}
# Key = the boss key that OPENS the superior's biome (2026-09-24: frontier superiors; was the biome's own boss).
ROWS = [
    ('Greydwarf', 'defeated_eikthyr', 40, 70, 'Amber', 1, 2, 'FineWood', 'Resin', 'Ruby', 3),
    ('Skeleton', 'defeated_eikthyr', 40, 70, 'AmberPearl', 1, 1, 'BoneFragments', 'Feathers', 'Ruby', 3),
    ('Draugr', 'defeated_gdking', 80, 140, 'AmberPearl', 1, 2, 'Entrails', 'IronScrap', 'SilverNecklace', 3),
    ('Wolf', 'defeated_bonemass', 100, 180, 'Ruby', 1, 1, 'WolfPelt', 'WolfFang', 'SilverNecklace', 4),
    ('Goblin', 'defeated_dragon', 140, 240, 'Ruby', 1, 2, 'BlackMetalScrap', 'Needle', 'SilverNecklace', 5),
    ('Seeker', 'defeated_goblinking', 200, 340, 'Ruby', 1, 2, 'Carapace', 'ScaleHide', 'SilverNecklace', 6),
    ('Charred_Melee', 'defeated_queen', 280, 460, 'Ruby', 2, 3, 'CharredBone', 'FlametalOreNew', 'SilverNecklace', 8),
    ('JotunWarrior', 'defeated_fader', 360, 600, 'Ruby', 2, 4, 'Crystal', 'Chain', 'SilverNecklace', 8),
]

def save(name, text):
    path = CFG / name
    backup = path.with_name(path.name + '.bak-before-superior-balance')
    if not backup.exists():
        shutil.copy2(path, backup)
    with open(path, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(text)

def main():
    require_current(__file__)
    wiring = '--wiring' in sys.argv
    interval, chance = (WIRING_INTERVAL, WIRING_CHANCE) if wiring else (SPAWN_INTERVAL, SPAWN_CHANCE)
    path = CFG / 'spawn_that.world_spawners_advanced.cfg'
    source = path.read_text(encoding='utf-8-sig')
    blocks = re.split(r'(?=^\[WorldSpawner\.\d+\]$)', source, flags=re.M)[1:]
    out = ['# OSRSheim custom encounters; runtime verification pending.\n'
           '# Superiors unlock with the key that opens their biome (the previous boss), so they roam the frontier;\n'
           f'# {chance:g}% per {interval}-second check.\n'
           '# MaxSpawned 10: vanilla counts every loaded instance of the shared prefab, so 1 let any\n'
           '# loaded common block the roll; vanilla also rolls min(MaxSpawned, elapsed/interval) times,\n'
           '# so a stale zone gets 10 rolls (~0.3% a superior at 0.03%).\n'
           '# No spawn within 150 m horizontally of any listed station.\n'
           '# Base/outpost coverage requires a listed station (a forge is the earliest;\n'
           '# 510 also counts piece_workbench, the only station a Meadows base has).\n'
           '# SpawnDistance: 0 on 500-507 on purpose, they share the common prefab.\n'
           '# This is spawn prevention, not protection from enemies lured back home.\n'
           '# All loot bonuses use IDs 200+; vanilla/shared loot remains intact.\n\n']
    for block in blocks:
        sid = int(re.search(r'WorldSpawner\.(\d+)', block)[1])
        block = re.sub(r'^#.*\n', '', block, flags=re.M)
        if 500 <= sid <= 507:
            block = re.sub(r'^SpawnInterval = .*$', f'SpawnInterval = {interval}', block, flags=re.M)
            block = re.sub(r'^SpawnChance = .*$', f'SpawnChance = {chance:g}', block, flags=re.M)
            block = re.sub(r'^MaxSpawned = .*$', f'MaxSpawned = {MAX_SPAWNED}', block, flags=re.M)
            block = re.sub(r'^RequiredGlobalKey = .*$', 'RequiredGlobalKey = ' + ROWS[sid-500][1], block, flags=re.M)
        if sid in ROAMER_CHANCE:
            block = re.sub(r'^SpawnChance = .*$', f'SpawnChance = {ROAMER_CHANCE[sid]:g}', block, flags=re.M)
        block = re.sub(r'^(?:TemplateId|HuntPlayer|SetRelentless|ConditionPositionMustNotBeNearPrefabs|ConditionPositionMustNotBeNearPrefabsDistance|ConditionAltitudeMin) = .*\n', '', block, flags=re.M)
        anchors = EARLY_ANCHORS if sid in EARLY_ANCHOR_IDS else ANCHORS
        safety = ('HuntPlayer = false\nSetRelentless = false\n'
                  'ConditionPositionMustNotBeNearPrefabs = ' + anchors + '\n'
                  'ConditionPositionMustNotBeNearPrefabsDistance = 150\n'
                  f'ConditionAltitudeMin = {ALTITUDE_MIN[sid]:g}\n')
        if 500 <= sid <= 507:
            safety = f'TemplateId = {TEMPLATE}\n' + safety
        if sid == 510:
            safety = f'TemplateId = {WANDERER}\n' + safety
        block = block.replace('Enabled = true\n', 'Enabled = true\n' + safety)
        # Roamers keep Spawn That's LevelMin/Max (1 = no stars); without this CLLC rolls its own stars.
        if sid in ROAMER_CHANCE and f'[WorldSpawner.{sid}.CreatureLevelAndLootControl]' not in block:
            block = block.rstrip() + f'\n[WorldSpawner.{sid}.CreatureLevelAndLootControl]\nUseDefaultLevels = true\n'
        out.append(block.rstrip() + '\n\n')
    save(path.name, ''.join(out))

    out = ['# OSRSheim superior bonus loot; independent rolls, no vanilla replacements.\n'
           '# IDs 200+ avoid normal purses and shared-list IDs.\n'
           f'# World boss gate + exactly two stars + not tamed + Spawn That template {TEMPLATE}.\n'
           '# Coin ranges are exact totals; each entry <=100, no level/player multiplication.\n\n']
    def entry(creature, idx, item, low, high, chance, conditions, template=TEMPLATE):
        out.append(f'[{creature}.{idx}]\nPrefabName = {item}\nAmountMin = {low}\n'
                   f'AmountMax = {high}\nChanceToDrop = {chance}\nScaleByLevel = false\n'
                   'DropOnePerPlayer = false\n' + conditions + '\n')
        if template:
            out.append(f'[{creature}.{idx}.SpawnThat]\nConditionTemplateId = {template}\n\n')
    for creature, key, low, high, gem, gl, gh, material, extra, rare, rate in ROWS:
        cond = (f'ConditionGlobalKeys = {key}\nConditionMinLevel = 3\n'
                'ConditionMaxLevel = 3\nConditionNotCreatureStates = Tamed\n')
        chunks = (high + 99) // 100
        for i in range(chunks):
            entry(creature, 200+i, 'Coins', low//chunks + (i < low%chunks),
                  high//chunks + (i < high%chunks), 100, cond)
        entry(creature, 210, gem, gl, gh, 30, cond)
        entry(creature, 211, material, 2, 4, 40, cond)
        entry(creature, 212, extra, 1, 2, 20, cond)
        entry(creature, 213, rare, 1, 1, rate, cond)
    # 510 wandering troll reward: keyed on the 510 template (not the biome), collision-free IDs, key gate.
    cond = 'ConditionGlobalKeys = defeated_eikthyr\nConditionNotCreatureStates = Tamed\n'
    entry('Troll', 200, 'Coins', 50, 100, 100, cond, WANDERER)
    entry('Troll', 201, 'Coins', 50, 100, 100, cond, WANDERER)
    entry('Troll', 210, 'Ruby', 1, 1, 50, cond, WANDERER)
    save('drop_that.character_drop.osrsheim_superiors.cfg', ''.join(out))

if __name__ == '__main__':
    main()
