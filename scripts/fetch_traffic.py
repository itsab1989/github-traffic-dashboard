#!/usr/bin/env python3
"""
Fetch GitHub traffic + release-download data and write traffic_data.json.

This replaces the ~250-line bash+jq fetch step that used to live inline in the
workflow. It produces a traffic_data.json with exactly the structure
merge_history.py expects, so the rest of the pipeline is unchanged.

Why Python: the bash step was the only untested stage and the most failure-prone
(network, pagination, asset classification). The pure data-shaping here is unit
tested (test_fetch_traffic.py), and the asset matching lives in classify.py.

Repositories are read from a single source - repos.txt at the repo root (one
"owner/name" per line; blank lines and #comments ignored) - or from argv after
the output path. Auth + API config come from the environment:
  TRAFFIC_ACTION_TOKEN  (required)  - token with 'repo' scope
  GITHUB_API_BASE_URL   (optional)  - default https://api.github.com
  GITHUB_API_VERSION    (optional)  - default 2022-11-28

GitHub's traffic API returns the last 14 days; release download_count is a
cumulative all-time counter (snapshotted here, diffed later by merge_history).

Usage:
    python scripts/fetch_traffic.py [output_path] [owner/repo ...]

Error codes (kept from the original step):
  TF001 clones  TF002 views  TF003 referrers  TF004 releases
  JV001-004     invalid JSON for the above
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

# scripts/ on path so this works whether run as a script or imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classify import classify_platform, classify_arch  # noqa: E402

DEFAULT_OUTPUT = "traffic_data.json"
REPOS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "repos.txt")
API_BASE = os.environ.get("GITHUB_API_BASE_URL", "https://api.github.com")
API_VERSION = os.environ.get("GITHUB_API_VERSION", "2022-11-28")
PLATFORMS = ["windows", "macos", "linux"]


class FetchError(Exception):
    """Raised with a stable error code so the workflow log stays diagnosable."""
    def __init__(self, code, message):
        super().__init__(f"ERROR_CODE: {code} - {message}")


def _utc_now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _utc_today():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')


# --------------------------------------------------------------------------- #
# Pure data shaping (unit tested) - no network here.
# --------------------------------------------------------------------------- #

def build_daily_data(clones, views):
    """
    Merge clones and views arrays (GitHub traffic API shape) into daily entries.

    Each clone/view item looks like {"timestamp": "2026-05-25T00:00:00Z",
    "count": N, "uniques": M}. Output entries are keyed by the YYYY-MM-DD date
    with clones_total/clones_unique/views_total/views_unique, date-sorted.
    """
    by_date = {}
    for c in clones or []:
        ts = (c.get('timestamp') or '')[:10]
        if not ts:
            continue
        e = by_date.setdefault(ts, {})
        e['clones_total'] = c.get('count', 0)
        e['clones_unique'] = c.get('uniques', 0)
    for v in views or []:
        ts = (v.get('timestamp') or '')[:10]
        if not ts:
            continue
        e = by_date.setdefault(ts, {})
        e['views_total'] = v.get('count', 0)
        e['views_unique'] = v.get('uniques', 0)
    out = []
    for date in sorted(by_date):
        e = by_date[date]
        out.append({
            'date': date,
            'clones_total': e.get('clones_total', 0),
            'clones_unique': e.get('clones_unique', 0),
            'views_total': e.get('views_total', 0),
            'views_unique': e.get('views_unique', 0),
        })
    return out


def aggregate_release(release):
    """Per-release lifetime totals split by platform (matching the by_release shape)."""
    counts = {'downloads': 0, 'windows': 0, 'macos': 0, 'linux': 0}
    for asset in release.get('assets') or []:
        dc = asset.get('download_count', 0) or 0
        counts['downloads'] += dc
        platform = classify_platform(asset.get('name'))
        if platform:
            counts[platform] += dc
    return {
        'tag': release.get('tag_name', ''),
        'downloads': counts['downloads'],
        'windows': counts['windows'],
        'macos': counts['macos'],
        'linux': counts['linux'],
        'published_at': release.get('published_at'),
    }


def aggregate_downloads(releases):
    """
    Aggregate all releases into cumulative totals, per-release, and per-arch.

    'cumulative_total' counts every asset (matched or not), so it can exceed the
    sum of the platform buckets - the gap is the dashboard's "unclassified" note.
    """
    cumulative = {'total': 0, 'windows': 0, 'macos': 0, 'linux': 0}
    by_arch = {'windows': {}, 'macos': {}, 'linux': {}}
    by_release = []
    for release in releases or []:
        rel = aggregate_release(release)
        by_release.append(rel)
        cumulative['total'] += rel['downloads']
        for p in PLATFORMS:
            cumulative[p] += rel[p]
        for asset in release.get('assets') or []:
            platform = classify_platform(asset.get('name'))
            if not platform:
                continue
            arch = classify_arch(asset.get('name'))
            dc = asset.get('download_count', 0) or 0
            by_arch[platform][arch] = by_arch[platform].get(arch, 0) + dc
    return {
        'cumulative_total': cumulative['total'],
        'cumulative_windows': cumulative['windows'],
        'cumulative_macos': cumulative['macos'],
        'cumulative_linux': cumulative['linux'],
        'by_release': by_release,
        'by_arch': by_arch,
    }


def build_repo_payload(clones, views, referrers, releases, fetch_date=None, today=None):
    """Assemble the per-repository object stored under repositories[repo]."""
    fetch_date = fetch_date or _utc_now_iso()
    today = today or _utc_today()
    daily = build_daily_data(clones, views)
    downloads = aggregate_downloads(releases)
    downloads.update({'date': today, 'last_fetched': fetch_date})
    return {
        'daily_data': daily,
        'referrers': referrers or [],
        'metadata': {
            'last_fetched': fetch_date,
            'clones_total': sum(d['clones_total'] for d in daily),
            'clones_unique_total': sum(d['clones_unique'] for d in daily),
            'views_total': sum(d['views_total'] for d in daily),
            'views_unique_total': sum(d['views_unique'] for d in daily),
        },
        'downloads': downloads,
    }


def build_traffic_data(repos_raw, generated_at=None):
    """
    Build the full traffic_data.json structure from raw per-repo API responses.

    Args:
        repos_raw: ordered list of (repo_name, {clones, views, referrers, releases})
        generated_at: optional timestamp; defaults to now (UTC)

    Returns:
        {'metadata': {generated_at, repositories: [...]}, 'repositories': {...}}
    """
    generated_at = generated_at or _utc_now_iso()
    fetch_date = _utc_now_iso()
    today = _utc_today()
    repositories = {}
    order = []
    for repo, raw in repos_raw:
        repositories[repo] = build_repo_payload(
            raw.get('clones', {}).get('clones', []),
            raw.get('views', {}).get('views', []),
            raw.get('referrers', []),
            raw.get('releases', []),
            fetch_date=fetch_date, today=today,
        )
        order.append(repo)
    return {
        'metadata': {'generated_at': generated_at, 'repositories': order},
        'repositories': repositories,
    }


# --------------------------------------------------------------------------- #
# Network layer.
# --------------------------------------------------------------------------- #

def http_get_json(url, token, fetch_code, validate_code, expect_array=False):
    """GET a URL and parse JSON, raising FetchError with stable codes on failure."""
    req = urllib.request.Request(url, headers={
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {token}',
        'X-GitHub-Api-Version': API_VERSION,
        'User-Agent': 'github-traffic-dashboard',
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
            body = resp.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        raise FetchError(fetch_code, f"HTTP {e.code} for {url}")
    except urllib.error.URLError as e:
        raise FetchError(fetch_code, f"request failed for {url}: {e.reason}")
    if status != 200:
        raise FetchError(fetch_code, f"HTTP {status} for {url}")
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise FetchError(validate_code, f"invalid JSON from {url}")
    if expect_array and not isinstance(data, list):
        raise FetchError(validate_code, f"expected JSON array from {url}")
    return data


def fetch_releases(repo, token):
    """Fetch all releases, following pagination (100/page)."""
    releases = []
    page = 1
    while True:
        url = f"{API_BASE}/repos/{repo}/releases?per_page=100&page={page}"
        chunk = http_get_json(url, token, 'TF004', 'JV004', expect_array=True)
        releases.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    return releases


def fetch_repo(repo, token):
    """Fetch all raw API responses for a single repository."""
    return {
        'clones': http_get_json(f"{API_BASE}/repos/{repo}/traffic/clones", token, 'TF001', 'JV001'),
        'views': http_get_json(f"{API_BASE}/repos/{repo}/traffic/views", token, 'TF002', 'JV002'),
        'referrers': http_get_json(f"{API_BASE}/repos/{repo}/traffic/popular/referrers", token, 'TF003', 'JV003'),
        'releases': fetch_releases(repo, token),
    }


def load_repos(extra_args):
    """Repos from CLI args if given, else from repos.txt (comments/blanks ignored)."""
    if extra_args:
        return extra_args
    repos = []
    if os.path.exists(REPOS_FILE):
        with open(REPOS_FILE) as f:
            for line in f:
                line = line.split('#', 1)[0].strip()
                if line:
                    repos.append(line)
    return repos


def main():
    output = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT
    repos = load_repos(sys.argv[2:])
    if not repos:
        print("ERROR_CODE: TF000 - no repositories configured (repos.txt empty?)", file=sys.stderr)
        sys.exit(1)

    token = os.environ.get('TRAFFIC_ACTION_TOKEN', '')
    if not token:
        print("ERROR_CODE: TF000 - TRAFFIC_ACTION_TOKEN is not set", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching traffic for {len(repos)} repository(ies): {', '.join(repos)}")
    repos_raw = []
    try:
        for repo in repos:
            print(f"  - {repo}")
            repos_raw.append((repo, fetch_repo(repo, token)))
    except FetchError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    data = build_traffic_data(repos_raw)
    with open(output, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {output}")


if __name__ == '__main__':
    main()
