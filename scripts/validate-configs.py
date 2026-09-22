#!/usr/bin/env python3
"""OSRSheim config validator — run before every test launch. Needs no game running.

    python scripts\\validate-configs.py

Read-only. Checks the authoring copy in the Gale profile:
  1. Prefab names used by Drop That / KG Marketplace / Spawn That / WIRSL / wackydb configs exist in
     the on-disk dumps (BepInEx\\Debug), EpicLoot's item tables, or are our own OSRS_* wackydb clones.
  2. Drop That append-only rule: per-creature IDs >= 100, shared-list IDs >= 110; cfgs match loot\\*.csv.
  3. WIRSL yml parses, entry count, no duplicate PrefabNames.
  4. KG Marketplace cfg cross-references: quest profiles -> quests, dialogues -> nodes/profiles; handbook cfg matches loot\\*.csv.
  5. Every JSON / YAML we touched still parses; EpicLoot loot tables still roll zero items.
  6. reference\\mods.tsv still matches the profile's installed mods (the frozen mod list).
Exit code 1 when any ERROR is printed (WARNs are advisory: names we could not verify on disk).
"""
import glob
import json
import os
import re
import sys

APPDATA = os.environ.get("APPDATA") or os.path.expanduser(r"~\AppData\Roaming")
BEP = os.path.join(APPDATA, "com.kesomannen.gale", "valheim", "profiles", "OSRSheim", "BepInEx")
CFG = os.path.join(BEP, "config")
DBG = os.path.join(BEP, "Debug")
KG = os.path.join(CFG, "Marketplace", "Configs")
HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(os.path.dirname(HERE), "reference")

errors, warns = [], []
def err(msg): errors.append(msg); print("ERROR ", msg)
def warn(msg): warns.append(msg); print("WARN  ", msg)
def ok(msg): print("ok    ", msg)

def read(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.read()

# ---------------------------------------------------------------- verified name universe
items, objects, creatures, clones = set(), set(), set(), set()
try:
    j = json.load(open(os.path.join(REF, "verified-prefab-names.json"), encoding="utf-8"))
    items |= set(j["items"]); objects |= set(j["objects"]); creatures |= set(j.get("creatures", []))
except Exception as e:
    warn(f"reference/verified-prefab-names.json unreadable ({e}); rebuilding from dumps")
before = os.path.join(DBG, "drop_that.character_drop.before_changes.cfg")
if os.path.exists(before):
    t = read(before)
    creatures |= set(re.findall(r"^\[([^\].]+)\.\d+\]", t, re.M))
    items |= set(re.findall(r"^PrefabName\s*=\s*(\S+)", t, re.M))
else:
    err(f"missing dump {before} — load a world once with the Drop That dump flags on")
prefabs = os.path.join(DBG, "drop_that.drop_table.prefabs.txt")
if os.path.exists(prefabs):
    t = read(prefabs)
    objects |= set(re.findall(r"^\[([^\].]+)\]", t, re.M))
    items |= set(re.findall(r"^PrefabName\s*=\s*(\S+)", t, re.M))
for f in glob.glob(os.path.join(CFG, "wackysDatabase", "Items", "Item_*.yml")):
    t = read(f)
    m = re.search(r"^name:\s*(\S+)", t, re.M)
    if m: clones.add(m.group(1))
    m2 = re.search(r"^clonePrefabName:\s*(\S+)", t, re.M)
    if m2 and m2.group(1) not in items:
        err(f"wackydb {os.path.basename(f)} clones unknown prefab {m2.group(1)}")
    # No top-level m_weight = WackysDatabase drops the file at load, silently, no log line.
    # Proven 2026-09-21: of 56 ymls only the 7 without it failed to build; m_maxStackSize
    # does not substitute. Restate the clone target's base weight to keep it a no-op.
    if not re.search(r"^m_weight:\s*\S", t, re.M):
        err(f"wackydb {os.path.basename(f)} has no m_weight; wackydb will skip it silently")
    if re.search(r"^Primary_Attack:", t, re.M) and not re.search(r"^Secondary_Attack:", t, re.M):
        err(f"wackydb {os.path.basename(f)}: Primary_Attack without Secondary_Attack "
            f"(WackysDatabase dereferences Secondary_Attack unguarded; the item's data is dropped)")
known_items = items | clones
ok(f"name universe: {len(items)} items, {len(objects)} objects, {len(creatures)} creatures, {len(clones)} wackydb clones")
if len(clones) != 62:
    warn(f"expected 62 wackydb clones (16 p9-9 + 24 capes + 7 elite uniques + 3 crystal key parts + 6 hull keels + 6 jewellery), found {len(clones)}")

# wackydb Recipes and status effects. Filename prefixes are load-bearing: ReadFiles.cs
# globs "?ecipe_*.yml" and "SE_*.yml" over the whole config tree, so a misnamed file
# is skipped with no log line. A recipe's clonePrefabName is the item it produces.
STATIONS = {"forge", "piece_workbench", "piece_artisanstation", "piece_stonecutter",
            "piece_magetable", "blackforge", "piece_preptable", "opalchemy", "opcauldron", ""}
se_names = set()
for f in glob.glob(os.path.join(CFG, "wackysDatabase", "**", "SE_*.yml"), recursive=True):
    m = re.search(r"^Name:\s*(\S+)", read(f), re.M)
    if m: se_names.add(m.group(1))
for f in glob.glob(os.path.join(CFG, "wackysDatabase", "**", "Recipe_*.yml"), recursive=True):
    t, base = read(f), os.path.basename(f)
    m = re.search(r"^clonePrefabName:\s*(\S+)", t, re.M)
    if not m:
        err(f"wackydb {base}: no clonePrefabName; wackydb cannot resolve the item and creates no recipe")
    elif m.group(1) not in known_items:
        err(f"wackydb {base} makes unknown item {m.group(1)}")
    st = re.search(r"^craftingStation:\s*(\S*)", t, re.M)
    if st and st.group(1) not in STATIONS:
        err(f"wackydb {base}: unknown craftingStation {st.group(1)}")
    for req in re.findall(r"^\s*-\s*(\w+):", t, re.M):
        if req not in known_items:
            err(f"wackydb {base}: req prefab {req} unknown")
# An item pointing at a status effect that no SE_*.yml defines equips with no bonus at all.
for f in glob.glob(os.path.join(CFG, "wackysDatabase", "Items", "Item_*.yml")):
    m = re.search(r"^SE_Equip:\s*\n\s*EffectName:\s*(\S+)", read(f), re.M)
    if m and m.group(1).startswith("SE_OSRS_") and m.group(1) not in se_names:
        err(f"wackydb {os.path.basename(f)}: SE_Equip {m.group(1)} has no SE_*.yml defining it")

KNOWN_KEYS = {"defeated_eikthyr", "defeated_gdking", "defeated_bonemass", "defeated_dragon",
              "defeated_goblinking", "defeated_queen", "defeated_fader", "defeated_frozenking_p3"}


# ---------------------------------------------------------------- 1+2. Drop That
for f in glob.glob(os.path.join(CFG, "drop_that.character_drop*.cfg")):
    if f.endswith(".disabled"): continue
    t = read(f); base = os.path.basename(f)
    is_list = "character_drop_list" in base
    sec = None
    for line in t.splitlines():
        m = re.match(r"^\[([^\]]+)\]", line)
        if m:
            sec = m.group(1)
            head, _, idx = sec.partition(".")
            if idx:
                try: n = int(idx)
                except ValueError: err(f"{base}: bad section {sec}"); continue
                if is_list and n < 110: err(f"{base}: list entry {sec} below 110 (would overwrite vanilla drops)")
                if not is_list and n < 100: err(f"{base}: entry {sec} below 100 (append-only rule)")
            if not is_list and head not in creatures:
                err(f"{base}: [{sec}] creature '{head}' not in the dump roster")
            continue
        m = re.match(r"^PrefabName\s*=\s*(\S+)", line)
        if m and m.group(1) not in known_items:
            err(f"{base}: [{sec}] PrefabName {m.group(1)} unknown")
        m = re.match(r"^ConditionGlobalKeys\s*=\s*(\S+)", line)
        if m and m.group(1) not in KNOWN_KEYS:
            warn(f"{base}: [{sec}] global key {m.group(1)} not in the known boss-key list")
    ok(f"{base}: {t.count(chr(10)+'[')} sections checked")
t = read(os.path.join(CFG, "drop_that.drop_table.cfg"))
for sec in re.findall(r"^\[([^\].]+)(?:\.\d+)?\]", t, re.M):
    if sec not in objects: err(f"drop_that.drop_table.cfg: object '{sec}' not in prefabs dump")
for p in re.findall(r"^PrefabName\s*=\s*(\S+)", t, re.M):
    if p not in known_items: err(f"drop_that.drop_table.cfg: PrefabName {p} unknown")
ok("drop_that.drop_table.cfg objects + items checked")
import subprocess
r = subprocess.run([sys.executable, os.path.join(HERE, "gen-loot.py"), "--check"], capture_output=True, text=True)
if r.returncode == 0: ok("loot cfgs match loot\\*.csv (gen-loot.py --check)")
elif r.returncode == 2: warn(r.stdout.strip())
else: err("loot cfgs differ from loot\\*.csv: run python scripts\\gen-loot.py  (" + r.stdout.strip() + ")")
for flag in ("--check", "--audit"):
    r = subprocess.run([sys.executable, os.path.join(HERE, "gen-collection-log.py"), flag], capture_output=True, text=True)
    if r.returncode == 0: ok(r.stdout.strip())
    else: err(r.stdout.strip().replace(chr(10), " | ") + "  (fix loot\\collection-log.csv, run python scripts\\gen-collection-log.py)")

r = subprocess.run([sys.executable, os.path.join(HERE, "gen-handbook.py"), "--check"], capture_output=True, text=True)
if r.returncode == 0: ok(r.stdout.strip())
else: err(r.stdout.strip().replace(chr(10), " | "))

r = subprocess.run([sys.executable, os.path.join(HERE, "gen-mods.py"), "--check"], capture_output=True, text=True)
if r.returncode == 0: ok("reference\\mods.tsv matches the profile's installed mods")
else: err(r.stdout.strip().replace(chr(10), " | ") + "  (mod list is frozen: an unexpected line means Gale installed, "
          "removed or updated something)")

# ---------------------------------------------------------------- 3. WIRSL
try:
    import yaml
    w = yaml.safe_load(read(os.path.join(CFG, "WackyMole.ItemRequiresSkillLevel.yml")))
    names = [e["PrefabName"] for e in w["Requirements"]]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes: err(f"WIRSL duplicate PrefabNames: {sorted(dupes)}")
    unknown = [n for n in names if n not in known_items]
    if unknown: err(f"WIRSL unknown prefabs: {unknown}")
    ok(f"WIRSL parses: {len(names)} gates (log must say 'Loaded: {len(names)}')")
    skills = {r.get("Skill") for e in w["Requirements"] for r in e.get("Requirements", [])}
    ok(f"WIRSL skills referenced: {sorted(skills)}")
except ImportError:
    warn("PyYAML not installed (pip install pyyaml) — skipped WIRSL/ItemConfig YAML checks")
    yaml = None
except Exception as e:
    err(f"WIRSL yml failed to parse: {e}")

# ---------------------------------------------------------------- 4. KG Marketplace
def kg_sections(folder):
    out = {}
    for f in glob.glob(os.path.join(KG, folder, "*.cfg")):
        cur = None
        for line in read(f).splitlines():
            if line.startswith("#") or not line.strip(): continue
            m = re.match(r"^\[([^\]=@]+)", line)
            if m:
                cur = m.group(1).strip().lower(); out.setdefault(cur, [])
            elif cur is not None:
                out[cur].append(line.strip())
    return out
quests = kg_sections("Quests")
for q, lines in quests.items():
    if len(lines) < 6: err(f"KG quest [{q}] has {len(lines)} lines; needs Type/Title/Desc/Target/Rewards/Cooldown")
    else:
        qtype, target, rewards = lines[0], lines[3], lines[4]
        if qtype in ("Kill", "KillAndCollect"):
            for tgt in target.split("|"):
                c = tgt.split(",")[0].strip()
                if c not in creatures: err(f"KG quest [{q}] kill target '{c}' not a known creature")
        elif qtype in ("Collect", "Craft"):
            for tgt in target.split("|"):
                c = tgt.split(",")[0].strip()
                if c not in known_items: err(f"KG quest [{q}] item '{c}' unknown")
        for r in rewards.split("|"):
            r = r.strip()
            if r.startswith("Item:"):
                c = r[5:].split(",")[0].strip()
                if c not in known_items: err(f"KG quest [{q}] reward item '{c}' unknown")
        for cond in lines[6:]:
            for part in re.split(r"\|\||\|", cond):
                part = part.strip()
                if part.startswith("GlobalKey") and part.split(",")[1].strip() not in KNOWN_KEYS:
                    warn(f"KG quest [{q}] global key {part} not in the known boss-key list")
                if part.startswith("HasItem") and part.split(",")[1].strip() not in known_items:
                    err(f"KG quest [{q}] HasItem prefab {part.split(',')[1].strip()} unknown")
ok(f"KG quests: {len(quests)} parsed")
profiles = kg_sections("QuestProfiles")
for p, lines in profiles.items():
    for qid in ",".join(lines).split(","):
        qid = qid.strip().lower()
        if qid and qid not in quests: err(f"KG quest profile [{p}] references missing quest '{qid}'")
ok(f"KG quest profiles: {sorted(profiles)}")
traders = kg_sections("Traders")
for p, lines in traders.items():
    for line in lines:
        for side in line.split("="):
            toks = [x.strip() for x in side.split(",")]
            for i in range(0, len(toks) - 1, 2):
                if toks[i] and toks[i] not in known_items: err(f"KG trader [{p}]: unknown item '{toks[i]}'")
ok(f"KG traders: {sorted(traders)}")
for p, lines in kg_sections("Bankers").items():
    bad = [l for l in lines if l not in known_items]
    if bad: err(f"KG banker [{p}] unknown items: {bad}")
    ok(f"KG banker [{p}]: {len(lines)} bankable items")
for p, lines in kg_sections("Gamblers").items():
    toks = [x.strip() for x in lines[-1].split(",")]
    for i in range(0, len(toks) - 1, 2):
        if toks[i] not in known_items: err(f"KG gambler [{p}] unknown item '{toks[i]}'")
buffs = kg_sections("Buffers")
for p, lines in kg_sections("BufferProfiles").items():
    for b in lines[0].split(","):
        if b.strip().lower() not in buffs: err(f"KG buffer profile [{p}] references missing buff '{b.strip()}'")
dialogs = kg_sections("Dialogues")
menu_profiles = {"trader": traders, "banker": kg_sections("Bankers"), "quests": profiles,
                 "gambler": kg_sections("Gamblers"), "buffer": kg_sections("BufferProfiles"),
                 "info": kg_sections("ServerInfos")}
for node, lines in dialogs.items():
    for line in lines[1:]:
        for field in line.split("|"):
            field = field.strip()
            if field.startswith("Transition:"):
                tgt = field.split(":", 1)[1].strip().lower()
                if tgt not in dialogs: err(f"KG dialogue [{node}] transition to missing node '{tgt}'")
            if field.startswith("Condition:") and "QuestFinished" in field:
                qref = field.split(",", 1)[1].strip().lower()
                if qref not in quests: err(f"KG dialogue [{node}] QuestFinished references missing quest '{qref}'")
            if field.startswith("Command: OpenUI"):
                args = [a.strip() for a in field.split(",")[1:]]
                if len(args) == 2 and args[1].lower() not in menu_profiles.get(args[0].lower(), {}):
                    err(f"KG dialogue [{node}] OpenUI {args} -> no such profile")
            if "," in field.split(":", 1)[-1] and field.startswith("Text:"):
                warn(f"KG dialogue [{node}] reply text contains a comma (KG field separator): {field}")
ok(f"KG dialogues: {len(dialogs)} nodes")
for p, lines in kg_sections("LeaderboardAchievements").items():
    if len(lines) != 6: err(f"KG achievement [{p}] has {len(lines)} lines, needs 6")
    elif lines[0] in ("MonstersKilled", "KilledBy") and lines[3].split(",")[0].strip() not in creatures:
        err(f"KG achievement [{p}] creature '{lines[3]}' unknown")
    elif lines[0] in ("ItemsCrafted", "Harvested") and lines[3].split(",")[0].strip() not in known_items:
        err(f"KG achievement [{p}] item '{lines[3]}' unknown")

# ---------------------------------------------------------------- Spawn That
t = read(os.path.join(CFG, "spawn_that.world_spawners_advanced.cfg"))
for p in re.findall(r"^PrefabName\s*=\s*(\S+)", t, re.M):
    if p not in creatures: err(f"spawn_that world spawner prefab '{p}' unknown")
for k in re.findall(r"^RequiredGlobalKey\s*=\s*(\S+)", t, re.M):
    if k not in KNOWN_KEYS: warn(f"spawn_that RequiredGlobalKey {k} not in the known boss-key list")
ids = [int(x) for x in re.findall(r"^\[WorldSpawner\.(\d+)\]", t, re.M)]
# Dump 2026-09-20 shows templates 0-102 occupied (44-102 modded, 99-102 Fimbulvinter).
if any(i < 103 for i in ids): err("spawn_that world spawner ID below 103 would MODIFY a vanilla or modded template")
# Station names come from the generator (EpicLoot cfg comments + DLL-derived _TW).
import runpy
_stations = set(runpy.run_path(os.path.join(HERE, "update-superiors.py"))["ANCHOR_LIST"])
_stations.add("piece_workbench")
for line in re.findall(r"^ConditionPositionMustNotBeNearPrefabs\s*=\s*(.+)$", t, re.M):
    bad = [s.strip() for s in line.split(",") if s.strip() and s.strip() not in _stations]
    if bad: err(f"spawn_that base-exclusion prefab(s) not a known station: {bad}")
if re.findall(r"^ConditionPositionMustNotBeNearPrefabs\s*=", t, re.M).__len__() != len(ids):
    err("spawn_that: not every world spawner template has a base-exclusion list")
ok(f"spawn_that world spawners: IDs {ids}")

# Superior safety and actual merged drop-ID collisions (including inherited lists).
import configparser
def ini(path):
    result = configparser.ConfigParser(interpolation=None, strict=True)
    result.read(path, encoding="utf-8-sig")
    return result

try:
    from update_superiors_placeholder import ROWS  # replaced below by file loading
except ImportError:
    import runpy
    superior_spec = runpy.run_path(os.path.join(HERE, 'update-superiors.py'))
    superior_rows = superior_spec['ROWS']
    superior_anchors = set(superior_spec['ANCHOR_LIST'])
try:
    spawns = ini(os.path.join(CFG, 'spawn_that.world_spawners_advanced.cfg'))
    drops = ini(os.path.join(CFG, 'drop_that.character_drop.osrsheim_superiors.cfg'))
    owners, inherited = {}, {}
    lists = ini(os.path.join(CFG, 'drop_that.character_drop_list.shared_tables.cfg'))
    for filename in glob.glob(os.path.join(CFG, 'drop_that.character_drop*.cfg')):
        if 'character_drop_list' in filename:
            continue
        for section, options in ini(filename).items():
            if section == 'DEFAULT':
                continue
            if '.' in section:
                if section in owners:
                    err(f'duplicate drop ID {section}: {owners[section]} / {filename}')
                owners[section] = filename
            elif options.get('usedroplist'):
                inherited[section] = options['usedroplist']
    for creature, list_name in inherited.items():
        for section in lists.sections():
            if section.startswith(list_name + '.'):
                merged = creature + '.' + section.split('.')[1]
                if merged in owners:
                    err(f'drop ID {merged} collides with shared list {section}')
    for sid in [*range(500, 508), 510, 511]:
        opts = spawns[f'WorldSpawner.{sid}']
        listed = {s.strip() for s in opts.get('conditionpositionmustnotbenearprefabs', '').split(',') if s.strip()}
        if not listed >= superior_anchors or opts.getint('conditionpositionmustnotbenearprefabsdistance', 0) < 150:
            err(f'WorldSpawner.{sid}: missing base-station exclusion')
        if opts.getboolean('huntplayer', True) or opts.getboolean('setrelentless', True):
            err(f'WorldSpawner.{sid}: custom encounter hunts players')
    for sid, row in enumerate(superior_rows, 500):
        creature, key, low, high, *_ = row
        opts = spawns[f'WorldSpawner.{sid}']
        if opts.get('requiredglobalkey') != key:
            err(f'WorldSpawner.{sid}: wrong boss gate')
        if opts.getint('spawninterval') != 900 or opts.getfloat('spawnchance') != 8:
            err(f'WorldSpawner.{sid}: superior test spawn rates still active')
        purse = [0, 0]
        for section in drops.sections():
            if not section.startswith(creature + '.'):
                continue
            d = drops[section]
            if int(section.split('.')[1]) < 200 or d.get('conditionglobalkeys') != key or d.getint('conditionminlevel', 0) != 3 or d.getint('conditionmaxlevel', 0) != 3 or d.get('conditionnotcreaturestates') != 'Tamed':
                err(f'{section}: missing superior eligibility condition or reserved ID')
            if d.getboolean('scalebylevel', True) or d.getboolean('droponeperplayer', True) or not 1 <= d.getint('amountmin') <= d.getint('amountmax') <= 100 or not 0 < d.getfloat('chancetodrop') <= 100:
                err(f'{section}: invalid superior quantity or scaling')
            if d.get('prefabname') == 'Coins':
                purse[0] += d.getint('amountmin'); purse[1] += d.getint('amountmax')
                if d.getfloat('chancetodrop') != 100:
                    err(f'{section}: purse is not guaranteed')
        if purse != [low, high]:
            err(f'{creature}: superior purse {purse} differs from {[low, high]}')
    ok('superiors: boss gates, base exclusions, production rates, loot eligibility, purse totals and merged IDs checked')
except Exception as exc:
    err(f'superior safety checks: {exc}')

# ---------------------------------------------------------------- 5. JSON / YAML sanity
EL = os.path.join(CFG, "EpicLoot", "baseconfig")
a = json.loads(read(os.path.join(EL, "adventuredata.json")))
tok = sum(t["RewardIron"] + t["RewardGold"] for t in a["Bounties"]["Targets"])
tok += sum(b["ForestTokens"] + b["GoldTokens"] + b["IronTokens"] for b in a["TreasureMap"]["BiomeInfo"])
if tok: err(f"EpicLoot adventuredata still pays {tok} tokens (should be coins only)")
if a["Gamble"]["GamblesCount"] or a["SecretStash"]["Materials"]: err("EpicLoot gambles/stash still stocked")
ok("EpicLoot adventuredata.json: coins-only economy intact")
lt = json.loads(read(os.path.join(EL, "loottables.json")))
def rollable(node):
    n = 0
    if isinstance(node, dict):
        d = node.get("Drops")
        if isinstance(d, list):
            n += sum(1 for pair in d if isinstance(pair, list) and len(pair) == 2 and pair[0] > 0 and pair[1] > 0)
        for v in node.values(): n += rollable(v)
    elif isinstance(node, list):
        for v in node: n += rollable(v)
    return n
r = rollable(lt)
if r: err(f"EpicLoot loottables.json: {r} entries can still roll a magic item")
else: ok("EpicLoot loottables.json: 0 rollable magic drops")
if yaml:
    for f in [os.path.join(CFG, "ItemConfig.yml"), os.path.join(CFG, "CreatureConfig.yml"),
              os.path.join(KG, "RandomNpcSpeech.yml")]:
        try: yaml.safe_load(read(f)); ok(f"{os.path.basename(f)} parses")
        except Exception as e: err(f"{f} failed to parse: {e}")

# ---------------------------------------------------------------- reminders
mp = read(os.path.join(CFG, "MarketplaceAndServerNPCs.cfg"))
m = re.search(r"^Use Marketplace Locally = (\w+)", mp, re.M)
print(f"note   KG 'Use Marketplace Locally' = {m.group(1) if m else '?'} (true for solo ModTest, false once the server exists)")
cl = read(os.path.join(CFG, "org.bepinex.plugins.creaturelevelcontrol.cfg"))
print("note   CLLC item yaml:", re.search(r"^Use item configuration yaml = (\w+)", cl, re.M).group(1))

print()
print(f"SUMMARY: {len(errors)} error(s), {len(warns)} warning(s)")
sys.exit(1 if errors else 0)
