#!/usr/bin/env python3
"""
Generate a realistic but FAKE history.json for previewing the dashboard locally.

This produces data shaped exactly like the real pipeline's history.json, seeded
so it deterministically exercises every dashboard feature:

- ~60 days of daily clones/views with a recent uptick (so momentum shows ▲)
- a per-day release-download series with a small "unclassified" gap (so the
  All-vs-platform-sum note appears)
- a per-release lifetime breakdown + a low-volume arch (so the pruning hint fires)
- a per-release daily snapshot series for recent releases (so the Recent Release
  Reception table renders)

It writes to the path given as argv[1] (default: history.json in the cwd). It is
a preview helper only - the real dashboard never uses this.

Usage:  python generate_sample_history.py [output_path]
"""

import json
import random
import sys
from datetime import datetime, timedelta, timezone

REPO = "itsab1989/SampleApp"
DAYS = 60                       # length of the traffic history
DOWNLOAD_DAYS = 45             # length of the per-day download series
RNG = random.Random(42)        # deterministic output


def _date(offset_from_today):
    today = datetime.now(timezone.utc).date()
    return (today - timedelta(days=offset_from_today)).strftime('%Y-%m-%d')


def _iso(offset_from_today, hour=12):
    today = datetime.now(timezone.utc).date()
    d = today - timedelta(days=offset_from_today)
    return f"{d.strftime('%Y-%m-%d')}T{hour:02d}:00:00Z"


def build_daily_data():
    """Daily clones/views: gentle weekly pattern + an upward trend in the last week."""
    rows = []
    for off in range(DAYS - 1, -1, -1):
        weekday_boost = 1.4 if (datetime.now(timezone.utc).date() -
                                timedelta(days=off)).weekday() < 5 else 0.7
        recent_boost = 1.8 if off <= 6 else 1.0   # last 7 days run hotter -> ▲ momentum
        base_views = RNG.randint(8, 22)
        views_total = int(base_views * weekday_boost * recent_boost)
        views_unique = max(1, int(views_total * RNG.uniform(0.45, 0.7)))
        clones_total = int(RNG.randint(2, 9) * weekday_boost * recent_boost)
        clones_unique = max(1, int(clones_total * RNG.uniform(0.5, 0.85)))
        rows.append({
            'date': _date(off),
            'clones_total': clones_total,
            'clones_unique': clones_unique,
            'views_total': views_total,
            'views_unique': views_unique,
        })
    return rows


def build_downloads_daily():
    """Per-day download series with running cumulative and a small unclassified gap."""
    rows = []
    cum = {'total': 0, 'windows': 0, 'macos': 0, 'linux': 0}
    for off in range(DOWNLOAD_DAYS - 1, -1, -1):
        dwin = RNG.randint(0, 4)
        dmac = RNG.randint(1, 9)
        dlin = RNG.randint(0, 2)
        # Occasionally an asset that matched no platform filter (e.g. a .zip),
        # so the grand total drifts above the platform sum -> "unclassified" note.
        dother = 1 if RNG.random() < 0.1 else 0
        dtotal = dwin + dmac + dlin + dother
        cum['windows'] += dwin
        cum['macos'] += dmac
        cum['linux'] += dlin
        cum['total'] += dtotal
        rows.append({
            'date': _date(off),
            'cumulative_total': cum['total'],
            'downloads_total': dtotal,
            'cumulative_windows': cum['windows'],
            'downloads_windows': dwin,
            'cumulative_macos': cum['macos'],
            'downloads_macos': dmac,
            'cumulative_linux': cum['linux'],
            'downloads_linux': dlin,
        })
    return rows, cum


def build_releases():
    """~9 releases over the last ~45 days; the 3 newest are still in early life."""
    specs = [
        # (tag, published offset days ago, windows, macos, linux)
        ('v2.3.0', 2, 3, 14, 1),
        ('v2.2.1', 6, 5, 22, 2),
        ('v2.2.0', 11, 8, 31, 3),
        ('v2.1.0', 18, 6, 25, 2),
        ('v2.0.0', 27, 12, 60, 5),
        ('v1.4.2', 36, 9, 40, 3),
        ('v1.4.1', 44, 4, 18, 1),
        ('v1.4.0', 52, 7, 33, 2),
        ('v1.3.0', 61, 5, 21, 1),
    ]
    by_release = []
    for tag, off, win, mac, lin in specs:
        by_release.append({
            'tag': tag,
            'downloads': win + mac + lin,
            'windows': win, 'macos': mac, 'linux': lin,
            'published_at': _iso(off, hour=10),
        })
    return by_release


def build_by_arch(by_release):
    """Split lifetime per-OS totals across architectures; Linux arm64 is tiny (pruning hint)."""
    win = sum(r['windows'] for r in by_release)
    mac = sum(r['macos'] for r in by_release)
    lin = sum(r['linux'] for r in by_release)
    return {
        'windows': {'x86_64': round(win * 0.8), 'arm64': win - round(win * 0.8)},
        'macos': {'arm64': round(mac * 0.6), 'x86_64': round(mac * 0.25),
                  'universal': mac - round(mac * 0.6) - round(mac * 0.25)},
        # arm64 deliberately tiny -> shows up as a <2% "candidate to stop shipping"
        'linux': {'x86_64': max(0, lin - 1), 'arm64': 1},
    }


def build_by_release_daily(by_release):
    """Per-release daily snapshots for releases published within the 14-day window."""
    out = {}
    for r in by_release:
        published_off = (datetime.now(timezone.utc).date() -
                         datetime.strptime(r['published_at'][:10], '%Y-%m-%d').date()).days
        if published_off > 14:
            continue
        # Build a few snapshots from publish day to today, ramping up to the lifetime total.
        snaps = []
        steps = min(published_off + 1, 5)
        for i in range(steps):
            frac = (i + 1) / steps
            off = published_off - int(published_off * (i / max(1, steps - 1)))
            snaps.append({
                'date': _date(off),
                'downloads': int(r['downloads'] * frac),
                'windows': int(r['windows'] * frac),
                'macos': int(r['macos'] * frac),
                'linux': int(r['linux'] * frac),
            })
        # De-dup by date and keep sorted
        dedup = {s['date']: s for s in snaps}
        out[r['tag']] = {
            'published_at': r['published_at'],
            'snapshots': sorted(dedup.values(), key=lambda s: s['date']),
        }
    return out


def build_history():
    daily = build_daily_data()
    downloads_daily, cum = build_downloads_daily()
    by_release = build_releases()
    by_arch = build_by_arch(by_release)
    by_release_daily = build_by_release_daily(by_release)

    referrers = [
        {'referrer': 'github.com', 'count': 142, 'uniques': 38},
        {'referrer': 'Google', 'count': 89, 'uniques': 41},
        {'referrer': 'reddit.com', 'count': 33, 'uniques': 27},
        {'referrer': 'news.ycombinator.com', 'count': 21, 'uniques': 19},
        {'referrer': 'duckduckgo.com', 'count': 8, 'uniques': 6},
    ]
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    return {
        'metadata': {'generated_at': now, 'last_updated': now, 'repositories': [REPO]},
        'repositories': {
            REPO: {
                'daily_data': daily,
                'referrers': referrers,
                'metadata': {
                    'last_fetched': now,
                    'clones_total': sum(d['clones_total'] for d in daily),
                    'clones_unique_total': sum(d['clones_unique'] for d in daily),
                    'views_total': sum(d['views_total'] for d in daily),
                    'views_unique_total': sum(d['views_unique'] for d in daily),
                },
                'downloads': {
                    'daily_data': downloads_daily,
                    'metadata': {
                        'last_fetched': now,
                        'cumulative_total': cum['total'],
                        'cumulative_windows': cum['windows'],
                        'cumulative_macos': cum['macos'],
                        'cumulative_linux': cum['linux'],
                    },
                    'by_release': by_release,
                    'by_arch': by_arch,
                    'by_release_daily': by_release_daily,
                },
            }
        },
    }


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else 'history.json'
    with open(out_path, 'w') as f:
        json.dump(build_history(), f, indent=2)
    print(f"Wrote sample history to {out_path}")


if __name__ == '__main__':
    main()
