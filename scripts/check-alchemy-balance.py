#!/usr/bin/env python3
r"""OSRSheim Alchemy balance check — run after any edit to the herb-run chain.

    python scripts\check-alchemy-balance.py
    python scripts\check-alchemy-balance.py --stone 2.0

Read-only. Checks the repo's config\ (the source of truth), not the profile.

Invariants (ERROR):
  A1 every potion above the entry tier costs Potion_Meadbase (the pipeline holds)
  A2 no trader sells a finished potion, a Potion_Meadbase or a crop
  A3 the herbwife sells seeds only
  A4 Alchemy gates rise with tier and never exceed the reachable cap
  A5 every WIRSL Alchemy gate names a real PotionPlus prefab, craft AND use blocked
  A6 every gated recipe has a farm leg, so coins can never buy the whole potion
  A7 every Harvest contract targets a Pickable_ prefab and is on a quest profile
  A8 no PotionPlus recipe asks a station level its station can never reach

Then prints the grind budget: crafts, real crop units and garden cycles to each
gate, so a recipe edit that quietly triples the grind shows up as a number.

Curve (vanilla Skills.Skill): level L->L+1 costs (L+1)^1.5 * 0.5 + 0.5 XP.
PotionPlus pays 1 XP per craft at a station named opalchemy* and nothing
else: opcauldron is a plain CraftingStation (no Incinerator in the 4.3.4
bundle). A Potion_Meadbase pays 1 XP only if it is brewed at opalchemy.
A Philosopher's Stone is ADDITIVE on the vanilla multiplier
(SE_Stats.ModifyRaiseSkill does value += factor), so cfg 2.0 means 3x.
"""
import argparse
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CFG = os.path.join(ROOT, "config")
KG = os.path.join(CFG, "Marketplace", "Configs")

CROPS = {"Carrot", "Turnip", "Onion", "Barley", "Flax",
         "Kale", "Oat", "Poteitr", "Vineberry"}
FARM_LEG = CROPS | {"Potion_Meadbase"}
# station -> max level: Odins_Alchemy_Book is the bundle's only StationExtension
# and it extends opalchemy; nothing extends opcauldron (PotionsPlus 4.3.4)
MAX_LEVEL = {"opalchemy": 2, "opcauldron": 1}
ENTRY_TIER = {"Lesser_Healing_Tide_Vial", "Lesser_Spiritual_Healing_Vial",
              "Lesser_Stamina_Vial"}

# cfg section name -> prefab name (DLL literals, PotionsPlus.dll 4.3.4)
PREFAB = {
    "Lesser Healing Tide Vial": "Lesser_Healing_Tide_Vial",
    "Lesser Spiritual Healing Vial": "Lesser_Spiritual_Healing_Vial",
    "Lesser Stamina Vial": "Lesser_Stamina_Vial",
    "Medium Healing Tide Flask": "Medium_Healing_Tide_Flask",
    "Medium Spiritual Healing Flask": "Medium_Spiritual_Healing_Flask",
    "Medium Stamina Flask": "Medium_Stamina_Flask",
    "Grand Healing Tide Potion": "Grand_Healing_Tide_Potion",
    "Grand Spiritual Healing Potion": "Grand_Spiritual_Healing_Potion",
    "Grand Stamina Elixir": "Grand_Stamina_Elixir",
    "Grand Stealth Elixir": "Grand_Stealth_Elixir",
    "Hellbroth of Flames": "Hellbroth_of_Flames",
    "Hellbroth of Eternal Life": "Hellbroth_of_Eternal_Life",
    "Hellbroth of Frost": "Hellbroth_of_Frost",
    "Hellbroth of Thors Fury": "Hellbroth_of_Thors_Fury",
    "Flask of Magelight": "Flask_of_Magelight",
    "Flask of Second Wind": "Flask_of_Second_Wind",
    "Flask of Fortification": "Flask_of_Fortification",
    "Flask of Elements": "Flask_of_Elements",
    "Flask of the Gods": "Flask_of_the_Gods",
    "Odins Weapon Oil": "Odins_Weapon_Oil",
    "Amethyst Philosophers Stone": "PhilosopherStonePurple",
    "Emerald Philosophers Stone": "PhilosopherStoneGreen",
    "Ruby Philosophers Stone": "PhilosopherStoneRed",
    "Sapphire Philosophers Stone": "PhilosopherStoneBlue",
}
# A4 checks monotonicity WITHIN a ladder, not across them: the hellbroth ladder
# (10/15/30/40) deliberately interleaves with the flask ladder, so comparing the
# two would be meaningless. Each entry is (family, rung).
LADDER = {
    "Lesser_Healing_Tide_Vial": ("healing", 0),
    "Lesser_Spiritual_Healing_Vial": ("healing", 0),
    "Lesser_Stamina_Vial": ("healing", 0),
    "Medium_Healing_Tide_Flask": ("healing", 1),
    "Medium_Spiritual_Healing_Flask": ("healing", 1),
    "Medium_Stamina_Flask": ("healing", 1),
    "Grand_Healing_Tide_Potion": ("healing", 2),
    "Grand_Spiritual_Healing_Potion": ("healing", 2),
    "Grand_Stamina_Elixir": ("healing", 2),
    "Grand_Stealth_Elixir": ("healing", 3),
    "Hellbroth_of_Flames": ("hellbroth", 0),
    "Hellbroth_of_Eternal_Life": ("hellbroth", 1),
    "Hellbroth_of_Frost": ("hellbroth", 2),
    "Hellbroth_of_Thors_Fury": ("hellbroth", 3),
    "Odins_Weapon_Oil": ("flask", 0),
    "Flask_of_Magelight": ("flask", 0),
    "Flask_of_Fortification": ("flask", 1),
    "Flask_of_Second_Wind": ("flask", 1),
    "Flask_of_Elements": ("flask", 2),
    "Flask_of_the_Gods": ("flask", 3),
    "PhilosopherStonePurple": ("stone", 0),
    "PhilosopherStoneGreen": ("stone", 0),
    "PhilosopherStoneRed": ("stone", 0),
    "PhilosopherStoneBlue": ("stone", 0),
}
for _p in list(LADDER):
    if _p.startswith("Hellbroth_"):
        LADDER[_p + "_Charge"] = LADDER[_p]


def farm_closure(prefab, recipes, seen=None):
    """Ingredients of a recipe, following crafted ingredients down to raw ones."""
    seen = seen or set()
    if prefab in seen:
        return set()
    seen.add(prefab)
    legs = set()
    for item, _ in recipes.get(prefab, {}).get("costs", []):
        legs.add(item)
        if item in recipes:
            legs |= farm_closure(item, recipes, seen)
    return legs


errors, warns = [], []


def err(m):
    errors.append(m)
    print("ERROR ", m)


def warn(m):
    warns.append(m)
    print("WARN  ", m)


def ok(m):
    print("ok    ", m)


def read(p):
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        return f.read()


# ------------------------------------------------------------------ PotionPlus
def parse_potionsplus():
    """section -> {station, level, costs:[(item, n)]} for every craftable entry."""
    out, section = {}, None
    for line in read(os.path.join(CFG, "com.odinplus.potionsplus.cfg")).splitlines():
        line = line.strip()
        m = re.match(r"^\[(.+)\]$", line)
        if m:
            section = m.group(1)
            out.setdefault(section, {})
            continue
        if section is None or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        m = re.match(r"^(Custom Crafting Station|Crafting Costs|"
                     r"Crafting Station Level)(?: \((\w+)\))?$", key)
        if not m:
            continue
        field, variant = m.group(1), m.group(2) or ""
        slot = out[section].setdefault(variant, {})
        if field == "Custom Crafting Station":
            slot["station"] = val
        elif field == "Crafting Station Level":
            slot["level"] = val
        else:
            costs = []
            for part in filter(None, val.split(",")):
                bits = part.split(":")
                if len(bits) >= 2 and bits[1].isdigit():
                    costs.append((bits[0], int(bits[1])))
            slot["costs"] = costs
    return out


# ----------------------------------------------------------------------- WIRSL
def parse_wirsl():
    """prefab -> (level, blockcraft, blockequip) for Alchemy entries only, skillcapes excluded."""
    text = read(os.path.join(CFG, "WackyMole.ItemRequiresSkillLevel.yml"))
    gates, prefab, skill = {}, None, None
    cur = {}
    for line in text.splitlines():
        m = re.match(r"^- PrefabName:\s*(\S+)", line)
        if m:
            if skill == "Alchemy" and prefab:
                gates[prefab] = cur
            prefab, skill, cur = m.group(1), None, {}
            continue
        m = re.match(r"^\s*-?\s*Skill:\s*(\S+)", line)
        if m:
            skill = m.group(1)
            continue
        m = re.match(r"^\s*(Level|BlockCraft|BlockEquip):\s*(\S+)", line)
        if m:
            cur[m.group(1)] = m.group(2)
    if skill == "Alchemy" and prefab:
        gates[prefab] = cur
    return {p: (int(v.get("Level", 0)),
                v.get("BlockCraft") == "true",
                v.get("BlockEquip") == "true") for p, v in gates.items()
            if not p.startswith("OSRS_Cape")}


# --------------------------------------------------------------------- traders
def parse_traders():
    """profile -> list of (cost_item, cost_n, result_item, result_n)."""
    out, profile = {}, None
    for line in read(os.path.join(KG, "Traders", "osrsheim_traders.cfg")).splitlines():
        line = line.strip()
        m = re.match(r"^\[([^\]=\s]+)", line)
        if m:
            profile = m.group(1)
            out.setdefault(profile, [])
            continue
        if profile is None or line.startswith("#") or not line:
            continue
        bits = [b.strip() for b in line.split(",")]
        if len(bits) >= 4:
            out[profile].append((bits[0], bits[1], bits[2], bits[3]))
    return out


# ---------------------------------------------------------------------- quests
def parse_quests():
    """id -> {type, target, profile_listed}"""
    out, qid, buf = {}, None, []
    for line in read(os.path.join(KG, "Quests",
                                  "osrsheim_quests_slayer.cfg")).splitlines():
        s = line.strip()
        m = re.match(r"^\[([^\]=\s]+)", s)
        if m:
            if qid:
                out[qid] = buf
            qid, buf = m.group(1), []
            continue
        if qid and s and not s.startswith("#"):
            buf.append(s)
    if qid:
        out[qid] = buf
    profiles = read(os.path.join(KG, "QuestProfiles",
                                 "osrsheim_quest_profiles.cfg"))
    listed = set(re.findall(r"[A-Za-z_0-9]+", profiles))
    return {q: {"type": b[0] if b else "",
                "target": b[3] if len(b) > 3 else "",
                "listed": q in listed} for q, b in out.items()}


# ------------------------------------------------------------------ XP budget
def cum_xp(level):
    return sum(n ** 1.5 * 0.5 + 0.5 for n in range(1, level + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stone", type=float, default=None,
                    help="Philosophers Stone cfg factor; default reads the cfg")
    ap.add_argument("--cap", type=int, default=50,
                    help="highest Alchemy level a gate may demand")
    ap.add_argument("--garden", type=int, default=60,
                    help="plants per garden cycle, for the cycle estimate")
    args = ap.parse_args()

    pp = parse_potionsplus()
    gates = parse_wirsl()
    traders = parse_traders()
    quests = parse_quests()

    recipes = {}
    for section, variants in pp.items():
        if section not in PREFAB:
            continue
        slot = variants.get("", {})
        if "costs" not in slot:
            continue
        recipes[PREFAB[section]] = slot

    base = pp.get("Potion Base", {}).get("Table", {})

    # -- A1 ------------------------------------------------------------------
    # transitive: a stone costs 5 flasks, and each flask costs a base
    bad = [p for p in recipes
           if p not in ENTRY_TIER
           and "Potion_Meadbase" not in farm_closure(p, recipes)]
    if bad:
        err("A1 no Potion_Meadbase anywhere in the chain of: "
            + ", ".join(sorted(bad)))
    else:
        ok("A1 every potion above the entry tier reaches Potion_Meadbase")

    # -- A2 ------------------------------------------------------------------
    sold = set()
    for profile, lines in traders.items():
        for cost_item, _, result_item, _ in lines:
            if cost_item == "Coins":
                sold.add((profile, result_item))
    banned = {p for p in recipes} | {"Potion_Meadbase"} | CROPS
    hits = sorted("%s sells %s" % (pr, it) for pr, it in sold if it in banned)
    if hits:
        err("A2 " + "; ".join(hits))
    else:
        ok("A2 no trader sells a potion, a base or a crop (%d shop lines)"
           % sum(len(v) for v in traders.values()))

    # -- A3 ------------------------------------------------------------------
    hw = traders.get("herbwife", [])
    if not hw:
        err("A3 no [herbwife] trader profile")
    else:
        nonseed = [r for _, _, r, _ in hw if not r.endswith("Seeds")]
        if nonseed:
            err("A3 herbwife sells non-seed items: " + ", ".join(nonseed))
        else:
            ok("A3 herbwife sells %d seed lines and nothing else" % len(hw))

    # -- A4 ------------------------------------------------------------------
    families = {}
    unplaced = []
    for prefab, (lvl, _, _) in gates.items():
        if prefab not in LADDER:
            unplaced.append(prefab)
            continue
        fam, rung = LADDER[prefab]
        families.setdefault(fam, []).append((rung, lvl, prefab))
    slips = []
    for fam, rows in sorted(families.items()):
        rows.sort()
        highest = -1
        for rung, lvl, prefab in rows:
            if lvl < highest:
                slips.append("%s gates at %d under a lower rung of the %s ladder"
                             % (prefab, lvl, fam))
            highest = max(highest, lvl)
    over = ["%s @%d" % (p, l) for p, (l, _, _) in sorted(gates.items())
            if l > args.cap]
    if unplaced:
        warn("A4 gate not on a declared ladder: " + ", ".join(sorted(unplaced)))
    if slips:
        err("A4 " + "; ".join(slips))
    if over:
        err("A4 gates above the reachable cap %d: %s" % (args.cap, ", ".join(over)))
    if not slips and not over:
        ok("A4 %d Alchemy gates rise within each ladder, top gate %d <= cap %d"
           % (len(gates), max(l for l, _, _ in gates.values()), args.cap))

    # -- A5 ------------------------------------------------------------------
    known = set(PREFAB.values()) | {p + "_Charge" for p in PREFAB.values()
                                    if p.startswith("Hellbroth_")}
    unknown = sorted(p for p in gates if p not in known)
    loose = sorted("%s (craft=%s use=%s)" % (p, c, e)
                   for p, (_, c, e) in gates.items() if not (c and e))
    if unknown:
        err("A5 WIRSL Alchemy gate on an unknown prefab: " + ", ".join(unknown))
    if loose:
        err("A5 gate does not block both craft and use: " + "; ".join(loose))
    if not unknown and not loose:
        ok("A5 every Alchemy gate names a real prefab and blocks craft + use")

    # -- A6 ------------------------------------------------------------------
    shop_items = {it for _, it in sold}
    leaky = []
    for prefab, (lvl, _, _) in sorted(gates.items()):
        if prefab not in recipes:
            continue
        legs = farm_closure(prefab, recipes)
        if not (legs & FARM_LEG):
            leaky.append("%s @%d has no farm leg" % (prefab, lvl))
        elif legs <= shop_items:
            leaky.append("%s @%d is fully purchasable" % (prefab, lvl))
    if leaky:
        err("A6 " + "; ".join(leaky))
    else:
        ok("A6 every gated recipe keeps a farm leg coins cannot buy")

    # -- A7 ------------------------------------------------------------------
    harvest = {q: v for q, v in quests.items() if v["type"] == "Harvest"}
    if not harvest:
        warn("A7 no Harvest contracts found")
    else:
        bad = []
        for q, v in sorted(harvest.items()):
            target = v["target"].split(",")[0].strip()
            if not target.startswith("Pickable_"):
                bad.append("%s targets %s" % (q, target or "nothing"))
            if not v["listed"]:
                bad.append("%s is not on a quest profile" % q)
        if bad:
            err("A7 " + "; ".join(bad))
        else:
            ok("A7 %d Harvest contracts target Pickable_ prefabs and are listed"
               % len(harvest))

    # -- A8 ------------------------------------------------------------------
    bad = []
    for section, variants in pp.items():
        for variant, slot in variants.items():
            top = MAX_LEVEL.get(slot.get("station"))
            lvl = slot.get("level", "1")
            if top and lvl.isdigit() and int(lvl) > top:
                bad.append("%s%s needs %s level %s (max %d)"
                           % (section, " (%s)" % variant if variant else "",
                              slot["station"], lvl, top))
    if bad:
        err("A8 " + "; ".join(bad))
    else:
        ok("A8 every PotionPlus recipe asks a station level it can reach")

    # -- budget --------------------------------------------------------------
    stone = args.stone
    if stone is None:
        m = re.search(r"Philosophers Stone XP Gain Factor\s*=\s*([\d.]+)",
                      read(os.path.join(CFG, "com.odinplus.potionsplus.cfg")))
        stone = float(m.group(1)) if m else 1.25
    mult = 1.0 + stone

    base_costs = base.get("costs", [])
    base_units = sum(n for i, n in base_costs if i in CROPS)
    print("\n  Potion Base (%s): %s  -> %d crop units per base"
          % (base.get("station", "?"),
             ", ".join("%s:%d" % c for c in base_costs) or "none", base_units))
    print("  Philosophers Stone cfg %.2f -> %.2fx Alchemy XP (additive)"
          % (stone, mult))
    base_xp = 1 if base.get("station", "").startswith("opalchemy") else 0
    print("  XP = 1 per opalchemy craft; a base pays %d\n" % base_xp)

    # average crop units in a finished potion, gated tiers only
    gated = [(p, l) for p, (l, _, _) in gates.items() if p in recipes]
    if gated:
        avg = sum(sum(n for i, n in recipes[p]["costs"] if i in CROPS)
                  for p, _ in gated) / float(len(gated))
    else:
        avg = 0.0
    print("  avg crop units in a gated potion: %.1f (plus %d for its base)"
          % (avg, base_units))
    # the stone is itself gated: XP below its level is earned without it
    stone_lvl = min([l for p, (l, _, _) in gates.items() if p.startswith("PhilosopherStone")] or [0])
    print("  a Philosophers Stone needs Alchemy %d; XP below that has no stone" % stone_lvl)

    print("\n  %-7s %9s %9s %9s %12s %9s"
          % ("gate", "XP", "crafts", "w/ stone", "crop units", "cycles"))
    for lvl in sorted({l for _, l in gated} | {args.cap, 100}):
        xp = cum_xp(lvl)
        # each potion eats one base; a base brewed at opalchemy pays XP too
        crafts = xp
        pre = cum_xp(min(lvl, stone_lvl))
        with_stone = pre + (xp - pre) / mult
        units = with_stone / (1 + base_xp) * (avg + base_units)
        cycles = units / float(args.garden)
        print("  %-7d %9.0f %9.0f %9.0f %12.0f %9.1f"
              % (lvl, xp, crafts, with_stone, units, cycles))
    print("\n  crafts = opalchemy clicks with no stone."
          "\n  crop units / cycles use the stone from its gate on, %d plants per cycle"
          " (a cycle is 67-83 min at Farming 0, 22-28 at 100)." % args.garden)

    print("\n%d error(s), %d warning(s)" % (len(errors), len(warns)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
