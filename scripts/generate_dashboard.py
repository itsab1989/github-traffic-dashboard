#!/usr/bin/env python3
"""
Generate GitHub traffic dashboard with graphs and statistics.

This script:
1. Loads historical traffic data from history.json
2. Generates graphs for different time intervals (daily, weekly, bi-weekly, cumulative)
3. Calculates statistics for 30 days, 90 days, and lifetime
4. Updates README.md with statistics and embedded graph images

Error codes: GD001-008
"""

# ============================================================================
# CONFIGURATION SECTION - MODIFY THESE PARAMETERS FOR YOUR NEEDS
# ============================================================================

# File Paths Configuration
# These paths are relative to the repository root directory
HISTORY_FILE_PATH = "history.json"           # Path to historical traffic data
README_FILE_PATH = "README.md"               # Path to README file to update
GRAPHS_DIRECTORY = "graphs"                  # Directory for storing graph images

# Graph Configuration
# Graph dimensions and quality settings
GRAPH_DPI = 100                              # Dots per inch for graph quality
GRAPH_FIGSIZE_DAILY = (12, 6)                # Dimensions for daily graphs (width, height)
GRAPH_FIGSIZE_WEEKLY = (14, 6)               # Dimensions for weekly graphs
GRAPH_FIGSIZE_BIWEEKLY = (16, 6)             # Dimensions for bi-weekly graphs
GRAPH_FIGSIZE_CUMULATIVE = (14, 6)           # Dimensions for cumulative graphs

# Time Period Configuration
# Number of days for different time periods
DAILY_GRAPH_DAYS = 30                        # Days to show in daily graphs
WEEKLY_GRAPH_WEEKS = 12                     # Weeks to show in weekly graphs (3 months)
BIWEEKLY_GRAPH_PERIODS = 26                 # Bi-weekly periods to show (1 year)

# Statistics Periods
# Days for calculating statistics
STATS_PERIOD_SHORT_TERM = 30               # Short-term statistics period (default: 30 days)
STATS_PERIOD_MEDIUM_TERM = 90               # Medium-term statistics period (default: 90 days)

# Graph Style Configuration
# Color schemes for graphs
CLONES_COLOR = "#2196F3"                    # Blue for clones
VIEWS_COLOR = "#4CAF50"                     # Green for views
GRID_COLOR = "#E0E0E0"                      # Light gray for grid lines
TEXT_COLOR = "#333333"                      # Dark gray for text

# Release Downloads Configuration
# Whether to include the release-downloads section (tables + graphs)
INCLUDE_DOWNLOADS = True
# Number of releases to show in the "Top Releases by Downloads" table
TOP_RELEASES_COUNT = 10
# Series plotted on the download graphs: (label, data_key, color, marker, linewidth)
# data_key maps to downloads_<key> (daily) and cumulative_<key> (lifetime) fields.
# "All" is drawn thicker so the combined line stands out from the per-platform lines.
DOWNLOAD_SERIES = [
    ("All",     "total",   "#212121", "o", 2.5),   # Near-black for the combined total
    ("Windows", "windows", "#0078D6", "s", 2.0),   # Windows blue
    ("macOS",   "macos",   "#8E8E93", "^", 2.0),   # Apple silver/gray
    ("Linux",   "linux",   "#E95420", "D", 2.0),   # Ubuntu orange
]

# Repository Display Configuration
# How repository names are displayed in graphs and README
# Set to True to show full "owner/repo" name, False to show only repo name
SHOW_FULL_REPO_NAME = False                  # If False, shows only repository name

# README Generation Configuration
# Settings for README.md generation
README_HEADER_LEVEL = 1                      # Markdown header level for repository names (1-6)
INCLUDE_CUMULATIVE_GRAPHS = True            # Whether to include cumulative graphs
INCLUDE_SEPARATE_CUMULATIVE = True          # Whether to include separate clones/views cumulative graphs

# Project / Branding Configuration
# Canonical published location of THIS dashboard's reference guide (its own
# GitHub Pages site), not the upstream project's.
DASHBOARD_GUIDE_URL = "https://itsab1989.github.io/github-traffic-downloads-dashboard/"
# Attribution to the upstream project this is extended from (correct to keep).
UPSTREAM_NAME = "github-traffic-dashboard"
UPSTREAM_URL = "https://github.com/soul-traveller/github-traffic-dashboard"

# At-a-glance Configuration
INCLUDE_BADGES = True                        # shields.io summary badges per repository
INCLUDE_MOMENTUM = True                      # Week-over-week momentum line
INCLUDE_FUNNEL = True                        # Views -> Clones -> Downloads engagement funnel
# Early-life window (days) for the "recent release reception" table. Keep in sync
# with RELEASE_DAILY_TRACKING_DAYS in merge_history.py (the data it reads from).
RELEASE_RECEPTION_WINDOW_DAYS = 14

# Charts Configuration
# INCLUDE_CHARTS writes an interactive chart-data JSON (read by dashboard.html)
# and links the README to that JS-rendered page. GitHub's README view can't run
# JavaScript, so the interactive charts live on the GitHub Pages site and the
# README links out to them. INCLUDE_GRAPHS keeps the legacy static matplotlib
# PNGs (off by default now that interactive charts replace them).
INCLUDE_CHARTS = True
INCLUDE_GRAPHS = False
CHART_DATA_PATH = "assets/chart-data.json"   # Written relative to the repo root
# Live URL of the interactive dashboard page (GitHub Pages), linked from the README
CHARTS_PAGE_URL = "https://itsab1989.github.io/github-traffic-downloads-dashboard/dashboard.html"

# ============================================================================
# END OF CONFIGURATION SECTION
# The following settings typically do not need modification
# ============================================================================

# Standard library imports
import json  # For JSON file operations
import sys   # For system exit and error handling
import os    # For file system operations

# Date and time handling
from datetime import datetime, timedelta, timezone  # For date calculations (UTC-aware)

# Type hints for better code documentation
from typing import Dict, List, Any, Tuple, Optional  # For type annotations

# Plotting libraries (optional). Only the legacy static-PNG path (INCLUDE_GRAPHS)
# needs matplotlib; the default interactive-charts path does not. Importing it
# lazily keeps the module - and its tests - usable without matplotlib installed.
try:
    import matplotlib
    matplotlib.use("Agg")  # headless backend (no display needed in CI)
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
except ImportError:  # pragma: no cover - only hit when PNG mode is unavailable
    plt = None
    mdates = None


def load_json_file(filepath: str) -> Dict[str, Any]:
    """
    Load a JSON file from disk with comprehensive error handling.
    
    Args:
        filepath: Path to the JSON file to load
        
    Returns:
        Dictionary containing the parsed JSON data
        
    Raises:
        SystemExit: If file not found (GD001), invalid JSON (GD002), or other error (GD003)
    """
    try:
        # Open and read the JSON file
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # ERROR_CODE: GD001 - File not found
        print(f"ERROR_CODE: GD001 - File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        # ERROR_CODE: GD002 - Invalid JSON format
        print(f"ERROR_CODE: GD002 - Invalid JSON in {filepath}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # ERROR_CODE: GD003 - General load error
        print(f"ERROR_CODE: GD003 - Error loading {filepath}: {e}", file=sys.stderr)
        sys.exit(1)


def save_file(content: str, filepath: str) -> None:
    """
    Save content to a file with error handling.
    
    Args:
        content: String content to write to the file
        filepath: Path where the file should be saved
        
    Raises:
        SystemExit: If file cannot be saved (GD004)
    """
    try:
        # Open the file in write mode and save the content
        with open(filepath, 'w') as f:
            f.write(content)
    except Exception as e:
        # ERROR_CODE: GD004 - File save error
        print(f"ERROR_CODE: GD004 - Error saving to {filepath}: {e}", file=sys.stderr)
        sys.exit(1)


def prepare_graphs_directory() -> None:
    """
    Create the graphs directory if it doesn't exist.
    
    This ensures the directory for storing graph images exists before
    attempting to save any graphs.
    
    Raises:
        SystemExit: If directory cannot be created (GD005)
    """
    try:
        # Create directory if it doesn't exist, don't error if it does
        # Uses GRAPHS_DIRECTORY configuration parameter
        os.makedirs(GRAPHS_DIRECTORY, exist_ok=True)
    except Exception as e:
        # ERROR_CODE: GD005 - Directory creation error
        print(f"ERROR_CODE: GD005 - Error creating graphs directory: {e}", file=sys.stderr)
        sys.exit(1)


def calculate_period_stats(daily_data: List[Dict[str, Any]], days: int) -> Dict[str, int]:
    """
    Calculate statistics for a specific time period (e.g., last 30 days, last 90 days).
    
    This function sums up clones and views for all entries within the specified
    number of days from today.
    
    Args:
        daily_data: List of daily data entries with date, clones, and views
        days: Number of days to look back from today
        
    Returns:
        Dictionary with keys: clones_total, clones_unique, views_total, views_unique
    """
    # Return zeros if no data available
    if not daily_data:
        return {
            'clones_total': 0,
            'clones_unique': 0,
            'views_total': 0,
            'views_unique': 0
        }
    
    # Calculate the cutoff date (N days ago)
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # Initialize statistics counters
    stats = {
        'clones_total': 0,
        'clones_unique': 0,
        'views_total': 0,
        'views_unique': 0
    }
    
    # Sum up statistics for entries within the time period
    for entry in daily_data:
        if entry.get('date', '') >= cutoff_date:
            stats['clones_total'] += entry.get('clones_total', 0)
            stats['clones_unique'] += entry.get('clones_unique', 0)
            stats['views_total'] += entry.get('views_total', 0)
            stats['views_unique'] += entry.get('views_unique', 0)
    
    return stats


def calculate_lifetime_stats(daily_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Calculate lifetime statistics from all available daily data.
    
    This function sums up all clones and views across the entire
    historical data set.
    
    Args:
        daily_data: List of all daily data entries
        
    Returns:
        Dictionary with keys: clones_total, clones_unique, views_total, views_unique
    """
    # Return zeros if no data available
    if not daily_data:
        return {
            'clones_total': 0,
            'clones_unique': 0,
            'views_total': 0,
            'views_unique': 0
        }
    
    # Initialize statistics counters
    stats = {
        'clones_total': 0,
        'clones_unique': 0,
        'views_total': 0,
        'views_unique': 0
    }
    
    # Sum up statistics for all entries
    for entry in daily_data:
        stats['clones_total'] += entry.get('clones_total', 0)
        stats['clones_unique'] += entry.get('clones_unique', 0)
        stats['views_total'] += entry.get('views_total', 0)
        stats['views_unique'] += entry.get('views_unique', 0)
    
    return stats


def get_daily_data(daily_data: List[Dict[str, Any]], days: int) -> Tuple[List[str], List[int], List[int]]:
    """
    Extract daily data for the last N days.
    
    This function filters daily_data to only include entries within
    the specified number of days from today.
    
    Args:
        daily_data: List of all daily data entries
        days: Number of days to include
        
    Returns:
        Tuple containing:
        - List of date strings
        - List of clone counts
        - List of view counts
    """
    # Return empty lists if no data available
    if not daily_data:
        return [], [], []
    
    # Calculate the cutoff date (N days ago)
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # Initialize lists to hold the filtered data
    dates = []
    clones = []
    views = []
    
    # Filter and extract data within the time period
    for entry in daily_data:
        if entry.get('date', '') >= cutoff_date:
            dates.append(entry.get('date', ''))
            clones.append(entry.get('clones_total', 0))
            views.append(entry.get('views_total', 0))
    
    return dates, clones, views


def get_weekly_data(daily_data: List[Dict[str, Any]], weeks: int) -> Tuple[List[str], List[int], List[int]]:
    """
    Aggregate daily data into weekly intervals for the last N weeks.
    
    This function groups daily data by week and sums up clones and views
    for each week. A week is defined as 7 consecutive days.
    
    Args:
        daily_data: List of all daily data entries
        weeks: Number of weeks to include
        
    Returns:
        Tuple containing:
        - List of week start dates
        - List of weekly clone totals
        - List of weekly view totals
    """
    # Return empty lists if no data available
    if not daily_data:
        return [], [], []
    
    # Get today's date
    today = datetime.now(timezone.utc).date()
    weekly_data = []
    
    # Iterate through weeks from oldest to newest
    for w in range(weeks - 1, -1, -1):
        # Calculate week start and end dates
        week_start = today - timedelta(weeks=w)
        week_end = week_start + timedelta(days=6)
        
        # Initialize counters for this week
        week_clones = 0
        week_views = 0
        
        # Sum up data for entries within this week
        for entry in daily_data:
            entry_date = datetime.strptime(entry.get('date', ''), '%Y-%m-%d').date()
            if week_start <= entry_date <= week_end:
                week_clones += entry.get('clones_total', 0)
                week_views += entry.get('views_total', 0)
        
        # Store the aggregated week data
        weekly_data.append({
            'date': week_start.strftime('%Y-%m-%d'),
            'clones': week_clones,
            'views': week_views
        })
    
    # Extract lists from the aggregated data
    dates = [w['date'] for w in weekly_data]
    clones = [w['clones'] for w in weekly_data]
    views = [w['views'] for w in weekly_data]
    
    return dates, clones, views


def get_biweekly_data(daily_data: List[Dict[str, Any]], periods: int) -> Tuple[List[str], List[int], List[int]]:
    """
    Aggregate daily data into bi-weekly (2-week) intervals for the last N periods.
    
    This function groups daily data by 2-week periods and sums up clones and views
    for each period. A period is defined as 14 consecutive days.
    
    Args:
        daily_data: List of all daily data entries
        periods: Number of bi-weekly periods to include
        
    Returns:
        Tuple containing:
        - List of period start dates
        - List of period clone totals
        - List of period view totals
    """
    # Return empty lists if no data available
    if not daily_data:
        return [], [], []
    
    # Get today's date
    today = datetime.now(timezone.utc).date()
    biweekly_data = []
    
    # Iterate through periods from oldest to newest
    for p in range(periods - 1, -1, -1):
        # Calculate period start and end dates (14 days)
        period_start = today - timedelta(days=p * 14)
        period_end = period_start + timedelta(days=13)
        
        # Initialize counters for this period
        period_clones = 0
        period_views = 0
        
        # Sum up data for entries within this period
        for entry in daily_data:
            entry_date = datetime.strptime(entry.get('date', ''), '%Y-%m-%d').date()
            if period_start <= entry_date <= period_end:
                period_clones += entry.get('clones_total', 0)
                period_views += entry.get('views_total', 0)
        
        # Store the aggregated period data
        biweekly_data.append({
            'date': period_start.strftime('%Y-%m-%d'),
            'clones': period_clones,
            'views': period_views
        })
    
    # Extract lists from the aggregated data
    dates = [b['date'] for b in biweekly_data]
    clones = [b['clones'] for b in biweekly_data]
    views = [b['views'] for b in biweekly_data]
    
    return dates, clones, views


def get_cumulative_data(daily_data: List[Dict[str, Any]]) -> Tuple[List[str], List[int], List[int]]:
    """
    Calculate cumulative (additive) data over time.
    
    This function calculates running totals of clones and views,
    showing how the total grows over time. Each data point represents
    the sum of all previous days plus the current day.
    
    Args:
        daily_data: List of all daily data entries (should be sorted by date)
        
    Returns:
        Tuple containing:
        - List of dates
        - List of cumulative clone totals
        - List of cumulative view totals
    """
    # Return empty lists if no data available
    if not daily_data:
        return [], [], []
    
    # Initialize lists to hold the cumulative data
    dates = []
    cumulative_clones = []
    cumulative_views = []
    
    # Initialize running totals
    total_clones = 0
    total_views = 0
    
    # Calculate running totals for each day
    for entry in daily_data:
        # Add current day's values to running totals
        total_clones += entry.get('clones_total', 0)
        total_views += entry.get('views_total', 0)
        
        # Store the date and running totals
        dates.append(entry.get('date', ''))
        cumulative_clones.append(total_clones)
        cumulative_views.append(total_views)
    
    return dates, cumulative_clones, cumulative_views


def get_downloads_daily(downloads_daily: List[Dict[str, Any]], days: int) -> Tuple[List[str], Dict[str, List[int]]]:
    """
    Extract per-day release-download deltas for the last N days, per platform.

    Args:
        downloads_daily: List of downloads daily entries (with downloads_<platform> deltas)
        days: Number of days to include

    Returns:
        Tuple of (list of date strings, dict mapping platform key -> list of daily counts).
        Platform keys: total, windows, macos, linux.
    """
    series = {'total': [], 'windows': [], 'macos': [], 'linux': []}
    if not downloads_daily:
        return [], series

    # Calculate the cutoff date (N days ago)
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%d')

    dates = []
    for entry in downloads_daily:
        if entry.get('date', '') >= cutoff_date:
            dates.append(entry.get('date', ''))
            for platform in series:
                series[platform].append(entry.get(f'downloads_{platform}', 0))

    return dates, series


def get_downloads_cumulative(downloads_daily: List[Dict[str, Any]]) -> Tuple[List[str], Dict[str, List[int]]]:
    """
    Extract cumulative (all-time running total) release downloads, per platform.

    The cumulative values are already stored in each entry (as snapshots), so no
    running sum is computed here - they are read directly.

    Args:
        downloads_daily: List of downloads daily entries (with cumulative_<platform> snapshots)

    Returns:
        Tuple of (list of date strings, dict mapping platform key -> list of cumulative totals).
    """
    series = {'total': [], 'windows': [], 'macos': [], 'linux': []}
    if not downloads_daily:
        return [], series

    dates = []
    for entry in downloads_daily:
        dates.append(entry.get('date', ''))
        for platform in series:
            series[platform].append(entry.get(f'cumulative_{platform}', 0))

    return dates, series


def calculate_downloads_period_stats(downloads_daily: List[Dict[str, Any]], days: int) -> Dict[str, int]:
    """
    Sum per-day release downloads over the last N days, per platform.

    Args:
        downloads_daily: List of downloads daily entries
        days: Number of days to look back from today

    Returns:
        Dictionary mapping platform key -> total downloads in the period.
    """
    stats = {'total': 0, 'windows': 0, 'macos': 0, 'linux': 0}
    if not downloads_daily:
        return stats

    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%d')
    for entry in downloads_daily:
        if entry.get('date', '') >= cutoff_date:
            for platform in stats:
                stats[platform] += entry.get(f'downloads_{platform}', 0)

    return stats


def calculate_downloads_lifetime(downloads_daily: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Get lifetime (all-time) release downloads, per platform.

    Lifetime is read from the most recent cumulative snapshot rather than summed
    from daily deltas, so it reflects the true all-time download_count even for
    downloads that happened before per-day tracking began.

    Args:
        downloads_daily: List of downloads daily entries

    Returns:
        Dictionary mapping platform key -> all-time download total.
    """
    stats = {'total': 0, 'windows': 0, 'macos': 0, 'linux': 0}
    if not downloads_daily:
        return stats

    latest = downloads_daily[-1]
    for platform in stats:
        stats[platform] = latest.get(f'cumulative_{platform}', 0)

    return stats


def compute_tracking_window(daily_data: List[Dict[str, Any]]) -> Tuple[Optional[str], int]:
    """
    Determine when meaningful tracking actually began and how long it spans.

    GitHub's traffic API only returns the last 14 days, and history is zero-filled
    back a year, so the early part of daily_data is all zeros. The "real" tracking
    window starts at the first day with any clone or view activity. Reporting this
    keeps the Lifetime/90-day columns honest when they only reflect a short window.

    Args:
        daily_data: List of daily data entries (date-sorted, possibly zero-filled)

    Returns:
        (first_active_date or None, active_days). active_days is inclusive of both
        ends; 0 if there is no activity yet.
    """
    first = None
    last = None
    for entry in daily_data:
        if (entry.get('clones_total', 0) or entry.get('views_total', 0)):
            date_str = entry.get('date')
            if date_str:
                first = first or date_str
                last = date_str
    if not first:
        return None, 0
    d0 = datetime.strptime(first, '%Y-%m-%d').date()
    d1 = datetime.strptime(last, '%Y-%m-%d').date()
    return first, (d1 - d0).days + 1


def _pct_change(current: int, previous: int) -> Optional[float]:
    """Percentage change current vs previous; None when there is no baseline."""
    if previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)


def _sum_window(daily_data: List[Dict[str, Any]], field: str,
                oldest_offset: int, newest_offset: int) -> int:
    """Sum `field` over days in [today-oldest_offset, today-newest_offset], inclusive."""
    today = datetime.now(timezone.utc).date()
    lo = (today - timedelta(days=oldest_offset)).strftime('%Y-%m-%d')
    hi = (today - timedelta(days=newest_offset)).strftime('%Y-%m-%d')
    return sum(e.get(field, 0) for e in daily_data
               if lo <= e.get('date', '') <= hi)


def compute_momentum(daily_data: List[Dict[str, Any]],
                     field: str = 'clones_total') -> Dict[str, Any]:
    """
    Week-over-week momentum for a metric: last 7 days (incl. today) vs the prior 7.

    Args:
        daily_data: Date-sorted daily entries
        field: Which numeric field to compare (e.g. 'clones_total', 'views_total')

    Returns:
        {'current': int, 'previous': int, 'delta_pct': float|None}
    """
    current = _sum_window(daily_data, field, 6, 0)    # today and the 6 days before
    previous = _sum_window(daily_data, field, 13, 7)  # the 7 days before that
    return {'current': current, 'previous': previous,
            'delta_pct': _pct_change(current, previous)}


def compute_funnel(views: int, clones: int, downloads: int) -> Dict[str, Any]:
    """
    Engagement funnel ratios across views -> clones -> downloads for a period.

    Views, clones and downloads are independent GitHub metrics, so these are
    interest ratios rather than a strict per-user funnel - but they answer
    "of the people who looked, how many took a deeper action?".

    Returns:
        {'views', 'clones', 'downloads', 'clone_rate', 'download_rate'} where the
        rates are percentages (float) or None when the denominator is zero.
    """
    clone_rate = round(clones / views * 100, 1) if views else None
    download_rate = round(downloads / clones * 100, 1) if clones else None
    return {'views': views, 'clones': clones, 'downloads': downloads,
            'clone_rate': clone_rate, 'download_rate': download_rate}


def compute_unclassified(dl_lifetime: Dict[str, int]) -> int:
    """
    Downloads counted in the grand total but matched to no platform.

    The fetch sums every asset into 'total' but only filename-matched assets land
    in windows/macos/linux, so 'total' can exceed their sum. Surfacing the gap
    explains the discrepancy and flags asset-naming regressions. Clamped at >= 0.
    """
    matched = dl_lifetime.get('windows', 0) + dl_lifetime.get('macos', 0) + dl_lifetime.get('linux', 0)
    return max(0, dl_lifetime.get('total', 0) - matched)


def compute_release_reception(by_release_daily: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Summarize how recently published releases are being adopted in their early life.

    Reads the bounded per-release daily snapshot series (by_release_daily) produced
    by merge_history. For each tracked release it reports downloads accrued since we
    first observed it - i.e. early-life reception, comparable across releases of
    different ages because each is measured over its own tracked window.

    Args:
        by_release_daily: {tag: {'published_at', 'snapshots': [{date, downloads,
            windows, macos, linux} ...]}} (snapshots date-sorted)

    Returns:
        Rows {tag, published, tracked_days, accrued, accrued_windows, accrued_macos,
        accrued_linux, lifetime}, newest published first. Empty until data accrues.
    """
    rows = []
    for tag, info in (by_release_daily or {}).items():
        snaps = info.get('snapshots') or []
        if not snaps:
            continue
        first, last = snaps[0], snaps[-1]
        try:
            d0 = datetime.strptime(first['date'], '%Y-%m-%d').date()
            d1 = datetime.strptime(last['date'], '%Y-%m-%d').date()
            tracked_days = (d1 - d0).days + 1
        except (ValueError, KeyError):
            tracked_days = len(snaps)
        rows.append({
            'tag': tag,
            'published': (info.get('published_at') or '')[:10],
            'tracked_days': tracked_days,
            'accrued': max(0, last.get('downloads', 0) - first.get('downloads', 0)),
            'accrued_windows': max(0, last.get('windows', 0) - first.get('windows', 0)),
            'accrued_macos': max(0, last.get('macos', 0) - first.get('macos', 0)),
            'accrued_linux': max(0, last.get('linux', 0) - first.get('linux', 0)),
            'lifetime': last.get('downloads', 0),
        })
    rows.sort(key=lambda r: r['published'], reverse=True)
    return rows


def render_badges(repo_name: str, dl_lifetime: Dict[str, int],
                  stats_lifetime: Dict[str, int], release_count: int) -> str:
    """
    Build a row of shields.io static badges summarizing a repository at a glance.

    Uses static badge endpoints (no extra service/auth) so they render anywhere
    the markdown is shown. Returns a single markdown line.
    """
    def badge(label: str, value: Any, color: str) -> str:
        # shields.io static badge: encode '-' (its field separator) as '--'
        safe_label = str(label).replace('-', '--').replace(' ', '%20')
        safe_value = str(value).replace('-', '--').replace(' ', '%20')
        return (f"![{label}](https://img.shields.io/badge/"
                f"{safe_label}-{safe_value}-{color})")

    parts = [
        badge('downloads', dl_lifetime.get('total', 0), '212121'),
        badge('clones', stats_lifetime.get('clones_total', 0), '2196F3'),
        badge('views', stats_lifetime.get('views_total', 0), '4CAF50'),
        badge('releases', release_count, '6f42c1'),
    ]
    return " ".join(parts) + "\n\n"


def _format_delta(delta_pct: Optional[float]) -> str:
    """Render a percentage delta with a direction arrow, or a neutral dash."""
    if delta_pct is None:
        return "—"
    if delta_pct > 0:
        return f"▲ +{delta_pct}%"
    if delta_pct < 0:
        return f"▼ {delta_pct}%"
    return "▬ 0%"


def get_latest_release(downloads_by_release: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Find the most recently published release, regardless of its download count.

    Unlike the "Top Releases by Downloads" table (which is sorted by count and
    skips releases with zero downloads), this always returns the newest release -
    so a freshly published release shows up immediately, even at 0 downloads.

    The newest release is chosen by the latest ``published_at`` timestamp
    (ISO-8601 strings sort chronologically). Entries without a timestamp sort
    last, falling back to input order so a usable release is still returned.

    Args:
        downloads_by_release: List of per-release entries
            (each with 'tag', 'downloads', 'published_at').

    Returns:
        The most recent release entry, or None if the list is empty.
    """
    if not downloads_by_release:
        return None

    return max(downloads_by_release, key=lambda r: r.get('published_at') or '')


def get_release_breakdown(downloads_by_release: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build a per-release download breakdown, newest first, split by platform.

    Powers the collapsible "Per-version downloads" table. Releases are ordered by
    published_at (newest first). The per-platform fields (windows/macos/linux)
    default to 0 for releases fetched before per-release platform tracking was
    added, while 'total' always reflects the all-time download_count.

    Args:
        downloads_by_release: List of per-release entries (each with 'tag',
            'downloads', optional 'windows'/'macos'/'linux', and 'published_at').

    Returns:
        A list of rows, each {tag, windows, macos, linux, total, published}.
    """
    if not downloads_by_release:
        return []

    ordered = sorted(
        downloads_by_release,
        key=lambda r: r.get('published_at') or '',
        reverse=True,
    )
    return [
        {
            'tag': r.get('tag', '?'),
            'windows': r.get('windows', 0),
            'macos': r.get('macos', 0),
            'linux': r.get('linux', 0),
            'total': r.get('downloads', 0),
            'published': (r.get('published_at') or '')[:10],
        }
        for r in ordered
    ]


def create_graph(dates: List[str], values: List[int], title: str, ylabel: str,
                 filename: str, color: str = 'blue', figsize: Tuple[int, int] = None) -> None:
    """
    Create a single-line graph with the given data.
    
    This function creates a line graph showing one metric over time.
    The graph includes markers, grid lines, and properly formatted dates.
    
    Args:
        dates: List of date strings in 'YYYY-MM-DD' format
        values: List of numeric values corresponding to each date
        title: Title for the graph
        ylabel: Label for the y-axis
        filename: Path where the graph image will be saved
        color: Color for the line (default: 'blue')
        figsize: Figure size as (width, height) tuple (uses GRAPH_FIGSIZE_CUMULATIVE if None)
        
    Raises:
        SystemExit: If graph creation fails (GD006)
    """
    try:
        # Check if we have data to plot
        if not dates or not values:
            print(f"WARNING: No data for graph: {title}")
            return
        
        # Use configured figure size if not provided
        if figsize is None:
            figsize = GRAPH_FIGSIZE_CUMULATIVE
        
        # Convert date strings to datetime objects for plotting
        dates_dt = [datetime.strptime(d, '%Y-%m-%d') for d in dates]
        
        # Create a new figure with specified size from configuration
        plt.figure(figsize=figsize)
        
        # Plot the data with markers
        plt.plot(dates_dt, values, marker='o', linewidth=2, markersize=4, color=color)
        
        # Set title and axis labels with configured text color
        plt.title(title, fontsize=14, fontweight='bold', color=TEXT_COLOR)
        plt.xlabel('Date', fontsize=12, color=TEXT_COLOR)
        plt.ylabel(ylabel, fontsize=12, color=TEXT_COLOR)
        
        # Add grid with configured color and transparency
        plt.grid(True, color=GRID_COLOR, alpha=0.3)
        
        # Format x-axis to show dates properly
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45, ha='right')
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Save the figure with configured DPI
        plt.savefig(filename, dpi=GRAPH_DPI, bbox_inches='tight')
        
        # Close the figure to free memory
        plt.close()
        
    except Exception as e:
        # ERROR_CODE: GD006 - Graph creation error
        print(f"ERROR_CODE: GD006 - Error creating graph {filename}: {e}", file=sys.stderr)
        sys.exit(1)


def create_multi_line_graph(dates: List[str], clones: List[int], views: List[int], 
                            title: str, filename: str, figsize: Tuple[int, int] = None) -> None:
    """
    Create a multi-line graph showing both clones and views.
    
    This function creates a line graph with two lines: one for clones
    and one for views. Each line has a different color and marker style.
    Includes a legend to distinguish between the two metrics.
    
    Args:
        dates: List of date strings in 'YYYY-MM-DD' format
        clones: List of clone counts corresponding to each date
        views: List of view counts corresponding to each date
        title: Title for the graph
        filename: Path where the graph image will be saved
        figsize: Figure size as (width, height) tuple (uses GRAPH_FIGSIZE_DAILY if None)
        
    Raises:
        SystemExit: If graph creation fails (GD007)
    """
    try:
        # Check if we have data to plot
        if not dates or not clones or not views:
            print(f"WARNING: No data for graph: {title}")
            return
        
        # Use configured figure size if not provided
        if figsize is None:
            figsize = GRAPH_FIGSIZE_DAILY
        
        # Convert date strings to datetime objects for plotting
        dates_dt = [datetime.strptime(d, '%Y-%m-%d') for d in dates]
        
        # Create a new figure with specified size from configuration
        plt.figure(figsize=figsize)
        
        # Plot clones data with configured color and circle markers
        plt.plot(dates_dt, clones, marker='o', linewidth=2, markersize=4, 
                 color=CLONES_COLOR, label='Clones')
        
        # Plot views data with configured color and square markers
        plt.plot(dates_dt, views, marker='s', linewidth=2, markersize=4, 
                 color=VIEWS_COLOR, label='Views')
        
        # Set title and axis labels with configured text color
        plt.title(title, fontsize=14, fontweight='bold', color=TEXT_COLOR)
        plt.xlabel('Date', fontsize=12, color=TEXT_COLOR)
        plt.ylabel('Count', fontsize=12, color=TEXT_COLOR)
        
        # Add legend in upper left corner
        plt.legend(loc='upper left', fontsize=10)
        
        # Add grid with configured color and transparency
        plt.grid(True, color=GRID_COLOR, alpha=0.3)
        
        # Format x-axis to show dates properly
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45, ha='right')
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Save the figure with configured DPI
        plt.savefig(filename, dpi=GRAPH_DPI, bbox_inches='tight')
        
        # Close the figure to free memory
        plt.close()
        
    except Exception as e:
        # ERROR_CODE: GD007 - Multi-line graph creation error
        print(f"ERROR_CODE: GD007 - Error creating graph {filename}: {e}", file=sys.stderr)
        sys.exit(1)


def create_downloads_graph(dates: List[str], series_by_key: Dict[str, List[int]],
                           title: str, ylabel: str, filename: str,
                           figsize: Tuple[int, int] = None,
                           release_dates: List[str] = None) -> None:
    """
    Create a multi-line graph of release downloads split by platform.

    Plots one line per entry in DOWNLOAD_SERIES (All, Windows, macOS, Linux),
    each with its own color and marker, plus a legend. Optionally annotates the
    x-axis with vertical markers at release publish dates, turning an unexplained
    download spike into "a release landed here".

    Args:
        dates: List of date strings in 'YYYY-MM-DD' format
        series_by_key: Dict mapping platform key (total/windows/macos/linux) to value lists
        title: Title for the graph
        ylabel: Label for the y-axis
        filename: Path where the graph image will be saved
        figsize: Figure size as (width, height) tuple (uses GRAPH_FIGSIZE_CUMULATIVE if None)
        release_dates: Optional list of 'YYYY-MM-DD' publish dates to mark with
            vertical lines (only those within the plotted date range are drawn)

    Raises:
        SystemExit: If graph creation fails (GD009)
    """
    try:
        # Check if we have data to plot
        if not dates:
            print(f"WARNING: No data for graph: {title}")
            return

        # Use configured figure size if not provided
        if figsize is None:
            figsize = GRAPH_FIGSIZE_CUMULATIVE

        # Convert date strings to datetime objects for plotting
        dates_dt = [datetime.strptime(d, '%Y-%m-%d') for d in dates]

        # Create a new figure with specified size from configuration
        plt.figure(figsize=figsize)

        # Plot one line per platform using the configured series styling
        for label, key, color, marker, linewidth in DOWNLOAD_SERIES:
            values = series_by_key.get(key, [])
            if not values:
                continue
            plt.plot(dates_dt, values, marker=marker, linewidth=linewidth,
                     markersize=4, color=color, label=label)

        # Mark release publish dates that fall within the plotted range
        if release_dates and dates_dt:
            lo, hi = dates_dt[0], dates_dt[-1]
            seen = set()
            labelled = False
            for rd in release_dates:
                try:
                    rd_dt = datetime.strptime(rd, '%Y-%m-%d')
                except (ValueError, TypeError):
                    continue
                if lo <= rd_dt <= hi and rd not in seen:
                    seen.add(rd)
                    plt.axvline(rd_dt, color='#9C27B0', linestyle='--', linewidth=0.8,
                                alpha=0.5, label='Release' if not labelled else None)
                    labelled = True

        # Set title and axis labels with configured text color
        plt.title(title, fontsize=14, fontweight='bold', color=TEXT_COLOR)
        plt.xlabel('Date', fontsize=12, color=TEXT_COLOR)
        plt.ylabel(ylabel, fontsize=12, color=TEXT_COLOR)

        # Add legend in upper left corner
        plt.legend(loc='upper left', fontsize=10)

        # Add grid with configured color and transparency
        plt.grid(True, color=GRID_COLOR, alpha=0.3)

        # Format x-axis to show dates properly
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45, ha='right')

        # Adjust layout to prevent label cutoff
        plt.tight_layout()

        # Save the figure with configured DPI
        plt.savefig(filename, dpi=GRAPH_DPI, bbox_inches='tight')

        # Close the figure to free memory
        plt.close()

    except Exception as e:
        # ERROR_CODE: GD009 - Downloads graph creation error
        print(f"ERROR_CODE: GD009 - Error creating downloads graph {filename}: {e}", file=sys.stderr)
        sys.exit(1)


def generate_repository_downloads_graphs(repo_name: str, downloads_daily: List[Dict[str, Any]],
                                         downloads_by_release: List[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Generate release-download graphs for a single repository.

    Creates two graphs (each split by platform: All, Windows, macOS, Linux):
    1. Daily downloads (DAILY_GRAPH_DAYS) - per-day downloads derived from snapshots,
       annotated with vertical markers at release publish dates
    2. Cumulative downloads (lifetime) - all-time running totals

    Args:
        repo_name: Full repository name (e.g., 'owner/repo')
        downloads_daily: List of downloads daily entries for the repository
        downloads_by_release: Optional per-release list (for publish-date markers)

    Returns:
        Dictionary mapping graph type to file path:
        - 'downloads_daily': Path to daily downloads graph
        - 'downloads_cumulative': Path to cumulative downloads graph
    """
    safe_repo_name = repo_name.replace('/', '_')
    graphs = {}

    # Release publish dates for annotating the daily graph
    release_dates = [
        (r.get('published_at') or '')[:10]
        for r in (downloads_by_release or [])
        if r.get('published_at')
    ]

    # 1. Daily downloads graph (uses DAILY_GRAPH_DAYS configuration)
    daily_dates, daily_series = get_downloads_daily(downloads_daily, DAILY_GRAPH_DAYS)
    if daily_dates:
        create_downloads_graph(
            daily_dates, daily_series,
            f'Daily Release Downloads ({DAILY_GRAPH_DAYS} Days) - {repo_name}',
            'Downloads',
            f'{GRAPHS_DIRECTORY}/{safe_repo_name}_downloads_daily_{DAILY_GRAPH_DAYS}d.png',
            figsize=GRAPH_FIGSIZE_DAILY,
            release_dates=release_dates
        )
        graphs['downloads_daily'] = f'{GRAPHS_DIRECTORY}/{safe_repo_name}_downloads_daily_{DAILY_GRAPH_DAYS}d.png'

    # 2. Cumulative downloads graph (lifetime)
    cumulative_dates, cumulative_series = get_downloads_cumulative(downloads_daily)
    if cumulative_dates:
        create_downloads_graph(
            cumulative_dates, cumulative_series,
            f'Cumulative Release Downloads (Lifetime) - {repo_name}',
            'Total Downloads',
            f'{GRAPHS_DIRECTORY}/{safe_repo_name}_downloads_cumulative.png',
            figsize=GRAPH_FIGSIZE_CUMULATIVE
        )
        graphs['downloads_cumulative'] = f'{GRAPHS_DIRECTORY}/{safe_repo_name}_downloads_cumulative.png'

    return graphs


def generate_repository_graphs(repo_name: str, daily_data: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Generate all required graphs for a single repository.
    
    This function creates up to six types of graphs based on configuration:
    1. Daily traffic (configurable days) - shows daily clones and views
    2. Weekly traffic (configurable weeks) - shows weekly aggregates
    3. Bi-weekly traffic (configurable periods) - shows bi-weekly aggregates
    4. Cumulative traffic - shows running totals of both metrics (if INCLUDE_CUMULATIVE_GRAPHS)
    5. Cumulative clones only - separate cumulative graph for clones (if INCLUDE_SEPARATE_CUMULATIVE)
    6. Cumulative views only - separate cumulative graph for views (if INCLUDE_SEPARATE_CUMULATIVE)
    
    Args:
        repo_name: Full repository name (e.g., 'owner/repo')
        daily_data: List of daily data entries for the repository
        
    Returns:
        Dictionary mapping graph type to file path:
        - 'daily_30d': Path to daily graph
        - 'weekly_3m': Path to weekly graph
        - 'biweekly_1y': Path to bi-weekly graph
        - 'cumulative': Path to cumulative graph (if enabled)
        - 'cumulative_clones': Path to cumulative clones graph (if enabled)
        - 'cumulative_views': Path to cumulative views graph (if enabled)
    """
    # Create a safe filename by replacing '/' with '_'
    safe_repo_name = repo_name.replace('/', '_')
    graphs = {}
    
    # 1. Generate daily traffic graph (uses DAILY_GRAPH_DAYS configuration)
    daily_dates, daily_clones, daily_views = get_daily_data(daily_data, DAILY_GRAPH_DAYS)
    
    if daily_dates:
        # Create multi-line graph with clones and views using DAILY_GRAPH_DAYS
        create_multi_line_graph(
            daily_dates, daily_clones, daily_views,
            f'Daily Traffic ({DAILY_GRAPH_DAYS} Days) - {repo_name}',
            f'{GRAPHS_DIRECTORY}/{safe_repo_name}_daily_{DAILY_GRAPH_DAYS}d.png',
            figsize=GRAPH_FIGSIZE_DAILY
        )
        # Store the graph filename
        graphs['daily'] = f'{GRAPHS_DIRECTORY}/{safe_repo_name}_daily_{DAILY_GRAPH_DAYS}d.png'
    
    # 2. Generate weekly traffic graph (uses WEEKLY_GRAPH_WEEKS configuration)
    weekly_dates, weekly_clones, weekly_views = get_weekly_data(daily_data, WEEKLY_GRAPH_WEEKS)
    
    if weekly_dates:
        # Create multi-line graph with clones and views using WEEKLY_GRAPH_WEEKS
        create_multi_line_graph(
            weekly_dates, weekly_clones, weekly_views,
            f'Weekly Traffic ({WEEKLY_GRAPH_WEEKS} Weeks) - {repo_name}',
            f'{GRAPHS_DIRECTORY}/{safe_repo_name}_weekly_{WEEKLY_GRAPH_WEEKS}m.png',
            figsize=GRAPH_FIGSIZE_WEEKLY
        )
        # Store the graph filename
        graphs['weekly'] = f'{GRAPHS_DIRECTORY}/{safe_repo_name}_weekly_{WEEKLY_GRAPH_WEEKS}m.png'
    
    # 3. Generate bi-weekly traffic graph (uses BIWEEKLY_GRAPH_PERIODS configuration)
    biweekly_dates, biweekly_clones, biweekly_views = get_biweekly_data(daily_data, BIWEEKLY_GRAPH_PERIODS)
    
    if biweekly_dates:
        # Create multi-line graph with clones and views using BIWEEKLY_GRAPH_PERIODS
        create_multi_line_graph(
            biweekly_dates, biweekly_clones, biweekly_views,
            f'Bi-Weekly Traffic ({BIWEEKLY_GRAPH_PERIODS} Periods) - {repo_name}',
            f'{GRAPHS_DIRECTORY}/{safe_repo_name}_biweekly_{BIWEEKLY_GRAPH_PERIODS}y.png',
            figsize=GRAPH_FIGSIZE_BIWEEKLY
        )
        # Store the graph filename
        graphs['biweekly'] = f'{GRAPHS_DIRECTORY}/{safe_repo_name}_biweekly_{BIWEEKLY_GRAPH_PERIODS}y.png'
    
    # 4. Generate cumulative (additive) traffic graph (if INCLUDE_CUMULATIVE_GRAPHS enabled)
    cumulative_dates, cumulative_clones, cumulative_views = get_cumulative_data(daily_data)
    
    if cumulative_dates and INCLUDE_CUMULATIVE_GRAPHS:
        # Create multi-line graph with cumulative clones and views
        create_multi_line_graph(
            cumulative_dates, cumulative_clones, cumulative_views,
            f'Cumulative Traffic (Lifetime) - {repo_name}',
            f'{GRAPHS_DIRECTORY}/{safe_repo_name}_cumulative.png',
            figsize=GRAPH_FIGSIZE_CUMULATIVE
        )
        # Store the graph filename
        graphs['cumulative'] = f'{GRAPHS_DIRECTORY}/{safe_repo_name}_cumulative.png'
    
    # 5. Generate cumulative clones only graph (if INCLUDE_SEPARATE_CUMULATIVE enabled)
    if cumulative_dates and INCLUDE_SEPARATE_CUMULATIVE:
        create_graph(
            cumulative_dates, cumulative_clones,
            f'Cumulative Clones (Lifetime) - {repo_name}',
            'Total Clones',
            f'{GRAPHS_DIRECTORY}/{safe_repo_name}_cumulative_clones.png',
            color=CLONES_COLOR,
            figsize=GRAPH_FIGSIZE_CUMULATIVE
        )
        # Store the graph filename
        graphs['cumulative_clones'] = f'{GRAPHS_DIRECTORY}/{safe_repo_name}_cumulative_clones.png'
    
    # 6. Generate cumulative views only graph (if INCLUDE_SEPARATE_CUMULATIVE enabled)
    if cumulative_dates and INCLUDE_SEPARATE_CUMULATIVE:
        create_graph(
            cumulative_dates, cumulative_views,
            f'Cumulative Views (Lifetime) - {repo_name}',
            'Total Views',
            f'{GRAPHS_DIRECTORY}/{safe_repo_name}_cumulative_views.png',
            color=VIEWS_COLOR,
            figsize=GRAPH_FIGSIZE_CUMULATIVE
        )
        # Store the graph filename
        graphs['cumulative_views'] = f'{GRAPHS_DIRECTORY}/{safe_repo_name}_cumulative_views.png'
    
    # Return dictionary of all generated graphs
    return graphs


def calculate_referrer_stats(referrers_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate referrer statistics from referrers data.
    
    This function processes referrer data to provide:
    - Total unique referrers
    - Referrers by count (sorted)
    - Total views from referrers
    - Total unique visitors from referrers
    
    Args:
        referrers_data: List of referrer entries from GitHub API
        
    Returns:
        Dictionary with referrer statistics including:
        - total_unique_referrers: Count of unique referrer sources
        - referrers_by_count: List of referrers sorted by total views
        - total_referrer_views: Sum of all views from referrers
        - total_referrer_uniques: Sum of all unique visitors from referrers
    """
    if not referrers_data:
        return {
            'total_unique_referrers': 0,
            'referrers_by_count': [],
            'total_referrer_views': 0,
            'total_referrer_uniques': 0
        }
    
    # Sort referrers by count (descending)
    referrers_sorted = sorted(referrers_data, key=lambda x: x.get('count', 0), reverse=True)
    
    # Calculate totals
    total_views = sum(r.get('count', 0) for r in referrers_data)
    total_uniques = sum(r.get('uniques', 0) for r in referrers_data)
    
    return {
        'total_unique_referrers': len(referrers_data),
        'referrers_by_count': referrers_sorted,
        'total_referrer_views': total_views,
        'total_referrer_uniques': total_uniques
    }


def calculate_repeat_vs_new_stats(daily_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """
    Calculate repeat visitors vs new visitors statistics.
    
    This function calculates:
    - Total views vs unique visitors for different time periods
    - Repeat visitors = Total views - Unique visitors
    - Shows engagement level and returning user behavior
    
    Args:
        daily_data: List of daily data entries
        
    Returns:
        Dictionary with statistics for different periods:
        - short_term: Last STATS_PERIOD_SHORT_TERM days
        - medium_term: Last STATS_PERIOD_MEDIUM_TERM days
        - lifetime: All available data
        Each period contains:
        - total_views: Total views in period
        - unique_visitors: Unique visitors in period
        - repeat_visitors: Repeat visitors (total - unique)
        - repeat_percentage: Percentage of repeat visitors
    """
    # Calculate for different periods
    stats_short = calculate_period_stats(daily_data, STATS_PERIOD_SHORT_TERM)
    stats_medium = calculate_period_stats(daily_data, STATS_PERIOD_MEDIUM_TERM)
    stats_lifetime = calculate_lifetime_stats(daily_data)
    
    def calculate_repeat_stats(stats: Dict[str, int]) -> Dict[str, Any]:
        """Calculate repeat visitor statistics from period stats."""
        total_views = stats.get('views_total', 0)
        unique_visitors = stats.get('views_unique', 0)
        repeat_visitors = total_views - unique_visitors
        
        # Calculate percentage (avoid division by zero)
        repeat_percentage = 0
        if total_views > 0:
            repeat_percentage = round((repeat_visitors / total_views) * 100, 1)
        
        return {
            'total_views': total_views,
            'unique_visitors': unique_visitors,
            'repeat_visitors': repeat_visitors,
            'repeat_percentage': repeat_percentage
        }
    
    return {
        'short_term': calculate_repeat_stats(stats_short),
        'medium_term': calculate_repeat_stats(stats_medium),
        'lifetime': calculate_repeat_stats(stats_lifetime)
    }


def calculate_repeat_vs_new_clones_stats(daily_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """
    Calculate repeat clones vs new clones statistics.

    This function calculates:
    - Total clones vs unique clones for different time periods
    - Repeat clones = Total clones - Unique clones
    - Shows repository adoption level and returning user behavior

    Args:
        daily_data: List of daily data entries

    Returns:
        Dictionary with statistics for different periods:
        - short_term: Last STATS_PERIOD_SHORT_TERM days
        - medium_term: Last STATS_PERIOD_MEDIUM_TERM days
        - lifetime: All available data
        Each period contains:
        - total_clones: Total clones in period
        - unique_clones: Unique clones in period
        - repeat_clones: Repeat clones (total - unique)
        - repeat_percentage: Percentage of repeat clones
    """
    # Calculate for different periods
    stats_short = calculate_period_stats(daily_data, STATS_PERIOD_SHORT_TERM)
    stats_medium = calculate_period_stats(daily_data, STATS_PERIOD_MEDIUM_TERM)
    stats_lifetime = calculate_lifetime_stats(daily_data)

    def calculate_repeat_clones_stats(stats: Dict[str, int]) -> Dict[str, Any]:
        """Calculate repeat clone statistics from period stats."""
        total_clones = stats.get('clones_total', 0)
        unique_clones = stats.get('clones_unique', 0)
        repeat_clones = total_clones - unique_clones

        # Calculate percentage (avoid division by zero)
        repeat_percentage = 0
        if total_clones > 0:
            repeat_percentage = round((repeat_clones / total_clones) * 100, 1)

        return {
            'total_clones': total_clones,
            'unique_clones': unique_clones,
            'repeat_clones': repeat_clones,
            'repeat_percentage': repeat_percentage
        }

    return {
        'short_term': calculate_repeat_clones_stats(stats_short),
        'medium_term': calculate_repeat_clones_stats(stats_medium),
        'lifetime': calculate_repeat_clones_stats(stats_lifetime)
    }


def generate_readme(history_data: Dict[str, Any]) -> None:
    """
    Generate the README.md file with statistics and embedded graphs.
    
    This function creates a comprehensive README.md that includes:
    - Dashboard title and description
    - Clickable index for quick navigation
    - Last updated timestamp
    - Per-repository sections with:
      - Clone statistics in table format (configurable periods)
      - Repeat vs New clone statistics
      - View statistics in table format (configurable periods)
      - Referrer statistics (total unique referrers, top referrers)
      - Repeat vs New visitor statistics
      - All generated graphs with descriptive titles and explanations
      - All generated graphs embedded as images
    
    Args:
        history_data: Dictionary containing the complete history data with
                      metadata and repositories sections
    """
    # Reference to user guide (this project's own published site)
    md = "See full Reference and Usage Guide at:\n"
    md += f"{DASHBOARD_GUIDE_URL}\n\n"
    md += (f"> This is a modified version of the original "
           f"[{UPSTREAM_NAME}]({UPSTREAM_URL}), "
           f"extended with platform-specific download statistics (Windows / macOS / Linux).\n\n")

    # Start with dashboard title and description
    md += "# \U0001f4ca GitHub Traffic & Downloads Dashboard\n\n"
    md += "This dashboard tracks historical traffic data (clones, views, and release downloads) for GitHub repositories.\n\n"
    
    # Add last updated timestamp if available
    if 'metadata' in history_data:
        metadata = history_data['metadata']
        last_updated = metadata.get('last_updated', 'Unknown')
        md += f"**Last Updated:** {last_updated}\n\n"
    
    # Add calculation rules section
    md += "## \U0001f4cb How Metrics Are Calculated\n\n"
    md += "This dashboard uses GitHub Traffic API data to calculate the following metrics:\n\n"
    md += "### \U0001f4ca Core Metrics\n\n"
    md += "**Views:**\n"
    md += "- Counted when someone visits the repository page\n"
    md += "- Includes page views from web browsers\n"
    md += "- Does not include visits via command-line tools or APIs\n\n"
    md += "**Clones:**\n"
    md += "- Counted when someone clones the repository\n"
    md += "- Includes clones via `git clone`, GitHub Desktop, download ZIP, and API\n"
    md += "- Can occur without a corresponding view event\n\n"
    md += "**Release Downloads:**\n"
    md += "- Counted when someone downloads a pre-compiled release asset (binary/installer)\n"
    md += "- Split by platform from the asset file name (Windows, macOS, Linux); **All** is the combined total\n"
    md += "- This is a **separate metric** from Clones - cloning the source is not a release download\n"
    md += "- **Lifetime** totals reflect all-time downloads (GitHub's cumulative `download_count`) and are accurate immediately\n"
    md += "- **Per-day** figures are derived by diffing daily snapshots, so they only accrue from the first tracked day onward\n\n"
    md += "**Important:** Views and Clones are **independent metrics**. Users can:\n"
    md += "- View without cloning\n"
    md += "- Clone without viewing (e.g., via `git clone` command)\n"
    md += "- Both view and clone\n\n"
    md += "### \U0001f522 Calculation Formulas\n\n"
    md += "**For any time period (short-term, medium-term, lifetime):**\n\n"
    md += "**Total Metrics:**\n"
    md += "- Total Views = Sum of daily views for the period\n"
    md += "- Total Clones = Sum of daily clones for the period\n\n"
    md += "**Unique Metrics:**\n"
    md += "- Unique Views = Sum of daily unique views for the period\n"
    md += "- Unique Clones = Sum of daily unique clones for the period\n"
    md += "  - Note: This sums daily unique counts, which may count the same user on multiple days\n\n"
    md += "**Repeat Metrics:**\n"
    md += "- Repeat Views = Total Views - Unique Views\n"
    md += "- Repeat Clones = Total Clones - Unique Clones\n"
    md += "- Repeat Percentage = (Repeat / Total) × 100\n\n"
    md += "**Example:**\n"
    md += "```\n"
    md += "If a repository has:\n"
    md +="- Total Views: 100\n"
    md += "- Unique Views: 20\n"
    md += "Then:\n"
    md += "- Repeat Views = 100 - 20 = 80\n"
    md += "- Repeat Percentage = (80 / 100) × 100 = 80%\n"
    md += "```\n\n"
    md += "### \U0001f4c8 Graph Data Aggregation\n\n"
    md += "**Daily Graphs:**\n"
    md += "- Shows raw daily data points\n"
    md += "- Each point represents one day's activity\n\n"
    md += "**Weekly Graphs:**\n"
    md += "- Aggregates daily data into 7-day periods\n"
    md += "- Each point represents the sum of 7 consecutive days\n\n"
    md += "**Bi-Weekly Graphs:**\n"
    md += "- Aggregates daily data into 14-day periods\n"
    md += "- Each point represents the sum of 14 consecutive days\n\n"
    md += "**Cumulative Graphs:**\n"
    md += "- Shows running totals over time\n"
    md += "- Each point represents the sum of all previous days plus current day\n\n"
    
    # Get all repositories from the history data
    repositories = history_data.get('repositories', {})
    
    # Get repository order from metadata if available (matches repos array in main.yml)
    repo_order = history_data.get('metadata', {}).get('repositories', list(repositories.keys()))
    
    # Generate clickable index for repositories
    if repositories:
        md += "## \U0001f4cb Table of Contents\n\n"
        md += "Quick navigation to repository statistics:\n\n"
        for repo_name in repo_order:
            if repo_name not in repositories:
                continue
            # Determine display name
            if SHOW_FULL_REPO_NAME:
                display_name = repo_name
            else:
                display_name = repo_name.split('/')[-1]
            # Create anchor link (replace spaces with hyphens, remove special chars)
            anchor = display_name.lower().replace(' ', '-').replace('_', '-')
            md += f"- [{display_name}](#{anchor})\n"
        md += "\n"
    
    # Process each repository in the order defined in metadata
    for repo_name in repo_order:
        if repo_name not in repositories:
            continue
        repo_data = repositories[repo_name]
        # Extract daily data and metadata for this repository
        daily_data = repo_data.get('daily_data', [])
        metadata = repo_data.get('metadata', {})
        referrers = repo_data.get('referrers', [])
        # Release-download data, if tracked
        downloads_section = repo_data.get('downloads', {})
        downloads_daily = downloads_section.get('daily_data', [])
        downloads_by_release = downloads_section.get('by_release', [])
        downloads_by_arch = downloads_section.get('by_arch', {})
        downloads_by_release_daily = downloads_section.get('by_release_daily', {})
        # Download stats (period + lifetime). Computed once here so the at-a-glance
        # funnel/momentum and the Release Downloads section share the same figures.
        dl_short = calculate_downloads_period_stats(downloads_daily, STATS_PERIOD_SHORT_TERM)
        dl_medium = calculate_downloads_period_stats(downloads_daily, STATS_PERIOD_MEDIUM_TERM)
        dl_lifetime = calculate_downloads_lifetime(downloads_daily)
        
        # Determine display name based on SHOW_FULL_REPO_NAME configuration
        if SHOW_FULL_REPO_NAME:
            display_name = repo_name
        else:
            # Extract only repository name (after the last '/')
            display_name = repo_name.split('/')[-1]
        
        # Create anchor for this repository
        anchor = display_name.lower().replace(' ', '-').replace('_', '-')
        
        # Add repository section header using configured header level
        header_prefix = '#' * README_HEADER_LEVEL
        md += f"{header_prefix} {display_name}\n\n"
        
        # Calculate statistics for different time periods using configuration
        # Short-term period (configurable via STATS_PERIOD_SHORT_TERM)
        stats_short = calculate_period_stats(daily_data, STATS_PERIOD_SHORT_TERM)
        # Medium-term period (configurable via STATS_PERIOD_MEDIUM_TERM)
        stats_medium = calculate_period_stats(daily_data, STATS_PERIOD_MEDIUM_TERM)
        # Lifetime (all available data)
        stats_lifetime = calculate_lifetime_stats(daily_data)
        
        # Calculate referrer statistics
        referrer_stats = calculate_referrer_stats(referrers)

        # Calculate repeat vs new visitor statistics
        repeat_stats = calculate_repeat_vs_new_stats(daily_data)

        # Calculate repeat vs new clone statistics
        repeat_clones_stats = calculate_repeat_vs_new_clones_stats(daily_data)

        # ---- At a glance: badges, tracking window, week-over-week momentum ----
        if INCLUDE_BADGES:
            md += render_badges(repo_name, dl_lifetime, stats_lifetime, len(downloads_by_release))

        first_active, active_days = compute_tracking_window(daily_data)
        if first_active:
            md += (f"*Tracking since **{first_active}** ({active_days} active "
                   f"day{'s' if active_days != 1 else ''}). Where the 90-day and "
                   f"Lifetime columns match the {STATS_PERIOD_SHORT_TERM}-day column, "
                   f"it is because only ~{active_days} days have been tracked so far.*\n\n")

        if INCLUDE_MOMENTUM:
            mom_clones = compute_momentum(daily_data, 'clones_total')
            mom_views = compute_momentum(daily_data, 'views_total')
            mom_downloads = compute_momentum(downloads_daily, 'downloads_total')
            md += "**This week vs last week:**\n\n"
            md += "| Metric | This week | Last week | Change |\n"
            md += "|--------|-----------|-----------|--------|\n"
            md += f"| Clones | {mom_clones['current']} | {mom_clones['previous']} | {_format_delta(mom_clones['delta_pct'])} |\n"
            md += f"| Views | {mom_views['current']} | {mom_views['previous']} | {_format_delta(mom_views['delta_pct'])} |\n"
            if downloads_daily:
                md += f"| Downloads | {mom_downloads['current']} | {mom_downloads['previous']} | {_format_delta(mom_downloads['delta_pct'])} |\n"
            md += "\n"

        # Add Clones section with emoji
        md += "### \U0001f5c5\ufe0f Clones\n\n"
        md += "*Repository clone statistics showing total and unique clones over different time periods.*\n\n"

        # Create professional table for clones statistics
        md += "| Period | Total | Unique |\n"
        md += "|--------|-------|--------|\n"
        md += f"| Last {STATS_PERIOD_SHORT_TERM} Days | {stats_short['clones_total']} | {stats_short['clones_unique']} |\n"
        md += f"| Last {STATS_PERIOD_MEDIUM_TERM} Days | {stats_medium['clones_total']} | {stats_medium['clones_unique']} |\n"
        md += f"| Lifetime | {stats_lifetime['clones_total']} | {stats_lifetime['clones_unique']} |\n\n"

        # Add Repeat vs New Clones section with emoji
        md += "### \U0001f4c4 Repeat vs New Clones\n\n"
        md += "*Analysis of repository adoption showing repeat clones vs new unique clones.*\n\n"
        md += "*Note: GitHub API does not provide geographical location data for cloners.*\n\n"

        # Create table for repeat vs new clone statistics
        md += "| Period | Total Clones | Unique Clones | Repeat Clones | Repeat % |\n"
        md += "|--------|--------------|----------------|----------------|----------|\n"
        md += f"| Last {STATS_PERIOD_SHORT_TERM} Days | {repeat_clones_stats['short_term']['total_clones']} | {repeat_clones_stats['short_term']['unique_clones']} | {repeat_clones_stats['short_term']['repeat_clones']} | {repeat_clones_stats['short_term']['repeat_percentage']}% |\n"
        md += f"| Last {STATS_PERIOD_MEDIUM_TERM} Days | {repeat_clones_stats['medium_term']['total_clones']} | {repeat_clones_stats['medium_term']['unique_clones']} | {repeat_clones_stats['medium_term']['repeat_clones']} | {repeat_clones_stats['medium_term']['repeat_percentage']}% |\n"
        md += f"| Lifetime | {repeat_clones_stats['lifetime']['total_clones']} | {repeat_clones_stats['lifetime']['unique_clones']} | {repeat_clones_stats['lifetime']['repeat_clones']} | {repeat_clones_stats['lifetime']['repeat_percentage']}% |\n\n"

        # Add Views section with emoji
        md += "### \U0001f440 Views\n\n"
        md += "*Repository view statistics showing total and unique views over different time periods.*\n\n"

        # Create professional table for views statistics
        md += "| Period | Total | Unique |\n"
        md += "|--------|-------|--------|\n"
        md += f"| Last {STATS_PERIOD_SHORT_TERM} Days | {stats_short['views_total']} | {stats_short['views_unique']} |\n"
        md += f"| Last {STATS_PERIOD_MEDIUM_TERM} Days | {stats_medium['views_total']} | {stats_medium['views_unique']} |\n"
        md += f"| Lifetime | {stats_lifetime['views_total']} | {stats_lifetime['views_unique']} |\n\n"

        # Add Engagement Ratios (views -> clones -> downloads), last short-term period.
        # Deliberately not called a "funnel": these are independent GitHub metrics,
        # and clones frequently exceed views (CI, mirrors, `git clone` without a page
        # view), so the ratio can exceed 100%.
        if INCLUDE_FUNNEL:
            funnel = compute_funnel(
                stats_short['views_total'], stats_short['clones_total'], dl_short['total'])
            md += "### \U0001f3af Engagement Ratios\n\n"
            md += (f"*How interest deepens over the last {STATS_PERIOD_SHORT_TERM} days. "
                   f"Views, clones and downloads are independent GitHub metrics, so this "
                   f"is not a strict per-user funnel - clones can exceed views (CI, "
                   f"mirrors, `git clone` without a page view), which shows up as a "
                   f"ratio above 100%.*\n\n")
            md += "| Stage | Count | Ratio to previous stage |\n"
            md += "|-------|-------|-------------------------|\n"
            md += f"| \U0001f440 Views | {funnel['views']} | — |\n"
            clone_rate = f"{funnel['clone_rate']}%" if funnel['clone_rate'] is not None else "—"
            dl_rate = f"{funnel['download_rate']}%" if funnel['download_rate'] is not None else "—"
            md += f"| \U0001f5c5️ Clones | {funnel['clones']} | {clone_rate} |\n"
            md += f"| \U0001f4e5 Downloads | {funnel['downloads']} | {dl_rate} |\n\n"

        # Add Referrers section with emoji
        md += "### \U0001f4de Referrers\n\n"
        md += "*Top referrer sources driving traffic to this repository.*\n\n"
        
        # Create table for referrer statistics
        md += f"**Total Unique Referrers:** {referrer_stats['total_unique_referrers']}\n\n"
        
        if referrer_stats['referrers_by_count']:
            md += "| Referrer | Total Views | Unique Visitors |\n"
            md += "|----------|-------------|----------------|\n"
            for ref in referrer_stats['referrers_by_count'][:10]:  # Show top 10
                referrer_name = ref.get('referrer', 'Unknown')
                count = ref.get('count', 0)
                uniques = ref.get('uniques', 0)
                md += f"| {referrer_name} | {count} | {uniques} |\n"
            md += "\n"
        else:
            md += "*No referrer data available.*\n\n"
        
        # Add Repeat vs New Visitors section with emoji
        md += "### \U0001f465 Repeat vs New Visitors\n\n"
        md += "*Analysis of visitor engagement showing repeat visitors vs new unique visitors.*\n\n"
        md += "*Note: GitHub API does not provide geographical location data for visitors.*\n\n"
        
        # Create table for repeat vs new visitor statistics
        md += "| Period | Total Views | Unique Visitors | Repeat Visitors | Repeat % |\n"
        md += "|--------|-------------|-----------------|-----------------|----------|\n"
        md += f"| Last {STATS_PERIOD_SHORT_TERM} Days | {repeat_stats['short_term']['total_views']} | {repeat_stats['short_term']['unique_visitors']} | {repeat_stats['short_term']['repeat_visitors']} | {repeat_stats['short_term']['repeat_percentage']}% |\n"
        md += f"| Last {STATS_PERIOD_MEDIUM_TERM} Days | {repeat_stats['medium_term']['total_views']} | {repeat_stats['medium_term']['unique_visitors']} | {repeat_stats['medium_term']['repeat_visitors']} | {repeat_stats['medium_term']['repeat_percentage']}% |\n"
        md += f"| Lifetime | {repeat_stats['lifetime']['total_views']} | {repeat_stats['lifetime']['unique_visitors']} | {repeat_stats['lifetime']['repeat_visitors']} | {repeat_stats['lifetime']['repeat_percentage']}% |\n\n"

        # Add Release Downloads section (table + per-platform graphs), if tracked.
        # dl_short / dl_medium / dl_lifetime were computed above for the funnel.
        if INCLUDE_DOWNLOADS and downloads_daily:
            md += "### \U0001f4e5 Release Downloads\n\n"
            md += "*Pre-compiled release-asset downloads, split by platform. This is separate from clones.*\n\n"
            md += "*Lifetime totals reflect all-time downloads (GitHub's cumulative counter). "
            md += "Per-day figures (Last 30/90 Days) are derived from daily snapshots and only accrue from the first tracked day onward.*\n\n"

            # Table: rows per platform, columns per period
            md += f"| Platform | Last {STATS_PERIOD_SHORT_TERM} Days | Last {STATS_PERIOD_MEDIUM_TERM} Days | Lifetime |\n"
            md += "|----------|-----------|-----------|----------|\n"
            md += f"| \U0001fa9f Windows | {dl_short['windows']} | {dl_medium['windows']} | {dl_lifetime['windows']} |\n"
            md += f"| \U0001f34e macOS | {dl_short['macos']} | {dl_medium['macos']} | {dl_lifetime['macos']} |\n"
            md += f"| \U0001f427 Linux | {dl_short['linux']} | {dl_medium['linux']} | {dl_lifetime['linux']} |\n"
            md += f"| **All** | **{dl_short['total']}** | **{dl_medium['total']}** | **{dl_lifetime['total']}** |\n\n"

            # Explain any gap between the All total and the per-platform sum
            unclassified = compute_unclassified(dl_lifetime)
            if unclassified > 0:
                md += (f"*ℹ️ {unclassified} lifetime download"
                       f"{'s' if unclassified != 1 else ''} are counted in **All** but "
                       f"matched no platform (the asset filename didn't match the "
                       f"Windows/macOS/Linux patterns).*\n\n")

            # Latest release callout (always shown, even at 0 downloads), if available
            latest_release = get_latest_release(downloads_by_release)
            if latest_release:
                lr_tag = latest_release.get('tag', '?')
                lr_downloads = latest_release.get('downloads', 0)
                lr_published = (latest_release.get('published_at') or '')[:10]
                lr_published_str = f" (published {lr_published})" if lr_published else ""
                md += (
                    f"\U0001f195 **Latest Release:** `{lr_tag}` - "
                    f"**{lr_downloads}** download{'s' if lr_downloads != 1 else ''}"
                    f"{lr_published_str}\n\n"
                )

            # Collapsed per-version download breakdown (newest first), if available.
            # Rendered as an HTML <details> block so it stays collapsed until clicked.
            breakdown_rows = get_release_breakdown(downloads_by_release)
            if breakdown_rows:
                md += "<details>\n"
                md += (
                    f"<summary><strong>\U0001f4e6 Per-version downloads</strong> "
                    f"({len(breakdown_rows)} releases - click to expand)</summary>\n\n"
                )
                md += "| Release | \U0001fa9f Windows | \U0001f34e macOS | \U0001f427 Linux | Total |\n"
                md += "|---------|-----------|----------|----------|-------|\n"
                for row in breakdown_rows:
                    md += (
                        f"| {row['tag']} | {row['windows']} | {row['macos']} | "
                        f"{row['linux']} | **{row['total']}** |\n"
                    )
                md += "\n</details>\n\n"

            # Architecture breakdown table (lifetime), if available
            if downloads_by_arch:
                os_rows = [('windows', '\U0001fa9f Windows'), ('macos', '\U0001f34e macOS'), ('linux', '\U0001f427 Linux')]
                # Determine which arch columns to show (union across OSes), in a stable order
                arch_order = ['arm64', 'x86_64', 'universal', 'other']
                present = set()
                for _os_key, _ in os_rows:
                    present.update((downloads_by_arch.get(_os_key) or {}).keys())
                cols = [a for a in arch_order if a in present]
                cols += sorted(c for c in present if c not in arch_order)

                if cols:
                    md += "**By Architecture (lifetime):**\n\n"
                    md += "*Lifetime downloads split by CPU architecture - useful for deciding which builds are still worth shipping.*\n\n"
                    md += "| Platform | " + " | ".join(cols) + " | Total |\n"
                    md += "|----------|" + "|".join(["-------"] * (len(cols) + 1)) + "|\n"
                    for os_key, os_label in os_rows:
                        row = downloads_by_arch.get(os_key) or {}
                        cells = [str(row.get(c, 0)) for c in cols]
                        row_total = sum(row.get(c, 0) for c in row)
                        md += f"| {os_label} | " + " | ".join(cells) + f" | **{row_total}** |\n"
                    md += "\n"

                    # Pruning hint: flag OS/arch builds with a negligible lifetime share
                    total_dl = dl_lifetime.get('total', 0)
                    if total_dl > 0:
                        low = []
                        for os_key, os_label in os_rows:
                            row = downloads_by_arch.get(os_key) or {}
                            for arch, cnt in sorted(row.items()):
                                share = cnt / total_dl * 100
                                if 0 < share < 2:
                                    low.append(f"{os_label} {arch} ({cnt}, {share:.1f}%)")
                        if low:
                            md += ("*\U0001f4a1 Low-volume builds (<2% of lifetime downloads), "
                                   "candidates to stop shipping: " + "; ".join(low) + ".*\n\n")

            # Top releases by downloads table (lifetime), if available
            if downloads_by_release:
                top_releases = sorted(
                    (r for r in downloads_by_release if r.get('downloads', 0) > 0),
                    key=lambda r: r.get('downloads', 0),
                    reverse=True
                )[:TOP_RELEASES_COUNT]
                if top_releases:
                    md += f"**Top {len(top_releases)} Releases by Downloads (lifetime):**\n\n"
                    md += "| Release | Downloads | Published |\n"
                    md += "|---------|-----------|-----------|\n"
                    for r in top_releases:
                        tag = r.get('tag', '?')
                        downloads = r.get('downloads', 0)
                        published = (r.get('published_at') or '')[:10]
                        md += f"| {tag} | {downloads} | {published} |\n"
                    md += "\n"

            # Recent release reception (early-life adoption), once per-release daily
            # snapshots have started accruing (by_release_daily from merge_history).
            reception_rows = compute_release_reception(downloads_by_release_daily)
            if reception_rows:
                md += f"**Recent Release Reception (first ~{RELEASE_RECEPTION_WINDOW_DAYS} days):**\n\n"
                md += (f"*Downloads accrued per release since it was first tracked. Measured "
                       f"over each release's own early-life window, so a brand-new release "
                       f"isn't unfairly compared against a mature one. Only releases published "
                       f"within ~{RELEASE_RECEPTION_WINDOW_DAYS} days appear; this accrues over "
                       f"time and cannot be backfilled.*\n\n")
                md += "| Release | Published | Tracked | \U0001fa9f | \U0001f34e | \U0001f427 | Downloads (tracked) |\n"
                md += "|---------|-----------|---------|----|----|----|---------------------|\n"
                for r in reception_rows:
                    md += (f"| {r['tag']} | {r['published']} | {r['tracked_days']}d | "
                           f"{r['accrued_windows']} | {r['accrued_macos']} | {r['accrued_linux']} | "
                           f"**{r['accrued']}** |\n")
                md += "\n"

            # Legacy: embed static download PNG graphs (only when INCLUDE_GRAPHS)
            if INCLUDE_GRAPHS:
                print(f"Generating download graphs for {repo_name}...")
                dl_graphs = generate_repository_downloads_graphs(repo_name, downloads_daily, downloads_by_release)

                if 'downloads_daily' in dl_graphs:
                    md += f"#### Daily Release Downloads ({DAILY_GRAPH_DAYS} Days)\n\n"
                    md += f"*Per-day downloads for the last {DAILY_GRAPH_DAYS} days, by platform. Useful for spotting download spikes after new releases.*\n\n"
                    md += f"![Daily Downloads {DAILY_GRAPH_DAYS} Days]({dl_graphs['downloads_daily']})\n\n"

                if 'downloads_cumulative' in dl_graphs:
                    md += "#### Cumulative Release Downloads (Lifetime)\n\n"
                    md += "*All-time running download totals by platform. Useful for seeing overall adoption per platform.*\n\n"
                    md += f"![Cumulative Downloads]({dl_graphs['downloads_cumulative']})\n\n"

        # Charts: interactive (linked) or legacy static PNGs (embedded)
        if INCLUDE_GRAPHS:
            # Generate and embed static traffic PNG graphs
            print(f"Generating graphs for {repo_name}...")
            graphs = generate_repository_graphs(repo_name, daily_data)

            md += "### \U0001f4c8 Traffic Graphs\n\n"
            md += "*Visual representations of traffic trends over different time periods.*\n\n"

            if 'daily' in graphs:
                md += f"#### Daily Traffic ({DAILY_GRAPH_DAYS} Days)\n\n"
                md += f"*Shows daily clones and views trends for the last {DAILY_GRAPH_DAYS} days. Useful for identifying short-term patterns and recent activity spikes.*\n\n"
                md += f"![Daily {DAILY_GRAPH_DAYS} Days]({graphs['daily']})\n\n"

            if 'weekly' in graphs:
                md += f"#### Weekly Traffic ({WEEKLY_GRAPH_WEEKS} Weeks)\n\n"
                md += f"*Shows weekly aggregated clones and views for the last {WEEKLY_GRAPH_WEEKS} weeks (~3 months). Useful for identifying medium-term trends and seasonal patterns.*\n\n"
                md += f"![Weekly {WEEKLY_GRAPH_WEEKS} Weeks]({graphs['weekly']})\n\n"

            if 'biweekly' in graphs:
                md += f"#### Bi-Weekly Traffic ({BIWEEKLY_GRAPH_PERIODS} Periods)\n\n"
                md += f"*Shows bi-weekly aggregated clones and views for the last {BIWEEKLY_GRAPH_PERIODS} periods (~1 year). Useful for identifying long-term trends and yearly patterns.*\n\n"
                md += f"![Bi-Weekly {BIWEEKLY_GRAPH_PERIODS} Periods]({graphs['biweekly']})\n\n"

            if 'cumulative' in graphs and INCLUDE_CUMULATIVE_GRAPHS:
                md += "#### Cumulative Traffic (Lifetime)\n\n"
                md += "*Shows running totals of both clones and views over the entire lifetime of tracking. Useful for seeing overall growth and total adoption.*\n\n"
                md += f"![Cumulative]({graphs['cumulative']})\n\n"

            if 'cumulative_clones' in graphs and 'cumulative_views' in graphs and INCLUDE_SEPARATE_CUMULATIVE:
                md += "#### Separate Cumulative Graphs\n\n"
                md += "*Individual cumulative graphs for clones and views, allowing for easier comparison between the two metrics.*\n\n"
                md += f"**Cumulative Clones:**\n\n"
                md += f"![Cumulative Clones]({graphs['cumulative_clones']})\n\n"
                md += f"**Cumulative Views:**\n\n"
                md += f"![Cumulative Views]({graphs['cumulative_views']})\n\n"
        elif INCLUDE_CHARTS:
            # Interactive charts can't run in GitHub's README (no JS), so link to
            # the JS-rendered dashboard page instead of embedding static images.
            md += "### \U0001f4c8 Interactive Charts\n\n"
            md += ("*Clones/views and per-platform download charts - with hover tooltips, "
                   "dark mode, and release-date markers - are rendered live on the dashboard "
                   "page (GitHub can't run the charts inside this README):*\n\n")
            md += f"\U0001f4ca **[Open the interactive dashboard →]({CHARTS_PAGE_URL}#{anchor})**\n\n"

        # Add horizontal separator between repositories
        md += "---\n\n"
    
    # Add footer with automation note
    md += "*This dashboard is automatically updated daily using GitHub Actions.*\n"
    
    # Save the generated README.md using configured path
    save_file(md, README_FILE_PATH)


def _trim_leading_zeros(dates: List[str], *series: List[int]) -> Tuple[List[str], List[List[int]]]:
    """
    Drop leading entries where every series is zero.

    The cumulative traffic series is zero-filled back ~a year, so it carries
    hundreds of all-zero leading points that never change. Trimming them keeps
    the chart focused on real activity and shrinks the hourly chart-data.json diff.
    Always keeps at least the final point so a chart is never emptied.
    """
    start = 0
    for i in range(len(dates)):
        if any(s[i] for s in series):
            start = i
            break
    else:
        start = max(0, len(dates) - 1)  # all zero: keep just the last point
    return dates[start:], [list(s[start:]) for s in series]


def build_chart_data(history_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assemble the time-series payload consumed by the interactive dashboard page.

    Reuses the same extraction helpers that fed the matplotlib graphs, so the
    interactive charts plot exactly the series the PNGs used to: daily/weekly/
    bi-weekly/cumulative traffic, plus per-platform daily/cumulative downloads
    and release publish dates (for vertical markers).

    Args:
        history_data: The full history.json structure.

    Returns:
        A JSON-serializable dict: {'generated_at', 'repositories': [ ... ]}.
    """
    repositories = history_data.get('repositories', {})
    repo_order = history_data.get('metadata', {}).get('repositories', list(repositories.keys()))

    repos_out = []
    for repo_name in repo_order:
        if repo_name not in repositories:
            continue
        repo_data = repositories[repo_name]
        daily_data = repo_data.get('daily_data', [])
        downloads_section = repo_data.get('downloads', {})
        downloads_daily = downloads_section.get('daily_data', [])
        downloads_by_release = downloads_section.get('by_release', [])
        display = repo_name if SHOW_FULL_REPO_NAME else repo_name.split('/')[-1]

        d_dates, d_clones, d_views = get_daily_data(daily_data, DAILY_GRAPH_DAYS)
        w_dates, w_clones, w_views = get_weekly_data(daily_data, WEEKLY_GRAPH_WEEKS)
        b_dates, b_clones, b_views = get_biweekly_data(daily_data, BIWEEKLY_GRAPH_PERIODS)
        c_dates, c_clones, c_views = get_cumulative_data(daily_data)
        # Trim the long zero-filled lead-in so the cumulative chart (and the
        # committed JSON diff) only spans days with real activity.
        c_dates, (c_clones, c_views) = _trim_leading_zeros(c_dates, c_clones, c_views)

        dl_d_dates, dl_d_series = get_downloads_daily(downloads_daily, DAILY_GRAPH_DAYS)
        dl_c_dates, dl_c_series = get_downloads_cumulative(downloads_daily)

        release_markers = [
            {'date': (r.get('published_at') or '')[:10], 'tag': r.get('tag', '')}
            for r in downloads_by_release if r.get('published_at')
        ]

        repos_out.append({
            'name': repo_name,
            'display': display,
            'anchor': display.lower().replace(' ', '-').replace('_', '-'),
            'traffic': {
                'daily': {'dates': d_dates, 'clones': d_clones, 'views': d_views},
                'weekly': {'dates': w_dates, 'clones': w_clones, 'views': w_views},
                'biweekly': {'dates': b_dates, 'clones': b_clones, 'views': b_views},
                'cumulative': {'dates': c_dates, 'clones': c_clones, 'views': c_views},
            },
            'downloads': {
                'has_data': bool(downloads_daily),
                'daily': dict({'dates': dl_d_dates}, **dl_d_series),
                'cumulative': dict({'dates': dl_c_dates}, **dl_c_series),
                'releases': release_markers,
            },
            'config': {
                'daily_days': DAILY_GRAPH_DAYS,
                'weekly_weeks': WEEKLY_GRAPH_WEEKS,
                'biweekly_periods': BIWEEKLY_GRAPH_PERIODS,
            },
        })

    return {
        'generated_at': history_data.get('metadata', {}).get('last_updated', ''),
        'repositories': repos_out,
    }


def write_chart_data(history_data: Dict[str, Any]) -> None:
    """Write the interactive chart payload to CHART_DATA_PATH (creating its dir)."""
    data = build_chart_data(history_data)
    out_dir = os.path.dirname(CHART_DATA_PATH)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    save_file(json.dumps(data, indent=2), CHART_DATA_PATH)
    print(f"Wrote chart data to {CHART_DATA_PATH}")


def main():
    """
    Main function to generate the GitHub traffic dashboard.
    
    This function orchestrates the entire dashboard generation process:
    1. Loads historical data from configured HISTORY_FILE_PATH
    2. Validates the data structure
    3. Prepares the graphs directory using GRAPHS_DIRECTORY
    4. Generates all graphs and statistics using configuration
    5. Updates README.md using configured README_FILE_PATH
    
    Raises:
        SystemExit: If any step fails (various error codes)
    """
    # Print start message
    print("Starting dashboard generation...")
    
    # Load the history data from configured HISTORY_FILE_PATH
    print(f"Loading {HISTORY_FILE_PATH}...")
    history_data = load_json_file(HISTORY_FILE_PATH)
    
    # Validate that the history data has the required structure
    # ERROR_CODE: GD008 - Missing repositories key
    if 'repositories' not in history_data:
        print("ERROR_CODE: GD008 - history.json missing 'repositories' key", file=sys.stderr)
        sys.exit(1)
    
    # Ensure the graphs directory exists (only needed for legacy PNG graphs)
    if INCLUDE_GRAPHS:
        prepare_graphs_directory()

    # Write the interactive chart-data JSON consumed by dashboard.html
    if INCLUDE_CHARTS:
        write_chart_data(history_data)

    # Generate README.md with all statistics and embedded graphs
    print(f"Generating {README_FILE_PATH} with graphs...")
    generate_readme(history_data)
    
    # Print completion message
    print("Dashboard generation completed successfully")


# Entry point: Run main() if this script is executed directly
if __name__ == '__main__':
    main()
