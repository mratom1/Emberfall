import {HEROES} from './model.js?v=8.0.0';
import {EXTRA_HEROES} from './content.js?v=8.0.0';
import {appearance} from './raids.js?v=8.0.0';
export function heroPortrait(id,extra='',level=1){
 if(!Object.hasOwn(HEROES,id))return '';
 const originals=['king','queen','prince','warden','champion','machine'],newcomers=Object.keys(EXTRA_HEROES),isNew=newcomers.includes(id),index=(isNew?newcomers:originals).indexOf(id),columns=isNew?5:3,rows=isNew?3:2,look=appearance(level),src=isNew?'/assets/hero-recruits-v8.webp':'/assets/hero-atlas.webp';
 return `<span class="hero-art ${extra} hero-tier-${look.tier}" style="--rank-color:#${look.color.toString(16)}"><svg class="hero-picture" viewBox="${index%columns} ${Math.floor(index/columns)} 1 1" role="img" aria-label="${HEROES[id].name} portrait" preserveAspectRatio="xMidYMid slice"><image href="${src}" width="${columns}" height="${rows}" preserveAspectRatio="none"/></svg><span class="hero-rank">${look.name} · Lv ${look.level}</span></span>`;
}
