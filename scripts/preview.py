#!/usr/bin/env python3
"""
Build and serve a local, browser-viewable preview of the dashboard using FAKE data.

What it does (all inside ./.preview, nothing real is touched):
1. Generates seeded sample data (scripts/generate_sample_history.py).
2. Runs the real generator (scripts/generate_dashboard.py) with cwd=.preview, so
   it reads/writes only inside the preview directory.
3. Copies the interactive dashboard.html and drops an index.html that renders the
   produced README.md the way GitHub would (marked.js + github-markdown-css).
4. Serves .preview over HTTP and opens the interactive charts in your browser.

The default (interactive-charts) dashboard is pure standard library, so no
dependencies are needed - the browser pulls Chart.js / marked.js from a CDN, so
internet is only required when actually viewing the page.

Usage:
    python scripts/preview.py            # build + serve on http://localhost:8000
    python scripts/preview.py --port 9000
    python scripts/preview.py --no-serve # just build .preview/, don't serve
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
        href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.1/github-markdown.min.css"
        integrity="sha384-LTbdgUzZ3SXn50n5dAZ75Kpp86fR5oSHELRlFJqZ08kHpI2/Jwsgi/KA8UdnqXSK"
        crossorigin="anonymous">
  <script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"
          integrity="sha384-/TQbtLCAerC3jgaim+N78RZSDYV7ryeoBCVqTuzRrFec2akfBkHS7ACQ3PQhvMVi"
          crossorigin="anonymous"></script>
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
    # Copy the interactive charts page so it can read .preview/assets/chart-data.json
    src = os.path.join(REPO_ROOT, 'dashboard.html')
    if os.path.exists(src):
        with open(src) as f:
            html = f.read()
        with open(os.path.join(PREVIEW_DIR, 'dashboard.html'), 'w') as f:
            f.write(html)
    print(f"Preview built in {PREVIEW_DIR}")


def serve(port):
    handler = partial(SimpleHTTPRequestHandler, directory=PREVIEW_DIR)
    httpd = ThreadingHTTPServer(('127.0.0.1', port), handler)
    base = f"http://localhost:{port}/"
    # Open the interactive charts page; the README render is at index.html
    url = base + ('dashboard.html' if os.path.exists(os.path.join(PREVIEW_DIR, 'dashboard.html')) else '')
    print(f"\nServing preview at {base}  (Ctrl+C to stop)")
    print(f"  • Interactive charts: {base}dashboard.html")
    print(f"  • README render:      {base}index.html")
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

    build(sys.executable)
    if not args.no_serve:
        serve(args.port)


if __name__ == '__main__':
    main()
