import assert from 'node:assert/strict';
import * as M from '../dist/model.js';
import {buildingModel,makeUnit} from '../dist/world.js';
import * as THREE from '../dist/assets/three.module.js';
for(const type of Object.keys(M.DEFENSES)){
 let previous=0;for(let level=1;level<=15;level++){const d=M.defenseStats({type,level});assert.ok(d.damage/d.rate>previous);previous=d.damage/d.rate;}
}
assert.equal(M.defenseStats({type:'hall',level:6}),null);assert.ok(M.defenseStats({type:'hall',level:7}));
console.log('PASS Defense DPS scales at every level; Town Hall weapon unlocks at level 7');
function fight(strategy){
 const s=M.initialState();M.advance(s);s.buildings[0].level=5;s.buildings.find(b=>b.type==='camp').level=5;s.army={ranger:24};s.research.ranger=7;assert.ok(M.armySize(s.army)<=M.armyCapacity(s));
 const b=M.createBattle(s,0);b.bounds=15.2;b.heroStock={};b.remaining={ranger:24};
 b.buildings=[{id:'hall',type:'hall',level:5,x:0,z:-10},{id:'mortar',type:'mortar',level:6,x:0,z:3}].map(x=>({...x,hp:M.buildingHp(x),maxHp:M.buildingHp(x),cooldown:0}));
 for(let i=0;i<24;i++){const point=strategy==='clustered'?[0,17]:[[0,17],[17,0],[0,-17],[-17,0]][i%4];assert.ok(M.deploy(s,b,'ranger',...point).unit);}
 while(!b.ended&&b.elapsed<151)M.stepBattle(b,.1);return b.stats;
}
const clustered=fight('clustered'),split=fight('split');assert.equal(clustered.stars,0);assert.ok(split.stars>=1);
console.log(`PASS Identical 24-ranger army: clustered ${clustered.stars} stars, flanking ${split.stars} stars against the same legal-level defenses`);
for(const type of ['wall','hall','cannon','barracks']){
 const low=buildingModel({type,level:1,x:0,z:0}),high=buildingModel({type,level:15,x:0,z:0});
 const size=g=>new THREE.Box3().setFromObject(g).getSize(new THREE.Vector3());assert.ok(size(high).y>size(low).y*1.2,type+' grows structurally');
 let a=0,z=0;low.traverse(o=>a+=o.geometry?.attributes.position.count||0);high.traverse(o=>z+=o.geometry?.attributes.position.count||0);assert.ok(z>a*1.2,type+' gains geometry');
}
for(const type of ['guardian','ranger','king']){let a=0,z=0;makeUnit(type,false,{level:1}).traverse(o=>a+=o.geometry?.attributes.position.count||0);makeUnit(type,false,{level:type==='king'?50:15}).traverse(o=>z+=o.geometry?.attributes.position.count||0);assert.ok(type==='king'?z-a>=2000:z>a*1.3,type);}
for(let level=1;level<15;level++)assert.ok(M.buildingHp({type:'wall',level:level+1})>M.buildingHp({type:'wall',level}));
console.log('PASS Buildings/walls grow in height and geometry; troops/heroes gain physical armor; wall HP rises at every level');
