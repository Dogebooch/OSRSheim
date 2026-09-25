#!/usr/bin/env python3
r"""Extract vanilla prefab values from the Valheim install into reference\game-data\. Never edit the output.

    python scripts\extract-game-data.py            index (cached) + extract + write
    python scripts\extract-game-data.py --reindex  rebuild the bundle index (after a Valheim patch)

Needs: pip install UnityPy TypeTreeGeneratorAPI. Reads only the game install; about 2-3 min.

Prefabs live in valheim_Data\StreamingAssets\SoftRef\Bundles. The bundles carry no typetrees,
so field layouts are rebuilt from valheim_Data\Managed\*.dll (TypeTreeGenerator). MonoScripts
and pointer targets sit in other bundles, so pass 1 indexes every bundle:
  CAB name -> bundle, (CAB, PathID) -> script class, (CAB, PathID) -> GameObject name.
Pointers in the output are written as "@<GameObject name>".

Output (vanilla values; OSRSheim overrides live in config\):
  player.json       Player: speeds, stamina, carry, skill steps
  nodes.json        MineRock5 / MineRock / TreeBase / TreeLog / Destructible roots: HP, tool tier, areas
  items.json        ItemDrop shared data: damages, tool tier, attack, stamina, durability, equip/set effect
  creatures.json    Humanoid/Character + MonsterAI roots
  spawners.json     SpawnSystemList, CreatureSpawner, SpawnArea
  stations.json     Plant, Pickable, Smelter, Fermenter, CookingStation
  vegetation.json   ZoneSystem.m_vegetation: per-zone placement attempts (not realised counts)
  animations.json   Player_animator states: speed, exit time, clip length, clip events
  pieces.json       Piece roots (name, category, station, resources) + PieceTable piece lists (hammer, hoe, ...)
  bosses.json       OfferingBowl altars and boss CreatureSpawners at any depth, keyed "<root>/<object>"
"""
import json
import os
import sys
import time
from pathlib import Path

GAME = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Valheim")
BUNDLES = GAME / r"valheim_Data\StreamingAssets\SoftRef\Bundles"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reference" / "game-data"
CACHE = ROOT / ".cache" / "game-data-index.json"
UNITY = "6000.0.75f1"
COLLIDERS = {"MeshCollider", "BoxCollider", "SphereCollider", "CapsuleCollider"}

SKIP = {"m_GameObject", "m_Script", "m_Enabled", "m_EditorHideFlags", "m_EditorClassIdentifier", "m_Name"}
# Field filters per class; None = keep every non-effect field.
KEEP = {
    "MineRock5": ["m_health", "m_minToolTier", "m_damageModifiers", "m_dropItems", "m_supportCheck", "m_allDestroyedLoot"],
    "MineRock": ["m_health", "m_minToolTier", "m_damageModifiers", "m_dropItems", "m_removeWhenDestroyed"],
    "TreeBase": ["m_health", "m_minToolTier", "m_damageModifiers", "m_dropWhenDestroyed", "m_logPrefab", "m_stubPrefab"],
    "TreeLog": ["m_health", "m_minToolTier", "m_damages", "m_dropWhenDestroyed", "m_subLogPrefab", "m_useSubLogPointRotation"],
    "Destructible": ["m_health", "m_minToolTier", "m_damages", "m_destructibleType", "m_spawnWhenDestroyed"],
    "Character": ["m_name", "m_group", "m_faction", "m_boss", "m_health", "m_damageModifiers", "m_walkSpeed", "m_speed",
                  "m_runSpeed", "m_swimSpeed", "m_flySlowSpeed", "m_flyFastSpeed", "m_staggerWhenBlocked", "m_staggerDamageFactor", "m_tolerateWater"],
    "Humanoid": None,  # filtered to Character fields + weapon sets below
    "MonsterAI": ["m_viewRange", "m_hearRange", "m_alertRange", "m_fleeIfHurtWhenTargetCantBeReached", "m_fleeIfLowHealth",
                  "m_circulateWhileCharging", "m_minAttackInterval", "m_attackPlayerObjects", "m_enableHuntPlayer", "m_idleSound"],
    "ItemDrop": None,
    "SpawnSystemList": ["m_spawners"],
    "CreatureSpawner": ["m_creaturePrefab", "m_levelupChance", "m_minLevel", "m_maxLevel", "m_respawnTimeMinuts",
                        "m_spawnAtDay", "m_spawnAtNight", "m_requireSpawnArea", "m_spawnInPlayerBase", "m_triggerDistance", "m_wakeUpAnimation"],
    "SpawnArea": ["m_prefabs", "m_levelupChance", "m_spawnIntervalSec", "m_triggerDistance", "m_setPatrolSpawnPoint",
                  "m_spawnRadius", "m_nearRadius", "m_farRadius", "m_maxNear", "m_maxTotal", "m_onGroundOnly"],
    "Plant": ["m_name", "m_growTime", "m_growTimeMax", "m_grownPrefabs", "m_minScale", "m_maxScale", "m_growRadius",
              "m_needCultivatedGround", "m_destroyIfCantGrow", "m_biome", "m_tolerateHeat", "m_tolerateCold"],
    "Pickable": ["m_itemPrefab", "m_amount", "m_extraDrops", "m_respawnTimeMinutes", "m_respawnTimeInitMin", "m_respawnTimeInitMax",
                 "m_minAmountScaled", "m_dontScale", "m_harvestable", "m_defaultPicked", "m_enabled"],
    "Smelter": ["m_name", "m_fuelItem", "m_maxOre", "m_maxFuel", "m_fuelPerProduct", "m_secPerProduct", "m_conversion", "m_requiresRoof"],
    "Fermenter": ["m_name", "m_fermentationDuration", "m_conversion"],
    "CookingStation": ["m_name", "m_conversion", "m_requireFire", "m_useFuel", "m_fuelItem", "m_maxFuel", "m_secPerFuel", "m_slots"],
    "Player": ["m_walkSpeed", "m_speed", "m_runSpeed", "m_swimSpeed", "m_crouchSpeed", "m_acceleration", "m_jumpForce",
               "m_staminaRegen", "m_staminaRegenDelay", "m_runStaminaDrain", "m_sneakStaminaDrain", "m_swimStaminaDrainMinSkill",
               "m_swimStaminaDrainMaxSkill", "m_dodgeStaminaUsage", "m_jumpStaminaUsage", "m_blockStaminaDrain", "m_encumberedStaminaDrain",
               "m_maxCarryWeight", "m_eiterRegen", "m_eitrRegenDelay", "m_autoPickupRange", "m_maxInteractDistance"],
    "Skills": ["m_skills", "m_DeathLowerFactor", "m_useSkillCap", "m_totalSkillCap"],
    "ZoneSystem": ["m_vegetation"],
    "Piece": ["m_name", "m_category", "m_craftingStation", "m_resources", "m_enabled", "m_comfort", "m_groundOnly",
              "m_onlyInBiome", "m_canBeRemoved"],
    "PieceTable": ["m_pieces"],
    "OfferingBowl": None,
}
CHILD_OK = {"OfferingBowl", "CreatureSpawner"}  # boss altars and boss spawners sit inside location prefabs
SHARED = ["m_name", "m_itemType", "m_skillType", "m_toolTier", "m_maxQuality", "m_weight", "m_maxStackSize", "m_damages",
          "m_damagesPerLevel", "m_attackForce", "m_backstabBonus", "m_blockPower", "m_blockPowerPerLevel", "m_deflectionForce",
          "m_timedBlockBonus", "m_armor", "m_armorPerLevel", "m_useDurability", "m_useDurabilityDrain", "m_maxDurability",
          "m_durabilityPerLevel", "m_movementModifier", "m_attack", "m_secondaryAttack", "m_food", "m_foodStamina", "m_foodEitr",
          "m_foodBurnTime", "m_foodRegen", "m_value", "m_ammoType", "m_setName", "m_setSize"]
ATTACK = ["m_attackType", "m_attackAnimation", "m_attackRandomAnimations", "m_attackChainLevels", "m_attackStamina",
          "m_attackEitr", "m_attackHealth", "m_speedFactor", "m_speedFactorRotation", "m_attackStartNoise", "m_damageMultiplier",
          "m_damageMultiplierPerMissingHP", "m_damageMultiplierByTotalHealthMissed", "m_staggerMultiplier", "m_forceMultiplier",
          "m_attackRange", "m_attackHeight", "m_attackAngle", "m_attackRayWidth", "m_maxYAngle", "m_lowerDamagePerHit",
          "m_hitTerrain", "m_hitFriendly", "m_multiHit", "m_pickaxeSpecial", "m_lastChainDamageMultiplier", "m_resetChainIfHit",
          "m_projectileVel", "m_projectileVelMin", "m_projectileAccuracy", "m_projectileAccuracyMin", "m_projectiles",
          "m_projectileBursts", "m_burstInterval", "m_reloadTime", "m_reloadStaminaDrain", "m_drawDurationMin", "m_drawStaminaDrain"]


def cab_of(sf):
    return sf.name.split("/")[-1].lower()


def ext_cab(sf, file_id):
    return cab_of(sf) if file_id == 0 else sf.externals[file_id - 1].path.split("/")[-1].lower()


def build_index(UnityPy):
    cab2bundle, scripts, names, mb_class = {}, {}, {}, {}
    files = sorted(os.listdir(BUNDLES))
    envs = []
    for f in files:
        try:
            env = UnityPy.load(str(BUNDLES / f))
        except Exception:
            continue
        for sf in env.assets:
            cab = cab_of(sf)
            cab2bundle[cab] = f
            for pid, o in sf.objects.items():
                t = o.type.name
                if t == "MonoScript":
                    s = o.read()
                    scripts[f"{cab}:{pid}"] = f"{s.m_AssemblyName}|{s.m_Namespace}|{s.m_ClassName}"
                elif t == "GameObject":
                    try:
                        names[f"{cab}:{pid}"] = o.read().m_Name
                    except Exception:
                        pass
        envs.append(f)
    # second pass: MonoBehaviour -> (class, gameobject name) now that every script and GO is known
    for f in envs:
        env = UnityPy.load(str(BUNDLES / f))
        for sf in env.assets:
            cab = cab_of(sf)
            for pid, o in sf.objects.items():
                if o.type.name != "MonoBehaviour":
                    continue
                try:
                    mb = o.read(check_read=False)
                    p = mb.m_Script
                    cls = scripts.get(f"{ext_cab(sf, p.m_FileID)}:{p.m_PathID}", "?|?|?")
                    go = names.get(f"{cab}:{mb.m_GameObject.m_PathID}") or getattr(mb, "m_Name", None) or None  # ScriptableObjects (status effects) have no GameObject
                    mb_class[f"{cab}:{pid}"] = [cls, go]
                except Exception:
                    pass
    return {"unity": UNITY, "cab2bundle": cab2bundle, "scripts": scripts, "names": names, "mb": mb_class}


def main():
    try:
        import UnityPy
        from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
        import UnityPy.helpers.TypeTreeHelper as TTH
    except ImportError:
        sys.exit("pip install UnityPy TypeTreeGeneratorAPI")
    t0 = time.time()
    if "--reindex" in sys.argv or not CACHE.exists():
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        json.dump(build_index(UnityPy), open(CACHE, "w"))
        print(f"indexed in {time.time() - t0:.0f} s")
    idx = json.load(open(CACHE))
    names, mbidx = idx["names"], idx["mb"]
    gen = TypeTreeGenerator(UNITY)
    gen.load_local_game(str(GAME))

    def clean(sf, v):
        if isinstance(v, dict):
            if "m_FileID" in v and "m_PathID" in v and len(v) == 2:
                if not v["m_PathID"]:
                    return None
                key = f"{ext_cab(sf, v['m_FileID'])}:{v['m_PathID']}"
                n = names.get(key) or (mbidx.get(key) or [None, None])[1]
                return f"@{n}" if n else None
            return {k: clean(sf, x) for k, x in v.items() if not k.endswith("Effect") and not k.endswith("Effects")}
        if isinstance(v, list):
            return [clean(sf, x) for x in v]
        if isinstance(v, float):
            return round(v, 4)
        if isinstance(v, (bytes, bytearray)):
            return None
        return v

    def pick(d, keys):
        return {k: d[k] for k in keys if k in d} if keys else {k: v for k, v in d.items() if k not in SKIP}

    wanted = set(KEEP)
    rows = {c: {} for c in wanted}
    deep = {}
    colliders = {}
    anim = {}
    bundles = sorted({idx["cab2bundle"][k.split(":")[0]] for k, (cls, _) in mbidx.items() if cls.split("|")[-1] in wanted})
    for b in bundles:
        env = UnityPy.load(str(BUNDLES / b))
        env.typetree_generator = gen
        for sf in env.assets:
            cab = cab_of(sf)
            for pid, o in sf.objects.items():
                t = o.type.name
                if t == "AnimatorController" and not anim:
                    c = o.read()
                    if c.m_Name == "Player_animator":
                        anim = read_animator(c)
                    continue
                if t != "MonoBehaviour":
                    continue
                cls_full, go_name = mbidx.get(f"{cab}:{pid}", ["?|?|?", None])
                asm, ns, cls = cls_full.split("|")
                if cls not in wanted:
                    continue
                mb = o.read(check_read=False)
                go = mb.m_GameObject.read()
                root = root_of(go)
                child = cls in CHILD_OK and root != go.m_Name
                if child:
                    if f"{root}/{go.m_Name}" in deep.setdefault(cls, {}):
                        continue
                elif root != go.m_Name or root in rows[cls]:
                    continue  # prefab roots only; scene copies and children are skipped
                node = fix_nodes(gen.get_nodes_up(asm, f"{ns}.{cls}" if ns else cls))
                try:
                    tt = o.read_typetree(node)
                except Exception:
                    # the C reader ignores fix_nodes' retype; the pure-Python reader honours it
                    boost, TTH.read_typetree_boost = TTH.read_typetree_boost, None
                    try:
                        tt = o.read_typetree(node)
                    except Exception as e:
                        print(f"  {b} {cls} {root}: {type(e).__name__}")
                        continue
                    finally:
                        TTH.read_typetree_boost = boost
                d = {k: clean(sf, v) for k, v in tt.items() if k not in SKIP}
                if cls == "ItemDrop":
                    sh = (d.get("m_itemData") or {}).get("m_shared") or {}
                    d = {k: sh[k] for k in SHARED if k in sh}
                    for k in ("m_setName", "m_setSize"):
                        if not d.get(k):
                            d.pop(k, None)
                    raw = (tt.get("m_itemData") or {}).get("m_shared") or {}
                    for k in ("m_equipStatusEffect", "m_setStatusEffect"):  # clean() drops *Effect keys
                        if raw.get(k) and clean(sf, raw[k]):
                            d[k] = clean(sf, raw[k])
                    for k in ("m_damages", "m_damagesPerLevel"):
                        if isinstance(d.get(k), dict):
                            d[k] = {t: x for t, x in d[k].items() if x}
                    armed = d.get("m_damages") or d.get("m_toolTier")
                    for a in ("m_attack", "m_secondaryAttack"):
                        if armed and isinstance(d.get(a), dict) and d[a].get("m_attackAnimation"):
                            d[a] = {k: d[a][k] for k in ATTACK if k in d[a]}
                        else:
                            d.pop(a, None)
                elif cls == "Humanoid":
                    d = pick(d, KEEP["Character"] + ["m_defaultItems", "m_randomWeapon", "m_randomArmor", "m_randomShield", "m_randomSets"])
                else:
                    d = pick(d, KEEP[cls])
                if cls == "MineRock5":
                    colliders[root] = count_colliders(go)
                    d["areas"] = colliders[root]
                if child:
                    deep[cls][f"{root}/{go.m_Name}"] = d
                else:
                    rows[cls][root] = d
    OUT.mkdir(parents=True, exist_ok=True)
    creatures = {**rows["Character"], **rows["Humanoid"]}
    for k, v in rows["MonsterAI"].items():
        creatures.setdefault(k, {})["ai"] = v
    files = {
        "player.json": {"Player": rows["Player"].get("Player"), "Skills": rows["Skills"].get("Player")},
        "nodes.json": {c: rows[c] for c in ("MineRock5", "MineRock", "TreeBase", "TreeLog", "Destructible")},
        "items.json": rows["ItemDrop"],
        "creatures.json": creatures,
        "spawners.json": {c: rows[c] for c in ("SpawnSystemList", "CreatureSpawner", "SpawnArea")},
        "vegetation.json": next(iter(rows["ZoneSystem"].values()), {}).get("m_vegetation", []),
        "stations.json": {c: rows[c] for c in ("Plant", "Pickable", "Smelter", "Fermenter", "CookingStation")},
        "animations.json": anim,
        "pieces.json": {c: rows[c] for c in ("Piece", "PieceTable")},
        "bosses.json": {
            "OfferingBowl": {**rows["OfferingBowl"], **deep.get("OfferingBowl", {})},
            "CreatureSpawner": {k: v for k, v in deep.get("CreatureSpawner", {}).items()
                                if (v.get("m_creaturePrefab") or "@")[1:] in {n for n, c in creatures.items() if c.get("m_boss")}},
        },
    }
    for name, data in files.items():
        with open(OUT / name, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, indent=1, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
        print(f"{name}: {os.path.getsize(OUT / name) // 1024} KB")
    print(f"done in {time.time() - t0:.0f} s")


def fix_nodes(node):
    """TypeTreeGenerator types List<string> as "string"; UnityPy then reads one string. Retype it."""
    stack = [node]
    while stack:
        n = stack.pop()
        if n.m_Type == "string" and n.m_Children and n.m_Children[0].m_Children[-1].m_Type != "char":
            n.m_Type = "vector"
        stack.extend(n.m_Children)
    return node


def root_of(go):
    try:
        t = transform_of(go)
        while t.m_Father and t.m_Father.m_PathID:
            t = t.m_Father.read()
        return t.m_GameObject.read().m_Name
    except Exception:
        return go.m_Name


def transform_of(go):
    for c in go.m_Component:
        ptr = c.component if hasattr(c, "component") else c.second
        o = ptr.deref()
        if o.type.name in ("Transform", "RectTransform"):
            return o.read()
    raise ValueError("no transform")


def count_colliders(go):
    """MineRock5.Awake: every Collider in children is one hit area."""
    n, stack = 0, [transform_of(go)]
    while stack:
        t = stack.pop()
        g = t.m_GameObject.read()
        if not g.m_IsActive:
            continue
        for c in g.m_Component:
            ptr = c.component if hasattr(c, "component") else c.second
            if ptr.deref().type.name in COLLIDERS:
                n += 1
        stack.extend(ch.read() for ch in t.m_Children)
    return n


def read_animator(c):
    def d(p):
        return p.data if hasattr(p, "data") else p
    tos = dict(c.m_TOS)
    clips = {}
    states = {}
    cc = d(c.m_Controller)
    for smp in cc.m_StateMachineArray:
        for stp in d(smp).m_StateConstantArray:
            st = d(stp)
            name = str(tos.get(st.m_NameID, st.m_NameID))
            used = []
            for btp in st.m_BlendTreeConstantArray:
                for ndp in d(btp).m_NodeArray:
                    nd = d(ndp)
                    if 0 <= nd.m_ClipID < len(c.m_AnimationClips):
                        cl = c.m_AnimationClips[nd.m_ClipID].read()
                        used.append(cl.m_Name)
                        if cl.m_Name not in clips:
                            mc = cl.m_MuscleClip
                            clips[cl.m_Name] = {
                                "length": round(mc.m_StopTime - mc.m_StartTime, 4),
                                "events": [[round(e.time, 4), e.functionName, round(e.floatParameter, 4)] for e in cl.m_Events],
                            }
            exits = sorted({round(d(x).m_ExitTime, 4) for x in st.m_TransitionConstantArray if d(x).m_HasExitTime})
            states[name] = {"speed": round(st.m_Speed, 4), "exit": exits, "clips": used}
    used_clips = {n for s in states.values() for n in s["clips"] if len(s["clips"]) == 1}
    return {"states": {k: v for k, v in states.items() if len(v["clips"]) == 1},
            "clips": {k: v for k, v in clips.items() if k in used_clips}}


if __name__ == "__main__":
    main()
