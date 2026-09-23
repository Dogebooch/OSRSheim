"""Apply the reviewed superior balance profile; preserve originals beside each config."""
import os
import re
import shutil
from pathlib import Path

from main_guard import require_current

CFG = Path(os.environ['APPDATA']) / 'com.kesomannen.gale/valheim/profiles/OSRSheim/BepInEx/config'
# Station names: EpicLoot's recipe/station tables and the verified Wizardry roster.
ANCHOR_LIST = ['forge', 'blackforge', 'piece_stonecutter', 'piece_artisanstation',
               'WizardTable_TW', 'ArcaneAnvil_TW', 'WeavingLoom_TW', 'PotionCauldron_TW']
ANCHORS = ', '.join(ANCHOR_LIST)
# 510 fires at defeated_eikthyr, when a Meadows base has a workbench and no forge.
EARLY_ANCHORS = ', '.join(ANCHOR_LIST[:2] + ['piece_workbench'] + ANCHOR_LIST[2:])
EARLY_ANCHOR_IDS = {510}
ROWS = [
    ('Greydwarf', 'defeated_gdking', 40, 70, 'Amber', 1, 2, 'FineWood', 'Resin', 'Ruby', 3),
    ('Skeleton', 'defeated_gdking', 40, 70, 'AmberPearl', 1, 1, 'BoneFragments', 'Feathers', 'Ruby', 3),
    ('Draugr', 'defeated_bonemass', 80, 140, 'AmberPearl', 1, 2, 'Entrails', 'IronScrap', 'SilverNecklace', 3),
    ('Wolf', 'defeated_dragon', 100, 180, 'Ruby', 1, 1, 'WolfPelt', 'WolfFang', 'SilverNecklace', 4),
    ('Goblin', 'defeated_goblinking', 140, 240, 'Ruby', 1, 2, 'BlackMetalScrap', 'Needle', 'SilverNecklace', 5),
    ('Seeker', 'defeated_queen', 200, 340, 'Ruby', 1, 2, 'Carapace', 'ScaleHide', 'SilverNecklace', 6),
    ('Charred_Melee', 'defeated_fader', 280, 460, 'Ruby', 2, 3, 'CharredBone', 'FlametalNew', 'SilverNecklace', 8),
    ('JotunWarrior', 'defeated_frozenking_p3', 360, 600, 'Ruby', 2, 4, 'Crystal', 'Chain', 'SilverNecklace', 8),
]

def save(name, text):
    path = CFG / name
    backup = path.with_name(path.name + '.bak-before-superior-balance')
    if not backup.exists():
        shutil.copy2(path, backup)
    path.write_text(text, encoding='utf-8')

def main():
    require_current(__file__)
    path = CFG / 'spawn_that.world_spawners_advanced.cfg'
    source = path.read_text(encoding='utf-8-sig')
    blocks = re.split(r'(?=^\[WorldSpawner\.\d+\]$)', source, flags=re.M)[1:]
    out = ['# OSRSheim custom encounters; runtime verification pending.\n'
           '# Superiors unlock after their own biome boss; 8% per 900-second check.\n'
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
            block = re.sub(r'^SpawnInterval = .*$', 'SpawnInterval = 900', block, flags=re.M)
            block = re.sub(r'^SpawnChance = .*$', 'SpawnChance = 8', block, flags=re.M)
            block = re.sub(r'^RequiredGlobalKey = .*$', 'RequiredGlobalKey = ' + ROWS[sid-500][1], block, flags=re.M)
        block = re.sub(r'^(?:HuntPlayer|SetRelentless|ConditionPositionMustNotBeNearPrefabs|ConditionPositionMustNotBeNearPrefabsDistance) = .*\n', '', block, flags=re.M)
        anchors = EARLY_ANCHORS if sid in EARLY_ANCHOR_IDS else ANCHORS
        safety = ('HuntPlayer = false\nSetRelentless = false\n'
                  'ConditionPositionMustNotBeNearPrefabs = ' + anchors + '\n'
                  'ConditionPositionMustNotBeNearPrefabsDistance = 150\n')
        block = block.replace('Enabled = true\n', 'Enabled = true\n' + safety)
        out.append(block.rstrip() + '\n\n')
    save(path.name, ''.join(out))

    out = ['# OSRSheim superior bonus loot; independent rolls, no vanilla replacements.\n'
           '# IDs 200+ avoid normal purses and shared-list IDs.\n'
           '# World boss gate + exactly two stars + not tamed; not a unique spawn identity.\n'
           '# Coin ranges are exact totals; each entry <=100, no level/player multiplication.\n\n']
    def entry(creature, idx, item, low, high, chance, conditions):
        out.append(f'[{creature}.{idx}]\nPrefabName = {item}\nAmountMin = {low}\n'
                   f'AmountMax = {high}\nChanceToDrop = {chance}\nScaleByLevel = false\n'
                   'DropOnePerPlayer = false\n' + conditions + '\n')
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
    # Retain the existing off-biome encounter reward, with collision-free IDs and a key gate.
    cond = 'ConditionBiomes = Meadows\nConditionGlobalKeys = defeated_eikthyr\nConditionNotCreatureStates = Tamed\n'
    entry('Troll', 200, 'Coins', 50, 100, 100, cond)
    entry('Troll', 201, 'Coins', 50, 100, 100, cond)
    entry('Troll', 210, 'Ruby', 1, 1, 50, cond)
    save('drop_that.character_drop.osrsheim_superiors.cfg', ''.join(out))

if __name__ == '__main__':
    main()
