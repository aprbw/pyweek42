"""Optimize Pyxel Web HTML for 3:4 aspect-ratio containment on both PC and mobile viewports."""

for fname in ['grain_of_doubt.html']:
    with open(fname, 'r') as f:
        content = f.read()

    # Disable default virtual gamepad cross so our tailored 2-button touch layout is used
    content = content.replace('gamepad: "enabled"', 'gamepad: "disabled"')

    # Inject mobile/PC viewport, responsive 3:4 aspect-ratio containment styling, and dev/mobile flags
    web_head = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<title>Grain of Doubt - PyWeek 42</title>
<style>
  :root {
    --safe-top: env(safe-area-inset-top, 0px);
    --safe-bottom: env(safe-area-inset-bottom, 0px);
    --safe-left: env(safe-area-inset-left, 0px);
    --safe-right: env(safe-area-inset-right, 0px);
    --avail-w: calc(100vw - var(--safe-left) - var(--safe-right) - 32px);
    --avail-h: calc(100vh - var(--safe-top) - var(--safe-bottom) - 32px);
  }
  @supports (height: 100dvh) {
    :root {
      --avail-h: calc(100dvh - var(--safe-top) - var(--safe-bottom) - 32px);
    }
  }
  :root {
    --target-w: min(var(--avail-w), calc(var(--avail-h) * 0.75));
    --target-h: calc(var(--target-w) * 4 / 3);
  }
  html, body {
    margin: 0 !important;
    padding: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    height: 100dvh !important;
    background: #000 !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
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
    width: var(--target-w) !important;
    height: var(--target-h) !important;
    max-width: var(--avail-w) !important;
    max-height: var(--avail-h) !important;
    aspect-ratio: 3 / 4 !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    background-color: #000 !important;
    margin: auto !important;
    overflow: hidden !important;
    touch-action: none !important;
  }
  canvas#canvas {
    position: absolute !important;
    left: 0 !important;
    top: 0 !important;
    width: 100% !important;
    height: 100% !important;
    max-width: 100% !important;
    max-height: 100% !important;
    object-fit: contain !important;
    image-rendering: pixelated !important;
    touch-action: none !important;
  }
</style>
</head>
<body>
<script>
window.__PYXEL_IS_MOBILE__ = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0) || /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);
if (window.location.search.toLowerCase().includes('dev')) {
  window.__DEV_MODE__ = true;
}

function fitScreen() {
  const screenEl = document.getElementById('pyxel-screen');
  const canvasEl = document.getElementById('canvas');
  if (!screenEl) return;

  const vv = window.visualViewport;
  const vw = vv ? vv.width : window.innerWidth;
  const vh = vv ? vv.height : window.innerHeight;

  // Safe area metrics
  const rootStyle = getComputedStyle(document.documentElement);
  const safeTop = parseFloat(rootStyle.getPropertyValue('--safe-top')) || 0;
  const safeBottom = parseFloat(rootStyle.getPropertyValue('--safe-bottom')) || 0;
  const safeLeft = parseFloat(rootStyle.getPropertyValue('--safe-left')) || 0;
  const safeRight = parseFloat(rootStyle.getPropertyValue('--safe-right')) || 0;

  // 16px lateral cushion, 20px vertical cushion + safe area insets
  const availW = Math.max(100, vw - safeLeft - safeRight - 32);
  const availH = Math.max(100, vh - safeTop - safeBottom - 32);

  let targetW = Math.min(availW, availH * 3 / 4);
  let targetH = targetW * 4 / 3;
  if (targetH > availH) {
    targetH = availH;
    targetW = targetH * 3 / 4;
  }

  const w = Math.floor(targetW);
  const h = Math.floor(targetH);

  screenEl.style.setProperty('width', w + 'px', 'important');
  screenEl.style.setProperty('height', h + 'px', 'important');
  screenEl.style.setProperty('max-width', w + 'px', 'important');
  screenEl.style.setProperty('max-height', h + 'px', 'important');
  screenEl.style.setProperty('position', 'relative', 'important');
  screenEl.style.setProperty('left', 'auto', 'important');
  screenEl.style.setProperty('top', 'auto', 'important');
  screenEl.style.setProperty('margin', 'auto', 'important');

  if (canvasEl) {
    canvasEl.style.setProperty('width', w + 'px', 'important');
    canvasEl.style.setProperty('height', h + 'px', 'important');
    canvasEl.style.setProperty('max-width', w + 'px', 'important');
    canvasEl.style.setProperty('max-height', h + 'px', 'important');
    canvasEl.style.setProperty('position', 'absolute', 'important');
    canvasEl.style.setProperty('left', '0px', 'important');
    canvasEl.style.setProperty('top', '0px', 'important');
  }
}

window.addEventListener('resize', fitScreen);
window.addEventListener('orientationchange', fitScreen);
if (window.visualViewport) {
  window.visualViewport.addEventListener('resize', fitScreen);
  window.visualViewport.addEventListener('scroll', fitScreen);
}

// Watch DOM for when pyxel-screen and canvas are created by pyxel.js
const domObserver = new MutationObserver(() => fitScreen());
domObserver.observe(document.documentElement, { childList: true, subtree: true });

// Continuous timer to guarantee layout is maintained across any SDL2 canvas mutations
setInterval(fitScreen, 250);
</script>
'''
    if '<!doctype html>' in content:
        content = content.replace('<!doctype html>', web_head, 1)
        content += '\n</body></html>'

    with open(fname, 'w') as f:
        f.write(content)
print("Web HTML optimization complete.")
