import {HEROES,TROOPS,TYPES} from './model.js?v=11.0.0';
import {appearance} from './raids.js?v=11.0.0';
export function modelPortrait(kind,type,level=1,extra=''){
 const def=(kind==='building'?TYPES:kind==='hero'?HEROES:TROOPS)[type];if(!def)return '';
 level=Math.max(1,Math.min(kind==='hero'?50:15,Math.floor(level)||1));
 return `<canvas class="model-picture ${extra}" width="280" height="280" data-model-kind="${kind}" data-model-type="${type}" data-model-level="${level}" role="img" aria-label="${def.name} · Level ${level}">${def.name} · Level ${level}</canvas>`;
}
export function heroPortrait(id,extra='',level=1){
 if(!Object.hasOwn(HEROES,id))return '';const look=appearance(level);
 return `<span class="hero-art ${extra} hero-tier-${look.tier}" style="--rank-color:#${look.color.toString(16)}">${modelPortrait('hero',id,level,'hero-picture')}<span class="hero-rank">${look.name} · Lv ${look.level}</span></span>`;
}
// Portraits use the same model constructors and levels as village and battle objects.
// One offscreen renderer, a bounded bitmap cache, and two renders per frame avoid many GPU contexts.
export function installModelPictures(world,root=document.getElementById('app')){
 const cache=new Map(),pending=new Set();let scheduled=false,stopped=false;
 function scan(){for(const c of root.querySelectorAll('canvas[data-model-kind]:not([data-model-ready])'))pending.add(c);if(pending.size&&!scheduled){scheduled=true;requestAnimationFrame(draw);}}
 function draw(){scheduled=false;if(stopped)return;let count=0;
  for(const canvas of pending){pending.delete(canvas);if(!canvas.isConnected)continue;
   const item={kind:canvas.dataset.modelKind,type:canvas.dataset.modelType,level:Number(canvas.dataset.modelLevel)},key=JSON.stringify(item);
   try{let bitmap=cache.get(key);if(!bitmap){world.paintDetail(canvas,item,.48);bitmap=document.createElement('canvas');bitmap.width=canvas.width;bitmap.height=canvas.height;bitmap.getContext('2d').drawImage(canvas,0,0);cache.set(key,bitmap);if(cache.size>96)cache.delete(cache.keys().next().value);}else canvas.getContext('2d').drawImage(bitmap,0,0,canvas.width,canvas.height);canvas.dataset.modelReady='true';}
   catch{canvas.dataset.modelReady='failed';const ctx=canvas.getContext('2d');ctx.fillStyle='#eee0b9';ctx.font='16px sans-serif';ctx.fillText('3D preview unavailable',18,135);}
   if(++count===2)break;
  }if(pending.size){scheduled=true;requestAnimationFrame(draw);}
 }
 const observer=new MutationObserver(scan);observer.observe(root,{childList:true,subtree:true});scan();
 return ()=>{stopped=true;observer.disconnect();pending.clear();cache.clear();};
}
