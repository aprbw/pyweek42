"""Optimize Pyxel Web HTML for mobile viewport and 3:4 aspect-ratio containment."""
for fname in ['grain_of_doubt.html']:
    with open(fname, 'r') as f:
        content = f.read()

    # Disable default virtual gamepad cross so our tailored 2-button touch layout is used
    content = content.replace('gamepad: "enabled"', 'gamepad: "disabled"')

    # Inject mobile viewport, responsive 3:4 aspect-ratio containment styling, and mobile flag
    mobile_head = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<title>Grain of Doubt - PyWeek 42</title>
<style>
  :root {
    --safe-top: env(safe-area-inset-top, 0px);
    --safe-bottom: env(safe-area-inset-bottom, 0px);
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
    padding-top: calc(env(safe-area-inset-top, 0px) + 24px) !important;
    padding-bottom: calc(env(safe-area-inset-bottom, 0px) + 24px) !important;
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
  const vv = window.visualViewport;
  const vw = vv ? vv.width : window.innerWidth;
  const vh = vv ? vv.height : window.innerHeight;
  // User explicitly confirmed: "lots of empty spaces at the top and bottom is ok, no part should ever be cut off"
  const availW = Math.max(120, vw - 24);
  const availH = Math.max(120, Math.min(vh * 0.80, vh - 120));
  let targetW = Math.min(availW, availH * 3 / 4);
  let targetH = targetW * 4 / 3;
  if (targetH > availH) {
    targetH = availH;
    targetW = targetH * 3 / 4;
  }
  const w = Math.floor(targetW);
  const h = Math.floor(targetH);
  el.style.setProperty('width', w + 'px', 'important');
  el.style.setProperty('height', h + 'px', 'important');
  el.style.setProperty('max-width', w + 'px', 'important');
  el.style.setProperty('max-height', h + 'px', 'important');
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
print("Mobile HTML optimization complete.")
