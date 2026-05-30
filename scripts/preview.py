#!/usr/bin/env python3
"""
Build and serve a local, browser-viewable preview of the dashboard using FAKE data.

What it does (all inside ./.preview, nothing real is touched):
1. Ensures a Python with matplotlib is available (reuses .preview/venv, creating
   and populating it once if the current interpreter lacks matplotlib).
2. Generates seeded sample data (scripts/generate_sample_history.py).
3. Runs the real generator (scripts/generate_dashboard.py) with cwd=.preview, so
   it reads/writes only inside the preview directory.
4. Drops an index.html that renders the produced README.md the way GitHub would
   (marked.js + github-markdown-css from a CDN).
5. Serves .preview over HTTP and opens it in your browser.

Usage:
    python scripts/preview.py            # build + serve on http://localhost:8000
    python scripts/preview.py --port 9000
    python scripts/preview.py --no-serve # just build .preview/, don't serve

Requires internet the first time (to create the venv / load the CDN assets).
"""

import argparse
import os
import subprocess
import sys
import webbrowser
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO_ROOT, 'scripts')
PREVIEW_DIR = os.path.join(REPO_ROOT, '.preview')

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dashboard preview (sample data)</title>
  <link rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.1/github-markdown.min.css">
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    body { margin: 0; background: #f6f8fa; }
    .banner { background: #fff3cd; color: #664d03; border-bottom: 1px solid #ffe69c;
              padding: 8px 16px; font: 14px -apple-system, system-ui, sans-serif; text-align: center; }
    .markdown-body { box-sizing: border-box; max-width: 980px; margin: 24px auto;
                     padding: 32px; background: #fff; border: 1px solid #d0d7de; border-radius: 6px; }
    @media (max-width: 767px) { .markdown-body { margin: 0; border-radius: 0; padding: 16px; } }
  </style>
</head>
<body>
  <div class="banner">⚠️ Local preview with <strong>fake, seeded data</strong> — not real traffic.</div>
  <article class="markdown-body" id="content">Loading…</article>
  <script>
    fetch('README.md').then(r => r.text()).then(text => {
      marked.setOptions({ gfm: true, breaks: false });
      document.getElementById('content').innerHTML = marked.parse(text);
    }).catch(e => {
      document.getElementById('content').textContent = 'Failed to load README.md: ' + e;
    });
  </script>
</body>
</html>
"""


def _has_matplotlib(python):
    return subprocess.run(
        [python, '-c', 'import matplotlib'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    ).returncode == 0


def resolve_python():
    """Return a python executable that can import matplotlib, bootstrapping a venv if needed."""
    if _has_matplotlib(sys.executable):
        return sys.executable

    venv_dir = os.path.join(PREVIEW_DIR, 'venv')
    venv_python = os.path.join(venv_dir, 'bin', 'python')
    if os.name == 'nt':
        venv_python = os.path.join(venv_dir, 'Scripts', 'python.exe')

    if not _has_matplotlib(venv_python if os.path.exists(venv_python) else sys.executable):
        if not os.path.exists(venv_python):
            print("Creating preview venv (.preview/venv)…")
            subprocess.run([sys.executable, '-m', 'venv', venv_dir], check=True)
        print("Installing matplotlib into the preview venv (one-time)…")
        subprocess.run([venv_python, '-m', 'pip', 'install', '-q', '--upgrade', 'pip'], check=True)
        subprocess.run([venv_python, '-m', 'pip', 'install', '-q',
                        '-r', os.path.join(REPO_ROOT, 'requirements.txt')], check=True)
    return venv_python


def build(python):
    os.makedirs(os.path.join(PREVIEW_DIR, 'graphs'), exist_ok=True)
    print("Generating sample data…")
    subprocess.run([python, os.path.join(SCRIPTS, 'generate_sample_history.py'),
                    os.path.join(PREVIEW_DIR, 'history.json')], check=True)
    print("Rendering dashboard…")
    subprocess.run([python, os.path.join(SCRIPTS, 'generate_dashboard.py')],
                   cwd=PREVIEW_DIR, check=True)
    with open(os.path.join(PREVIEW_DIR, 'index.html'), 'w') as f:
        f.write(INDEX_HTML)
    print(f"Preview built in {PREVIEW_DIR}")


def serve(port):
    handler = partial(SimpleHTTPRequestHandler, directory=PREVIEW_DIR)
    httpd = ThreadingHTTPServer(('127.0.0.1', port), handler)
    url = f"http://localhost:{port}/"
    print(f"\nServing preview at {url}  (Ctrl+C to stop)")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        httpd.server_close()


def main():
    parser = argparse.ArgumentParser(description="Preview the dashboard with fake data.")
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--no-serve', action='store_true', help="Build .preview/ but don't serve.")
    args = parser.parse_args()

    python = resolve_python()
    build(python)
    if not args.no_serve:
        serve(args.port)


if __name__ == '__main__':
    main()
