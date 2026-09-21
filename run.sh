#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv --python 3.12 .venv
    uv pip install --python .venv pyxel pytest
fi

echo "Launching Grain of Doubt..."
.venv/bin/python3 -m pyxel run main.py
