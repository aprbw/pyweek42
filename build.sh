#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "1. Running unit test suite..."
.venv/bin/pytest tests/ -v

echo "2. Cleaning old bundle files..."
rm -f *.pyxapp *.html tests/*.mp4 *.mp4

echo "3. Packaging pyxapp..."
.venv/bin/pyxel package . main.py
mv *.pyxapp grain_of_doubt.pyxapp

echo "4. Exporting WebAssembly HTML..."
.venv/bin/pyxel app2html grain_of_doubt.pyxapp

echo "5. Optimizing HTML for mobile browser execution..."
.venv/bin/python optimize_web.py
cp grain_of_doubt.html index.html

echo "6. Creating official PyWeek source distribution zip (grain-of-doubt-0.19.0.zip)..."
ZIP_NAME="grain-of-doubt-0.19.0.zip"
DIR_NAME="grain-of-doubt-0.19.0"
rm -rf grain-of-doubt-*.zip "$DIR_NAME"
mkdir -p "$DIR_NAME"

cp -r run_game.py main.py engine tests requirements.txt README.md LICENSE.md build.sh run.sh playtest_bot.py optimize_web.py "$DIR_NAME/"
find "$DIR_NAME" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$DIR_NAME" -name "*.pyc" -delete 2>/dev/null || true
find "$DIR_NAME" -name "*.mp4" -delete 2>/dev/null || true
zip -r "$ZIP_NAME" "$DIR_NAME" > /dev/null
rm -rf "$DIR_NAME"

echo "Build and packaging complete:"
ls -lh grain_of_doubt.pyxapp grain_of_doubt.html index.html "$ZIP_NAME"
