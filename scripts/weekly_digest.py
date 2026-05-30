#!/usr/bin/env python3
"""
Build a short weekly digest of the dashboard's headline movements.

Reads history.json and emits a Markdown summary (to stdout, or a file given as
argv[1]) covering, per repository:
- week-over-week clones / views / downloads, with direction arrows
- lifetime totals
- releases published in the last 7 days and their early-life reception

The weekly workflow (.github/workflows/digest.yml) posts this as a GitHub Issue
so the highlights are pushed to you instead of waiting on the dashboard. The
content builder is pure (stdlib only) and reuses the same metric helpers as the
dashboard, so the numbers always match.

Usage:  python scripts/weekly_digest.py [output_path]   # default: stdout
"""

import os
import sys
from datetime import datetime, timezone, timedelta

# Reuse the dashboard's metric helpers so the digest can't drift from the dashboard
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_dashboard import (  # noqa: E402
    compute_momentum, compute_release_reception, calculate_downloads_lifetime,
    calculate_lifetime_stats, _format_delta, SHOW_FULL_REPO_NAME,
)

HISTORY_FILE = "history.json"
# Cap the per-repo "new releases this week" list (high-cadence repos ship dozens).
MAX_RELEASES_LISTED = 8


def _recent_releases(by_release, now, days=7):
    """Releases published within the last `days`, newest first."""
    cutoff = (now - timedelta(days=days)).strftime('%Y-%m-%d')
    recent = [r for r in (by_release or [])
              if (r.get('published_at') or '')[:10] >= cutoff]
    return sorted(recent, key=lambda r: r.get('published_at') or '', reverse=True)


def _mom_line(label, mom):
    """One '- Label: N (▲ +x%)' bullet from a compute_momentum result."""
    return f"- {label}: **{mom['current']}** vs {mom['previous']} last week ({_format_delta(mom['delta_pct'])})"


def build_digest(history_data, now=None):
    """Assemble the Markdown digest for all tracked repositories."""
    now = now or datetime.now(timezone.utc)
    repositories = history_data.get('repositories', {})
    repo_order = history_data.get('metadata', {}).get('repositories', list(repositories.keys()))

    out = ["# 📊 Weekly Dashboard Digest",
           f"_Week ending {now.strftime('%Y-%m-%d')} (UTC)_", ""]

    for repo_name in repo_order:
        if repo_name not in repositories:
            continue
        repo = repositories[repo_name]
        daily = repo.get('daily_data', [])
        downloads = repo.get('downloads', {})
        downloads_daily = downloads.get('daily_data', [])
        by_release = downloads.get('by_release', [])
        by_release_daily = downloads.get('by_release_daily', {})
        display = repo_name if SHOW_FULL_REPO_NAME else repo_name.split('/')[-1]

        clones = compute_momentum(daily, 'clones_total')
        views = compute_momentum(daily, 'views_total')
        dl = compute_momentum(downloads_daily, 'downloads_total')
        dl_life = calculate_downloads_lifetime(downloads_daily)
        life = calculate_lifetime_stats(daily)

        out.append(f"## {display}")
        out.append("**This week vs last week**")
        out.append(_mom_line("🗂️ Clones", clones))
        out.append(_mom_line("👀 Views", views))
        if downloads_daily:
            out.append(_mom_line("📥 Downloads", dl))
        out.append("")
        out.append(
            f"**Lifetime:** {dl_life['total']} downloads "
            f"(🪟 {dl_life['windows']} · 🍎 {dl_life['macos']} · 🐧 {dl_life['linux']}), "
            f"{life['clones_total']} clones, {life['views_total']} views"
        )
        out.append("")

        recent = _recent_releases(by_release, now)
        if recent:
            total_dl = sum(r.get('downloads', 0) for r in recent)
            noun = "release" if len(recent) == 1 else "releases"
            out.append(f"**New releases this week:** {len(recent)} {noun}, "
                       f"{total_dl} downloads total")
            # High-cadence repos can ship dozens/week, so show only the top few
            # by downloads and summarize the rest.
            top_rel = sorted(recent, key=lambda r: r.get('downloads', 0), reverse=True)
            for r in top_rel[:MAX_RELEASES_LISTED]:
                pub = (r.get('published_at') or '')[:10]
                out.append(f"- `{r.get('tag', '?')}` — {r.get('downloads', 0)} downloads (published {pub})")
            if len(recent) > MAX_RELEASES_LISTED:
                out.append(f"- …and {len(recent) - MAX_RELEASES_LISTED} more")
            out.append("")

        reception = [r for r in compute_release_reception(by_release_daily) if r['accrued'] > 0]
        if reception:
            top = sorted(reception, key=lambda r: r['accrued'], reverse=True)[:3]
            out.append("**Top early-life reception** (downloads since first tracked)")
            for r in top:
                out.append(f"- `{r['tag']}` — **{r['accrued']}** in {r['tracked_days']}d")
            out.append("")

        out.append("---")
        out.append("")

    out.append("_Full interactive dashboard: "
               "https://itsab1989.github.io/github-traffic-downloads-dashboard/dashboard.html_")
    return "\n".join(out)


def main():
    import json
    history = json.load(open(HISTORY_FILE))
    digest = build_digest(history)
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'w') as f:
            f.write(digest)
        print(f"Wrote digest to {sys.argv[1]}")
    else:
        print(digest)


if __name__ == '__main__':
    main()
