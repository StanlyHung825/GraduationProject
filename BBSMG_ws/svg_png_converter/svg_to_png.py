#!/usr/bin/env python3
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


parser = argparse.ArgumentParser(description="Convert an SVG to a 1024x1024 PNG.")
parser.add_argument("input", type=Path)
parser.add_argument("output", nargs="?", type=Path)
args = parser.parse_args()

source = args.input.resolve()
output = (args.output or source.with_suffix(".png")).resolve()
chrome = shutil.which("google-chrome") or shutil.which("chromium")
if not chrome:
    parser.error("Google Chrome or Chromium is required")
if not source.is_file():
    parser.error(f"file not found: {source}")

with tempfile.TemporaryDirectory() as directory:
    html = Path(directory) / "render.html"
    html.write_text(
        f'<style>*{{margin:0}}img{{display:block;width:1024px;height:1024px}}</style>'
        f'<img src="{source.as_uri()}">',
        encoding="utf-8",
    )
    subprocess.run(
        [chrome, "--headless", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
         "--allow-file-access-from-files", "--window-size=1024,1024",
         f"--screenshot={output}", html.as_uri()],
        check=True,
        stdout=subprocess.DEVNULL,
    )

print(output)
