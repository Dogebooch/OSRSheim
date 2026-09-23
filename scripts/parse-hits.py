#!/usr/bin/env python3
r"""In-game checks (#67) measured from the client LogOutput.log. Console first: `test`, then `test damage`.

    python scripts\parse-hits.py mark            note the log's current line (start of a check)
    python scripts\parse-hits.py [--from N] [--since HH:MM:SS] [--until HH:MM:SS] [--log path] [--json]
      default --from: the last mark

Log lines used (decompiled 1.0.15; ZLog timestamps are whole seconds):
  "<who> initiating an attack with weapon <w>"      one per player melee swing, at the hit frame   Attack
  "<who> hit <object> for Hit: PlayerHit, Chop: d"  per object hit, damage before its resistances   Attack
  "<who> hit N objects"                             objects touched by the swing (>1: roll / 0.75 N) Attack
  "hit mine rock <area>"                            per MineRock5 area damaged, incl. collapses       MineRock5
  "Damage: Character <m_name> took d damage"        creature damage after resistances                 Character
  "Playerstat increment <stat>"                     no `test` needed: Tree (felled), Logs (pieces), TreeChops,
                                                    LogChops, MineHits, Mines (areas the player broke; not collapses)
Trees: a tree starts at a trunk hit once the last trunk is down; cycle = start to next start (idle = cycle -
swings x 1.28 s: fall, walk, stamina). Mining: an area is broken by damage when its logged damage reaches its
HP; the rest collapsed. Combat rows: runs of hits on one creature name with gaps < 5 s; the species table
credits each EnemyKills stat to the creature hit last (exact when targets alternate).
Per-tree rows split badly in real play (falling trees fell trees, stumps get hit); the stat summary is the count.
"""
import importlib.util
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = Path(os.environ.get("APPDATA", "")) / "com.kesomannen.gale/valheim/profiles/OSRSheim/BepInEx/LogOutput.log"
MARK = ROOT / ".cache" / "parse-hits.mark"
SWING_S = 1.28  # AxeStone tree swing (rate-model swings)
KILL_GAP = 5.0

spec = importlib.util.spec_from_file_location("rate_model", ROOT / "scripts" / "rate-model.py")
RM = importlib.util.module_from_spec(spec)
_argv, sys.argv = sys.argv, sys.argv[:1]
spec.loader.exec_module(RM)
sys.argv = _argv

TS = re.compile(r"\] (\d\d/\d\d/\d{4} \d\d:\d\d:\d\d): (.*)$")
INIT = re.compile(r"^(.+?) initiating an attack with weapon (.*)$")
NHIT = re.compile(r"^(.+?) hit (\d+) objects$")
HIT = re.compile(r"^(.+?) hit (.+?) for Hit: (\w+), (.*)$")
MINE = re.compile(r"^hit mine rock (\d+)$")
STAT = re.compile(r"^Playerstat increment (\w+) by ([-\d.E]+)")
SKIP_STATS = ("TimeOutOfBase", "TimeInBase", "DistanceTraveled", "DistanceWalk", "DistanceRun", "DistanceAir", "DistanceSail")
CDMG = re.compile(r"^Damage: Character (\S+) took ([-\d.E]+) damage from Hit: (\w+)")
DMG = re.compile(r"(Blunt|Slash|Pierce|Chop|Pickaxe|Fire|Frost|Lightning|Poison|Spirit): ([-\d.E]+)")


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def obj_name(s):
    return re.sub(r"\(Clone\).*$|\s*\(UnityEngine\.GameObject\)$", "", s).strip()


def effective(dmg, mods):
    return sum(v * RM.MOD.get((mods or {}).get(k, 0), 1.0) for k, v in dmg.items())


NODE = {k.lower(): (kind, k) for kind in ("Destructible", "MineRock", "MineRock5", "TreeLog", "TreeBase") for k in RM.NODES[kind]}


def node_info(name):
    """(kind, prefab, hp, damage modifiers) of a logged object name; kind None if not a node."""
    kind, key = NODE.get(name.lower(), (None, name))
    n = RM.NODES[kind][key] if kind else {}
    return kind, key, n.get("m_health", 0), n.get("m_damageModifiers") or n.get("m_damages") or {}


def read_swings(path, start, since, until):
    """Player swings in order: {t, weapon, n, hits: [(object, damage dict)], mine: [area], cdmg: [(name, d)]};
    Playerstat totals."""
    swings, cur, stats, kills, last_mob = [], None, {}, [], None
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            if i < start:
                continue
            m = TS.search(line)
            if not m:
                continue
            t = datetime.strptime(m.group(1), "%m/%d/%Y %H:%M:%S")
            hms = t.strftime("%H:%M:%S")
            if (since and hms < since) or (until and hms > until):
                continue
            msg = m.group(2).strip()
            if (x := STAT.match(msg)):
                if x.group(1) not in SKIP_STATS:
                    stats[x.group(1)] = stats.get(x.group(1), 0) + float(x.group(2))
                if x.group(1) == "EnemyKills" and last_mob:
                    kills.append((t, last_mob))
            elif (x := INIT.match(msg)):
                cur = None
                if x.group(1).startswith("Player"):
                    cur = {"t": t, "weapon": x.group(2), "n": 0, "hits": [], "mine": [], "cdmg": []}
                    swings.append(cur)
            elif cur is None:
                continue
            elif (x := NHIT.match(msg)):
                if x.group(1).startswith("Player"):
                    cur["n"] = int(x.group(2))
            elif (x := HIT.match(msg)):
                if x.group(1).startswith("Player"):
                    d = {"m_" + k.lower(): float(v) for k, v in DMG.findall(x.group(4).split(", ")[0])}
                    cur["hits"].append((obj_name(x.group(2)), d))
            elif (x := MINE.match(msg)):
                cur["mine"].append(int(x.group(1)))
            elif (x := CDMG.match(msg)):
                if x.group(3) == "PlayerHit":
                    cur["cdmg"].append((x.group(1), float(x.group(2))))
                    last_mob = x.group(1)
    return swings, stats, kills


def trees(swings):
    out, tree = [], None
    for k, s in enumerate(swings):
        hits = [(o, d) for o, d in s["hits"] if node_info(o)[0] in ("TreeBase", "TreeLog")]
        for o, d in hits:
            kind, _, hp, mods = node_info(o)
            if kind == "TreeBase" and (tree is None or tree["trunk_dmg"] >= tree["trunk_hp"] or tree["trunk"] != o):
                tree = {"trunk": o, "trunk_hp": hp, "trunk_dmg": 0.0, "start": s["t"], "k0": k, "hits": 0,
                        "split": 0, "pieces": {}, "done": 0, "last": s["t"]}
                out.append(tree)
            if tree is None:
                continue
            e = effective(d, mods)
            if kind == "TreeBase":
                tree["trunk_dmg"] += e
            else:
                acc = tree["pieces"].get(o, 0.0) + e
                if acc >= hp:
                    tree["done"], acc = tree["done"] + 1, 0.0
                tree["pieces"][o] = acc
        if hits and tree is not None:
            tree["hits"] += 1
            tree["split"] += s["n"] > 1
            tree["last"] = s["t"]
    rows = []
    for j, tr in enumerate(out):
        nxt = out[j + 1]["start"] if j + 1 < len(out) else None
        cycle = (nxt - tr["start"]).total_seconds() if nxt else None
        rows.append({"tree": tr["trunk"], "start": tr["start"].strftime("%H:%M:%S"), "hits": tr["hits"],
                     "split swings": tr["split"], "pieces down": tr["done"],
                     "chop s": round((tr["last"] - tr["start"]).total_seconds() + SWING_S, 1),
                     "cycle s": cycle, "idle s": round(cycle - tr["hits"] * SWING_S, 1) if cycle else None})
    return rows


def mining(swings):
    nodes, cur = [], None
    for s in swings:
        rock = next((o for o, _ in s["hits"] if node_info(o)[0] == "MineRock5"), None)
        if not rock:
            continue
        _, key, hp, mods = node_info(rock)
        total = RM.NODES["MineRock5"][key].get("areas", 0)
        if cur is None or cur["node"] != rock or len(cur["areas"]) >= total:
            cur = {"node": rock, "key": key, "hp": hp, "areas": {}, "broken": set(), "swings": 0, "start": s["t"], "last": s["t"]}
            nodes.append(cur)
        per = [effective(d, mods) for o, d in s["hits"] if o == rock]
        dmg = sum(per) / len(per) if per else 0.0
        cur["swings"] += 1
        cur["last"] = s["t"]
        for a in s["mine"]:
            acc = cur["areas"].get(a, 0.0)
            if a not in cur["broken"] and acc < hp:
                acc += dmg
                if acc >= hp:
                    cur["broken"].add(a)
            cur["areas"][a] = acc
    return [{"node": n["node"], "start": n["start"].strftime("%H:%M:%S"), "swings": n["swings"],
             "areas": len(n["areas"]), "of": RM.NODES["MineRock5"][n["key"]].get("areas"),
             "broken by damage": len(n["broken"]), "collapsed": len(n["areas"]) - len(n["broken"]),
             "s": (n["last"] - n["start"]).total_seconds() + 1} for n in nodes]


def combat(swings):
    kills, cur = [], None
    for s in swings:
        for name, d in s["cdmg"]:
            if cur is None or cur["mob"] != name or (s["t"] - cur["last"]).total_seconds() > KILL_GAP:
                cur = {"mob": name, "start": s["t"], "last": s["t"], "hits": 0, "dmg": 0.0, "swings": set()}
                kills.append(cur)
            cur["hits"] += 1
            cur["dmg"] += d
            cur["last"] = s["t"]
            cur["swings"].add(id(s))
    return [{"mob": k["mob"], "start": k["start"].strftime("%H:%M:%S"), "swings": len(k["swings"]), "hits": k["hits"],
             "damage": round(k["dmg"], 1), "s": (k["last"] - k["start"]).total_seconds()} for k in kills]


def mean(rows, key):
    xs = [r[key] for r in rows if r.get(key) is not None]
    return round(sum(xs) / len(xs), 2) if xs else None


def table(title, rows):
    if not rows:
        return
    keys = list(rows[0])
    w = {k: max(len(k), *(len(str(r[k])) for r in rows)) for k in keys}
    print(f"== {title}")
    print("  ".join(k.ljust(w[k]) for k in keys))
    for r in rows:
        print("  ".join(str(r[k]).ljust(w[k]) for k in keys))
    print()


def main():
    path = Path(arg("--log", LOG))
    if len(sys.argv) > 1 and sys.argv[1] == "mark":
        n = sum(1 for _ in open(path, encoding="utf-8", errors="replace"))
        MARK.parent.mkdir(exist_ok=True)
        MARK.write_text(str(n + 1))
        print(f"mark: line {n + 1} of {path.name}, {datetime.now():%H:%M:%S}")
        return
    start = int(arg("--from", MARK.read_text() if MARK.exists() else 1))
    swings, stats, kill_log = read_swings(path, start, arg("--since"), arg("--until"))
    if not swings:
        print(f"no player swings logged from line {start}: run `test` and `test damage` in the console")
        return
    span = (swings[-1]["t"] - swings[0]["t"]).total_seconds() + SWING_S
    by_n = {}
    for s in swings:
        by_n[s["n"]] = by_n.get(s["n"], 0) + 1
    summary = {"from line": start, "first": swings[0]["t"].strftime("%H:%M:%S"),
               "last": swings[-1]["t"].strftime("%H:%M:%S"), "swings": len(swings), "span s": span,
               "swings by objects hit": dict(sorted(by_n.items())), "stats": stats}
    tr, mi, co = trees(swings), mining(swings), combat(swings)
    species = {}
    for s in swings:
        for name, d in s["cdmg"]:
            r = species.setdefault(name, {"mob": name, "kills": 0, "hits": 0, "damage": 0.0})
            r["hits"] += 1
            r["damage"] += d
    for _, name in kill_log:
        species.setdefault(name, {"mob": name, "kills": 0, "hits": 0, "damage": 0.0})["kills"] += 1
    sp = [{**r, "damage": round(r["damage"]), "hits/kill": round(r["hits"] / r["kills"], 2) if r["kills"] else None,
           "damage/kill": round(r["damage"] / r["kills"]) if r["kills"] else None} for r in species.values()]
    done = [r for r in tr if r["cycle s"]]
    if tr:
        pieces = 1 + RM.CAL["log_halves"]
        eq = (stats.get("Tree", 0) + stats.get("Logs", 0) / pieces) / 2  # trees of work: trunks felled, pieces cleared
        tree_swings = sum(1 for s in swings if any(node_info(o)[0] in ("TreeBase", "TreeLog") for o, _ in s["hits"]))
        summary["trees"] = {"felled": stats.get("Tree"), "pieces": stats.get("Logs"), "tree equivalents": round(eq, 2),
                            "swings/tree": round(len(swings) / eq, 2) if eq else None,
                            "tree-touching swings/tree": round(tree_swings / eq, 2) if eq else None,
                            "split swing share": round(sum(s["n"] > 1 for s in swings) / len(swings), 3),
                            "trees/hr": round(3600 * eq / span, 1) if eq else None}
    if mi:
        areas = sum(r["areas"] for r in mi)
        summary["mining"] = {"nodes": len(mi), "swings": sum(r["swings"] for r in mi), "areas": areas,
                             "segments/hr": round(3600 * areas / span),
                             "hit fraction (Mines stat)": round(stats.get("Mines", 0) / max(1, areas), 3),
                             "hit fraction (damage)": round(sum(r["broken by damage"] for r in mi) / max(1, areas), 3)}
    if co:
        summary["combat"] = {"kills (stat)": len(kill_log), "kills/hr (stat)": round(3600 * len(kill_log) / span, 1),
                             "swings hitting nothing": round(by_n.get(0, 0) / len(swings), 3), "hit runs": len(co), "mean hits": mean(co, "hits"), "mean swings": mean(co, "swings"),
                             "mean s/run": mean(co, "s")}
    if "--json" in sys.argv:
        print(json.dumps({"summary": summary, "trees": tr, "mining": mi, "combat": co, "species": sp}, indent=1, default=str))
        return
    table("trees", tr)
    table("mining (MineRock5)", mi)
    table("combat hit runs (gap < 5 s)", co)
    table("combat by species (kills from EnemyKills stat)", sp)
    print(json.dumps(summary, indent=1, default=str))


if __name__ == "__main__":
    main()
