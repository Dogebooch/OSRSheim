r"""Frame-time summary of PresentMon captures (valheim.exe). Test-only (#66).

    python scripts\perf-frames.py              every CSV in perf\captures\, oldest first
    python scripts\perf-frames.py a.csv ...    named files

Captures come from scripts\perf-capture.bat. Per capture: frames, avg FPS,
p50/p99/p99.9 frame time, 1% low FPS, spikes (> 2x median and > 20 ms), and
how many spikes sit ~2 s apart (the Minimap.Explore tick, RESEARCH 16).
"""
import csv, glob, os, statistics, sys

CAPTURES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'perf', 'captures')
FT_COLS = ('FrameTime', 'MsBetweenPresents', 'MsBetweenAppStart')
T_COLS = ('TimeInMs', 'CPUStartTime', 'TimeInSeconds')


def pick(header, names):
    for n in names:
        if n in header:
            return n
    return None


def load(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return [], []
    h = rows[0].keys()
    fc, tc = pick(h, FT_COLS), pick(h, T_COLS)
    if not fc:
        sys.exit(f'{path}: no frame-time column in {list(h)}')
    ft, t, acc = [], [], 0.0
    for r in rows:
        if r.get('Application', 'valheim.exe').lower() != 'valheim.exe':
            continue
        try:
            v = float(r[fc])
        except (TypeError, ValueError):
            continue
        acc += v / 1000
        ft.append(v)
        try:
            t.append(float(r[tc]) if tc else acc)
        except (TypeError, ValueError):
            t.append(acc)
    # Time column unit varies by PresentMon version: rescale ms to s by span.
    if len(t) > 1 and (t[-1] - t[0]) > 10 * acc:
        t = [x / 1000 for x in t]
    return ft, t


def pct(s, p):
    return s[min(len(s) - 1, int(p / 100 * len(s)))]


def report(path):
    ft, t = load(path)
    if len(ft) < 50:
        print(f'{os.path.basename(path)}: {len(ft)} frames, too short')
        return
    s = sorted(ft)
    med = statistics.median(ft)
    dur = sum(ft) / 1000
    low1 = 1000 / statistics.mean(s[-max(1, len(s) // 100):])
    spikes = [t[i] for i, v in enumerate(ft) if v > max(2 * med, 20)]
    gaps = [b - a for a, b in zip(spikes, spikes[1:]) if b - a > 0.5]
    tick = sum(1 for g in gaps if 1.8 <= g <= 2.2 or 3.8 <= g <= 4.2)
    print(f'{os.path.basename(path)}  {dur:.0f} s  {len(ft)} frames  avg {len(ft) / dur:.0f} fps  1% low {low1:.0f} fps')
    print(f'  frame ms  p50 {med:.1f}  p99 {pct(s, 99):.1f}  p99.9 {pct(s, 99.9):.1f}  max {s[-1]:.1f}')
    print(f'  spikes {len(spikes)} ({len(spikes) / dur * 60:.0f}/min)  worst: '
          + ', '.join(f'{v:.0f}' for v in s[-5:][::-1]) + ' ms')
    if gaps:
        print(f'  spike spacing: median {statistics.median(gaps):.2f} s, {tick}/{len(gaps)} on a 2 s / 4 s beat')


args = sys.argv[1:] or [os.path.join(CAPTURES, '*.csv')]
files = [f for a in args for f in sorted(glob.glob(a), key=os.path.getmtime)]  # cmd passes wildcards unexpanded
if not files:
    sys.exit('no captures yet')
for f in files:
    report(f)
