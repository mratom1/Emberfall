import {TYPES} from './model.js?v=13.0.0';
import {unlockedLand,landContains} from './content.js?v=13.0.0';
// Half-tile navigation includes the real bridge at z=12, never the river.
export function villageNavigator(s){
 const land=unlockedLand(s),blocked=(s.buildings||[]).filter(b=>!TYPES[b.type].decoration),obstacles=s.obstacles||[],flags=s.flags||[];
 const openCache=new Map();
 const rawOpen=(x,z)=>((x>=-23.5&&x<=-14&&z>=11.5&&z<=12.5&&land.length>1)||landContains(land,x,z,.15))&&!blocked.some(b=>Math.abs(b.x-x)<TYPES[b.type].size/2+.15&&Math.abs(b.z-z)<TYPES[b.type].size/2+.15)&&!obstacles.some(o=>Math.hypot(o.x-x,o.z-z)<.8)&&!flags.some(f=>Math.hypot(f.x-x,f.z-z)<.4);
 const open=(x,z)=>{const key=x+','+z;if(!openCache.has(key))openCache.set(key,rawOpen(x,z));return openCache.get(key);};
 const nearest=p=>{let best=null,d=Infinity;for(let x=Math.round(p.x*2)-12;x<=Math.round(p.x*2)+12;x++)for(let z=Math.round(p.z*2)-12;z<=Math.round(p.z*2)+12;z++){const n=(x/2-p.x)**2+(z/2-p.z)**2;if(n<d&&open(x/2,z/2)){best={x:x/2,z:z/2};d=n;}}return best;};
 const cache=new Map();
 const route=(from,to,flying=false)=>{if(flying)return [{x:to.x,z:to.z}];const a=nearest(from),b=nearest(to);if(!a||!b)return null;const key=[a.x,a.z,b.x,b.z].join(',');if(cache.has(key))return cache.get(key).map(p=>({...p}));
 const q=[a],parents=new Map([[a.x+','+a.z,null]]);let found=false;
 for(let i=0;i<q.length&&i<18000;i++){const p=q[i];if(p.x===b.x&&p.z===b.z){found=true;break;}for(const [dx,dz] of [[.5,0],[-.5,0],[0,.5],[0,-.5]]){const n={x:p.x+dx,z:p.z+dz},k=n.x+','+n.z;if(!parents.has(k)&&open(n.x,n.z)){parents.set(k,p);q.push(n);}}}
 if(!found)return null;const path=[];for(let p=b;p;p=parents.get(p.x+','+p.z))path.push(p);path.reverse();cache.set(key,path);return path.map(p=>({...p}));};
 return {open,nearest,route};
}
export function advanceRoute(position,path,distance){let facing=null;while(path?.length&&distance>0){const p=path[0],dx=p.x-position.x,dz=p.z-position.z,d=Math.hypot(dx,dz);if(d<.001){path.shift();continue;}const step=Math.min(d,distance);position.x+=dx/d*step;position.z+=dz/d*step;facing=Math.atan2(dx,dz);distance-=step;if(step===d)path.shift();}return facing;}
