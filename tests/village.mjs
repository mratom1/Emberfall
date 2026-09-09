import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import * as M from '../dist/model.js';
import * as X from '../dist/expansion.js';
import {World} from '../dist/world.js';
import {workItems,VillageUI} from '../dist/village-ui.js';
import {LAND_REGIONS,unlockedLand,landContains} from '../dist/content.js';
import {COUNTRIES,FLAG_COST} from '../dist/flags.js';
const now=Date.now(),fresh=()=>{const s=M.initialState(now);M.advance(s,now);s.obstacles=[];return s;};
let checks=0;const pass=name=>{checks++;console.log('PASS',name);};
{
 const s=fresh();s.buildings=s.buildings.filter(b=>b.type==='hall');
 assert.equal(M.canPlace(s,'mine',-28,10),false);s.buildings[0].level=3;
 assert.equal(M.canPlace(s,'mine',-28,10),true);assert.equal(M.canPlace(s,'mine',-28,0),false);
 assert.equal(M.canPlace(s,'mine',-18,9),false);assert.equal(M.canPlace(s,'mine',-23,10),false);
 s.buildings[0].level=7;assert.equal(M.canPlace(s,'mine',-28,0),true);assert.equal(M.canPlace(s,'mine',-28,4),true);
 assert.equal(M.canPlace(s,'mine',-40,0),false);s.buildings[0].level=11;assert.equal(M.canPlace(s,'mine',-40,0),true);
 assert.equal(M.canPlace(s,'mine',-36,0),true);assert.equal(M.canPlace(s,'mine',-50,0),false);
 assert.equal(unlockedLand({...s,realm:'builder'}).length,1);assert.equal(landContains(LAND_REGIONS,Infinity,0),false);
 pass('TH 3/7/11 land gates, bridge exclusions, full footprints and adjacent unlocked region seams');
}
{
 // Exercise the actual pointer handlers with a canvas event harness, without a browser.
 const listeners={},canvas={addEventListener(k,fn){listeners[k]=fn;},setPointerCapture(){}};
 const oldDocument=globalThis.document;globalThis.document={documentElement:{classList:{contains:()=>false}}};
 const w={renderer:{domElement:canvas},pointers:new Map(),placing:{type:'wall',x:0,z:0,pinned:true},zoom:1,
  target:{x:0,z:0},camera:{top:20,bottom:-20},container:{clientHeight:500},positionCamera(){},
  point:(x,y)=>({x:x/10,z:y/10}),pick:(x,y)=>({point:{x:x/10,z:y/10}}),
  updatePlacement(x,z){this.placing.x=x;this.placing.z=z;},setZoom(z){this.zoom=z;},callbacks:{}};
 w.callbacks.click=p=>{w.updatePlacement(p.point.x,p.point.z);w.placing.pinned=true;};World.prototype.bindInput.call(w);
 const event=(kind,x,y,id=1)=>listeners[kind]({clientX:x,clientY:y,pointerId:id,preventDefault(){}});
 try{
  event('pointerdown',40,40);event('pointerup',40,40);event('pointermove',300,200);
  assert.deepEqual([w.placing.x,w.placing.z],[4,4],'moving toward Confirm must not move the chosen building');
  event('pointerdown',40,40);event('pointermove',70,60);event('pointerup',70,60);event('pointermove',500,400);
  assert.deepEqual([w.placing.x,w.placing.z],[7,6],'released ghost remains pinned');
  event('pointerdown',70,60);event('pointerdown',100,60,2);event('pointermove',130,60,2);
  assert.ok(w.zoom>1);assert.deepEqual([w.placing.x,w.placing.z],[7,6]);event('pointercancel',130,60,2);event('pointercancel',70,60);
  const camera={resize(){}};World.prototype.setZoom.call(camera,100);assert.equal(camera.zoom,6.5);World.prototype.setZoom.call(camera,.01);assert.equal(camera.zoom,.48);
 }finally{globalThis.document=oldDocument;}
 pass('Mouse click/drag placement stays pinned while approaching Confirm; two-pointer zoom and expanded zoom limits');
}
{
 const s=fresh();s.buildings[0].level=15;s.buildings.find(b=>b.type==='barracks').level=15;
 s.buildings.push({id:'altar',type:'altar',level:1,x:8,z:8});s.dark=100000;
 const oldHero={...s.heroes.king,level:7};s.heroes={king:oldHero};X.ensure(s,now);
 assert.equal(X.HOME_HEROES.length,20);assert.equal(Object.keys(s.heroes).length,20);assert.equal(s.heroes.king.level,7);
 assert.ok(X.HOME_HEROES.every(k=>M.heroUnlocked(s,k)));
 const r=M.upgradeHero(s,'regent',now);assert.ok(r.ok);assert.equal(s.heroes.regent.startedAt,now);
 pass('Existing saves retain hero progress and gain all 20 heroes with valid endgame unlocks');
}
{
 const s=fresh();s.heroes.king.level=1;const b=M.createBattle(s,0);
 b.buildings=[{id:'dead',type:'hall',x:0,z:0,hp:0,maxHp:1000}];
 assert.equal(M.canDeploy(b,0,0),true);assert.ok(M.deployHero(s,b,'king',0,0).unit);
 assert.ok(M.deploy(s,b,'guardian',0,0).unit);b.buildings.push({id:'alive',type:'cannon',x:1,z:0,hp:100,maxHp:100});
 assert.equal(M.canDeploy(b,0,0),false);assert.ok(M.deploy(s,b,'guardian',0,0).error);assert.equal(M.canDeploy(b,NaN,0),false);
 const training=X.createModeBattle(s,'training',now).battle;training.buildings=[{id:'dead',type:'hall',x:0,z:0,hp:0,maxHp:100}];
 assert.ok(X.deploySiege(s,training,'ram',0,0).unit);
 b.land=LAND_REGIONS;b.buildings=[];assert.equal(M.canDeploy(b,-51,0),true);assert.equal(M.canDeploy(b,-80,0),false);
 b.buildings=[{id:'far',type:'mine',x:-40,z:0,hp:1000,maxHp:1000}];assert.ok(M.castSpell(s,b,'thunder',-40,0).ok);assert.ok(b.buildings[0].hp<1000);
 pass('Troops, heroes and siege deploy in cleared footprints; live neighbors block drops; spells reach expansion land');
}
{
 const svg=JSON.parse(await readFile(new URL('../dist/assets/country-flags.json',import.meta.url),'utf8'));
 assert.equal(COUNTRIES.length,250);assert.equal(new Set(COUNTRIES.map(c=>c.code)).size,250);
 for(const c of COUNTRIES){assert.match(svg[c.code],/<svg/);assert.doesNotMatch(svg[c.code],/<script|onload\s*=/i);}
 const s=fresh(),before=s.gold;assert.ok(M.applyAction(s,{type:'flag-buy',code:'mm',x:9,z:8,cost:0},now).ok);
 assert.equal(s.gold,before-FLAG_COST);const f=s.flags[0];
 assert.ok(M.applyAction(s,{type:'flag-buy',code:'jp',x:9,z:8},now).error);
 assert.ok(M.applyAction(s,{type:'flag-buy',code:'__proto__',x:12,z:8},now).error);
 assert.ok(M.applyAction(s,{type:'flag-move',id:f.id,x:9,z:8},now).ok);
 assert.ok(M.applyAction(s,{type:'flag-move',id:f.id,x:10,z:8},now).ok);assert.equal(s.gold,before-FLAG_COST);
 s.gold=0;assert.ok(M.applyAction(s,{type:'flag-buy',code:'jp',x:12,z:8},now).error);
 assert.ok(M.applyAction(s,{type:'flag-buy',code:'jp',x:12,z:8,realm:'builder'},now).error);
 pass('250 bundled flag images, authoritative price, valid country, collisions, free movement and insufficient balance');
}
{
 const s=fresh();s.buildings.push({id:'altar',type:'altar',level:1,x:8,z:8});s.buildings[0].level=2;s.dark=10000;
 const mine=s.buildings.find(b=>b.type==='mine');assert.ok(M.upgrade(s,mine,now).ok);assert.ok(M.upgradeHero(s,'king',now).ok);
 const at=now+7500,items=workItems(s,at),building=items.find(w=>w.id===mine.id),hero=items.find(w=>w.id==='king');
 assert.equal(building.progress,.5);assert.equal(building.remaining,7500);assert.equal(building.gems,1);assert.ok(hero.progress>0&&hero.progress<1);
 const gems=s.gems;assert.ok(M.applyAction(s,{type:'skip',kind:'building',id:mine.id,gems:0},at).ok);assert.equal(mine.level,2);assert.equal(s.gems,gems-1);
 assert.ok(M.applyAction(s,{type:'skip',kind:'building',id:mine.id},at).error);assert.equal(s.gems,gems-1);
 const heroCost=M.skipCost(s.heroes.king.finishAt,at);assert.ok(M.applyAction(s,{type:'skip',kind:'hero',id:'king'},at).ok);
 assert.equal(s.heroes.king.level,1);assert.equal(s.gems,gems-1-heroCost);assert.equal(workItems(s,at).length,0);
 assert.ok(M.upgradeHero(s,'king',at).ok);s.gems=0;assert.ok(M.applyAction(s,{type:'skip',kind:'hero',id:'king'},at).error);assert.ok(s.heroes.king.finishAt>at);
 pass('World progress reflects elapsed time; building/hero Gem finish charges server-calculated cost once and rejects insufficient Gems');
}
{
 const calls=[],button={dataset:{village:'finish'},isConnected:false};
 const ui={activeWork:{kind:'hero',id:'machine',realm:'builder'},b:{mutate:async a=>calls.push(a),toast(){},closeModal(){}},sync(){}};
 await VillageUI.prototype.handle.call(ui,button);assert.deepEqual(calls,[{type:'skip',kind:'hero',id:'machine',realm:'builder'}]);
 pass('Clicking Finish on a hero upgrade sends the correct hero ID and saved village realm');
}
{
 const s=fresh(),hall=s.buildings[0],store=s.buildings.find(b=>b.type==='storage');
 for(let level=1;level<15;level++){
  hall.level=level;store.level=level;const cost=M.upgradeCost(hall);assert.ok(M.capacity(s)>=cost.gold,'TH '+level+' upgrade fits storage');
  s.gold=M.capacity(s);s.elixir=M.capacity(s);assert.ok(M.upgrade(s,hall,now).ok);M.advance(s,hall.finishAt);assert.equal(hall.level,level+1);
 }
 store.level=15;for(let i=1;i<M.TYPES.storage.max;i++)s.buildings.push({...store,id:'store-'+i});for(const type of Object.keys(M.TYPES).filter(k=>k!=='flag'))assert.ok(M.capacity(s)>=M.upgradeCost({type,level:14}).gold,type+' level 15 is affordable');
 assert.ok(M.upgrade(s,hall,now).error);
 pass('Town Hall upgrades reach 15 within real storage capacities and all final building upgrade costs fit');
}
console.log(`${checks} village checks passed.`);
