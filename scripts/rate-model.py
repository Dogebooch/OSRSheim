#!/usr/bin/env python3
r"""Actions/hr from game data (#67). Reads reference\game-data\ (extract-game-data.py), config\, reference\measured.csv.

    python scripts\rate-model.py                 early-game summary (all three activities)
    python scripts\rate-model.py mining   [--tool PickaxeAntler] [--node rock4_copper_frac] [--weapon-level <Pickaxes>]
    python scripts\rate-model.py trees    [--tool AxeStone] [--tree Beech1] [--no-logs] [--weapon-level 0]
    python scripts\rate-model.py combat   [--tool Club] [--mob Greydwarf]
    python scripts\rate-model.py swings   seconds per attack for every mapped animation
    python scripts\rate-model.py objects  [--write]  pet/curio/gem target per loot\objects.csv row at OBJ_SETUP
    common: --levels 0,25,50,100  --quality 1  --stamina 75  --world <save folder>  --json
    combat: --backstab 0.5  share of kills opened unaware; --chain-carry 0  isolated kills (default CAL)

Output is the ENGAGED rate (swinging at targets) plus travel from density. Every number the files
cannot give is a named parameter below (CAL); in-game checks in #67 replace them via measured.csv.

Formulas (decompiled 1.0.15 unless noted):
  skill roll        U[clamp(l-.15), clamp(l+.15)], l = lerp(.4, 1, L/100)            Skills.GetRandomSkillRange
  damage/hit        base(quality) x roll x mod factor x damage modifier; last combo hit x2   Attack.DoMeleeAttack
  Mining factor     1 + sf x (cfg - 1)          Lumberjacking factor  1 + sf x cfg      Smoothbrain DLLs
  yield             every GetDropList item x floor(1 + sf x (cfg - 1) + U[0,1]) on rocks and trees; Mining XP
                    +1 per pickaxe hit on any rock at or above its tool tier, ore or plain stone   Smoothbrain source
                    Lumberjacking swaps vanilla WoodCutting for a dummy at 0: tree rolls stay at skill 0
  stamina/swing     cost x (1 - .33 x sf(weapon skill)); no regen while attacking, 1 s delay, then
                    6 + 6 x (1 - s/max) per s; regen runs through fall, split and walk   Attack, Player
                    tree hits never raise Axes (Calib Axes 0 at Lumberjacking 80): tree cost uses --weapon-level 0
  swing time        Player_animator state speed x clip events (Speed, hit freeze .15 s, Chain), exit time
  XP/level          .5 x (L+1)^1.5 + .5; weapon +1 per swing that hits (x1.5 on creatures) x step x gain;
                    Mining +1 per rock hit x .5 step; vanilla gain x Global 0.5 (SkillGainModifier)
  creature hit      first hit on an unalerted mob x m_backstabBonus (once per 300 s); staggering mob x2;
                    stagger when (blunt+slash+pierce+lightning) x attack stagger mult reaches HP x
                    m_staggerDamageFactor, then capped there, decaying over 5 s              Character
"""
import csv
import json
import math
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GD = ROOT / "reference" / "game-data"
CFG = ROOT / "config"
ZONE_M2 = 64.0 * 64.0
DT = 0.02  # FixedUpdate step
FREEZE = 0.15  # Attack.m_freezeFrameDuration
MOD = {0: 1.0, 1: 0.5, 2: 1.5, 3: 0.0, 4: 0.0, 5: 0.25, 6: 2.0, 7: 0.75, 8: 1.25}  # HitData.DamageModifier
DTYPES = ["m_blunt", "m_slash", "m_pierce", "m_chop", "m_pickaxe", "m_fire", "m_frost", "m_lightning", "m_poison", "m_spirit"]
ALIAS = {"swing_longsword": "swing_sword {i}", "knife_stab": "knife slash {n}", "bow_fire": "bow fire",
         "dual_knives": "dual knives slash {n}"}

# Calibration parameters: files cannot give these. measured.csv keys of the same name override them.
CAL = {
    "hit_fraction": 1.0,        # MineRock5 parts broken by damage; the rest collapse unsupported (free)
    "rock_multi": 1 / 0.75,     # damage into broken areas per swing / unsplit swing: roll / (0.75 n) over every collider
                                # touched incl. ground, less overkill and damage on areas that later collapse
    "log_halves": 2,            # TreeLog -> subLog pieces
    "fall_s": 4.0,              # per tree idle time (regen runs): fall, split, walk to log and halves, s
    "speed_ms": 4.0,            # travel speed between targets (jog 4, run 7), m/s
    "tortuosity": 1.3,          # path length / straight line
    "placement": 0.52,          # realised / attempted vegetation (Beech1 ModTest 20.9 of 40 per zone)
    "engage_s": 3.0,            # per kill: approach, face, dodge, loot
    "refill": 1.0,              # stamina fraction a player waits for once empty
    "stagger_s": 2.0,           # creature stagger animation: hits landing inside it deal x2
    "backstab": 0.0,            # share of kills opened on an unalerted mob (x m_backstabBonus); normal play ~0
    "chain_carry": 1.0,         # share of kills that start mid-combo (swinging on from the last target)
    "melee_hit": 0.86,          # share of combat swings that connect
}


def load(name):
    return json.load(open(GD / name, encoding="utf-8"))


def cfg_value(file, key, default):
    try:
        for line in open(CFG / file, encoding="utf-8-sig"):
            m = re.match(rf"\s*{re.escape(key)}\s*=\s*([-\d.]+)", line)
            if m:
                return float(m.group(1))
    except FileNotFoundError:
        pass
    return default


def measured():
    out = {}
    p = ROOT / "reference" / "measured.csv"
    if p.exists():
        for r in csv.DictReader(open(p, encoding="utf-8")):
            try:
                out[r["key"]] = float(r["value"])
            except ValueError:
                pass
    return out


MEAS = measured()
for k in CAL:
    CAL[k] = MEAS.get(f"cal.{k}", CAL[k])
ITEMS, NODES, CREATURES, PLAYER, ANIM = (load(f) for f in ("items.json", "nodes.json", "creatures.json", "player.json", "animations.json"))
VEG, SPAWN = load("vegetation.json"), load("spawners.json")
STEPS = {s["m_skill"]: s["m_increseStep"] for s in PLAYER["Skills"]["m_skills"]}
GAIN_GLOBAL = cfg_value("jujuz1.mods.skillgainmodifier.cfg", "Global", 1.0)
MINING = (cfg_value("org.bepinex.plugins.mining.cfg", "Mining Damage Factor", 3.0),
          cfg_value("org.bepinex.plugins.mining.cfg", "Skill Experience Gain Factor", 1.0))
LUMBER = (cfg_value("org.bepinex.plugins.lumberjacking.cfg", "Damage to trees modifier at level 100", 3.0),
          cfg_value("org.bepinex.plugins.lumberjacking.cfg", "Skill Experience Gain Factor", 1.0))


# ---------- skills ----------
def roll_range(level):
    l = 0.4 + 0.6 * level / 100.0
    return max(0.0, l - 0.15), min(1.0, l + 0.15)


def xp_to_reach(level):
    return sum(0.5 * (L + 1) ** 1.5 + 0.5 for L in range(int(level)))


# ---------- animation ----------
def states_for(anim, levels):
    names = []
    for i in range(max(1, levels)):
        for pat in (ALIAS.get(anim, ""), f"{anim} {i}", anim):
            n = pat.format(i=i, n=i + 1) if pat else ""
            if n and n in ANIM["states"]:
                names.append(n)
                break
    return names


def run_state(name, hit, chain, speed):
    """One attack state at DT steps. Returns (seconds, hit count, animator speed carried on)."""
    st = ANIM["states"][name]
    clip = ANIM["clips"][st["clips"][0]]
    end = clip["length"] * (st["exit"][0] if st["exit"] else 1.0)
    events = sorted(clip["events"])
    t = tc = 0.0
    pause, restore, hits, i = 0.0, speed, 0, 0
    while tc < end:
        t += DT
        if pause > 0:
            pause -= DT
            if pause <= 0:
                speed = restore
        tc += DT * st["speed"] * speed
        while i < len(events) and events[i][0] <= tc:
            _, fn, val = events[i]
            i += 1
            if fn == "Speed":
                if pause > 0:
                    restore = val
                else:
                    speed = val
            elif fn in ("Hit", "OnAttackTrigger"):
                hits += 1
                if hit:
                    restore, speed, pause = speed, 0.0001, FREEZE
            elif fn == "Chain" and chain:
                return t, hits, speed
    return t, hits, 1.0


def combo(item, hit=True):
    """Seconds of each attack in a full combo, swung continuously."""
    a = item["m_attack"]
    names = states_for(a["m_attackAnimation"], a.get("m_attackChainLevels", 0))
    out, speed = [], 1.0
    for k, n in enumerate(names):
        s, _, speed = run_state(n, hit, chain=k < len(names) - 1, speed=speed)
        out.append(s)
    return out


# ---------- damage ----------
def item_damage(item, quality):
    d = dict(item.get("m_damages", {}))
    for k, v in item.get("m_damagesPerLevel", {}).items():
        d[k] = d.get(k, 0) + v * (quality - 1)
    return d


def hit_damage(dmg, mods, roll, mult):
    return sum(v * roll * mult * MOD.get((mods or {}).get(k, 0), 1.0) for k, v in dmg.items() if k in DTYPES)


def hits_to_kill(hp, dmg, mods, level, mult, chain_mult=None, n=4000, seed=1):
    """Monte Carlo: mean hits to take hp to 0 with random skill rolls (and combo last-hit bonus)."""
    lo, hi = roll_range(level)
    rng = random.Random(seed)
    total = 0
    for _ in range(n):
        h = k = 0
        while h < hp:
            m = mult * (chain_mult[k % len(chain_mult)] if chain_mult else 1.0)
            h += hit_damage(dmg, mods, rng.uniform(lo, hi), m)
            k += 1
            if k > 10000:
                return math.inf
        total += k
    return total / n


# ---------- stamina ----------
def sustained(cycle_s, cost, max_stam):
    """Swings/s over a long session: spend to empty, then stand still and refill."""
    if cost <= 0:
        return 1 / cycle_s, 0.0
    burst = int(max_stam // cost) or 1
    s, t = max_stam - burst * cost, 1.0  # 1 s regen delay
    target = max_stam * CAL["refill"]
    while s < target:
        s += (6 + 6 * (1 - s / max_stam)) * DT
        t += DT
    return burst / (burst * cycle_s + t), t


def regen(s, max_stam):
    return (6 + 6 * (1 - s / max_stam)) * DT


def chop_cycle(segments, gaps, cycle_s, cost, max_stam, n=30):
    """Mean s per target, steady state: swing each segment (no regen while attacking), idle gaps[i] after
    segment i (regen after 1 s delay); once empty, stand until stamina reaches refill x max."""
    s, timer, t, acc = max_stam, 0.0, 0.0, [0.0] * len(segments)
    target = max(cost + 0.1, max_stam * CAL["refill"])
    for _ in range(n):
        for i, (seg, gap) in enumerate(zip(segments, gaps)):
            acc[i] += seg
            k, acc[i] = int(acc[i]), acc[i] - int(acc[i])
            for _ in range(k):
                while s < cost + 0.1:
                    while s < target:
                        timer -= DT
                        if timer <= 0:
                            s = min(max_stam, s + regen(s, max_stam))
                        t += DT
                s, timer, t = s - cost, 1.0, t + cycle_s
            for _ in range(int(round(gap / DT))):
                timer -= DT
                if timer <= 0 and s < max_stam:
                    s = min(max_stam, s + regen(s, max_stam))
            t += gap
    return t / n


# ---------- density ----------
def density(prefab, world_counts=None):
    """Targets per m2 inside their biome: measured.csv density.<prefab> (count-world.py --biomes), world save,
    else vegetation attempts x placement (sums every biome's entries: an upper bound)."""
    if f"density.{prefab}" in MEAS:
        return MEAS[f"density.{prefab}"] / ZONE_M2, "measured per biome"
    if world_counts and prefab in world_counts:
        n, zones = world_counts[prefab]
        return n / zones / ZONE_M2, "world save"
    per_zone = 0.0
    for v in VEG:
        if v.get("m_enable") and v.get("m_prefab") == f"@{prefab}":
            per_zone += (v["m_min"] + v["m_max"]) / 2 * (v["m_groupSizeMin"] + v["m_groupSizeMax"]) / 2
    return per_zone * CAL["placement"] / ZONE_M2, "vegetation x placement"


def travel_s(rho):
    if rho <= 0:
        return math.inf
    return 0.5 / math.sqrt(rho) * CAL["tortuosity"] / CAL["speed_ms"]


# ---------- activities ----------
def mining(tool, node, level, quality, max_stam, world, weapon_level=None):
    it, rock = ITEMS[tool], NODES["MineRock5"].get(node) or NODES["MineRock"][node]
    if it.get("m_toolTier", 0) < rock["m_minToolTier"]:
        return {"error": f"{tool} tier {it.get('m_toolTier', 0)} < {node} tier {rock['m_minToolTier']}"}
    sf = level / 100
    wl = level if weapon_level is None else weapon_level  # vanilla Pickaxes: damage roll and stamina discount
    mult = 1 + sf * (MINING[0] - 1)
    areas = MEAS.get(f"segments.{node}", rock.get("areas", 1))
    lo, hi = roll_range(wl)
    per_swing = hit_damage({"m_pickaxe": item_damage(it, quality).get("m_pickaxe", 0)}, rock["m_damageModifiers"],
                           (lo + hi) / 2, mult * CAL["rock_multi"])
    swings = MEAS.get(f"swings.{node}.{tool}.{level}") or areas * CAL["hit_fraction"] * rock["m_health"] / per_swing
    cycle = sum(combo(it)) / max(1, len(combo(it)))
    cost = it["m_attack"]["m_attackStamina"] * (1 - 0.33 * wl / 100)
    rate, _ = sustained(cycle, cost, max_stam)
    work = swings / rate
    unbroken = node.replace("_frac", "")
    rho, src = density(unbroken, world)
    trav = travel_s(rho)
    per_node = work + trav
    xp_mining = swings * MINING[1]  # +1 per part hit x step: lower bound (a swing can hit several parts)
    return {"tool": tool, "node": node, "level": level, "areas": areas, "dmg/swing": round(per_swing, 1),
            "swings/node": round(swings), "s/swing": round(cycle, 3), "swings/s": round(rate, 3),
            "work s/node": round(work), "travel s/node": round(trav), "density src": src,
            "nodes/hr": round(3600 / per_node, 2), "segments/hr": round(3600 / per_node * areas),
            "Mining xp/hr >=": round(3600 / per_node * xp_mining)}


def trees(tool, tree, level, quality, max_stam, world, logs=True, weapon_level=0):
    it, tb = ITEMS[tool], NODES["TreeBase"][tree]
    if it.get("m_toolTier", 0) < tb["m_minToolTier"]:
        return {"error": f"{tool} tier {it.get('m_toolTier', 0)} < {tree} tier {tb['m_minToolTier']}"}
    sf = level / 100
    mult = 1 + sf * LUMBER[0]
    chop = {"m_chop": item_damage(it, quality).get("m_chop", 0)}
    a = it["m_attack"]
    reset = a.get("m_resetChainIfHit", 0) & 2  # DestructibleType.Tree: every tree hit restarts the combo
    chain = [1.0] * (1 if reset else max(1, a.get("m_attackChainLevels", 0)))
    if len(chain) > 1:
        chain[-1] = a.get("m_lastChainDamageMultiplier", 2.0)
    # Lumberjacking replaces vanilla WoodCutting with a dummy skill fixed at 0: the roll never improves
    roll_level = 0
    segs = [hits_to_kill(tb["m_health"], chop, tb["m_damageModifiers"], roll_level, mult, chain)]
    if logs:
        log = NODES["TreeLog"].get((tb.get("m_logPrefab") or "@")[1:])
        if log:
            segs.append(hits_to_kill(log["m_health"], chop, log.get("m_damages"), roll_level, mult, chain))
            half = NODES["TreeLog"].get((log.get("m_subLogPrefab") or "@")[1:])
            if half:
                segs.append(CAL["log_halves"] * hits_to_kill(half["m_health"], chop, half.get("m_damages"), roll_level, mult, chain))
    hits = sum(segs)
    times = [run_state(states_for(a["m_attackAnimation"], 1)[0], True, False, 1.0)[0]] if reset else combo(it)
    cycle = sum(times) / len(times)
    cost = a["m_attackStamina"] * (1 - 0.33 * weapon_level / 100)
    rho, src = density(tree, world)
    trav = travel_s(rho)
    gaps = [CAL["fall_s"] / max(1, len(segs) - 1)] * (len(segs) - 1) + [trav]
    per = chop_cycle(segs, gaps, cycle, cost, max_stam)
    work = per - trav
    return {"tool": tool, "tree": tree, "level": level, "logs": logs, "hits/tree": round(hits, 1),
            "s/swing": round(cycle, 3), "swings/s": round(hits / work, 3), "work s/tree": round(work, 1),
            "travel s/tree": round(trav, 1), "density src": src, "trees/hr": round(3600 / per, 1),
            "Lumberjacking xp/hr": round(3600 / per * hits * LUMBER[1], 1)}


# ---------- loot\objects.csv (#67) ----------
# Tool and skill level a player brings to each object: the biome's tool, level mid-band of its gate (§6).
OBJ_SETUP = {
    "Beech1": ("AxeFlint", 8), "Oak1": ("AxeBronze", 18), "FirTree": ("AxeBronze", 18),
    "FirTree_big": ("AxeBronze", 18), "Pinetree_01": ("AxeBronze", 18), "SwampTree1_log": ("AxeIron", 30),
    "SnowFirTree": ("AxeIron", 30), "SnowFirTree 2": ("AxeIron", 30), "Pinetree_Snow": ("AxeIron", 30),
    "Pinetree_Snow_dead": ("AxeIron", 30), "rock4_copper_frac": ("PickaxeBronze", 15),
    "MineRock_Tin": ("PickaxeBronze", 15), "mudpile_frac": ("PickaxeIron", 25), "mudpile2_frac": ("PickaxeIron", 25),
    "rock3_silver_frac": ("PickaxeIron", 35), "silvervein_frac": ("PickaxeIron", 35),
    "MineRock_Obsidian": ("PickaxeIron", 35),
}
for _p in ("Birch1", "Birch1_aut", "Birch2", "Birch2_aut"):
    OBJ_SETUP[_p] = ("AxeBronze", 18)
for _p in ("YggaShoot1", "YggaShoot2", "YggaShoot3"):
    OBJ_SETUP[_p] = ("AxeBlackMetal", 45)
for _p in ("AshlandsTree1", "AshlandsTree3", "AshlandsTree4", "AshlandsTree5", "AshlandsTree6", "AshlandsTree6_big"):
    OBJ_SETUP[_p] = ("AxeJotunBane", 60)
DENSITY_PROXY = {"rock3_silver": "silvervein", "SnowFirTree 2": "SnowFirTree"}
TRAVEL_FALLBACK = {"trees": 4.0, "mining": 27.0}  # s: rate-model Beech1/Fir/Pine and rock4_copper travel
YIELD = {"Pickaxe": cfg_value("org.bepinex.plugins.mining.cfg", "Mining Yield Factor", 2.0),  # x every GetDropList item
         "Axe": cfg_value("org.bepinex.plugins.lumberjacking.cfg", "Tree item yield modifier at level 100", 2.0)}
PET_HOURS = 400.0           # OSRS skilling pets (rock golem, beaver) at a normal rate
CURIO_PER_HR = 720 / 500    # Geode/Burl 35c each: the shipped 1/500 per segment at the old 720 segments/hr
GEM_PER_HR = 720 / 256      # ore gems: the shipped 1/256 per segment at 720/hr


def destructible_rate(tool, node, level, quality, max_stam):
    """Destructible ore (Tin, Obsidian): one drop roll per node."""
    it, rock = ITEMS[tool], NODES["Destructible"][node]
    if it.get("m_toolTier", 0) < rock["m_minToolTier"]:
        return None
    lo, hi = roll_range(level)
    per = hit_damage({"m_pickaxe": item_damage(it, quality).get("m_pickaxe", 0)}, rock.get("m_damages"),
                     (lo + hi) / 2, 1 + level / 100 * (MINING[0] - 1))
    swings = max(1.0, math.ceil(rock["m_health"] / per))
    cycle = sum(combo(it)) / max(1, len(combo(it)))
    rate, _ = sustained(cycle, it["m_attack"]["m_attackStamina"] * (1 - 0.33 * level / 100), max_stam)
    rho, _ = density(node)
    trav = travel_s(rho) if rho > 0 else TRAVEL_FALLBACK["mining"]
    return 3600 / (swings / rate + trav)


def object_rate(obj, quality, max_stam):
    """Drop events/hr for one objects.csv object: trees felled (or logs), segments, or nodes. None = unmodelled."""
    if obj not in OBJ_SETUP:
        return None, ""
    tool, level = OBJ_SETUP[obj]
    if obj in NODES["Destructible"]:
        r = destructible_rate(tool, obj, level, quality, max_stam)
        return r, f"{tool} Mining {level}, per node"
    if obj in NODES["TreeLog"]:  # SwampTree1: the log carries the table; the stump has no drops
        log = NODES["TreeLog"][obj]
        it = ITEMS[tool]
        hits = hits_to_kill(log["m_health"], {"m_chop": item_damage(it, quality).get("m_chop", 0)}, log.get("m_damages"),
                            0, 1 + level / 100 * LUMBER[0])
        tree = obj.replace("_log", "")
        base = NODES["TreeBase"].get(tree)
        if base:
            hits += hits_to_kill(base["m_health"], {"m_chop": item_damage(it, quality).get("m_chop", 0)},
                                 base["m_damageModifiers"], 0, 1 + level / 100 * LUMBER[0])
        rho, _ = density(tree)
        trav = travel_s(rho) if rho > 0 else TRAVEL_FALLBACK["trees"]
        t = run_state(states_for(it["m_attack"]["m_attackAnimation"], 1)[0], True, False, 1.0)[0]
        per = chop_cycle([hits], [trav + CAL["fall_s"]], t, it["m_attack"]["m_attackStamina"], max_stam)
        return 3600 / per, f"{tool} Lumberjacking {level}, per log"
    if obj in NODES["TreeBase"]:
        prox = DENSITY_PROXY.get(obj)
        if prox and f"density.{obj}" not in MEAS:
            MEAS[f"density.{obj}"] = MEAS.get(f"density.{prox}", density(prox)[0] * ZONE_M2)
        if density(obj)[0] <= 0:
            MEAS[f"density.{obj}"] = 0.5 / (TRAVEL_FALLBACK["trees"] * CAL["speed_ms"] / CAL["tortuosity"]) ** 2 * ZONE_M2
        r = trees(tool, obj, level, quality, max_stam, None)
        if "error" in r:
            return None, r["error"]
        return r["trees/hr"], f"{tool} Lumberjacking {level}, per tree"
    if obj in NODES["MineRock5"]:
        unbroken = obj.replace("_frac", "")
        prox = DENSITY_PROXY.get(unbroken)
        if f"density.{unbroken}" not in MEAS:
            if prox:
                MEAS[f"density.{unbroken}"] = MEAS.get(f"density.{prox}", density(prox)[0] * ZONE_M2)
            if density(unbroken)[0] <= 0:
                MEAS[f"density.{unbroken}"] = 0.5 / (TRAVEL_FALLBACK["mining"] * CAL["speed_ms"] / CAL["tortuosity"]) ** 2 * ZONE_M2
        r = mining(tool, obj, level, quality, max_stam, None)
        if "error" in r:
            return None, r["error"]
        return r["segments/hr"], f"{tool} Mining {level}, per segment"
    return None, ""


def share_cap(obj):
    """Highest per-destruction chance an added entry may have: gen-objects.py MAX_SHARE (1%) of the vanilla picks,
    less 5%. None when nodes.json has no drop table for the object (Destructible ore: DropOnDestroyed)."""
    for kind, key in (("TreeBase", "m_dropWhenDestroyed"), ("TreeLog", "m_dropWhenDestroyed"), ("MineRock5", "m_dropItems")):
        t = NODES[kind].get(obj, {}).get(key)
        if t and t.get("m_drops"):
            ns = range(t["m_dropMin"], t["m_dropMax"] + 1)
            return 0.95 * t["m_dropChance"] * sum(1 - (1 - 0.01) ** n for n in ns) / len(ns)
    return None


def fraction(p):
    """1/N, N rounded up (never above the solved chance or the share cap): to 10s, 100s, then 1000s."""
    if p <= 0:
        return "0"
    step = 10 if p > 1 / 1000 else 100 if p > 1 / 100000 else 1000
    return f"1/{math.ceil(1 / p / step) * step}"


def objects(quality, max_stam, write=False):
    """Solve every pet/curio/gem row in loot\objects.csv to a per-hour target at the modelled rate."""
    path = ROOT / "loot" / "objects.csv"
    lines = open(path, encoding="utf-8", newline="").read().splitlines()
    head, out, rows, cache = lines[0].split(","), [lines[0]], [], {}
    for line in lines[1:]:
        row = next(csv.reader([line]))
        rec = dict(zip(head, row))
        obj, item = rec.get("object", ""), rec.get("item", "")
        if obj not in cache:
            cache[obj] = object_rate(obj, quality, max_stam)
        rate, how = cache[obj]
        if rate and not rec["target"].startswith("w="):
            per_hr = {"OSRS_PetMining": 1 / PET_HOURS, "OSRS_PetWoodcutting": 1 / PET_HOURS,
                      "OSRS_Geode": CURIO_PER_HR, "OSRS_Burl": CURIO_PER_HR}.get(item, GEM_PER_HR)
            tool, level = OBJ_SETUP[obj]
            y = 1 + level / 100 * (YIELD["Pickaxe" if tool.startswith("Pickaxe") else "Axe"] - 1)
            p, cap = per_hr / (rate * y), share_cap(obj)
            if cap and p > cap:
                p, how = cap, how + f", share cap {cap * rate:.2f}/hr"
            rec["target"] = fraction(p)
            rec["note"] = f"rate-model {rate:.0f}/hr x yield {y:g}, {how}" + (f"; {rec['note']}" if rec["note"] and not rec["note"].startswith("rate-model") else "")
        rows.append({"object": obj, "item": item, "events/hr": round(rate, 1) if rate else "unmodelled",
                     "setup": how, "target": rec["target"]})
        buf = __import__("io").StringIO()
        csv.writer(buf, lineterminator="").writerow([rec[h] for h in head])
        out.append(buf.getvalue())
    if write:
        open(path, "w", encoding="utf-8", newline="").write("\n".join(out) + "\n")
    return rows


def kill_sim(it, cr, level, quality, times, n=4000, seed=1):
    """Monte Carlo hits per kill: rolls, combo last-hit bonus, opening backstab (CAL share), stagger x2."""
    a, dmg, mods = it["m_attack"], item_damage(it, quality), cr.get("m_damageModifiers")
    chain = [1.0] * max(1, a.get("m_attackChainLevels", 0))
    if len(chain) > 1:
        chain[-1] = a.get("m_lastChainDamageMultiplier", 2.0)
    hp, thr = cr["m_health"], cr["m_health"] * cr.get("m_staggerDamageFactor", 0)
    stag_types = ("m_blunt", "m_slash", "m_pierce", "m_lightning")
    lo, hi = roll_range(level)
    rng, total = random.Random(seed), 0
    for _ in range(n):
        h = k = t = s = 0.0
        until = -1.0
        back = it.get("m_backstabBonus", 1.0) if rng.random() < CAL["backstab"] else 1.0
        c0 = rng.randrange(len(chain)) if rng.random() < CAL["chain_carry"] else 0
        k = 0
        while h < hp:
            if k:
                dt = times[(c0 + k - 1) % len(times)]
                t, s = t + dt, max(0.0, s - thr / 5 * dt)
            m = chain[(c0 + k) % len(chain)] * (back if k == 0 else 1.0) * (2.0 if t < until else 1.0)
            roll = rng.uniform(lo, hi)
            h += hit_damage(dmg, mods, roll, m)
            if thr > 0:
                s += hit_damage({x: v for x, v in dmg.items() if x in stag_types}, mods, roll, m) * a.get("m_staggerMultiplier", 1.0)
                if s >= thr:
                    s = thr
                    if t >= until:
                        until = t + CAL["stagger_s"]
            k += 1
        total += k
    return total / n


def combat(tool, mob, level, quality, max_stam):
    it, cr = ITEMS[tool], CREATURES[mob]
    sf = level / 100
    a = it["m_attack"]
    times = combo(it) or [math.nan]
    hits = kill_sim(it, cr, level, quality, times)
    cycle = sum(times) / len(times)
    cost = a["m_attackStamina"] * (1 - 0.33 * sf)
    rate, _ = sustained(cycle, cost, max_stam)
    ttk = hits / CAL["melee_hit"] / rate
    return {"tool": tool, "mob": mob, "hp": cr["m_health"], "level": level, "hits/kill": round(hits, 2),
            "s/swing": round(cycle, 3), "TTK s": round(ttk, 1), "kills/hr engaged": round(3600 / (ttk + CAL["engage_s"]), 1),
            "weapon xp/hr": round(3600 / (ttk + CAL["engage_s"]) * hits * 1.5 * STEPS.get(it["m_skillType"], 1) * GAIN_GLOBAL, 1)}


def supply():
    """Spawn ceilings, kills/hr if every spawn dies at once (Meadows/Black Forest, 0 stars)."""
    rows = []
    for name, sa in SPAWN["SpawnArea"].items():
        if "Greydwarf" in name or "Skeleton" in name or name.startswith("Spawner_"):
            iv = sa.get("m_spawnIntervalSec") or 0
            if iv:
                rows.append((name, "SpawnArea", round(3600 / iv, 1), f"interval {iv}s, maxNear {sa.get('m_maxNear')}"))
    for sp in SPAWN["SpawnSystemList"].get("_SpawnList_base", {}).get("m_spawners", []):
        if sp.get("m_enabled") and sp.get("m_biome", 0) & 9 and sp.get("m_spawnInterval"):
            g = (sp["m_groupSizeMin"] + sp["m_groupSizeMax"]) / 2
            per_hr = 3600 / sp["m_spawnInterval"] * sp["m_spawnChance"] / 100 * g
            when = "night" if not sp.get("m_spawnAtDay") else "day" if not sp.get("m_spawnAtNight") else "any"
            rows.append((sp["m_name"], f"world biome {sp['m_biome']} {when}", round(per_hr, 1),
                         f"max {sp['m_maxSpawned']}, key {sp.get('m_requiredGlobalKey') or '-'}"))
    return rows


def world_counts(folder):
    import importlib.util
    spec = importlib.util.spec_from_file_location("cw", ROOT / "scripts" / "count-world.py")
    cw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cw)
    names = {cw.stable_hash(n): n for n in set(json.load(open(cw.INDEX))["names"].values())}
    zones = {}
    for f in Path(folder).glob("*.chunk"):
        r = cw.Reader(f.read_bytes())
        if r.take("<h") != 41:
            continue
        for _ in range(r.take("<i")):
            h, (x, z) = cw.read_zdo(r)
            zones.setdefault(names.get(h, h), {}).setdefault((int(x // 64), int(z // 64)), 0)
            zones[names.get(h, h)][(int(x // 64), int(z // 64))] += 1
    return {k: (sum(v.values()), len(v)) for k, v in zones.items()}


def table(rows):
    rows = [r for r in rows if r]
    keys = list(dict.fromkeys(k for r in rows for k in r))
    w = {k: max(len(k), *(len(str(r.get(k, ""))) for r in rows)) for k in keys}
    print("  ".join(k.ljust(w[k]) for k in keys))
    for r in rows:
        print("  ".join(str(r.get(k, "")).ljust(w[k]) for k in keys))
    print()


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    if "--backstab" in sys.argv:
        CAL["backstab"] = float(arg("--backstab", 0))
    if "--chain-carry" in sys.argv:
        CAL["chain_carry"] = float(arg("--chain-carry", 1))
    mode = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "summary"
    levels = [int(x) for x in arg("--levels", "0,25,50,100").split(",")]
    q, stam = int(arg("--quality", 1)), float(arg("--stamina", 75 + 20 + 15 + 10))  # base + 3 early foods
    world = world_counts(arg("--world", "")) if "--world" in sys.argv else None
    out = []
    if mode in ("mining", "summary"):
        out.append(("mining", [mining(arg("--tool", "PickaxeAntler"), arg("--node", "rock4_copper_frac"), L, q, stam, world,
                                         int(arg("--weapon-level", 0)) if "--weapon-level" in sys.argv else None) for L in levels]))
    if mode in ("trees", "summary"):
        for t in ([arg("--tree", None)] if "--tree" in sys.argv else ["Beech1", "FirTree", "Pinetree_01"]):
            out.append((f"trees {t}", [trees(arg("--tool", "AxeFlint"), t, L, q, stam, world, "--no-logs" not in sys.argv,
                                                     int(arg("--weapon-level", 0))) for L in levels]))
    if mode in ("combat", "summary"):
        tools = [arg("--tool", None)] if "--tool" in sys.argv else ["Club", "AxeFlint", "KnifeFlint", "SpearFlint"]
        mobs = [arg("--mob", None)] if "--mob" in sys.argv else ["Greydwarf", "Skeleton", "Boar", "Neck"]
        out.append(("combat (engaged)", [combat(t, m, levels[0], q, stam) for t in tools for m in mobs]))
    if mode == "objects":
        out.append(("loot\\objects.csv targets" + (" (written)" if "--write" in sys.argv else ""),
                    objects(q, stam, "--write" in sys.argv)))
    if mode == "swings":
        rows = []
        for k, it in sorted(ITEMS.items()):
            a = it.get("m_attack") or {}
            if a.get("m_attackAnimation") and not k.startswith(("OSRS_", "Mock")):
                c = combo(it, hit=True)
                if c:
                    rows.append({"item": k, "anim": a["m_attackAnimation"], "combo s": [round(x, 3) for x in c],
                                 "mean s/hit": round(sum(c) / len(c), 3), "stamina": a.get("m_attackStamina")})
        out.append(("swings (hit connects)", rows))
    if mode in ("supply", "summary"):
        out.append(("spawn supply", [{"source": a, "kind": b, "spawns/hr": c, "note": d} for a, b, c, d in supply()]))
    if "--json" in sys.argv:
        print(json.dumps(dict(out), indent=1))
        return
    print(f"stamina {stam:g}, quality {q}; CAL {CAL}\n")
    for title, rows in out:
        print(f"== {title}")
        table(rows)


if __name__ == "__main__":
    main()
