import assert from 'node:assert/strict';
import * as M from '../dist/model.js';
import {villageNavigator,advanceRoute} from '../dist/village-paths.js';
import {workItems} from '../dist/village-ui.js';
import {obstacleModel,riverPoint,riverWidth} from '../dist/world.js';
import {readFileSync} from 'node:fs';
const s=M.initialState(1000);s.obstacles=[];s.flags=[];s.buildings=[{id:'hall',type:'hall',level:3,x:0,z:0},{id:'barracks',type:'barracks',level:3,x:4,z:4},{id:'camp',type:'camp',level:3,x:-28,z:10}];
const nav=villageNavigator(s),path=nav.route({x:4,z:6},{x:-28,z:12});assert.ok(path?.length);assert.ok(path.some(p=>p.x<-15&&p.x>-23));assert.ok(path.filter(p=>p.x<-14.5&&p.x>-23).every(p=>Math.abs(p.z-12)<=.5));assert.ok(path.every(p=>nav.open(p.x,p.z)));const position={x:4,z:6};advanceRoute(position,path,200);assert.equal(path.length,0);assert.deepEqual(position,{x:-28,z:12});assert.equal(nav.route({x:4,z:6},{x:-28,z:12},true).length,1);
console.log('PASS Ground routes avoid footprints, cross the actual bridge and reach west-bank camps; flyers use air routes');
for(const type of ['tree','rock','gem-box']){const state=M.initialState(1000);state.obstacles=[{id:type,type,x:10,z:10}];const start=M.clearObstacle(state,type,1000,()=>.1);assert.ok(start.ok);const item=workItems(state,4000).find(w=>w.kind==='obstacle');assert.ok(item&&item.progress>0&&item.progress<1);assert.ok(item.remaining>0);const before=state.gems;assert.ok(M.applyAction(state,{type:'skip',kind:'obstacle',id:type},4000).ok);assert.ok(!state.obstacles.some(o=>o.id===type));assert.ok(state.gems>=before-item.gems);}
console.log('PASS Tree, rock and Gem Box removal exposes countdown/progress and authoritative Gem completion');
const original=Math.random;try{for(const rock of [false,true]){const state=M.initialState(1000);state.buildings=[];state.obstacles=[];state.nextObstacleAt=1000;Math.random=()=>rock?.9:.1;M.advanceProgression(state,1001);assert.ok(state.obstacles.some(o=>o.type===(rock?'rock':'tree')));assert.ok(state.nextObstacleAt>1001);}}finally{Math.random=original;}
console.log('PASS Periodic regrowth produces both trees and rocks and schedules the next interval');

for(const type of ['tree','rock','gem-box']){const model=obstacleModel({id:'click-'+type,type,x:4,z:5,variant:2});let meshes=0;model.traverse(node=>{if(node.isMesh){meshes++;assert.equal(node.userData.obstacleId,'click-'+type);}});assert.ok(meshes>0);}
console.log('PASS Every rendered obstacle mesh carries its clear-click target');

{const now=5000,state=M.initialState(now),tree=state.obstacles.find(o=>o.type==='tree');state.nextObstacleAt=now+1800000;assert.ok(M.clearObstacle(state,tree.id,now,()=>0).ok);assert.equal(state.nextObstacleAt,now+300000);const timer=workItems(state,now+1000).find(w=>w.kind==='obstacle'&&w.id===tree.id);assert.ok(timer&&timer.remaining===7000&&timer.progress>0);M.advanceProgression(state,tree.finishAt);assert.ok(!state.obstacles.some(o=>o.id===tree.id));}
console.log('PASS Clearing starts a visible timer and schedules randomized obstacle replacement');

{const variants=new Set(M.seedObstacles().filter(o=>o.type==='tree').map(o=>o.variant));assert.deepEqual([...variants].sort(),[0,1,2,3]);const source=readFileSync(new URL('../dist/world.js',import.meta.url),'utf8');assert.ok(!source.includes('landContains(LAND_REGIONS.slice(1),x,z,-1)'));}
console.log('PASS All four supplied tree variants are seeded and scenery stays outside playable land');

{const points=[];for(let z=-68;z<=68;z+=.5){const p=riverPoint(z);points.push(p);assert.ok(riverWidth(z)>2.4&&riverWidth(z)<4);if(points.length>1)assert.ok(Math.hypot(p.x-points.at(-2).x,p.z-points.at(-2).z)<.8);}assert.equal(points[0].z,-68);assert.equal(points.at(-1).z,68);}
console.log('PASS The stream is continuous beyond both map edges with smoothly varying natural width');

const {World}=await import('../dist/world.js');const THREE=await import('../dist/assets/three.module.js');const world={scene:new THREE.Group(),callbacks:{notice(){}}};s.army={};s.research={};World.prototype.setCampArmy.call(world,s,false);s.army.guardian=1;World.prototype.setCampArmy.call(world,s,false);const first=world.campArmy.children[0];assert.ok(Math.hypot(first.position.x-4,first.position.z-6)<2);assert.ok(first.userData.path.some(p=>p.x<-15&&p.x>-23));s.army.ranger=1;World.prototype.setCampArmy.call(world,s,false);assert.equal(world.campArmy.children[0],first);assert.equal(world.campArmy.children.length,2);for(const m of world.campArmy.children){assert.ok(m.userData.path.length);advanceRoute(m.position,m.userData.path,300);assert.ok(m.position.x<-23);}
console.log('PASS Newly trained units start at Barracks, retain in-progress journeys, and arrive at the assigned Camp');

world.setWorkers=World.prototype.setWorkers;world.stepWorkers=World.prototype.stepWorkers;world.setWorkers(s,false);assert.equal(world.workers.children.length,8);let crossed=false,working=false;
for(let i=0;i<2400;i++){world.stepWorkers(.05,i*.05);for(const worker of world.workers.children){assert.ok(world.workerNav.open(worker.position.x,worker.position.z));if(worker.position.x<-15&&worker.position.x>-23)crossed=true;if(!worker.userData.path.length&&worker.userData.joints.rightArm.rotation.x!==0)working=true;}}
assert.ok(crossed);assert.ok(working);world.setWorkers(s,true);assert.equal(world.workers.visible,false);
console.log('PASS Workers walk around occupied footprints, cross the bridge, work at destinations and hide during battle');
const originalFrame=globalThis.requestAnimationFrame,originalMedia=globalThis.matchMedia;globalThis.requestAnimationFrame=fn=>setTimeout(fn,5);globalThis.matchMedia=()=>({matches:true});
try{world.camera=new THREE.OrthographicCamera(-20,20,10,-10,.1,200);await World.prototype.journey.call(world,true);assert.equal(world.journeyActive,true);assert.ok(world.journeyGroup.children[0].material.opacity>.9);assert.ok(world.journeyGroup.children[0].scale.x>=40);assert.ok(world.journeyGroup.children.slice(1).every(x=>x.geometry.type==='PlaneGeometry'&&x.material.map?.isDataTexture));await World.prototype.journey.call(world,false);assert.equal(world.journeyActive,false);assert.equal(world.journeyGroup.visible,false);}finally{globalThis.requestAnimationFrame=originalFrame;globalThis.matchMedia=originalMedia;}
console.log('PASS Soft cloud layers cover the viewport without clipped spherical rings and release after arrival');
