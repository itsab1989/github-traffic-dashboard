#!/usr/bin/env python3
"""
Tests for scripts/fetch_traffic.py - the Python replacement for the old bash+jq
fetch step. Covers the pure data-shaping (no network) plus a full OFFLINE
end-to-end run of the real pipeline (fetch builders -> merge_history ->
generate_dashboard) so the whole chain is exercised without a token.

Run with:  python -m unittest discover -s tests -v
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = os.path.join(os.path.dirname(__file__), '..', 'scripts')
sys.path.insert(0, SCRIPTS)

from fetch_traffic import (  # noqa: E402
    build_daily_data, aggregate_release, aggregate_downloads,
    build_repo_payload, build_traffic_data,
)


def _release(tag, published, assets):
    return {'tag_name': tag, 'published_at': published,
            'assets': [{'name': n, 'download_count': c} for n, c in assets]}


class TestDailyData(unittest.TestCase):

    def test_merges_clones_and_views_by_date(self):
        clones = [{'timestamp': '2026-05-24T00:00:00Z', 'count': 10, 'uniques': 5},
                  {'timestamp': '2026-05-25T00:00:00Z', 'count': 4, 'uniques': 3}]
        views = [{'timestamp': '2026-05-25T00:00:00Z', 'count': 20, 'uniques': 12}]
        out = build_daily_data(clones, views)
        self.assertEqual(len(out), 2)
        # Date with only clones still zero-fills the view fields
        self.assertEqual(out[0], {'date': '2026-05-24', 'clones_total': 10,
                                  'clones_unique': 5, 'views_total': 0, 'views_unique': 0})
        self.assertEqual(out[1]['views_total'], 20)

    def test_sorted_by_date(self):
        clones = [{'timestamp': '2026-05-25T00:00:00Z', 'count': 1, 'uniques': 1},
                  {'timestamp': '2026-05-20T00:00:00Z', 'count': 1, 'uniques': 1}]
        dates = [e['date'] for e in build_daily_data(clones, [])]
        self.assertEqual(dates, ['2026-05-20', '2026-05-25'])

    def test_empty(self):
        self.assertEqual(build_daily_data([], []), [])


class TestDownloadAggregation(unittest.TestCase):

    def test_release_split_and_unclassified_in_total(self):
        rel = _release('v1.0.0', '2026-05-20T00:00:00Z', [
            ('App-windows-x64.exe', 7), ('App-macos-arm64.dmg', 12),
            ('App-linux-x86_64.AppImage', 3), ('checksums.txt', 5)])
        agg = aggregate_release(rel)
        self.assertEqual(agg['downloads'], 27)            # includes the 5 unclassified
        self.assertEqual((agg['windows'], agg['macos'], agg['linux']), (7, 12, 3))

    def test_aggregate_downloads_totals_and_arch(self):
        releases = [
            _release('v1.0.0', '2026-05-20T00:00:00Z',
                     [('App-win-x64.exe', 5), ('App-macos-universal.dmg', 10)]),
            _release('v0.9.0', '2026-05-10T00:00:00Z',
                     [('App-linux-arm64.deb', 2), ('notes.txt', 1)]),
        ]
        agg = aggregate_downloads(releases)
        self.assertEqual(agg['cumulative_total'], 18)     # 5+10+2+1
        self.assertEqual(agg['cumulative_windows'], 5)
        self.assertEqual(agg['cumulative_macos'], 10)
        self.assertEqual(agg['cumulative_linux'], 2)
        self.assertEqual(agg['by_arch']['macos'], {'universal': 10})
        self.assertEqual(agg['by_arch']['linux'], {'arm64': 2})
        self.assertEqual(len(agg['by_release']), 2)

    def test_empty_releases(self):
        agg = aggregate_downloads([])
        self.assertEqual(agg['cumulative_total'], 0)
        self.assertEqual(agg['by_release'], [])


class TestRepoPayload(unittest.TestCase):

    def test_metadata_totals_and_download_date(self):
        payload = build_repo_payload(
            clones=[{'timestamp': '2026-05-25T00:00:00Z', 'count': 4, 'uniques': 3}],
            views=[{'timestamp': '2026-05-25T00:00:00Z', 'count': 9, 'uniques': 6}],
            referrers=[{'referrer': 'github.com', 'count': 2, 'uniques': 1}],
            releases=[_release('v1', '2026-05-20T00:00:00Z', [('a-win.exe', 3)])],
            fetch_date='2026-05-25T10:00:00Z', today='2026-05-25')
        self.assertEqual(payload['metadata']['clones_total'], 4)
        self.assertEqual(payload['metadata']['views_total'], 9)
        self.assertEqual(payload['downloads']['date'], '2026-05-25')
        self.assertEqual(payload['downloads']['cumulative_windows'], 3)
        self.assertEqual(payload['referrers'][0]['referrer'], 'github.com')

    def test_traffic_data_preserves_repo_order(self):
        data = build_traffic_data([
            ('owner/B', {'clones': {}, 'views': {}, 'referrers': [], 'releases': []}),
            ('owner/A', {'clones': {}, 'views': {}, 'referrers': [], 'releases': []}),
        ])
        self.assertEqual(data['metadata']['repositories'], ['owner/B', 'owner/A'])


class TestEndToEndOffline(unittest.TestCase):
    """fetch builders -> merge_history.py -> generate_dashboard.py, no network."""

    def test_full_pipeline_produces_dashboard(self):
        fixtures = [('owner/Repo', {
            'clones': {'clones': [{'timestamp': '2026-05-25T00:00:00Z', 'count': 6, 'uniques': 4}]},
            'views': {'views': [{'timestamp': '2026-05-25T00:00:00Z', 'count': 15, 'uniques': 9}]},
            'referrers': [{'referrer': 'github.com', 'count': 3, 'uniques': 2}],
            'releases': [_release('v1.0.0', '2026-05-24T00:00:00Z',
                                  [('App-macos-arm64.dmg', 8), ('App-win-x64.exe', 4)])],
        })]
        traffic = build_traffic_data(fixtures)

        with tempfile.TemporaryDirectory() as d:
            tdata = os.path.join(d, 'traffic_data.json')
            hist = os.path.join(d, 'history.json')
            merged = os.path.join(d, 'merged.json')
            json.dump(traffic, open(tdata, 'w'))
            json.dump({'metadata': {'repositories': []}, 'repositories': {}}, open(hist, 'w'))

            merge = os.path.join(SCRIPTS, 'merge_history.py')
            gen = os.path.join(SCRIPTS, 'generate_dashboard.py')
            subprocess.run([sys.executable, merge, tdata, hist, merged], check=True, cwd=d)
            os.replace(merged, hist)
            subprocess.run([sys.executable, gen], check=True, cwd=d)

            readme = open(os.path.join(d, 'README.md')).read()
            self.assertIn('Repo', readme)
            self.assertIn('Engagement Ratios', readme)
            chart = json.load(open(os.path.join(d, 'assets', 'chart-data.json')))
            self.assertEqual(chart['repositories'][0]['name'], 'owner/Repo')
            self.assertTrue(chart['repositories'][0]['downloads']['has_data'])


if __name__ == '__main__':
    unittest.main()
