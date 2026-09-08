export const GRAPHICS = Object.freeze({
  smooth: {name: 'Smooth', ratio: 1.25, pixels: 2500000, shadow: 1024},
  high: {name: 'High', ratio: 2, pixels: 6000000, shadow: 2048},
  ultra: {name: 'Ultra HD', ratio: 3, pixels: 10000000, shadow: 4096}
});
export function graphicsProfile(value) {
  return Object.hasOwn(GRAPHICS, value) ? value : (value === false || value === 'low') ? 'smooth' : 'high';
}
export function renderScale(profile, width, height, dpr = 1, maxSize = 8192) {
  const p = GRAPHICS[graphicsProfile(profile)];
  return Math.max(Number.EPSILON, Math.min(p.ratio, Math.max(1, dpr), Math.sqrt(p.pixels / Math.max(1, width * height)), maxSize / Math.max(1, width, height)));
}
