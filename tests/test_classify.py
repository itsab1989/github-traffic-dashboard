#!/usr/bin/env python3
"""
Unit tests for scripts/classify.py - the single source of truth for matching
release-asset filenames to a platform and CPU architecture.

These lock in the rules that split download counts (and used to be duplicated jq
regexes), including the cases that matter: extension-only matches, arch keywords,
and filenames that match nothing (counted only in the grand total).

Run with:  python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from classify import classify_platform, classify_arch  # noqa: E402


class TestClassifyPlatform(unittest.TestCase):

    def test_windows(self):
        for name in ['App-Setup.exe', 'app.msi', 'App-windows-x64.zip', 'win-installer.bin']:
            self.assertEqual(classify_platform(name), 'windows', name)

    def test_macos(self):
        for name in ['App.dmg', 'App.pkg', 'App-macos.tar.gz', 'App-darwin-arm64', 'App-osx.zip']:
            self.assertEqual(classify_platform(name), 'macos', name)

    def test_linux(self):
        for name in ['App.AppImage', 'app.deb', 'app.rpm', 'App-linux-x86_64.tar.gz']:
            self.assertEqual(classify_platform(name), 'linux', name)

    def test_case_insensitive(self):
        self.assertEqual(classify_platform('APP-WINDOWS.EXE'), 'windows')

    def test_unmatched_is_none(self):
        for name in ['checksums.txt', 'source.zip', 'README.md', '']:
            self.assertIsNone(classify_platform(name))


class TestClassifyArch(unittest.TestCase):

    def test_arm64(self):
        self.assertEqual(classify_arch('App-arm64.dmg'), 'arm64')
        self.assertEqual(classify_arch('App-aarch64.AppImage'), 'arm64')

    def test_universal(self):
        self.assertEqual(classify_arch('App-universal.dmg'), 'universal')

    def test_x86_64(self):
        for name in ['App-x86_64.AppImage', 'App-x64.exe', 'App-amd64.deb']:
            self.assertEqual(classify_arch(name), 'x86_64', name)

    def test_default_other(self):
        self.assertEqual(classify_arch('App-installer.exe'), 'other')
        self.assertEqual(classify_arch(''), 'other')

    def test_arm64_precedence_over_x86(self):
        """A name mentioning both resolves to arm64 (checked first), deterministically."""
        self.assertEqual(classify_arch('App-arm64-from-x64-build'), 'arm64')


if __name__ == '__main__':
    unittest.main()
