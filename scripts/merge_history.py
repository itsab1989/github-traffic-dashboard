#!/usr/bin/env python3
"""
Merge new traffic data with existing history.json file.

This script is responsible for merging newly fetched traffic data with the
existing historical data. It ensures:
- Zero-filling for missing dates
- Proper deduplication (new data takes precedence)
- Recalculation of totals
- Maintenance of the standard structured format
- Recovery from server downtime (missed workflow runs)

## Server Downtime Handling

The GitHub Traffic API provides data for the last 14 days. This means:
1. If the workflow misses a day (e.g., server down on day 1), the next run on day 2
   will still fetch day 1's data from the API
2. The merge script properly integrates this data, filling in the gaps
3. Zero-filling ensures no dates are missing in the historical record
4. Up to 14 consecutive days can be recovered without data loss

## Calendar Edge Cases

The script handles:
- Year transitions (Dec 31 -> Jan 1)
- Leap years (Feb 29)
- Month boundaries
- All date calculations use UTC timezone for consistency

Error codes: MH001-007
"""

# ============================================================================
# CONFIGURATION SECTION - MODIFY THESE PARAMETERS FOR YOUR NEEDS
# ============================================================================

# File Paths Configuration
# These are the default paths, but can be overridden via command-line arguments
DEFAULT_HISTORY_FILE = "history.json"           # Path to existing historical data
DEFAULT_NEW_DATA_FILE = "traffic_data.json"     # Path to newly fetched data
DEFAULT_OUTPUT_FILE = "merged_history.json"     # Path for merged output

# ============================================================================
# END OF CONFIGURATION SECTION
# The following settings typically do not need modification
# ============================================================================

# Note: The following behaviors are hardcoded and always active:
# - Zero-filling: Always enabled, fills missing dates with zeros for 365 days
# - Data merging: New data always overwrites existing data for the same date
# - Metadata: Uses new metadata if available, otherwise keeps existing metadata
# - Totals: Always recalculated from merged data
# - Data retention: All historical data is retained indefinitely
# - Timezone: All operations use UTC
# - Date format: All dates use YYYY-MM-DD format
# - DateTime format: All timestamps use ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
# ============================================================================

# Standard library imports
import json  # For JSON file operations
import sys   # For system exit and error handling

# Date and time handling
from datetime import datetime, timedelta  # For date calculations

# Type hints for better code documentation
from typing import Dict, List, Any  # For type annotations


def load_json_file(filepath: str) -> Dict[str, Any]:
    """
    Load a JSON file from disk with comprehensive error handling.
    
    Args:
        filepath: Path to the JSON file to load
        
    Returns:
        Dictionary containing the parsed JSON data
        
    Raises:
        SystemExit: If file not found (MH001), invalid JSON (MH002), or other error (MH003)
    """
    try:
        # Open and read the JSON file
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # ERROR_CODE: MH001 - File not found
        print(f"ERROR_CODE: MH001 - File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        # ERROR_CODE: MH002 - Invalid JSON format
        print(f"ERROR_CODE: MH002 - Invalid JSON in {filepath}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # ERROR_CODE: MH003 - General load error
        print(f"ERROR_CODE: MH003 - Error loading {filepath}: {e}", file=sys.stderr)
        sys.exit(1)


def save_json_file(data: Dict[str, Any], filepath: str) -> None:
    """
    Save JSON data to a file with error handling.
    
    Args:
        data: Dictionary containing the data to save
        filepath: Path where the JSON file should be saved
        
    Raises:
        SystemExit: If file cannot be saved (MH004)
    """
    try:
        # Open the file in write mode and save the data with indentation
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        # ERROR_CODE: MH004 - File save error
        print(f"ERROR_CODE: MH004 - Error saving to {filepath}: {e}", file=sys.stderr)
        sys.exit(1)


def zero_fill_daily_data(daily_data: List[Dict[str, Any]], days_back: int = 365) -> List[Dict[str, Any]]:
    """
    Zero-fill daily data for missing dates.
    
    This function ensures that all dates from (today - days_back) to today
    are present in the data. Missing dates are filled with zero values.
    This is important for accurate graph generation and statistics.
    
    Args:
        daily_data: List of daily data entries (may have gaps)
        days_back: Number of days to look back from today (default: 365)
        
    Returns:
        List of daily data entries with all dates filled (no gaps)
    """
    # Return empty list if no data provided
    if not daily_data:
        return []
    
    # Calculate the date range
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=days_back)
    
    # Create a dictionary of existing data for fast lookup
    data_dict = {}
    for entry in daily_data:
        date_str = entry.get('date')
        if date_str:
            data_dict[date_str] = entry
    
    # Generate all dates and fill missing ones with zeros
    filled_data = []
    current_date = start_date
    
    # Iterate through each date in the range
    while current_date <= today:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Use existing data if available, otherwise create zero-filled entry
        if date_str in data_dict:
            filled_data.append(data_dict[date_str])
        else:
            filled_data.append({
                'date': date_str,
                'clones_total': 0,
                'clones_unique': 0,
                'views_total': 0,
                'views_unique': 0
            })
        
        # Move to the next day
        current_date += timedelta(days=1)
    
    return filled_data


def merge_daily_data(existing_data: List[Dict[str, Any]], new_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge existing daily data with new daily data.
    
    This function combines two sets of daily data, with new data taking
    precedence over existing data for the same date. This ensures that
    the most recent data is always used.
    
    ## Server Downtime Recovery
    
    When the workflow misses days (e.g., server down):
    1. The GitHub API provides the last 14 days of data in new_data
    2. This includes the missed days that weren't in existing_data
    3. The merge adds these missed days to the dataset
    4. For overlapping dates, new_data (from API) takes precedence
    
    Example:
    - Existing: [2026-04-10, 2026-04-11]
    - Missed: 2026-04-12 (server down)
    - New API data: [2026-04-11, 2026-04-12, 2026-04-13]
    - Result: [2026-04-10, 2026-04-11, 2026-04-12, 2026-04-13]
    
    Args:
        existing_data: List of existing daily data entries (may have gaps)
        new_data: List of new daily data entries from API (last 14 days)
        
    Returns:
        List of merged daily data entries, sorted by date
    """
    # Create a dictionary to hold merged data
    # Using a dictionary ensures no duplicate dates
    merged_dict = {}
    
    # Add existing data to the dictionary
    # This preserves all historical data we already have
    for entry in existing_data:
        date_str = entry.get('date')
        if date_str:
            merged_dict[date_str] = entry
    
    # Add/overwrite with new data (new takes precedence)
    # This ensures API data (most recent) is used for overlapping dates
    # Also adds any dates that were missing (server downtime recovery)
    for entry in new_data:
        date_str = entry.get('date')
        if date_str:
            merged_dict[date_str] = entry
    
    # Sort the merged data by date
    # Sorting ensures chronological order for graphs and statistics
    sorted_data = sorted(merged_dict.values(), key=lambda x: x.get('date', ''))
    
    return sorted_data


def calculate_totals(daily_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Calculate total statistics from daily data.
    
    This function sums up all clones and views across the entire
    daily data set to provide lifetime totals.
    
    Args:
        daily_data: List of daily data entries
        
    Returns:
        Dictionary with keys: clones_total, clones_unique_total, views_total, views_unique_total
    """
    # Initialize totals to zero
    totals = {
        'clones_total': 0,
        'clones_unique_total': 0,
        'views_total': 0,
        'views_unique_total': 0
    }
    
    # Sum up values from all daily entries
    for entry in daily_data:
        totals['clones_total'] += entry.get('clones_total', 0)
        totals['clones_unique_total'] += entry.get('clones_unique', 0)
        totals['views_total'] += entry.get('views_total', 0)
        totals['views_unique_total'] += entry.get('views_unique', 0)
    
    return totals


# Platforms tracked for release downloads.
# "total" is the grand total across all assets (matched or not); the others are
# the per-platform sums. Keys map to fields named cumulative_<platform> and
# downloads_<platform> in the downloads daily_data entries.
DOWNLOAD_PLATFORMS = ['total', 'windows', 'macos', 'linux']


def _cumulative_snapshot(entry: Dict[str, Any]) -> Dict[str, int]:
    """Extract the per-platform cumulative counts from a downloads entry."""
    return {
        f'cumulative_{p}': int(entry.get(f'cumulative_{p}', 0) or 0)
        for p in DOWNLOAD_PLATFORMS
    }


def merge_downloads(existing_downloads: Dict[str, Any], new_downloads: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge release-download snapshots and (re)compute per-day download deltas.

    ## Why this differs from clones/views

    The GitHub Releases API reports download_count as a CUMULATIVE, all-time
    counter per asset - it is not a rolling 14-day window. Each workflow run
    therefore records a snapshot of the per-platform cumulative totals, and this
    function derives per-day downloads as the difference between consecutive
    snapshots.

    ## Behavior

    - The new snapshot (today's cumulative totals) takes precedence for its date.
    - A continuous, date-sorted series is built from the first snapshot to the
      latest. Days with no snapshot carry the previous cumulative value forward
      and record a daily delta of 0 (no observed change).
    - Daily delta = max(0, cumulative_today - cumulative_previous). Negative
      deltas (e.g. a release or asset was deleted) are clamped to 0.
    - The first entry has a daily delta of 0 because there is no prior baseline.

    ## Data availability

    Lifetime totals are accurate immediately (the cumulative counter already
    reflects all-time downloads). Per-day figures only exist from the first
    snapshot onward - GitHub does not expose historical per-day download data.

    Args:
        existing_downloads: Existing downloads section ({daily_data, metadata}) or {}
        new_downloads: Newly fetched snapshot ({date, cumulative_*, last_fetched}) or {}

    Returns:
        Dictionary with 'daily_data' (per-day deltas + cumulative snapshots) and
        'metadata' (latest cumulative totals).
    """
    existing_downloads = existing_downloads or {}
    new_downloads = new_downloads or {}

    # Index existing cumulative snapshots by date
    by_date: Dict[str, Dict[str, int]] = {}
    for entry in existing_downloads.get('daily_data', []):
        date_str = entry.get('date')
        if date_str:
            by_date[date_str] = _cumulative_snapshot(entry)

    # Overlay the new snapshot (new data takes precedence for its date)
    new_date = new_downloads.get('date')
    if new_date:
        by_date[new_date] = _cumulative_snapshot(new_downloads)

    # Nothing to merge yet (e.g. first ever run before any snapshot exists)
    if not by_date:
        return {'daily_data': [], 'metadata': {}}

    # Build a continuous daily series from the first to the last snapshot,
    # carrying cumulative values forward across missing days.
    sorted_dates = sorted(by_date.keys())
    start = datetime.strptime(sorted_dates[0], '%Y-%m-%d').date()
    end = datetime.strptime(sorted_dates[-1], '%Y-%m-%d').date()

    daily_data: List[Dict[str, Any]] = []
    prev_cumulative = None
    last_known = by_date[sorted_dates[0]]
    current_date = start

    while current_date <= end:
        date_str = current_date.strftime('%Y-%m-%d')

        # Use a fresh snapshot if one exists for this date, else carry forward
        if date_str in by_date:
            last_known = by_date[date_str]

        entry: Dict[str, Any] = {'date': date_str}
        for p in DOWNLOAD_PLATFORMS:
            cumulative_key = f'cumulative_{p}'
            cumulative_value = last_known[cumulative_key]
            entry[cumulative_key] = cumulative_value

            if prev_cumulative is None:
                # No prior baseline for the very first day
                entry[f'downloads_{p}'] = 0
            else:
                # Clamp negative deltas (deleted releases/assets) to 0
                entry[f'downloads_{p}'] = max(0, cumulative_value - prev_cumulative[cumulative_key])

        daily_data.append(entry)
        prev_cumulative = {f'cumulative_{p}': entry[f'cumulative_{p}'] for p in DOWNLOAD_PLATFORMS}
        current_date += timedelta(days=1)

    # Metadata reflects the latest cumulative totals (true lifetime figures)
    latest = daily_data[-1]
    metadata = {
        'last_fetched': new_downloads.get(
            'last_fetched',
            existing_downloads.get('metadata', {}).get('last_fetched', '')
        ),
    }
    for p in DOWNLOAD_PLATFORMS:
        metadata[f'cumulative_{p}'] = latest[f'cumulative_{p}']

    return {'daily_data': daily_data, 'metadata': metadata}


def merge_repositories(existing_repos: Dict[str, Any], new_repos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge repository data from existing and new data sources.
    
    This function merges data for all repositories, combining daily data,
    referrers, and metadata. It ensures zero-filling and recalculates totals.
    
    Args:
        existing_repos: Dictionary of existing repository data
        new_repos: Dictionary of new repository data to merge
        
    Returns:
        Dictionary of merged repository data
    """
    # Initialize merged repositories dictionary
    merged_repos = {}
    
    # Get all repository names from both sources
    all_repos = set(existing_repos.keys()) | set(new_repos.keys())
    
    # Process each repository
    for repo_name in all_repos:
        # Get existing and new data for this repository
        existing_repo = existing_repos.get(repo_name, {})
        new_repo = new_repos.get(repo_name, {})
        
        # Merge daily data from both sources
        existing_daily = existing_repo.get('daily_data', [])
        new_daily = new_repo.get('daily_data', [])
        
        # Merge daily data (new takes precedence)
        merged_daily = merge_daily_data(existing_daily, new_daily)
        
        # Zero-fill the merged data to ensure no gaps
        zero_filled_daily = zero_fill_daily_data(merged_daily)
        
        # Recalculate totals from the zero-filled data
        calculated_totals = calculate_totals(zero_filled_daily)
        
        # Use metadata from new data if available, otherwise from existing
        metadata = new_repo.get('metadata', existing_repo.get('metadata', {}))
        
        # Update metadata with recalculated totals
        metadata.update(calculated_totals)
        
        # Use referrers from new data if available, otherwise from existing
        referrers = new_repo.get('referrers', existing_repo.get('referrers', []))

        # Merge release-download snapshots and recompute per-day deltas.
        # download_count is cumulative, so this diffs consecutive snapshots
        # rather than summing daily values like clones/views.
        merged_downloads = merge_downloads(
            existing_repo.get('downloads', {}),
            new_repo.get('downloads', {})
        )

        # Store the merged repository data
        merged_repos[repo_name] = {
            'daily_data': zero_filled_daily,
            'referrers': referrers,
            'metadata': metadata,
            'downloads': merged_downloads
        }

    return merged_repos


def main():
    """
    Main function to merge traffic data with history.
    
    This function:
    1. Validates command-line arguments
    2. Loads new traffic data and existing history
    3. Validates data structures
    4. Merges repository data
    5. Saves the merged data
    
    Usage:
        python merge_history.py <new_data_file> <history_file> <output_file>
        
    Raises:
        SystemExit: If any step fails (various error codes)
    """
    # Validate command-line arguments
    # ERROR_CODE: MH005 - Wrong number of arguments
    if len(sys.argv) != 4:
        print("ERROR_CODE: MH005 - Usage: merge_history.py <new_data_file> <history_file> <output_file>", file=sys.stderr)
        sys.exit(1)
    
    # Extract file paths from arguments
    new_data_file = sys.argv[1]
    history_file = sys.argv[2]
    output_file = sys.argv[3]
    
    # Load new traffic data
    print(f"Loading new data from: {new_data_file}")
    new_data = load_json_file(new_data_file)
    
    # Load existing history data
    print(f"Loading history from: {history_file}")
    history_data = load_json_file(history_file)
    
    # Validate that new data has the required structure
    # ERROR_CODE: MH006 - New data missing repositories key
    if 'repositories' not in new_data:
        print("ERROR_CODE: MH006 - New data missing 'repositories' key", file=sys.stderr)
        sys.exit(1)
    
    # Validate that history data has the required structure
    # ERROR_CODE: MH007 - History data missing repositories key
    if 'repositories' not in history_data:
        print("ERROR_CODE: MH007 - History data missing 'repositories' key", file=sys.stderr)
        sys.exit(1)
    
    # Merge repository data from both sources
    print("Merging repository data...")
    merged_repos = merge_repositories(history_data['repositories'], new_data['repositories'])
    
    # Preserve repository order from new_data if available, otherwise use existing order
    # This ensures the order matches the repos array in main.yml
    if 'repositories' in new_data.get('metadata', {}):
        repo_order = new_data['metadata']['repositories']
    elif 'repositories' in history_data.get('metadata', {}):
        repo_order = history_data['metadata']['repositories']
    else:
        repo_order = sorted(list(merged_repos.keys()))
    
    # Create the merged data structure with updated metadata
    merged_data = {
        'metadata': {
            'generated_at': new_data.get('metadata', {}).get('generated_at', datetime.utcnow().isoformat() + 'Z'),
            'last_updated': datetime.utcnow().isoformat() + 'Z',
            'repositories': repo_order
        },
        'repositories': merged_repos
    }
    
    # Save the merged data to the output file
    print(f"Saving merged data to: {output_file}")
    save_json_file(merged_data, output_file)
    
    print("Merge completed successfully")
    
    # Print summary statistics for each repository
    for repo_name, repo_data in merged_repos.items():
        daily_count = len(repo_data.get('daily_data', []))
        metadata = repo_data.get('metadata', {})
        downloads_meta = repo_data.get('downloads', {}).get('metadata', {})
        print(f"  {repo_name}: {daily_count} days, "
              f"{metadata.get('clones_total', 0)} clones, "
              f"{metadata.get('views_total', 0)} views, "
              f"{downloads_meta.get('cumulative_total', 0)} downloads")


# Entry point: Run main() if this script is executed directly
if __name__ == '__main__':
    main()
