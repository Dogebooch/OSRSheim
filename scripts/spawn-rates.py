r"""Theoretical creature supply per hour from the Spawn That pre-change dumps.

Reads BepInEx\Debug\spawn_that.*_pre_changes.txt and prints Markdown tables.
Model (vanilla SpawnSystem / SpawnArea / CreatureSpawner, one player zone):
  world     rolls/hr = 3600 / SpawnInterval; spawns/hr = rolls x SpawnChance/100
            x mean(GroupSizeMin..GroupSizeMax). Day and night summed separately.
  spawnarea spawns/hr per spawner = 3600 / SpawnInterval, split by SpawnWeight.
  local     RespawnTime 0 = one-shot per placement; else 60 / RespawnTime per hr.
Assumes the player kills spawns as they appear (caps never bind) and stays in
range. Real kills/hr are lower: travel, night gating, and spawn conditions.
Usage: python scripts\spawn-rates.py [debug_dir] [--min-rate N]
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

DEFAULT_DIR = Path.home() / (
    r"AppData\Roaming\com.kesomannen.gale\valheim\profiles\OSRSheim\BepInEx\Debug")
IGNORE = re.compile(r"^(Fish|CinderStorm|projectile_|FireFlies|odin$|Seagal|LavaRock|ElakingLantern|"
                    r"Spawner_|Seal_Pup|SeekerBrood|Hare$|Deer$|Neck$|CinderSky)")


def parse(path):
    """Yield (comment, section_name, {key: value}) for each [section]."""
    comment, pending, name, kv = "", "", None, {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if line.startswith("#"):
            pending = (pending + " " + line.lstrip("# ")).strip()
            continue
        if line.startswith("["):
            if name is not None:
                yield comment, name, kv
            comment, pending, name, kv = pending, "", line.strip("[]"), {}
        elif "=" in line and name is not None:
            k, v = line.split("=", 1)
            kv[k.strip()] = v.strip()
    if name is not None:
        yield comment, name, kv


def num(kv, key, default=0.0):
    try:
        return float(kv.get(key, default))
    except ValueError:
        return default


def world(path):
    out = defaultdict(lambda: {"day": 0.0, "night": 0.0, "biomes": set(), "key": set(), "n": 0})
    for _, _, kv in parse(path):
        pf = kv.get("PrefabName", "")
        if not pf or kv.get("Enabled", "True") != "True" or IGNORE.match(pf):
            continue
        interval = num(kv, "SpawnInterval", 0)
        if interval <= 0:
            continue
        rate = 3600 / interval * num(kv, "SpawnChance", 100) / 100 \
            * (num(kv, "GroupSizeMin", 1) + num(kv, "GroupSizeMax", 1)) / 2
        row = out[pf]
        row["n"] += 1
        if kv.get("SpawnDuringDay", "True") == "True":
            row["day"] += rate
        if kv.get("SpawnDuringNight", "True") == "True":
            row["night"] += rate
        row["biomes"].update(b.strip() for b in kv.get("Biomes", "").split(",")
                             if b.strip() and b.strip() != "Land")
        if kv.get("RequiredGlobalKey"):
            row["key"].add(kv["RequiredGlobalKey"])
    return out


def spawnarea(path):
    parents, children = {}, defaultdict(list)
    for comment, name, kv in parse(path):
        if "PrefabName" in kv:
            if kv.get("Enabled", "True") == "True" and kv["PrefabName"]:
                children[name.rsplit(".", 1)[0]].append(kv)
        else:
            parents[name] = (comment, kv)
    rows = []
    for name, (comment, kv) in parents.items():
        interval = num(kv, "SpawnInterval", 0)
        kids = children.get(name, [])
        if interval <= 0 or not kids:
            continue
        total_w = sum(num(k, "SpawnWeight", 1) for k in kids) or 1
        per_hr = 3600 / interval
        mix = ", ".join(f"{k['PrefabName']} {per_hr * num(k, 'SpawnWeight', 1) / total_w:.0f}"
                        for k in kids)
        m = re.search(r"Appears in Biomes:\s*([^#]*?)\s*Appears in Locations", comment)
        biomes = ", ".join(b.strip() for b in (m.group(1) if m else "").split(",")
                           if b.strip() and b.strip() != "Land")
        rows.append((name, interval, num(kv, "ConditionMaxCloseCreatures"),
                     num(kv, "ConditionMaxCreatures"), num(kv, "ConditionPlayerWithinDistance"),
                     biomes, mix))
    return rows


def local(path, label):
    out = defaultdict(lambda: {"oneshot": defaultdict(int), "respawn": []})
    for comment, _, kv in parse(path):
        pf = kv.get("PrefabName", "")
        if not pf or kv.get("Enabled", "True") != "True" or IGNORE.match(pf):
            continue
        m = re.search(r"(?:Location|Room Theme):\s*([^,]+)", comment)
        where = m.group(1).strip() if m else "?"
        rt = num(kv, "RespawnTime", 0)
        if rt > 0:
            out[pf]["respawn"].append((where, rt))
        else:
            out[pf]["oneshot"][where] += 1
    return out


def main():
    argv = sys.argv[1:]
    min_rate = 0.0
    if "--min-rate" in argv:
        i = argv.index("--min-rate")
        min_rate = float(argv[i + 1])
        del argv[i:i + 2]
    debug = Path(argv[0]) if argv else DEFAULT_DIR

    print("## World spawners (roaming), spawns/hr per player zone\n")
    print("| Prefab | Day | Night | Entries | Biomes | Key |")
    print("|---|---|---|---|---|---|")
    for pf, r in sorted(world(debug / "spawn_that.world_spawners_pre_changes.txt").items(),
                        key=lambda x: -(x[1]["day"] + x[1]["night"])):
        if max(r["day"], r["night"]) < min_rate:
            continue
        print(f"| {pf} | {r['day']:.0f} | {r['night']:.0f} | {r['n']} | "
              f"{', '.join(sorted(r['biomes']))} | {', '.join(sorted(r['key']))} |")

    print("\n## SpawnArea spawners (nests, piles), spawns/hr per spawner while camped\n")
    print("| Spawner | Interval s | Max near | Max total | Trigger m | Biomes | Prefab spawns/hr |")
    print("|---|---|---|---|---|---|---|")
    for row in sorted(spawnarea(debug / "spawn_that.spawnarea_spawners_pre_changes.txt"),
                      key=lambda r: r[1]):
        print("| " + " | ".join(f"{v:.0f}" if isinstance(v, float) else str(v) for v in row) + " |")

    for fname, label in (("spawn_that.local_spawners_pre_changes.txt", "locations"),
                         ("spawn_that.local_spawners_dungeons_pre_changes.txt", "dungeon rooms")):
        print(f"\n## Local spawners ({label}): one-shot placements per prefab\n")
        print("| Prefab | Placements | Where (count) | Respawning |")
        print("|---|---|---|---|")
        data = local(debug / fname, label)
        for pf, r in sorted(data.items(), key=lambda x: -sum(x[1]["oneshot"].values())):
            where = ", ".join(f"{k} {v}" for k, v in
                              sorted(r["oneshot"].items(), key=lambda x: -x[1])[:6])
            resp = ", ".join(f"{w} {60 / rt:.2f}/hr" for w, rt in r["respawn"][:3])
            if len(r["respawn"]) > 3:
                resp += f" (+{len(r['respawn']) - 3})"
            print(f"| {pf} | {sum(r['oneshot'].values())} | {where} | {resp} |")


if __name__ == "__main__":
    main()
