#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "1. Running unit test suite..."
.venv/bin/pytest tests/test_mechanics.py -v

echo "2. Cleaning old bundle files..."
rm -f *.pyxapp *.html

echo "3. Packaging pyxapp..."
.venv/bin/pyxel package . main.py
mv *.pyxapp grain_of_doubt.pyxapp

echo "4. Exporting WebAssembly HTML..."
.venv/bin/pyxel app2html grain_of_doubt.pyxapp
cp grain_of_doubt.html index.html

echo "Build and packaging complete:"
ls -lh grain_of_doubt.pyxapp grain_of_doubt.html index.html
