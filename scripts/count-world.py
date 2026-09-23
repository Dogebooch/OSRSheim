#!/usr/bin/env python3
r"""Count objects in a Valheim 1.0 world save (chunked format, world version 41). Read-only.

    python scripts\count-world.py <world folder>                     prefab counts, top 60
    python scripts\count-world.py <world folder> --match copper,tin  only prefabs containing these
    python scripts\count-world.py <world folder> --zones             also: zones generated, per-zone mean

<world folder> holds _main.<n>.chunks/.db2 and *.chunk, e.g.
%USERPROFILE%\AppData\LocalLow\IronGate\Valheim\worlds_local\<World>. Copy it first if the game
or a server has it open. Prefab names come from reference\..\.cache\game-data-index.json
(scripts\extract-game-data.py), hashed with Valheim's GetStableHashCode.

Counts only what exists now: generated zones hold every placed node/tree until it is destroyed,
so a fresh fly-over gives realised density; a played area gives what is left.
"""
import collections
import json
import os
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / ".cache" / "game-data-index.json"
ZONE = 64.0


def stable_hash(s):
    """Valheim StringExtensionMethods.GetStableHashCode (int32 wraparound)."""
    def i32(x):
        x &= 0xFFFFFFFF
        return x - 0x100000000 if x & 0x80000000 else x
    h1 = h2 = 5381
    i = 0
    while i < len(s) and s[i] != "\0":
        h1 = i32(((h1 << 5) + h1) ^ ord(s[i]))
        if i == len(s) - 1 or s[i + 1] == "\0":
            break
        h2 = i32(((h2 << 5) + h2) ^ ord(s[i + 1]))
        i += 2
    return i32(h1 + h2 * 1566083941)


class Reader:
    def __init__(self, data):
        self.b, self.p = data, 0

    def take(self, fmt):
        v = struct.unpack_from(fmt, self.b, self.p)
        self.p += struct.calcsize(fmt)
        return v if len(v) > 1 else v[0]

    def num_items(self):
        n = self.take("<B")
        return ((n & 0x7F) << 8) | self.take("<B") if n & 0x80 else n

    def string(self):  # .NET BinaryReader.ReadString: 7-bit length prefix
        n = shift = 0
        while True:
            b = self.take("<B")
            n |= (b & 0x7F) << shift
            shift += 7
            if not b & 0x80:
                break
        s = self.b[self.p:self.p + n]
        self.p += n
        return s


def read_zdo(r):
    """ZDO.Load for version >= ChunkedSave. Returns (prefab hash, x, z)."""
    flags = r.take("<H")
    if flags & 0x2000:
        x, z = r.take("<hh")
        pos = (float(x), float(z))
    else:
        x, _, z = r.take("<fff")
        pos = (x, z)
    prefab = r.take("<i")
    if flags & 0x1000:
        v = r.take("<H")
        if not v & 0x8000:
            r.take("<H")
    if flags & 0xFF:
        if flags & 0x01:
            r.take("<Bi")
        for bit, size in ((0x02, 4), (0x04, 12), (0x08, 16), (0x10, 4), (0x20, 8)):
            if flags & bit:
                for _ in range(r.num_items()):
                    r.take("<i")
                    r.p += size
        if flags & 0x40:
            for _ in range(r.num_items()):
                r.take("<i")
                r.string()
        if flags & 0x80:
            for _ in range(r.num_items()):
                r.take("<i")
                size = r.take("<i")
                r.p += size
    return prefab, pos


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    folder = Path(args[0])
    match = None
    if "--match" in sys.argv:
        match = [m.lower() for m in sys.argv[sys.argv.index("--match") + 1].split(",")]
        args = [a for a in args if a.lower() != ",".join(match)]
    if not INDEX.exists():
        sys.exit("run scripts\\extract-game-data.py first (builds the name index)")
    names = {stable_hash(n): n for n in set(json.load(open(INDEX))["names"].values())}
    counts = collections.Counter()
    zones = collections.defaultdict(collections.Counter)
    total = 0
    for f in sorted(folder.glob("*.chunk")):
        r = Reader(f.read_bytes())
        version, n = r.take("<h"), r.take("<i")
        if version != 41:
            print(f"{f.name}: world version {version}, expected 41; skipped")
            continue
        for _ in range(n):
            h, (x, z) = read_zdo(r)
            name = names.get(h, f"#{h}")
            counts[name] += 1
            zones[(int(x // ZONE), int(z // ZONE))][name] += 1
            total += 1
    rows = [(k, v) for k, v in counts.items() if not match or any(m in k.lower() for m in match)]
    rows.sort(key=lambda kv: -kv[1])
    print(f"{total} objects, {len(zones)} zones with objects")
    for k, v in rows[: None if match else 60]:
        present = sum(1 for c in zones.values() if c.get(k))
        extra = f"  in {present} zones, {v / present:.1f}/zone where present" if "--zones" in sys.argv and present else ""
        print(f"{v:8d}  {k}{extra}")


if __name__ == "__main__":
    main()
