import {HEROES} from './model.js?v=6.0.0';
import {appearance} from './raids.js?v=6.0.0';
export function heroPortrait(id, extra = '', level = 1) {
  if(!Object.hasOwn(HEROES,id)) return '';
  const index=['king','queen','prince','warden','champion','machine'].indexOf(id),look=appearance(level);
  return `<span class="hero-art hero-art-${id} ${extra} hero-tier-${look.tier}" style="--hero-col:${index%3};--hero-row:${Math.floor(index/3)};--rank-color:#${look.color.toString(16)}"><img src="/assets/hero-atlas.webp" alt="${HEROES[id].name} portrait" width="1536" height="1024" decoding="async"><span class="hero-rank">${look.name} · Lv ${look.level}</span></span>`;
}
