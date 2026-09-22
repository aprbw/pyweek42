#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "1. Running unit test suite..."
.venv/bin/pytest tests/ -v

echo "2. Cleaning old bundle files..."
rm -f *.pyxapp *.html

echo "3. Packaging pyxapp..."
.venv/bin/pyxel package . main.py
mv *.pyxapp grain_of_doubt.pyxapp

echo "4. Exporting WebAssembly HTML..."
.venv/bin/pyxel app2html grain_of_doubt.pyxapp

echo "5. Optimizing HTML for mobile browser execution..."
.venv/bin/python -c "
for fname in ['grain_of_doubt.html']:
    with open(fname, 'r') as f:
        content = f.read()
    
    # Disable default virtual gamepad cross so our tailored 2-button touch layout is used
    content = content.replace('gamepad: \"enabled\"', 'gamepad: \"disabled\"')
    
    # Inject mobile viewport and touch-action meta & styling
    mobile_head = '''<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover\">
<title>Grain of Doubt - PyWeek 42</title>
<style>
  html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    background: #000;
    overflow: hidden;
    touch-action: none;
    -webkit-touch-callout: none;
    -webkit-user-select: none;
    user-select: none;
  }
  #pyxel-screen, canvas#canvas {
    touch-action: none !important;
  }
</style>
</head>
<body>
'''
    if '<!doctype html>' in content:
        content = content.replace('<!doctype html>', mobile_head, 1)
        content += '\n</body></html>'
    
    with open(fname, 'w') as f:
        f.write(content)
"
cp grain_of_doubt.html index.html

echo "Build and packaging complete:"
ls -lh grain_of_doubt.pyxapp grain_of_doubt.html index.html
