import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import * as M from '../dist/model.js';
import {World} from '../dist/world.js';
import * as THREE from '../dist/assets/three.module.js';

const now=1900000000000;
let passed=0;
const check=(name,fn)=>{fn();passed++;console.log('PASS',name);};

check('Construction charges once, prevents overlapping placement, and completes on time',()=>{
  const s=M.initialState(now),before=s.gold;
  assert.equal(M.canPlace(s,'mine',0,0),false);
  let spot;
  for(let x=-9;x<=9&&!spot;x+=.5)for(let z=-9;z<=9;z+=.5)if(M.canPlace(s,'mine',x,z)){spot=[x,z];break;}
  assert.ok(spot);const r=M.build(s,'mine',...spot,now);assert.ok(r.building);
  assert.equal(s.gold,before-M.TYPES.mine.gold);assert.equal(M.freeBuilders(s),1);
  assert.ok(M.build(s,'well',...spot,now).error);
  M.advance(s,now+11999);assert.equal(r.building.constructing,true);
  M.advance(s,now+12000);assert.equal(r.building.constructing,false);assert.equal(M.freeBuilders(s),2);
});

check('Upgrades respect builder and hall gates and increase levels only on completion',()=>{
  const s=M.initialState(now);s.gold=50000;s.elixir=50000;
  const mine=s.buildings.find(b=>b.type==='mine'),well=s.buildings.find(b=>b.type==='well'),tower=s.buildings.find(b=>b.type==='tower');
  assert.ok(M.upgrade(s,mine,now).ok);assert.ok(M.upgrade(s,well,now).ok);assert.ok(M.upgrade(s,tower,now).error);assert.equal(mine.level,1);
  M.advance(s,now+16000);assert.equal(mine.level,2);assert.equal(well.level,2);assert.equal(s.stats.upgraded,2);assert.ok(M.upgrade(s,mine,now+17000).error);
});

check('Training queues serialize, charge elixir, and cannot exceed army capacity',()=>{
  const s=M.initialState(now),before=s.elixir;assert.ok(M.train(s,'guardian',now).ok);assert.ok(M.train(s,'ranger',now).ok);assert.equal(s.elixir,before-115);
  M.advance(s,now+2100);assert.equal(s.army.guardian,10);assert.equal(s.army.ranger,5);
  M.advance(s,now+5100);assert.equal(s.army.ranger,6);assert.equal(s.stats.trained,2);
  s.elixir=100000;let n=0;while(M.train(s,'guardian',now+6000).ok){n++;assert.ok(n<100);}
  assert.equal(M.armySize(s.army)+M.queueSize(s),M.armyCapacity(s));
});

check('Production and collection obey both producer storage and village capacity',()=>{
  const s=M.initialState(now);M.advance(s,now+3600000*20);
  for(const b of s.buildings.filter(b=>M.producerRate(b)))assert.equal(b.stored,M.productionCapacity(b));
  s.gold=M.capacity(s)-10;const r=M.collect(s);assert.equal(r.gold,10);assert.equal(s.gold,M.capacity(s));assert.ok(r.elixir>0);
  const mine=s.buildings.find(b=>b.type==='mine');assert.equal(mine.stored,590);
});

check('Deployment rejects the protected center and consumes only deployed troops',()=>{
  const s=M.initialState(now),b=M.createBattle(s,0);assert.ok(M.deploy(s,b,'guardian',0,0).error);assert.equal(s.army.guardian,9);
  assert.ok(M.deploy(s,b,'guardian',0,11).unit);assert.equal(s.army.guardian,8);assert.equal(b.remaining.guardian,8);assert.equal(s.army.ranger,5);
  assert.ok(M.deploy(s,b,'ranger',50,50).error);assert.equal(s.army.ranger,5);
});

check('A starter army can complete a real raid and settlement is idempotent',()=>{
  const s=M.initialState(now),b=M.createBattle(s,0);
  for(const type of Object.keys(M.TROOPS)){let i=0;while(b.remaining[type])M.deploy(s,b,type,(i++%5-2)*1.1,11);}
  let defenseEvents=0;for(let i=0;i<2600&&!b.ended;i++)M.stepBattle(b,.05,e=>{if(e.kind==='defend')defenseEvents++;});
  assert.ok(defenseEvents>0);assert.equal(b.ended,true);assert.equal(b.stats.stars,3);assert.equal(b.stats.percent,100);
  const before=s.gold,result=M.settleBattle(s,b);assert.equal(s.gold,before+result.gold);assert.equal(s.stats.wins,1);assert.equal(s.cleared[0],3);
  const settled=s.gold;M.settleBattle(s,b);assert.equal(s.gold,settled);assert.equal(s.stats.wins,1);
});

check('Thunder is limited and applies damage only inside its radius',()=>{
  const b=M.createBattle(M.initialState(now),0),hall=b.buildings.find(x=>x.type==='hall'),store=b.buildings.find(x=>x.type==='storage');
  const hp=hall.hp,storeHp=store.hp;assert.ok(M.strike(b,hall.x,hall.z));assert.equal(hall.hp,hp-350);assert.equal(store.hp,storeHp);assert.ok(M.strike(b,hall.x,hall.z));assert.equal(M.strike(b,hall.x,hall.z),false);
});

check('Retreat preserves reserves, quests pay once, and saved progress reloads',()=>{
  const s=M.initialState(now),b=M.createBattle(s,0);M.deploy(s,b,'guardian',0,11);M.settleBattle(s,b);assert.equal(s.army.guardian,8);assert.equal(s.army.giant,1);
  s.stats.built=1;assert.equal(M.claimQuest(s,'build'),true);const gold=s.gold;assert.equal(M.claimQuest(s,'build'),false);assert.equal(s.gold,gold);
  const loaded=M.loadState({getItem:()=>JSON.stringify(s)},now+10000);assert.equal(loaded.army.guardian,8);assert.ok(loaded.claimed.includes('build'));assert.equal(loaded.gold,gold);
  const reset=M.loadState({getItem:()=>'{broken'},now);assert.equal(reset.gold,4000);
});

check('Obstacle gems use random outcomes, require time, and block building placement',()=>{
 const s=M.initialState(now),tree=s.obstacles.find(o=>o.type==='tree');assert.equal(M.canPlace(s,'mine',tree.x,tree.z),false);
 const old=s.gems;assert.ok(M.clearObstacle(s,tree.id,now,()=>0).ok);assert.equal(s.gems,old);assert.equal(M.freeBuilders(s),1);
 M.advance(s,now+8000);assert.equal(s.gems,old+1);assert.ok(!s.obstacles.some(o=>o.id===tree.id));M.advance(s,now+18000);assert.equal(s.gems,old+1);
 const rock=s.obstacles.find(o=>o.type==='rock');M.clearObstacle(s,rock.id,now+18000,()=>.9);M.advance(s,now+31000);assert.equal(s.gems,old+1);
});
check('Town Hall, Barracks, Laboratory, Hero Hall and Spell Forge control progression',()=>{
 const s=M.initialState(now);s.gold=100000;s.elixir=100000;s.dark=100000;
 assert.ok(M.train(s,'wyvern',now).error);s.buildings.find(b=>b.type==='hall').level=5;s.buildings.find(b=>b.type==='barracks').level=5;
 s.buildings.push({id:'lab',type:'laboratory',level:3,x:0,z:12},{id:'altar',type:'altar',level:1,x:10,z:0},{id:'forge',type:'forge',level:3,x:0,z:-12});
 assert.ok(M.train(s,'wyvern',now).ok);assert.ok(M.beginResearch(s,'guardian',now).ok);assert.ok(M.beginResearch(s,'ranger',now).error);
 assert.ok(M.upgradeHero(s,'king',now).ok);assert.ok(M.brew(s,'heal',now).ok);M.advance(s,now+40000);assert.equal(s.heroes.king.level,1);assert.equal(s.research.guardian,2);assert.equal(s.spells.heal,1);
 const b=M.createBattle(s,0);assert.ok(M.deployHero(s,b,'king',0,11,now+40000).unit);assert.ok(M.heroAbility(b,'king').ok);assert.ok(M.heroAbility(b,'king').error);
 const u=b.units[0];u.hp=100;assert.ok(M.castSpell(s,b,'heal',0,11).ok);M.stepBattle(b,.1);assert.ok(u.hp>100);assert.equal(s.spells.heal,0);
});
check('Gem spending cannot exceed the wallet and builder hiring stops at five',()=>{
 const s=M.initialState(now);assert.ok(M.applyAction(s,{type:'builder'},now).error);s.gems=2000;assert.ok(M.applyAction(s,{type:'builder'},now).ok);assert.equal(s.builders,3);assert.equal(s.gems,1750);
 const mine=s.buildings.find(b=>b.type==='mine');M.upgrade(s,mine,now);const gems=s.gems;assert.ok(M.applyAction(s,{type:'skip',id:mine.id,kind:'building'},now).ok);assert.ok(s.gems<gems);assert.equal(mine.level,2);
 s.builders=5;assert.ok(M.applyAction(s,{type:'builder'},now).error);
});

check('Placement uses an actual translucent building model and validates its footprint',()=>{
 const s=M.initialState(now),w=Object.create(World.prototype);w.scene=new THREE.Scene();w.placement=new THREE.Mesh(new THREE.PlaneGeometry(1,1),new THREE.MeshBasicMaterial());w.buildGrid=new THREE.Group();let preview;
 w.callbacks={placement:p=>{preview=p;}};w.setPlacement('mine',s);assert.ok(w.ghost);assert.ok(preview.valid);assert.ok(w.buildGrid.visible);
 const meshes=[];w.ghost.traverse(o=>{if(o.isMesh)meshes.push(o);});assert.ok(meshes.length>0);assert.ok(meshes.every(m=>m.material.transparent&&m.material.opacity<1));
 w.updatePlacement(0,0);assert.equal(preview.valid,false);assert.equal(w.ghost.position.x,0);w.rotatePlacement();assert.equal(w.ghost.rotation.y,Math.PI/2);
 w.setPlacement(null);assert.equal(w.ghost,null);assert.equal(w.buildGrid.visible,false);
});

check('Every authored local page asset exists and IDs are unique',()=>{
  const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../dist'),html=fs.readFileSync(path.join(root,'index.html'),'utf8');
  const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]);assert.equal(new Set(ids).size,ids.length);
  for(const [,url]of html.matchAll(/(?:src|href)="(\/[^"#]+)"/g))assert.ok(fs.existsSync(path.join(root,url.split('?')[0])),url);
  for(const file of ['game.js','world.js','model.js','features.js','connection.js']){const js=fs.readFileSync(path.join(root,file),'utf8');for(const [,ref]of js.matchAll(/from ['"](\.[^'"]+)['"]/g))assert.ok(fs.existsSync(path.resolve(root,ref.split('?')[0])),ref);}
  assert.ok(fs.statSync(path.join(root,'assets/campaign.webp')).size>5000);
});
console.log(`${passed} gameplay and asset checks passed.`);
