import {HEROES} from './model.js';
export function heroPortrait(id, extra = '') {
  if(!Object.hasOwn(HEROES,id)) return '';
  return `<span class="hero-art hero-art-${id} ${extra}" role="img" aria-label="${HEROES[id].name} portrait"></span>`;
}
