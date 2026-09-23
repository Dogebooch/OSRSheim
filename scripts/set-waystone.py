#!/usr/bin/env python3
r"""Fill one waystone coordinate into the KG teleporter cfg. Never hand-edit those lines.

    python scripts\set-waystone.py <node> "<pos output>"   write one node
    python scripts\set-waystone.py --show                  list every node and its state

<node> is one of: kaupang meadows blackforest swamp mountain plains mistlands ashlands deepnorth
<pos output> is whatever the in-game console prints for `pos`; any three numbers are taken, so
all of these work:

    python scripts\set-waystone.py mountain "pos:(1043.2, 187.61, -2290.9)"
    python scripts\set-waystone.py mountain "1043.2 187.61 -2290.9"

KG parses x/y/z with int.Parse, so decimals are a load error for that line and the whole file
stops at it. This rounds them. Placement rules for each node are in the cfg header.
Writes config\Marketplace\Configs\Teleporters\osrsheim_teleports.cfg (the repo copy, which is the
source of truth); run scripts\sync-configs.ps1 -Push afterwards to move it to the profile.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / 'config/Marketplace/Configs/Teleporters/osrsheim_teleports.cfg'

# node key -> the destination name as it appears on the map pin
NODES = {
    'kaupang': 'Kaupang',
    'meadows': 'Meadows stone',
    'blackforest': 'Black Forest stone',
    'swamp': 'Swamp stone',
    'mountain': 'Mountain stone',
    'plains': 'Plains stone',
    'mistlands': 'Mistlands stone',
    'ashlands': 'Ashlands stone',
    'deepnorth': 'Deep North stone',
}
NUM = re.compile(r'-?\d+(?:\.\d+)?')


def fail(msg):
    print('ERROR', msg)
    sys.exit(1)


def lines():
    return CFG.read_text(encoding='utf-8').splitlines()


def show():
    for key, name in NODES.items():
        hit = [l for l in lines() if l.lstrip('# ').startswith(name + ',')]
        if not hit:
            print(f'  {key:<12} MISSING from the cfg')
        elif hit[0].lstrip().startswith('#'):
            print(f'  {key:<12} not placed yet')
        else:
            print(f'  {key:<12} {hit[0].strip()}')


def main():
    if not CFG.exists():
        fail(f'{CFG} not found')
    if len(sys.argv) == 2 and sys.argv[1] in ('--show', '-s'):
        show()
        return
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)

    key = sys.argv[1].strip().lower()
    if key not in NODES:
        fail(f"unknown node '{key}'; expected one of {' '.join(NODES)}")

    nums = NUM.findall(sys.argv[2])
    if len(nums) != 3:
        fail(f'need exactly three numbers in the pos text, found {len(nums)}: {nums}')
    x, y, z = (int(round(float(n))) for n in nums)
    if x == 0 and z == 0:
        fail('x and z are both 0 — that is the placeholder, not a real position')

    out = render(key, x, y, z)
    CFG.write_text(out, encoding='utf-8', newline='\n')
    tiers = [l for l in out.splitlines() if l.startswith('[oath_network_')]
    print(f'ok    {NODES[key]} -> {x}, {y}, {z}')
    print(f'      carried by every tier from its own upward; profiles: {len(tiers)}')
    print('      next: python scripts\\validate-configs.py, then scripts\\sync-configs.ps1 -Push')


def render(key, x, y, z, text=None):
    """The cfg text with node `key` set to x, y, z (every tier line that carries it)."""
    name = NODES[key]
    out, hits = [], 0
    for line in (text if text is not None else CFG.read_text(encoding='utf-8')).splitlines():
        if line.lstrip('# ').startswith(name + ','):
            indent = line[:len(line) - len(line.lstrip())]
            out.append(f'{indent}{name}, {x}, {y}, {z}')
            hits += 1
        else:
            out.append(line)
    if hits == 0:
        fail(f"no line for '{name}' in {CFG.name}; did the destination get renamed?")
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    main()
