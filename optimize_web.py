"""Optimize Pyxel Web HTML for 3:4 aspect-ratio containment, mobile responsiveness, and zoom prevention."""

for fname in ['grain_of_doubt.html', 'index.html']:
    try:
        with open(fname, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        continue

    # Disable default virtual gamepad cross so our tailored 2-button touch layout is used
    content = content.replace('gamepad: "enabled"', 'gamepad: "disabled"')

    # Inject mobile/PC viewport, responsive 3:4 aspect-ratio containment styling, dev/mobile flags, and zoom prevention
    web_head = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<title>Grain of Doubt - PyWeek 42</title>
<style>
  :root, html, body {
    -moz-text-size-adjust: 100% !important;
    -webkit-text-size-adjust: 100% !important;
    text-size-adjust: 100% !important;
  }
  :root {
    --safe-top: env(safe-area-inset-top, 0px);
    --safe-bottom: env(safe-area-inset-bottom, 0px);
    --safe-left: env(safe-area-inset-left, 0px);
    --safe-right: env(safe-area-inset-right, 0px);
    --avail-w: calc(100vw - var(--safe-left) - var(--safe-right) - 24px);
    --avail-h: calc(100vh - var(--safe-top) - var(--safe-bottom) - 24px);
  }
  @supports (height: 100dvh) {
    :root {
      --avail-h: calc(100dvh - var(--safe-top) - var(--safe-bottom) - 24px);
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
    touch-action: none !important;
    -webkit-touch-callout: none !important;
    -webkit-user-select: none !important;
    user-select: none !important;
    overscroll-behavior: none !important;
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
    -webkit-touch-callout: none !important;
    -webkit-user-select: none !important;
    user-select: none !important;
    overscroll-behavior: none !important;
  }
  canvas#canvas {
    position: absolute !important;
    left: 0 !important;
    top: 0 !important;
    width: 100% !important;
    height: 100% !important;
    max-width: 100% !important;
    max-height: 100% !important;
    image-rendering: pixelated !important;
    image-rendering: crisp-edges !important;
    touch-action: none !important;
    -webkit-touch-callout: none !important;
    -webkit-user-select: none !important;
    user-select: none !important;
    overscroll-behavior: none !important;
  }
</style>
</head>
<body>
<script>
window.__PYXEL_IS_MOBILE__ = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0) || /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);
if (window.location.search.toLowerCase().includes('dev')) {
  window.__DEV_MODE__ = true;
}

// Mobile browser zoom prevention
// 1. Prevent Safari multi-touch gesture zoom
document.addEventListener('gesturestart', function(e) { e.preventDefault(); }, { passive: false });
document.addEventListener('gesturechange', function(e) { e.preventDefault(); }, { passive: false });
document.addEventListener('gestureend', function(e) { e.preventDefault(); }, { passive: false });

// 2. Prevent multi-touch pinch to zoom
document.addEventListener('touchstart', function(e) {
  if (e.touches.length > 1) {
    e.preventDefault();
  }
}, { passive: false });

document.addEventListener('touchmove', function(e) {
  if (e.touches.length > 1) {
    e.preventDefault();
  }
}, { passive: false });

// 3. Prevent double-tap to zoom
let lastTouchEnd = 0;
document.addEventListener('touchend', function(e) {
  const now = Date.now();
  if (now - lastTouchEnd <= 300) {
    e.preventDefault();
  }
  lastTouchEnd = now;
}, { passive: false });

// 4. Prevent desktop / trackpad ctrl-wheel zoom
document.addEventListener('wheel', function(e) {
  if (e.ctrlKey) {
    e.preventDefault();
  }
}, { passive: false });

// 5. Prevent double-click zoom
document.addEventListener('dblclick', function(e) {
  e.preventDefault();
}, { passive: false });

function fitScreen() {
  const screenEl = document.getElementById('pyxel-screen');
  const canvasEl = document.getElementById('canvas');
  if (!screenEl) return;

  try {
    window.scrollTo(0, 0);
  } catch (err) {}

  const vv = window.visualViewport;
  const docW = document.documentElement.clientWidth || window.innerWidth;
  const docH = document.documentElement.clientHeight || window.innerHeight;
  const vw = vv ? Math.min(vv.width, docW, window.innerWidth) : Math.min(docW, window.innerWidth);
  const vh = vv ? Math.min(vv.height, docH, window.innerHeight) : Math.min(docH, window.innerHeight);

  // Safe area metrics
  const rootStyle = getComputedStyle(document.documentElement);
  const safeTop = parseFloat(rootStyle.getPropertyValue('--safe-top')) || 0;
  const safeBottom = parseFloat(rootStyle.getPropertyValue('--safe-bottom')) || 0;
  const safeLeft = parseFloat(rootStyle.getPropertyValue('--safe-left')) || 0;
  const safeRight = parseFloat(rootStyle.getPropertyValue('--safe-right')) || 0;

  // 12px lateral cushion, 12px vertical cushion + safe area insets
  const availW = Math.max(100, vw - safeLeft - safeRight - 24);
  const availH = Math.max(100, vh - safeTop - safeBottom - 24);

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
