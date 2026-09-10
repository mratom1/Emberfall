import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import * as M from '../dist/model.js';
import {World,makeUnit,buildingModel} from '../dist/world.js';
import {readFileSync} from 'node:fs';
for(const rotated of [false,true]){
 const listeners={},old=globalThis.document;globalThis.document={documentElement:{classList:{contains:()=>rotated}}};
 const w={renderer:{domElement:{addEventListener:(k,f)=>listeners[k]=f,setPointerCapture(){}}},pointers:new Map(),zoom:1,target:{x:0,z:0},camera:{top:20,bottom:-20},container:{clientHeight:400},positionCamera(){},setZoom(z){this.zoom=z;},pick:()=>({}),callbacks:{click(){throw Error('Pinch must never deploy a unit');}}};
 World.prototype.bindInput.call(w);const e=(kind,id,x,y)=>listeners[kind]({pointerId:id,clientX:x,clientY:y});
 e('pointerdown',1,100,100);e('pointerdown',2,200,100);e('pointermove',2,250,100);e('pointerup',2,250,100);e('pointermove',1,100,100);assert.deepEqual(w.target,{x:0,z:0});e('pointerup',1,100,100);assert.equal(w.zoom,1.5);globalThis.document=old;
}
console.log('PASS Pinch release never pans the camera or deploys units in either screen orientation');
const hashes=new Set();assert.equal(Object.keys(M.TROOPS).length,22);
for(const [type,d] of Object.entries(M.TROOPS)){const h=createHash('sha256');const model=makeUnit(type);model.traverse(o=>{if(o.geometry)h.update(Buffer.from(o.geometry.attributes.position.array.buffer));});const hash=h.digest('hex');assert.ok(!hashes.has(hash),type+' must have a unique silhouette, not only colors');hashes.add(hash);const s=M.initialState();s.buildings.find(b=>b.type==='barracks').level=d.unlock||1;assert.ok(M.troopUnlocked(s,type));if(d.unlock>1){s.buildings.find(b=>b.type==='barracks').level=d.unlock-1;assert.equal(M.troopUnlocked(s,type),false);}}
console.log('PASS All 22 troops have distinct geometry and authoritative Barracks unlock gates');
const s=M.initialState();s.obstacles=[];s.flags=[{id:'flag-a',code:'mm',x:10,z:10},{id:'flag-b',code:'jp',x:12,z:10}];const gold=s.gold;assert.ok(M.flagAction(s,{type:'flag-select',code:'jp'}).ok);assert.equal(s.gold,gold);assert.equal(s.bannerCode,'jp');assert.ok(s.flags.every(f=>f.code==='jp'));assert.ok(M.flagAction(s,{type:'flag-select',code:'mm'}).ok);assert.ok(M.flagAction(s,{type:'flag-select',code:'us'}).error);let banners=0;buildingModel({type:'hall',level:15,x:0,z:0}).traverse(o=>{if(o.userData.banner){banners++;assert.ok(o.geometry.attributes.uv);}});assert.ok(banners>=3);
console.log('PASS Owned flag selection is free, validates ownership, updates every pole and preserves textured Town Hall banners');
const b=M.createBattle(s,0);b.started=true;b.buildings=[{id:'hall',type:'hall',x:0,z:-20,level:1,hp:1600,maxHp:1600}];b.units=[{id:'medic',type:'healer',level:2,x:0,z:0,hp:260,maxHp:260,damage:0,cooldown:0},{id:'friend',type:'guardian',x:1,z:0,hp:20,maxHp:190,damage:35,cooldown:0}];M.stepBattle(b,.1);assert.ok(b.units[1].hp>20);assert.equal(b.buildings[0].hp,1600);
console.log('PASS Medic heals living wounded allies without damaging buildings');
const css=readFileSync(new URL('../dist/village-ui.css',import.meta.url),'utf8'),game=readFileSync(new URL('../dist/game.js',import.meta.url),'utf8');assert.ok(!game.includes('<h3>Your buildings</h3>'));assert.ok(css.includes('.game-compact .battle-top{min-width:0'));assert.ok(css.includes('.hero-gallery{max-height:none'));
console.log('PASS Removed owned-building list and compact mobile HUD/gallery rules are shipped');
