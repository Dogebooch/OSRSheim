#!/usr/bin/env python3
"""OSRSheim config validator — run before every test launch. Needs no game running.

    python scripts\\validate-configs.py

Read-only. Checks the authoring copy in the Gale profile:
  1. Prefab names used by Drop That / KG Marketplace / Spawn That / WIRSL / wackydb configs exist in
     the on-disk dumps (BepInEx\\Debug), EpicLoot's item tables, or are our own OSRS_* wackydb clones.
  2. Drop That append-only rule: per-creature IDs >= 100, shared-list IDs >= 110; cfgs match loot\\*.csv.
  3. WIRSL yml parses, entry count, no duplicate PrefabNames.
  4. KG Marketplace cfg cross-references: quest profiles -> quests, dialogues and saved NPCs -> nodes/profiles; handbook cfg matches loot\\*.csv.
  5. Every JSON / YAML we touched still parses; EpicLoot rolls magic items only from the #108 sources.
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
# --repo validates the repo's config\ in place, without pushing to the profile first. Use it from a
# worktree, or whenever another session may be writing the profile. Dumps still read the profile;
# the generators' --check calls always compare loot\*.csv against the repo's config\.
DBG = os.path.join(BEP, "Debug")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(ROOT, "config") if "--repo" in sys.argv else os.path.join(BEP, "config")
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
# reference\game-data\items.json is the ObjectDB item list extracted from the game bundles: every
# name in it is a registered item (cooked foods and fish are in no drop dump).
game_items = set(json.load(open(os.path.join(REF, "game-data", "items.json"), encoding="utf-8")))
items |= game_items
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
    # Object drop tables also spawn debris and creatures (IceShoreShard, SeekerBrood, #134):
    # only names that are real items in game-data count as items.
    items |= set(re.findall(r"^PrefabName\s*=\s*(\S+)", t, re.M)) & game_items
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
# wackydb attack multipliers are absolute (they replace the base's m_*Multiplier), so a
# relative twist must be written as base x twist. Below the base = the special got nerfed.
_base = json.load(open(os.path.join(REF, "game-data", "items.json"), encoding="utf-8"))
_mults = {"DmgMultiplier": "m_damageMultiplier", "StaggerMultiplier": "m_staggerMultiplier",
          "ForceMultiplier": "m_forceMultiplier"}
_mnames = {}
for f in glob.glob(os.path.join(CFG, "wackysDatabase", "Items", "Item_*.yml")):
    t = read(f)
    n = re.search(r"^name:\s*(\S+)", t, re.M)
    mn = re.search(r"^m_name:\s*(.+?)\s*$", t, re.M)
    if n and mn: _mnames[n.group(1)] = mn.group(1)
    m = re.search(r"^clonePrefabName:\s*(\S+)", t, re.M)
    if not m or m.group(1) not in _base: continue
    # A clone inherits its base's m_value: Haldor/Hildir would buy it for coin.
    if _base[m.group(1)].get("m_value", 0) > 0 and not re.search(r"^m_value:", t, re.M):
        err(f"wackydb {os.path.basename(f)}: base {m.group(1)} has m_value {_base[m.group(1)]['m_value']}; "
            f"set m_value (0 = no vendor sale)")
    for blk, key in (("Primary_Attack", "m_attack"), ("Secondary_Attack", "m_secondaryAttack")):
        body = re.search(rf"^{blk}:[ \t]*\r?\n((?:[ \t]+.*\r?\n?)*)", t, re.M)
        atk = _base[m.group(1)].get(key)
        if not body or not atk: continue
        for k, bk in _mults.items():
            v = re.search(rf"^[ \t]+{k}:\s*([\d.]+)", body.group(1), re.M)
            if v and float(v.group(1)) < atk.get(bk, 0):
                err(f"wackydb {os.path.basename(f)}: {blk} {k} {v.group(1)} is below "
                    f"{m.group(1)}'s {atk[bk]} (absolute, not relative: write base x twist)")
# Elite oath cape = its oath cape's name + " (trimmed)".
for n, mn in _mnames.items():
    if re.fullmatch(r"OSRS_OathCape\w+Hard", n):
        want = _mnames.get(n[:-4], "?") + " (trimmed)"
        if mn != want: err(f"wackydb {n}: m_name '{mn}' should be '{want}'")
known_items = items | clones
ok(f"name universe: {len(items)} items, {len(objects)} objects, {len(creatures)} creatures, {len(clones)} wackydb clones")
if len(clones) != 106:
    warn(f"expected 106 wackydb clones (24 capes + 12 pets + 8 uniques + 7 elite uniques "
         f"+ 6 hull keels + 6 riddle rewards + 6 jewellery + 4 riddle-stones "
         f"+ 3 crystal key parts + 8 oath capes + 2 curios + 4 vanity cloaks + 4 saga ranks + 8 elite oath capes + 4 tipped bolts), found {len(clones)}")

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
# Hull keels: OdinShip's PieceManager resolves hull costs at ObjectDB.Awake, before wackydb
# adds the OSRS_Keel* clones, and silently drops a missing requirement. Piece_<hull>.yml
# restates the cost after the clones exist; it must equal the OdinShip cfg (issue #31).
# Pieces are classified by the word "piecehammer" and read by "?iece_*.yml" (ReadFiles.cs).
HULLS = {"Big Cargo Ship": "BigCargoShip", "Cargo Ship": "CargoShip",
         "Double rowing canoe": "DoubleRowingCanoe", "Little Boat": "LittleBoat",
         "Merchants boat": "MercantShip", "Rowing canoe": "RowingCanoe", "War Ship": "WarShip"}
# Hull mats absent from the Drop That dumps; names from OdinShip.dll (new Item / RequiredItems.Add).
ODINSHIP_ITEMS = {"ClothShip", "CaulkedWood", "ResinWood", "ShipRope", "IronNails"}
odin = os.path.join(CFG, "marlthon.OdinShip.cfg")
if os.path.exists(odin):
    hull_cost = {}
    for sec, body in re.findall(r"^\[([^\]]+)\]\s*\n(.*?)(?=^\[|\Z)", read(odin), re.M | re.S):
        c = re.search(r"^Crafting Costs\s*=\s*(.*?)\s*$", body, re.M)
        if sec in HULLS and c:
            hull_cost[HULLS[sec]] = [tuple(t.strip().lower().split(":")) for t in c.group(1).split(",")]
    pieces = {}
    for f in glob.glob(os.path.join(CFG, "wackysDatabase", "**", "Piece_*.yml"), recursive=True):
        t, base = read(f), os.path.basename(f)
        m = re.search(r"^name:\s*(\S+)", t, re.M)
        if not m or "piecehammer" not in t:
            err(f"wackydb {base}: needs name and piecehammer (wackydb skips it otherwise)"); continue
        if re.search(r"^piecehammer:\s*$", t, re.M):
            err(f"wackydb {base}: empty piecehammer (SetPieceRecipeData passes it to GetItemPrefab unguarded)")
        reqs = [tuple(r.split(":")) for r in re.findall(r"^\s*-\s*(\S+)", t, re.M)]
        for r in reqs:
            if len(r) != 4:
                err(f"wackydb {base}: build entry {':'.join(r)} is not Prefab:amount:amountPerLevel:recover")
            elif r[0] not in known_items | ODINSHIP_ITEMS:
                err(f"wackydb {base}: build prefab {r[0]} unknown")
        pieces[m.group(1)] = [(r[0].lower(), r[1], r[3].lower()) for r in reqs if len(r) == 4]
    for hull, cost in hull_cost.items():
        # The build HUD has 6 requirement slots and puts the station after the costs (Hud.SetupPieceInfo):
        # a 6th cost overflows and throws every frame the piece is selected (#135).
        if len(cost) > 5:
            err(f"OdinShip {hull}: {len(cost)} Crafting Costs; the build HUD fits 5 plus the station")
        if any(p.startswith("osrs_") for p, *_ in cost):
            if hull not in pieces:
                err(f"OdinShip {hull} needs an OSRS_ item but has no Piece_{hull}.yml; the requirement is dropped at load")
            elif sorted(pieces[hull]) != sorted(cost):
                err(f"wackydb Piece_{hull}.yml build differs from marlthon.OdinShip.cfg Crafting Costs")
    ok(f"hull pieces: {len(pieces)} wackydb overrides, {len(hull_cost)} OdinShip hulls")

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
    entries, tamed = [], set()
    for line in t.splitlines():
        m = re.match(r"^\[([^\]]+)\]", line)
        if m:
            sec = m.group(1)
            head, _, idx = sec.partition(".")
            # [Creature.N.SpawnThat]: Drop That's Spawn That condition subsection (superior template)
            if idx.endswith(".SpawnThat"): continue
            if idx:
                try: n = int(idx)
                except ValueError: err(f"{base}: bad section {sec}"); continue
                if is_list and n < 110: err(f"{base}: list entry {sec} below 110 (would overwrite vanilla drops)")
                if not is_list and n < 100: err(f"{base}: entry {sec} below 100 (append-only rule)")
                entries.append(sec)
            if not is_list and head not in creatures:
                err(f"{base}: [{sec}] creature '{head}' not in the dump roster")
            continue
        m = re.match(r"^PrefabName\s*=\s*(\S+)", line)
        if m and m.group(1) not in known_items:
            err(f"{base}: [{sec}] PrefabName {m.group(1)} unknown")
        m = re.match(r"^ConditionGlobalKeys\s*=\s*(\S+)", line)
        if m and m.group(1) not in KNOWN_KEYS:
            warn(f"{base}: [{sec}] global key {m.group(1)} not in the known boss-key list")
        if re.match(r"^ConditionNotCreatureStates\s*=.*\bTamed\b", line): tamed.add(sec)
    untamed = [e for e in entries if e not in tamed]
    if untamed:
        err(f"{base}: {len(untamed)} entries without ConditionNotCreatureStates = Tamed "
            f"(tamed kills pay nothing): {untamed[:5]}")
    ok(f"{base}: {t.count(chr(10)+'[')} sections checked")
t = read(os.path.join(CFG, "drop_that.drop_table.cfg"))
for sec in re.findall(r"^\[([^\].]+)(?:\.\d+)?\]", t, re.M):
    if sec not in objects: err(f"drop_that.drop_table.cfg: object '{sec}' not in prefabs dump")
for p in re.findall(r"^PrefabName\s*=\s*(\S+)", t, re.M):
    if p not in known_items: err(f"drop_that.drop_table.cfg: PrefabName {p} unknown")
ok("drop_that.drop_table.cfg objects + items checked")

# Effective-rate check. Weight is a share of the table's picks, not a chance, so an entry
# is only rare relative to the vanilla entries already on the table. Hand-authored weights
# read as if they were rarities and shipped Feathers at 100% on ten empty log tables; this
# recomputes what each entry actually does against the dump.
RATE_CAP = 0.05
if os.path.exists(prefabs):
    dump, cur, cursrc = {}, None, None
    def _miss(ws, w, n):
        if n == 0: return 1.0
        if not ws: return 0.0
        tot = sum(ws) + w
        return sum(x / tot * _miss(ws[:i] + ws[i + 1:], w, n - 1) for i, x in enumerate(ws))
    heads, ents = {}, {}
    for line in read(prefabs).splitlines():
        m = re.match(r"^\[([^\]]+)\]", line)
        if m:
            cur = m.group(1)
            (ents if "." in cur else heads)[cur] = {}
            continue
        if cur and "=" in line:
            k, v = line.split("=", 1)
            (ents if "." in cur else heads)[cur][k.strip()] = v.strip()
    ours, sec, exempt, pending = {}, None, set(), False
    for line in t.splitlines():
        if line.lstrip().startswith("#"):
            if "rate-exempt" in line: pending = True
            continue
        m = re.match(r"^\[([^\]]+)\]", line)
        if m:
            sec = m.group(1); ours[sec] = {}
            if pending: exempt.add(sec)
            pending = False
            continue
        if sec and "=" in line:
            k, v = line.split("=", 1)
            ours[sec][k.strip()] = v.strip()
    for sec, d in ours.items():
        if "." not in sec or "Weight" not in d or sec in exempt: continue
        base = sec.rsplit(".", 1)[0]
        head = heads.get(base)
        if head is None: continue
        ws = [float(v.get("Weight", 0)) for k, v in ents.items() if k.rsplit(".", 1)[0] == base]
        W = sum(ws)
        try: w = float(d["Weight"])
        except ValueError: err(f"drop_that.drop_table.cfg: [{sec}] Weight {d['Weight']!r} is not a number"); continue
        if W <= 0:
            err(f"drop_that.drop_table.cfg: [{sec}] {d.get('PrefabName')} sits on a table with no vanilla "
                f"entries (total weight 0), so it drops on every destruction")
            continue
        lo, hi = int(head.get("DropMin", 1)), int(head.get("DropMax", 1))
        dc = float(head.get("DropChance", 100)) / 100.0
        p = w / (W + w)
        ns = range(lo, hi + 1)
        if head.get("DropOnlyOnce") == "True":  # each pick leaves the list (gen-objects.py miss())
            rate = dc * sum(1 - _miss(ws, w, n) for n in ns) / len(list(ns))
        else:
            rate = dc * sum(1 - (1 - p) ** n for n in ns) / len(list(ns))
        if rate > RATE_CAP:
            err(f"drop_that.drop_table.cfg: [{sec}] {d.get('PrefabName')} drops {rate:.1%} per destruction "
                f"and takes {p:.1%} of {base}'s picks (cap {RATE_CAP:.0%}); weight is a share, not a chance")
    ok(f"drop_that.drop_table.cfg effective rates checked against the dump (cap {RATE_CAP:.0%})")

# Mods that postfix DropTable.GetDropList and would silently multiply every object drop.
t2 = read(os.path.join(CFG, "ItemConfig.yml"))
if re.search(r"^\s*worldLevelToLootAmount\s*:", t2, re.M):
    err("ItemConfig.yml sets worldLevelToLootAmount; CLLC's GetDropList postfix would duplicate "
        "every object drop, including the skilling pets. Remove it.")
else:
    ok("ItemConfig.yml free of worldLevelToLootAmount (CLLC loot multiplier stays a no-op)")
for cfgname, key, expect in (("org.bepinex.plugins.mining.cfg", "Mining Yield Factor", "2"),
                             ("org.bepinex.plugins.lumberjacking.cfg", "Tree item yield modifier at level 100", "2")):
    m = re.search(rf"^{re.escape(key)}\s*=\s*(\S+)", read(os.path.join(CFG, cfgname)), re.M)
    if m and m.group(1) != expect:
        warn(f"{cfgname}: {key} = {m.group(1)} (was {expect}). Smoothbrain duplicates each rolled "
             f"drop floor(1 + skill*(factor-1) + rand) times, so this changes how often a pet lands as a pair.")
ok("Smoothbrain mining/lumberjacking yield factors checked")

import subprocess
r = subprocess.run([sys.executable, os.path.join(HERE, "gen-objects.py"), "--check"], capture_output=True, text=True)
if r.returncode == 0: ok("drop_that.drop_table.cfg matches loot\\objects.csv (gen-objects.py --check)")
else: err("drop_that.drop_table.cfg differs from loot\\objects.csv: run python scripts\\gen-objects.py  ("
          + r.stdout.strip().replace(chr(10), " | ") + ")")
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
    WEAPON_SKILLS = {"Swords": 1, "Knives": 2, "Clubs": 3, "Polearms": 4, "Spears": 5, "Axes": 7, "Bows": 8,
                     "ElementalMagic": 9, "BloodMagic": 10, "Unarmed": 11, "Crossbows": 14}
    WEAPON_TYPES = {3, 4, 14, 15, 19, 20, 22}   # ItemType: one/two-handed, bow, torch, tool, atgeir
    _clone_base = {}
    for f in glob.glob(os.path.join(CFG, "wackysDatabase", "Items", "Item_*.yml")):
        t = read(f)
        n, c = re.search(r"^name:\s*(\S+)", t, re.M), re.search(r"^clonePrefabName:\s*(\S+)", t, re.M)
        if n and c: _clone_base[n.group(1)] = c.group(1)
    for e in w["Requirements"]:
        d = _base.get(_clone_base.get(e["PrefabName"], e["PrefabName"]))
        if not d or d.get("m_itemType") not in WEAPON_TYPES: continue
        for r in e.get("Requirements", []):
            if r.get("Skill") in WEAPON_SKILLS and d.get("m_skillType") != WEAPON_SKILLS[r["Skill"]]:
                err(f"WIRSL {e['PrefabName']}: gated on {r['Skill']} but the item trains skill {d.get('m_skillType')}")
    skills = {r.get("Skill") for e in w["Requirements"] for r in e.get("Requirements", [])} - {None, ""}
    wirsl_keys = {r.get("GlobalKeyReq") for e in w["Requirements"] for r in e.get("Requirements", [])} - {None, ""}
    ok(f"WIRSL skills referenced: {sorted(skills)}")
except ImportError:
    warn("PyYAML not installed (pip install pyyaml) — skipped WIRSL/ItemConfig YAML checks")
    yaml = None
    skills, wirsl_keys = set(), set()
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
hammer_pieces = {x[1:] for x in json.load(open(os.path.join(REF, "game-data", "pieces.json"), encoding="utf-8"))["PieceTable"]["_HammerPieceTable"]["m_pieces"] if x}
# A Kill contract opens with its target's biome: it needs that biome's opening key or a later one.
KEY_ORDER = ["defeated_eikthyr", "defeated_gdking", "defeated_bonemass", "defeated_dragon",
             "defeated_goblinking", "defeated_queen", "defeated_fader"]
BIOME_KEY = {"Black Forest": 0, "Swamp": 1, "Ocean": 1, "Mountain": 2, "Plains": 3, "Mistlands": 4,
             "Ashlands": 5, "Deep North": 6}
creature_biome = {}
with open(os.path.join(os.path.dirname(HERE), "loot", "creatures.csv"), encoding="utf-8") as f:
    for row in f.read().splitlines()[1:]:
        cells = row.split(",")
        if len(cells) > 1: creature_biome.setdefault(cells[1], cells[0])
for q, lines in quests.items():
    if len(lines) < 6: err(f"KG quest [{q}] has {len(lines)} lines; needs Type/Title/Desc/Target/Rewards/Cooldown")
    else:
        qtype, target, rewards = lines[0], lines[3], lines[4]
        if qtype in ("Kill", "KillAndCollect"):
            for tgt in target.split("|"):
                c = tgt.split(",")[0].strip()
                if c not in creatures: err(f"KG quest [{q}] kill target '{c}' not a known creature")
                need = BIOME_KEY.get(creature_biome.get(c))
                if q.startswith("slayer_") and need is not None:
                    have = [KEY_ORDER.index(k) for k in re.findall(r"GlobalKey,\s*(\w+)", " ".join(lines[6:]))
                            if k in KEY_ORDER]
                    if not have or max(have) < need:
                        err(f"KG quest [{q}] hunts {c} ({creature_biome[c]}) without {KEY_ORDER[need]} or a later key")
        elif qtype == "Build":
            for tgt in target.split("|"):
                c = tgt.split(",")[0].strip()
                if c not in hammer_pieces: err(f"KG quest [{q}] build piece '{c}' not on the vanilla hammer (game-data pieces.json)")
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
import csv
with open(os.path.join(os.path.dirname(HERE), "loot", "collection-log.csv"), newline="", encoding="utf-8") as _f:
    _logged = [r["prefab"] for r in csv.DictReader(_f)]
_unbanked = [x for x in _logged if x not in kg_sections("Bankers").get("bank", [])]
if _unbanked: err(f"KG banker [bank]: collection-log items not bankable: {_unbanked}")
for p, lines in kg_sections("Gamblers").items():
    toks = [x.strip() for x in lines[-1].split(",")]
    # The Gambler UI holds 21 prize slots after the cost pair; KG truncates the rest silently.
    if (len(toks) - 2) // 2 > 21: err(f"KG gambler [{p}] has {(len(toks) - 2) // 2} prizes; the UI shows 21")
    for i in range(0, len(toks) - 1, 2):
        if toks[i] not in known_items: err(f"KG gambler [{p}] unknown item '{toks[i]}'")
# Buffers: re-implement the DLL's positional parser (Marketplace.Modules.Buffer.Buffer_Main_Server).
# A block is [id] then 7 RAW lines; the parser only skips blanks/# when scanning for the name line,
# so a blank or comment at i+1..i+6 silently shifts the whole block.
BUFF_MODS = {"modifyattack": "mult", "modifyhealthregen": "mult", "modifystaminaregen": "mult",
             "modifyraiseskills": "mult", "modifyspeed": "mult", "modifynoise": "mult",
             "modifystealth": "mult", "runstaminadrain": "mult",
             "modifymaxcarryweight": "add", "damagereduction": "frac"}
buffs = {}
coin_bought = {}                                # item -> trader profile that sells it for Coins
for _p, _lines in traders.items():
    for _l in _lines:
        _t = [x.strip() for x in _l.split("=")[0].split(",")]
        if len(_t) >= 4 and _t[0] == "Coins":
            coin_bought.setdefault(_t[2], _p)
for f in glob.glob(os.path.join(KG, "Buffers", "*.cfg")):
    raw, base = read(f).splitlines(), os.path.basename(f)
    i = 0
    while i < len(raw):
        line = raw[i].strip()
        if not line or line.startswith("#") or not line.startswith("["):
            i += 1; continue
        bid = line[1:].split("]")[0].strip().lower()
        if i + 6 >= len(raw):
            err(f"KG buffer [{bid}] in {base}: block is cut off; the parser reads 7 lines after [id] "
                f"(it bounds-checks i+5 but reads i+6, so never end the file on the group line)")
            break
        body = raw[i + 1:i + 7]
        bad = [n for n, l in enumerate(body, 1) if not l.strip() or l.strip().startswith("#")]
        if bad:
            err(f"KG buffer [{bid}] in {base}: blank/comment line at offset {bad} inside the block")
            i += 1; continue
        name, dur, icon, cost, mods, vfx, group = [l.strip() for l in raw[i + 1:i + 8]]
        if not dur.isdigit(): err(f"KG buffer [{bid}]: duration '{dur}' is not an integer")
        if icon not in known_items and icon not in objects and icon not in creatures:
            err(f"KG buffer [{bid}]: icon prefab '{icon}' unknown")
        ctoks = [t.strip() for t in cost.split(",")]
        if len(ctoks) != 2 or not ctoks[1].isdigit():
            err(f"KG buffer [{bid}]: cost line '{cost}' is not 'prefab, count'")
        elif ctoks[0] not in known_items:
            err(f"KG buffer [{bid}]: cost prefab '{ctoks[0]}' unknown (it must be an item: "
                f"Init() dereferences its ItemDrop unguarded)")
        elif ctoks[0] in coin_bought:
            err(f"KG buffer [{bid}]: cost prefab '{ctoks[0]}' is sold for coins at [{coin_bought[ctoks[0]]}] "
                f"(coins must not buy prayers)")
        for part in mods.split(","):
            if "=" not in part: err(f"KG buffer [{bid}]: modifier '{part.strip()}' is not 'Key = value'"); continue
            k, v = (x.strip() for x in part.split("=", 1))
            kind = BUFF_MODS.get(k.lower())
            if kind is None: err(f"KG buffer [{bid}]: unknown modifier key '{k}'"); continue
            try: fv = float(v)
            except ValueError: err(f"KG buffer [{bid}]: modifier {k} value '{v}' is not a number"); continue
            if kind == "mult" and fv < 1:
                err(f"KG buffer [{bid}]: {k} = {v} is a multiplier defaulting to 1.0, so this is a "
                    f"{round((1 - fv) * 100)}% PENALTY; use {round(1 + fv, 2)} for a buff")
            if kind == "frac" and not 0 <= fv <= 1:
                err(f"KG buffer [{bid}]: {k} = {v} must be a fraction 0..1 (applied as Clamp01(1 - x))")
        if not group: err(f"KG buffer [{bid}]: group is empty; CanTake() returns false and it can never be bought")
        buffs[bid] = group
        i += 8
ok(f"KG buffers: {len(buffs)} parsed, groups {sorted(set(buffs.values()))}")
for p, lines in kg_sections("BufferProfiles").items():
    for b in lines[0].split(","):
        if b.strip().lower() not in buffs: err(f"KG buffer profile [{p}] references missing buff '{b.strip()}'")
# Quest events: the section id is a quest id, and AddPlayerKey is the only source of a diary key.
player_keys = set()
for q, lines in kg_sections("QuestEvents").items():
    if q not in quests: err(f"KG quest event [{q}] is not a quest id")
    for line in lines:
        for cmd in re.split(r"(?<!\|)\|(?!\|)", line.split(":", 1)[-1]):
            m = re.match(r"\s*AddPlayerKey\s*,\s*(\S+)", cmd)
            if m: player_keys.add(m.group(1).strip())
ok(f"KG quest events: {sorted(player_keys)} granted")
# SkillMore/SkillLess: KG reads the vanilla enum name, else abs(GetStableHashCode(name)) (SkillManager's
# key). An unknown name returns -1, so the gate never opens (kg.Marketplace.dll GetPlayerSkillLevelCustom).
VANILLA_SKILLS = {"Swords", "Knives", "Clubs", "Polearms", "Spears", "Blocking", "Axes", "Bows", "ElementalMagic",
                  "BloodMagic", "Unarmed", "Pickaxes", "WoodCutting", "Crossbows", "Jump", "Sneak", "Run", "Swim",
                  "Fishing", "Cooking", "Farming", "Crafting", "Ride", "Dodge"}
KNOWN_SKILLS = VANILLA_SKILLS | skills
custom_written, custom_read = set(), set()
def kg_conditions(where, text):
    for m in re.finditer(r"(SkillMore|SkillLess)\s*,\s*([^,|]+?)\s*,\s*\d+", text):
        if m.group(2) not in KNOWN_SKILLS: err(f"{where}: {m.group(1)} skill '{m.group(2)}' unknown (the gate never opens)")
    for m in re.finditer(r"(?:Not)?HasPlayerKey\s*,\s*([^|\s]+)", text):
        if m.group(1) not in player_keys: err(f"{where}: HasPlayerKey '{m.group(1)}' is granted by no AddPlayerKey quest event")
    for m in re.finditer(r"CustomValue(?:More|Less)\s*,\s*([^,|\s]+)", text):
        custom_read.add(m.group(1))
# Quest skill gates must be skills sim-run.py levels (TRACKED), or the run cannot be sized.
_sim = read(os.path.join(HERE, "sim-run.py"))
SIM_TRACKED = set(re.findall(r"'(\w+)'", re.search(r"^TRACKED = \{(.*?)\}", _sim, re.M | re.S).group(1)))
for q, lines in quests.items():
    kg_conditions(f"KG quest [{q}]", " | ".join(lines[6:]))
    for s in re.findall(r"SkillMore\s*,\s*(\w+)", " | ".join(lines[6:])):
        if s not in SIM_TRACKED: err(f"KG quest [{q}] gates on {s}, which sim-run.py does not level (TRACKED)")
    if len(lines) > 4:
        for r in lines[4].split("|"):
            k, _, v = r.strip().partition(":")
            toks = [x.strip() for x in v.split(",")]
            if k.strip() == "RandomItem":
                # KG parses prefab, amount, level triples and calls GetPrefab(x).GetComponent unguarded
                if len(toks) % 3: err(f"KG quest [{q}] RandomItem pool is not prefab, amount, level triples")
                for i in range(0, len(toks) - 2, 3):
                    if toks[i] not in known_items: err(f"KG quest [{q}] RandomItem prefab '{toks[i]}' unknown (throws in the reward loop)")
            if k.strip() in ("AddCustomValue", "SetCustomValue"):
                custom_written.add(toks[0])
for q, lines in kg_sections("QuestEvents").items():
    for line in lines:
        custom_written |= set(re.findall(r"(?:Add|Set)CustomValue\s*,\s*([^,|\s]+)", line))
# Hunt contract skip fee = the pay's value in coins: coins + each item at the gem trader's (Gullveig) price
# (QuestEvents\osrsheim_slayer_skip.cfg). Contracts pay gems, not coins (2026-09-24), so the fee is what the pay is worth.
_gem_price = {}
for _l in kg_sections("Traders").get("gem_trader", []):
    _t = [x.strip() for x in _l.split(",")]
    if len(_t) == 4 and _t[2] == "Coins" and "=" not in _l:
        _gem_price[_t[0]] = int(_t[3]) / int(_t[1])
for q, lines in kg_sections("QuestEvents").items():
    m = re.search(r"OnCancelQuest:\s*RemoveItem,\s*Coins,\s*(\d+)", " ".join(lines))
    if not m or len(quests.get(q, [])) <= 4:
        continue
    pay = re.findall(r"Item:\s*(\w+),\s*(\d+)", quests[q][4])
    unpriced = [i for i, _ in pay if i != "Coins" and i not in _gem_price]
    if unpriced:
        err(f"KG quest event [{q}] skip fee: pay item(s) {unpriced} have no gem-trader price"); continue
    value = sum(int(n) * (1 if i == "Coins" else _gem_price[i]) for i, n in pay)
    if pay and int(m.group(1)) != max(1, round(value)):
        err(f"KG quest event [{q}] skip fee {m.group(1)} is not the pay's value ({value:g}c at Gullveig)")
for k in sorted(wirsl_keys):
    if k.startswith("oath_") and k not in player_keys:
        err(f"WIRSL GlobalKeyReq '{k}' is granted by no AddPlayerKey quest event")
dialogs = kg_sections("Dialogues")
menu_profiles = {"trader": traders, "banker": kg_sections("Bankers"), "quests": profiles,
                 "gambler": kg_sections("Gamblers"), "buffer": kg_sections("BufferProfiles"),
                 "info": kg_sections("ServerInfos"), "teleporter": kg_sections("Teleporters")}
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
            if field.startswith("Condition:") and "HasPlayerKey" in field:
                for grp in field.split(":", 1)[1].split("||"):
                    if "HasPlayerKey" not in grp: continue
                    k = grp.split(",", 1)[1].strip()
                    if k not in player_keys:
                        err(f"KG dialogue [{node}] HasPlayerKey '{k}' is granted by no AddPlayerKey quest event")
            if field.startswith("Command: OpenUI"):
                args = [a.strip() for a in field.split(",")[1:]]
                if len(args) == 2 and args[1].lower() not in menu_profiles.get(args[0].lower(), {}):
                    err(f"KG dialogue [{node}] OpenUI {args} -> no such profile")
            if field.startswith("Condition:"):
                kg_conditions(f"KG dialogue [{node}]", field)
                m = re.match(r"Condition:\s*(?:Not)?HasItem\s*,\s*([^,]+)", field)
                if m and m.group(1).strip() not in known_items:
                    err(f"KG dialogue [{node}] HasItem prefab '{m.group(1).strip()}' unknown (dialogue HasItem fails OPEN)")
            if field.startswith("Command:"):
                args = [a.strip() for a in field.split(":", 1)[1].split(",")]
                if args[0] == "GiveItem" and len(args) != 4:
                    err(f"KG dialogue [{node}] GiveItem needs item, amount, level (KG reads split[3] unguarded): {field}")
                if args[0] in ("GiveItem", "RemoveItem") and len(args) > 1 and args[1] not in known_items:
                    err(f"KG dialogue [{node}] {args[0]} prefab '{args[1]}' unknown")
                if args[0] in ("AddCustomValue", "SetCustomValue") and len(args) > 1:
                    custom_written.add(args[1])
            if "," in field.split(":", 1)[-1] and field.startswith("Text:"):
                warn(f"KG dialogue [{node}] reply text contains a comma (KG field separator): {field}")
ok(f"KG dialogues: {len(dialogs)} nodes")
for k in sorted(custom_read - custom_written):
    err(f"KG custom value '{k}' is read by a CustomValueMore/Less condition but no reward or command writes it")
# Saved NPCs (Marketplace Hammer templates): a mistyped Profile or Dialogue fails silently in game.
saved = glob.glob(os.path.join(CFG, "Marketplace_SavedNPCs", "*.yml"))
for f in saved:
    t = read(f)
    field = lambda k: (re.search(rf"^\s+{k}:\s*'?([^'\n]*)'?\s*$", t, re.M) or [None, ""])[1].strip()
    kind, prof, dlg = field("Type"), field("Profile"), field("Dialogue")
    name = os.path.basename(f)
    if kind.lower() in menu_profiles and prof.lower() not in menu_profiles[kind.lower()]:
        err(f"KG saved NPC {name}: {kind} profile '{prof}' does not exist")
    if dlg and dlg.lower() not in dialogs: err(f"KG saved NPC {name}: dialogue '{dlg}' does not exist")
    if not field("ModelScale"): err(f"KG saved NPC {name}: no ModelScale (1 = normal size)")
ok(f"KG saved NPCs: {len(saved)}")
for p, lines in kg_sections("LeaderboardAchievements").items():
    if len(lines) != 6: err(f"KG achievement [{p}] has {len(lines)} lines, needs 6")
    elif lines[0] in ("MonstersKilled", "KilledBy") and lines[3].split(",")[0].strip() not in creatures:
        err(f"KG achievement [{p}] creature '{lines[3]}' unknown")
    elif lines[0] in ("ItemsCrafted", "Harvested") and lines[3].split(",")[0].strip() not in known_items:
        err(f"KG achievement [{p}] item '{lines[3]}' unknown")
# I8: no OSRS item names in OSRSheim display text (prefab IDs and ids like crystal_chest stay).
OSRS_NAMES = re.compile(r"\bcrystal (key|chest)\b|\b(loop|tooth) half\b", re.I)
shown = glob.glob(os.path.join(KG, "**", "*.cfg"), recursive=True)
shown += glob.glob(os.path.join(CFG, "wackysDatabase", "**", "*.yml"), recursive=True)
shown.append(os.path.join(ROOT, "loot", "collection-log.csv"))
named = [f"{os.path.basename(f)}:{n}" for f in shown for n, line in enumerate(read(f).splitlines(), 1)
         if not line.lstrip().startswith("#") and OSRS_NAMES.search(line)]
for h in named: err(f"OSRS name in player-facing text: {h} (Hoard key / Gambler's hoard)")
if not named: ok(f"no OSRS key/chest names in {len(shown)} display-text files")

# ---------------------------------------------------------------- Spawn That
t = read(os.path.join(CFG, "spawn_that.world_spawners_advanced.cfg"))
for p in re.findall(r"^PrefabName\s*=\s*(\S+)", t, re.M):
    if p not in creatures: err(f"spawn_that world spawner prefab '{p}' unknown")
for k in re.findall(r"^RequiredGlobalKey\s*=\s*(\S+)", t, re.M):
    if k not in KNOWN_KEYS: warn(f"spawn_that RequiredGlobalKey {k} not in the known boss-key list")
ids = [int(x) for x in re.findall(r"^\[WorldSpawner\.(\d+)\]", t, re.M)]
# Dump 2026-09-22 shows templates 0-114 occupied (44-114 modded, 100-102 Fimbulvinter, 103-114 Wizardry).
if any(i < 115 for i in ids): err("spawn_that world spawner ID below 115 would MODIFY a vanilla or modded template")
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
        if opts.getfloat('conditionaltitudemin', -1000) != superior_spec['ALTITUDE_MIN'][sid]:
            err(f'WorldSpawner.{sid}: ConditionAltitudeMin not the vanilla value (Spawn That default -1000 spawns under water)')
        if sid in superior_spec['ROAMER_CHANCE'] and opts.getfloat('spawnchance') != superior_spec['ROAMER_CHANCE'][sid]:
            err(f'WorldSpawner.{sid}: SpawnChance differs from update-superiors.py ROAMER_CHANCE')
        cllc = f'WorldSpawner.{sid}.CreatureLevelAndLootControl'
        if cllc not in spawns.sections() or not spawns[cllc].getboolean('usedefaultlevels', False):
            err(f'{cllc}: missing or UseDefaultLevels not true (CLLC would roll its own stars)')
    # B7: the 510 troll purse keys on its Spawn That template, not the biome.
    wanderer = superior_spec['WANDERER']
    if spawns['WorldSpawner.510'].get('templateid') != wanderer:
        err(f'WorldSpawner.510: TemplateId is not {wanderer}')
    for section in drops.sections():
        if re.fullmatch(r'Troll\.2\d\d', section):
            sub = f'{section}.SpawnThat'
            if sub not in drops.sections() or drops[sub].get('conditiontemplateid') != wanderer:
                err(f'{section}: needs [{sub}] ConditionTemplateId = {wanderer}')
    for sid, row in enumerate(superior_rows, 500):
        creature, key, low, high, *_ = row
        opts = spawns[f'WorldSpawner.{sid}']
        if opts.get('requiredglobalkey') != key:
            err(f'WorldSpawner.{sid}: wrong boss gate')
        if opts.get('templateid') != superior_spec['TEMPLATE']:
            err(f'WorldSpawner.{sid}: TemplateId is not {superior_spec["TEMPLATE"]}')
        if (opts.getint('spawninterval') != superior_spec['SPAWN_INTERVAL'] or opts.getfloat('spawnchance') != superior_spec['SPAWN_CHANCE']
                or opts.getint('maxspawned') != superior_spec['MAX_SPAWNED']):
            err(f'WorldSpawner.{sid}: superior rates differ from update-superiors.py (test rates still active?)')
        purse = [0, 0]
        for section in drops.sections():
            if not section.startswith(creature + '.'):
                continue
            d = drops[section]
            if section.endswith('.SpawnThat'):
                if d.get('conditiontemplateid') != superior_spec['TEMPLATE']:
                    err(f'{section}: ConditionTemplateId is not {superior_spec["TEMPLATE"]}')
                continue
            # natural two-stars exist (CLLC Custom 9/1): only the Spawn That template may drop superior loot
            if f'{section}.SpawnThat' not in drops.sections():
                err(f'{section}: no [{section}.SpawnThat] ConditionTemplateId subsection')
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
# gen-loot.py writes one table per unique= row in drops.csv: a lone OSRS_ clone at Legendary rarity.
def unique_table(t):
    loot = t.get("Loot") or []
    return len(loot) == 1 and loot[0].get("Item") in clones and loot[0].get("Rarity") == [0, 0, 0, 1, 0, 0]
uniq = [t for t in lt["LootTables"] if unique_table(t)]
# #108 magic-item sources: 2-star roll (4%: superiors and CLLC's natural 1%) on the tier tables + JotunWarrior, and the treasure-map chests (#107).
EL_2STAR = {f"Tier{i}Mob" for i in range(10)} | {"JotunWarrior"}
def allowed(t):
    if t["Object"].startswith("TreasureMapChest_"):
        return all(p[0] <= 1 for p in t.get("Drops") or [])
    return False
rest = []
for t in lt["LootTables"]:
    if unique_table(t) or allowed(t): continue
    if t["Object"] in EL_2STAR and not t.get("Loot"):
        for x in t.get("LeveledLoot") or []:
            if x["Level"] == 3 and x["Drops"] == [[0, 96], [1, 4]]:
                if any((l.get("Rarity") or [0])[4:] != [0, 0] for l in x["Loot"]):
                    err(f"EpicLoot {t['Object']} level 3: Mythic/Ancient must be 0")
                x = {**x, "Drops": []}
            rest.append(x)
        rest.append({**t, "LeveledLoot": []})
        continue
    rest.append(t)
r = rollable(rest)
if r: err(f"EpicLoot loottables.json: {r} entries can still roll a magic item")
else: ok(f"EpicLoot loottables.json: magic drops only from {len(uniq)} unique tables, 2-star tiers and map chests (#108)")
# #108: fixed effect counts (Magic 1 ... Legendary 4); no carry weight on magic items (#17).
cnt = lt["MagicEffectsCount"]
bad = [r for n, r in enumerate(["Magic", "Rare", "Epic", "Legendary"], 1) if cnt.get(r) != [[n, 100]]]
if bad: err(f"EpicLoot MagicEffectsCount {bad} not fixed at Magic 1 / Rare 2 / Epic 3 / Legendary 4 (#108)")
me = {e["Type"]: e for e in json.loads(read(os.path.join(EL, "magiceffects.json")))["MagicItemEffects"]}
if me.get("AddCarryWeight", {}).get("SelectionWeight") != 0: err("EpicLoot AddCarryWeight SelectionWeight must be 0 (#108, #17)")
if not bad: ok("EpicLoot effect counts fixed 1/2/3/4; AddCarryWeight off")
leg = {x["ID"]: x for x in json.loads(read(os.path.join(EL, "legendaries.json")))["LegendaryItems"]}
for t in uniq:
    if t.get("RefObject"): err(f"EpicLoot unique table {t['Object']} still has RefObject {t['RefObject']} (aliased away)")
osrs_leg = [x for x in leg.values() if x["ID"].startswith("OSRSheim_")]
for x in osrs_leg:
    if x.get("GuaranteedEffectCount") != len(x.get("GuaranteedMagicEffects", [])):
        err(f"EpicLoot legendary {x['ID']}: GuaranteedEffectCount must equal its effect count (else random extras)")
    for g in x.get("GuaranteedMagicEffects", []):
        if me.get(g["Type"], {}).get("SelectionWeight") != 0:
            err(f"EpicLoot {x['ID']}: signature effect {g['Type']} still rolls on magic items (SelectionWeight must be 0)")
ok(f"EpicLoot legendaries.json: {len(osrs_leg)} OSRSheim legendaries, fixed effect counts, signature effects weight 0")
if yaml:
    for f in [os.path.join(CFG, "ItemConfig.yml"), os.path.join(CFG, "CreatureConfig.yml"),
              os.path.join(KG, "RandomNpcSpeech.yml")]:
        try: yaml.safe_load(read(f)); ok(f"{os.path.basename(f)} parses")
        except Exception as e: err(f"{f} failed to parse: {e}")

# ---------------------------------------------------------------- reminders
mp = read(os.path.join(CFG, "MarketplaceAndServerNPCs.cfg"))
m = re.search(r"^Use Marketplace Locally = (\w+)", mp, re.M)
print(f"note   KG 'Use Marketplace Locally' = {m.group(1) if m else '?'} (false joins the host; sync-configs -Push -Solo sets true for ModTest)")
cl = read(os.path.join(CFG, "org.bepinex.plugins.creaturelevelcontrol.cfg"))
print("note   CLLC item yaml:", re.search(r"^Use item configuration yaml = (\w+)", cl, re.M).group(1))

print()
print(f"SUMMARY: {len(errors)} error(s), {len(warns)} warning(s)")
sys.exit(1 if errors else 0)
