#!/usr/bin/env python3
"""
Classify release-asset filenames by platform and CPU architecture.

This is the single source of truth for the asset-name matching that used to live
as duplicated jq regexes in the workflow. fetch_traffic.py uses it to split
release download counts; keeping it here (with tests) means the rules can't drift
between the fetch step and anything else that needs them.

Matching mirrors the original jq patterns exactly (case-insensitive):
- Windows: 'windows', 'win-', or a .exe / .msi extension
- macOS:   'macos', 'darwin', 'osx', or a .dmg / .pkg extension
- Linux:   'linux', or a .appimage / .deb / .rpm extension
- Arch:    arm64/aarch64 -> arm64; 'universal' -> universal;
           x86_64/x64/amd64 -> x86_64; otherwise 'other'
"""

import re

# Order matters only in that the first matching platform wins; the patterns are
# mutually exclusive in practice for well-named assets.
#
# Note the (?<![a-z]) guard on the "win" token: without it, "win-" matches inside
# "dar(win-)arm64", so macOS darwin assets were misclassified as Windows (a latent
# bug in the original jq regex). The guard requires "win" to start a name token.
_PLATFORM_PATTERNS = [
    ('windows', re.compile(r'windows|(?<![a-z])win[-_.]|\.exe$|\.msi$', re.IGNORECASE)),
    ('macos', re.compile(r'macos|darwin|osx|\.dmg$|\.pkg$', re.IGNORECASE)),
    ('linux', re.compile(r'linux|\.appimage$|\.deb$|\.rpm$', re.IGNORECASE)),
]

_ARCH_PATTERNS = [
    ('arm64', re.compile(r'arm64|aarch64', re.IGNORECASE)),
    ('universal', re.compile(r'universal', re.IGNORECASE)),
    ('x86_64', re.compile(r'x86_64|x64|amd64', re.IGNORECASE)),
]


def classify_platform(name):
    """Return 'windows' | 'macos' | 'linux', or None if the name matches none."""
    if not name:
        return None
    for platform, pattern in _PLATFORM_PATTERNS:
        if pattern.search(name):
            return platform
    return None


def classify_arch(name):
    """Return 'arm64' | 'universal' | 'x86_64' | 'other'."""
    if not name:
        return 'other'
    for arch, pattern in _ARCH_PATTERNS:
        if pattern.search(name):
            return arch
    return 'other'
