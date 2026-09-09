import assert from 'node:assert/strict';
import {Connection} from '../dist/connection.js';
import {landscapeLayout, gamePoint, gameDelta, installLandscape, enterLandscapeFullscreen} from '../dist/viewport.js';

let checks = 0;
const pass = name => { checks++; console.log('PASS', name); };
const html = '<!doctype html><html><body>Static game page</body></html>';
for (const headers of [{'Content-Type':'text/html; charset=utf-8'}, {}]) {
  const connection = new Connection({fetcher: async () => new Response(html, {headers})});
  assert.equal(await connection.connect(), null);
  assert.equal(connection.status, 'standalone');
  assert.equal(connection.online, false);
}
pass('HTTP 200 HTML fallback starts a standalone village with and without a content type');

const originalDocument = globalThis.document;
try {
  globalThis.document = {querySelector: () => ({content:'server'})};
  for (const response of [() => new Response(html, {headers:{'Content-Type':'text/html'}}), () => new Response('', {status:404}), () => new Response('{broken')]) {
    const connection = new Connection({fetcher: async () => response()});
    await assert.rejects(connection.connect(), /server|configuration/);
    assert.notEqual(connection.status, 'standalone');
  }
  pass('Server-only villages never become editable standalone villages after a bad API response');
} finally { globalThis.document = originalDocument; }

for (const response of [() => new Response('{broken', {headers:{'Content-Type':'application/json'}}), () => new Response('null'), () => new Response(html, {status:503})]) {
  const connection = new Connection({fetcher: async () => response()});
  await assert.rejects(connection.connect(), /configuration|server/);
}
pass('Invalid JSON and server outages display readable errors without silently switching modes');

const routes = [];
const online = new Connection({fetcher: async (route, options) => {
  routes.push([route, options?.method]);
  return Response.json(route === '/api/config' ? {server:true, packs:[]} : {user:{id:'village-1'}, csrf:'session-token', state:{gold:50}});
}});
assert.equal((await online.connect()).state.gold, 50);
assert.equal(online.online, true);
assert.deepEqual(routes, [['/api/config', undefined], ['/api/session', 'POST']]);
online.fetcher = async () => new Response(html);
await assert.rejects(online.connect(), /server/);
assert.equal(online.online, true);
pass('Real servers still start a session and retain their authority during reconnect failures');

assert.deepEqual(landscapeLayout(393, 785), {rotated:true, width:785, height:393});
assert.deepEqual(landscapeLayout(785, 393), {rotated:false, width:785, height:393});
assert.deepEqual(landscapeLayout(500, 900, false), {rotated:false, width:500, height:900});
pass('Touch portrait views immediately use landscape dimensions while desktop windows stay upright');

const physical = {left:17, top:38, width:393, height:785};
for (const [x,y] of [[0,0],[1,0],[0,1],[1,1],[.2,.7],[.5,.5]]) {
  const point = gamePoint(physical.left + (1-y)*physical.width, physical.top+x*physical.height, physical, true);
  assert.ok(Math.abs(point.x-x) < 1e-10 && Math.abs(point.y-y) < 1e-10);
}
assert.deepEqual(gamePoint(110,70,{left:10,top:20,width:200,height:100}),{x:.5,y:.5});
assert.deepEqual(gameDelta(12,30,true),{x:30,y:-12});
assert.deepEqual(gameDelta(12,30,false),{x:12,y:30});
pass('Building selection, placement and camera dragging follow the rotated canvas at its corners and center');

// Exercise browser refusal and the transition to a native landscape viewport without a GPU.
const names = ['document','window','screen','navigator','matchMedia','innerWidth','innerHeight'];
const originals = names.map(name => [name, Object.getOwnPropertyDescriptor(globalThis,name)]);
try {
  const classes = new Set(), properties = new Map(), root = {
    style:{setProperty:(key,value)=>properties.set(key,value)},
    classList:{toggle:(key,on)=>on?classes.add(key):classes.delete(key), contains:key=>classes.has(key)},
    requestFullscreen:async()=>{throw new Error('Fullscreen denied by embedded browser');}
  };
  const doc = new EventTarget(); doc.documentElement = root;
  const win = new EventTarget(); win.visualViewport = new EventTarget();
  const orientation = new EventTarget(); orientation.lock = async()=>{throw new Error('Orientation lock unavailable');};
  for (const [key,value] of Object.entries({document:doc,window:win,screen:{orientation},navigator:{maxTouchPoints:5},matchMedia:()=>({matches:true}),innerWidth:393,innerHeight:785})) {
    Object.defineProperty(globalThis,key,{value,configurable:true,writable:true});
  }
  installLandscape();
  assert.ok(classes.has('landscape-rotated'));
  assert.equal(properties.get('--game-width'),'785px');
  await enterLandscapeFullscreen();
  assert.ok(classes.has('landscape-rotated'));
  globalThis.innerWidth=785; globalThis.innerHeight=393; win.dispatchEvent(new Event('resize'));
  assert.ok(!classes.has('landscape-rotated'));
  assert.equal(properties.get('--game-width'),'785px');
  assert.equal(properties.get('--game-height'),'393px');
  pass('Rejected fullscreen/rotation APIs leave the game playable and a real rotation never rotates twice');
} finally {
  for (const [name,descriptor] of originals) { if(descriptor)Object.defineProperty(globalThis,name,descriptor);else delete globalThis[name]; }
}
console.log(`${checks} WebView regression checks passed.`);
