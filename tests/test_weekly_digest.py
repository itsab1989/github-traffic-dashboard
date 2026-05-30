#!/usr/bin/env python3
"""
Unit tests for scripts/weekly_digest.py - the weekly summary posted as an issue.

These cover the structural promises the workflow relies on (sections render, the
repo appears, lifetime totals show) and the "new releases this week" windowing.
Exact week-over-week numbers come from compute_momentum, which has its own tests.

Run with:  python -m unittest discover -s tests -v
"""

import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from weekly_digest import build_digest, _recent_releases  # noqa: E402


def _day(offset):
    return (datetime.now(timezone.utc) - timedelta(days=offset)).strftime('%Y-%m-%d')


def _history():
    daily = [{'date': _day(i), 'clones_total': 3, 'clones_unique': 2,
              'views_total': 7, 'views_unique': 4} for i in range(14, -1, -1)]
    return {
        'metadata': {'repositories': ['owner/Repo']},
        'repositories': {'owner/Repo': {
            'daily_data': daily,
            'downloads': {
                'daily_data': [{'date': _day(1), 'cumulative_total': 50, 'downloads_total': 5,
                                'cumulative_windows': 20, 'downloads_windows': 2,
                                'cumulative_macos': 25, 'downloads_macos': 2,
                                'cumulative_linux': 5, 'downloads_linux': 1}],
                'by_release': [{'tag': 'v2.0.0', 'downloads': 9,
                                'published_at': _day(2) + 'T00:00:00Z'}],
                'by_release_daily': {'v2.0.0': {'published_at': _day(2) + 'T00:00:00Z',
                    'snapshots': [{'date': _day(2), 'downloads': 0},
                                  {'date': _day(0), 'downloads': 9}]}},
            },
        }},
    }


class TestWeeklyDigest(unittest.TestCase):

    def test_contains_core_sections(self):
        d = build_digest(_history())
        self.assertIn('Weekly Dashboard Digest', d)
        self.assertIn('## Repo', d)
        self.assertIn('This week vs last week', d)
        self.assertIn('Lifetime:', d)
        self.assertIn('dashboard.html', d)

    def test_lifetime_downloads_shown(self):
        d = build_digest(_history())
        self.assertIn('50 downloads', d)  # latest cumulative_total

    def test_new_release_and_reception_listed(self):
        d = build_digest(_history())
        self.assertIn('New releases this week', d)
        self.assertIn('v2.0.0', d)
        self.assertIn('early-life reception', d)

    def test_recent_releases_window(self):
        now = datetime.now(timezone.utc)
        rels = [
            {'tag': 'new', 'published_at': _day(1) + 'T00:00:00Z'},
            {'tag': 'old', 'published_at': _day(30) + 'T00:00:00Z'},
        ]
        tags = [r['tag'] for r in _recent_releases(rels, now, days=7)]
        self.assertEqual(tags, ['new'])

    def test_handles_repo_without_downloads(self):
        h = _history()
        h['repositories']['owner/Repo']['downloads'] = {}
        d = build_digest(h)
        self.assertIn('## Repo', d)            # still renders
        self.assertIn('0 downloads', d)        # lifetime falls back to zeros


if __name__ == '__main__':
    unittest.main()
