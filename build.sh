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
.venv/bin/python -c "
for fname in ['grain_of_doubt.html']:
    with open(fname, 'r') as f:
        content = f.read()
    
    # Disable default virtual gamepad cross so our tailored 2-button touch layout is used
    content = content.replace('gamepad: \"enabled\"', 'gamepad: \"disabled\"')
    
    # Inject mobile viewport, responsive 3:4 aspect-ratio containment styling, and mobile flag
    mobile_head = '''<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover\">
<title>Grain of Doubt - PyWeek 42</title>
<style>
  :root {
    --safe-top: env(safe-area-inset-top, 0px);
    --safe-bottom: env(safe-area-inset-bottom, 0px);
    --max-h: calc(100vh - var(--safe-top) - var(--safe-bottom) - 48px);
    --max-h: calc(100dvh - var(--safe-top) - var(--safe-bottom) - 48px);
    --max-h: calc(100svh - var(--safe-top) - var(--safe-bottom) - 48px);
    --max-w: calc(100vw - 16px);
  }
  html, body {
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
    height: 100% !important;
    height: 100svh !important;
    max-height: 100svh !important;
    background: #000 !important;
    overflow: hidden !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    touch-action: none;
    -webkit-touch-callout: none;
    -webkit-user-select: none;
    user-select: none;
    box-sizing: border-box !important;
  }
  div#pyxel-screen {
    position: relative !important;
    left: auto !important;
    top: auto !important;
    width: min(var(--max-w), calc(var(--max-h) * 3 / 4)) !important;
    height: min(var(--max-h), calc(var(--max-w) * 4 / 3)) !important;
    max-width: var(--max-w) !important;
    max-height: var(--max-h) !important;
    aspect-ratio: 3 / 4 !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    background-color: #000 !important;
    margin: auto !important;
    touch-action: none !important;
  }
  canvas#canvas {
    position: absolute !important;
    left: 0 !important;
    top: 0 !important;
    width: 100% !important;
    height: 100% !important;
    object-fit: contain !important;
    image-rendering: pixelated !important;
    touch-action: none !important;
  }
</style>
</head>
<body>
<script>
window.__PYXEL_IS_MOBILE__ = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0) || /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);

function fitScreen() {
  const el = document.getElementById('pyxel-screen');
  if (!el) return;
  const vw = window.visualViewport ? window.visualViewport.width : window.innerWidth;
  const vh = window.visualViewport ? window.visualViewport.height : window.innerHeight;
  const availW = Math.max(150, vw - 16);
  const availH = Math.max(150, vh - 48);
  let targetW = Math.min(availW, availH * 3 / 4);
  let targetH = targetW * 4 / 3;
  if (targetH > availH) {
    targetH = availH;
    targetW = targetH * 3 / 4;
  }
  el.style.setProperty('width', Math.floor(targetW) + 'px', 'important');
  el.style.setProperty('height', Math.floor(targetH) + 'px', 'important');
  el.style.setProperty('max-width', Math.floor(targetW) + 'px', 'important');
  el.style.setProperty('max-height', Math.floor(targetH) + 'px', 'important');
}
window.addEventListener('resize', fitScreen);
if (window.visualViewport) {
  window.visualViewport.addEventListener('resize', fitScreen);
  window.visualViewport.addEventListener('scroll', fitScreen);
}
window.addEventListener('orientationchange', fitScreen);
const fitPoller = setInterval(fitScreen, 100);
setTimeout(() => clearInterval(fitPoller), 6000);
</script>
'''
    if '<!doctype html>' in content:
        content = content.replace('<!doctype html>', mobile_head, 1)
        content += '\n</body></html>'
    
    with open(fname, 'w') as f:
        f.write(content)
"
cp grain_of_doubt.html index.html

echo "6. Creating official PyWeek source distribution zip (grain-of-doubt-0.8.0.zip)..."
ZIP_NAME="grain-of-doubt-0.8.0.zip"
DIR_NAME="grain-of-doubt-0.8.0"
rm -rf "$DIR_NAME" "$ZIP_NAME"
mkdir -p "$DIR_NAME"

cp -r run_game.py main.py engine tests requirements.txt README.md LICENSE.md build.sh run.sh playtest_bot.py "$DIR_NAME/"
find "$DIR_NAME" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$DIR_NAME" -name "*.pyc" -delete 2>/dev/null || true
find "$DIR_NAME" -name "*.mp4" -delete 2>/dev/null || true
zip -r "$ZIP_NAME" "$DIR_NAME" > /dev/null
rm -rf "$DIR_NAME"

echo "Build and packaging complete:"
ls -lh grain_of_doubt.pyxapp grain_of_doubt.html index.html "$ZIP_NAME"
