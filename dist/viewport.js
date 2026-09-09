// Keep a landscape play surface even when an embedded browser cannot lock the OS.
export function landscapeLayout(width, height, touch = true) {
  width = Math.max(1, width); height = Math.max(1, height);
  const rotated = touch && height > width;
  return {rotated, width: rotated ? height : width, height: rotated ? width : height};
}

export function gamePoint(clientX, clientY, rect, rotated = false) {
  return rotated
    ? {x: (clientY - rect.top) / rect.height, y: 1 - (clientX - rect.left) / rect.width}
    : {x: (clientX - rect.left) / rect.width, y: (clientY - rect.top) / rect.height};
}

export function gameDelta(dx, dy, rotated = false) {
  return rotated ? {x: dy, y: -dx} : {x: dx, y: dy};
}

export function isRotated() { return document.documentElement.classList.contains('landscape-rotated'); }

let fullscreenTask;
export function enterLandscapeFullscreen() {
  if (fullscreenTask) return fullscreenTask;
  fullscreenTask = (async () => {
    try {
      if (!document.fullscreenElement) await document.documentElement.requestFullscreen?.();
    } catch { /* The automatically rotated game remains playable. */ }
    try { await globalThis.screen?.orientation?.lock?.('landscape'); } catch {}
  })().finally(() => { fullscreenTask = null; });
  return fullscreenTask;
}

export function installLandscape() {
  const root = document.documentElement;
  const touch = matchMedia('(pointer: coarse)').matches || navigator.maxTouchPoints > 0;
  let previous = '';
  const update = () => {
    const layout = landscapeLayout(innerWidth, innerHeight, touch);
    const signature = JSON.stringify(layout);
    if (signature === previous) return;
    previous = signature;
    root.style.setProperty('--game-width', layout.width + 'px');
    root.style.setProperty('--game-height', layout.height + 'px');
    root.classList.toggle('landscape-rotated', layout.rotated);
    root.classList.toggle('game-compact', layout.width <= 900 || (layout.width >= layout.height && layout.height <= 620));
    window.dispatchEvent(new Event('gameviewportchange'));
  };
  update();
  window.addEventListener('resize', update);
  window.visualViewport?.addEventListener('resize', update);
  document.addEventListener('fullscreenchange', update);
  globalThis.screen?.orientation?.addEventListener('change', update);
  if (touch) {
    // Fullscreen requires a real user gesture. CSS rotation works before this tap.
    document.addEventListener('click', () => { void enterLandscapeFullscreen(); }, {once: true});
    try { Promise.resolve(globalThis.screen?.orientation?.lock?.('landscape')).catch(() => {}); } catch {}
  }
}
