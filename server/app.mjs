import {createOAuth, callbackHTML} from './oauth.mjs';
import {startBackups} from './backups.mjs';
import http from 'node:http';
import {DatabaseSync} from 'node:sqlite';
import {randomBytes,randomUUID,randomInt,createHash} from 'node:crypto';
import {readFile,mkdir} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import * as M from '../dist/model.js';
import * as X from '../dist/expansion.js';
import {createFrontiers} from './frontiers.mjs';
import {passwordHash,passwordMatches,setSecurityHeaders,validPassword,authTransportAllowed} from './security.mjs';
import {verifyWebhook,createCheckout,packById} from './payments.mjs';

const here=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(here,'../dist');
function fail(message,status=400){throw Object.assign(new Error(message),{status});}
const hash=s=>createHash('sha256').update(s).digest('hex');
const safeUser=u=>({id:u.id,name:u.name,registered:!!(u.password_hash||u.providers?.length),hasPassword:!!u.password_hash,providers:u.providers||[],clanId:u.clan_id});
export async function createApp(config={}){
 const port=Number(config.port??process.env.PORT??8080),dataDir=config.dataDir||process.env.DATA_DIR||path.resolve(here,'../data');await mkdir(dataDir,{recursive:true});
 const db=new DatabaseSync(path.join(dataDir,'emberfall.sqlite'));db.exec('PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON; PRAGMA busy_timeout=5000;');
 db.exec(`CREATE TABLE IF NOT EXISTS players(id TEXT PRIMARY KEY,name TEXT NOT NULL,login TEXT UNIQUE,password_hash TEXT,state TEXT NOT NULL,glory INTEGER NOT NULL DEFAULT 0,clan_id TEXT,updated_at INTEGER NOT NULL);
 CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,player_id TEXT NOT NULL REFERENCES players(id),csrf TEXT NOT NULL,expires_at INTEGER NOT NULL);
 CREATE TABLE IF NOT EXISTS battles(id TEXT PRIMARY KEY,player_id TEXT NOT NULL REFERENCES players(id),defender_id TEXT,state TEXT NOT NULL,last_step INTEGER NOT NULL,created_at INTEGER NOT NULL,settled INTEGER NOT NULL DEFAULT 0);
 CREATE INDEX IF NOT EXISTS battle_player ON battles(player_id,settled);
 CREATE TABLE IF NOT EXISTS commands(player_id TEXT NOT NULL,request_id TEXT NOT NULL,response TEXT NOT NULL,created_at INTEGER NOT NULL,PRIMARY KEY(player_id,request_id));
 CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY,player_id TEXT NOT NULL REFERENCES players(id),pack TEXT NOT NULL,gems INTEGER NOT NULL,cents INTEGER NOT NULL,currency TEXT NOT NULL DEFAULT 'usd',stripe_id TEXT UNIQUE,status TEXT NOT NULL DEFAULT 'pending',created_at INTEGER NOT NULL);
 CREATE TABLE IF NOT EXISTS payment_events(id TEXT PRIMARY KEY,processed_at INTEGER NOT NULL);
 CREATE TABLE IF NOT EXISTS clans(id TEXT PRIMARY KEY,name TEXT UNIQUE NOT NULL,owner_id TEXT NOT NULL REFERENCES players(id),created_at INTEGER NOT NULL);
 CREATE TABLE IF NOT EXISTS chat(id INTEGER PRIMARY KEY AUTOINCREMENT,clan_id TEXT NOT NULL,player_id TEXT NOT NULL,message TEXT NOT NULL,created_at INTEGER NOT NULL);
 CREATE TABLE IF NOT EXISTS raid_log(id TEXT PRIMARY KEY,attacker_id TEXT NOT NULL,defender_id TEXT,result TEXT NOT NULL,created_at INTEGER NOT NULL);`);
 const settings={origin:(config.origin||process.env.PUBLIC_URL||'').replace(/\/$/,''),stripeKey:config.stripeKey??process.env.STRIPE_SECRET_KEY??'',webhookSecret:config.webhookSecret??process.env.STRIPE_WEBHOOK_SECRET??'',secure:config.secure??(process.env.COOKIE_SECURE==='true'),fetcher:config.fetcher||fetch};
 if(process.env.NODE_ENV==='production'&&(!settings.origin.startsWith('https://')||!settings.secure))throw new Error('Production requires PUBLIC_URL=https://your-domain and COOKIE_SECURE=true.');
 const paymentEnabled=!!(settings.stripeKey&&settings.webhookSecret&&settings.origin.startsWith('https://'));
 const rate=new Map();const tx=fn=>{db.exec('BEGIN IMMEDIATE');try{const r=fn();db.exec('COMMIT');return r;}catch(e){db.exec('ROLLBACK');throw e;}};
 const getUser=id=>{const u=db.prepare('SELECT * FROM players WHERE id=?').get(id);if(u)u.providers=db.prepare('SELECT provider FROM auth_identities WHERE player_id=? ORDER BY provider').all(id).map(r=>r.provider);return u;};
 function stateOf(u,now=Date.now()){u=getUser(u.id)||u;const s=JSON.parse(u.state);M.advance(s,now);return s;}
 function persist(u,s,now=Date.now()){db.prepare('UPDATE players SET state=?,glory=?,updated_at=? WHERE id=?').run(JSON.stringify(s),s.glory,now,u.id);}
 const oauth=createOAuth({db,settings,config:config.oauth,tx,getUser,newSession,snapshot});
 const frontiers=createFrontiers({db,M,getUser,stateOf,persist,fail});
 function newSession(id,res){db.prepare('DELETE FROM sessions WHERE player_id=? AND token_hash NOT IN (SELECT token_hash FROM sessions WHERE player_id=? ORDER BY expires_at DESC LIMIT 9)').run(id,id);const token=randomBytes(32).toString('hex'),csrf=randomBytes(24).toString('hex'),expires=Date.now()+30*86400000;db.prepare('INSERT INTO sessions VALUES(?,?,?,?)').run(hash(token),id,csrf,expires);res.setHeader('Set-Cookie',`emberfall_session=${token}; HttpOnly; SameSite=Lax; Path=/; Max-Age=2592000${settings.secure?'; Secure':''}`);return {csrf,player_id:id};}
 function sessionOf(req){const token=/(?:^|;\s*)emberfall_session=([a-f0-9]{64})(?:;|$)/.exec(req.headers.cookie||'')?.[1];if(!token)return null;return db.prepare('SELECT * FROM sessions WHERE token_hash=? AND expires_at>?').get(hash(token),Date.now());}
 function json(res,status,data){res.writeHead(status,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});res.end(JSON.stringify(data));}
 async function body(req){let n=0,parts=[];for await(const chunk of req){n+=chunk.length;if(n>65536)fail('Request is too large.',413);parts.push(chunk);}return Buffer.concat(parts);}
 async function jsonBody(req){if(!(req.headers['content-type']||'').toLowerCase().startsWith('application/json'))fail('Send application/json.',415);const a=JSON.parse((await body(req)).toString()||'{}');if(!a||typeof a!=='object'||Array.isArray(a))fail('Expected a JSON object.');return a;}
 function originCheck(req){if(req.headers['sec-fetch-site']==='cross-site')fail('Cross-site request rejected.',403);const origin=req.headers.origin;if(origin&&origin!==(settings.origin||`http://${req.headers.host}`))fail('Origin rejected.',403);}
 function authenticate(req){const session=sessionOf(req);if(!session)fail('Sign in again to continue.',401);if(req.method!=='GET'&&req.headers['x-csrf-token']!==session.csrf)fail('Session verification failed.',403);return {session,user:getUser(session.player_id)};}
 function finishStoredBattle(row,b,u,s,now){
  const result=M.settleBattle(s,b);frontiers.finish(u,s,b,now);if(row.defender_id){const defender=getUser(row.defender_id);if(defender){const ds=stateOf(defender,now);if(b.lootEscrow){ds.gold=Math.min(M.capacity(ds),ds.gold+Math.max(0,b.lootEscrow.gold-result.gold));ds.elixir=Math.min(M.capacity(ds),ds.elixir+Math.max(0,b.lootEscrow.elixir-result.elixir));}else{ds.gold=Math.max(0,ds.gold-result.gold);ds.elixir=Math.max(0,ds.elixir-result.elixir);}ds.shieldUntil=now+300000;persist(defender,ds,now);}}
  db.prepare('INSERT OR IGNORE INTO raid_log VALUES(?,?,?,?,?)').run(row.id,u.id,row.defender_id||null,JSON.stringify(result),now);db.prepare('UPDATE battles SET state=?,settled=1,last_step=? WHERE id=?').run(JSON.stringify(b),now,row.id);persist(u,s,now);return result;
 }
 function advanceBattle(row,u,s,now){const b=JSON.parse(row.state);if(!row.settled){if(b.started){let elapsed=Math.min(151,Math.max(0,(now-row.last_step)/1000));while(elapsed>0&&!b.ended){const dt=Math.min(.05,elapsed);M.stepBattle(b,dt);elapsed-=dt;}}else if(now-row.created_at>300000)b.ended=true;
  if(b.ended)finishStoredBattle(row,b,u,s,now);else db.prepare('UPDATE battles SET state=?,last_step=? WHERE id=?').run(JSON.stringify(b),now,row.id);}return b;}
 function snapshot(user,now=Date.now()){const s=stateOf(user,now),row=db.prepare('SELECT * FROM battles WHERE player_id=? AND settled=0 ORDER BY created_at DESC LIMIT 1').get(user.id);const battle=row?advanceBattle(row,user,s,now):null;persist(user,s,now);return {state:s,battle,battleId:row?.id||null,user:safeUser(user),serverTime:now};}
 function command(user,a,now){
  user=getUser(user.id);if(a.realm!==undefined&&!['home','builder','capital'].includes(a.realm))fail('Unknown village realm.');if(typeof a.type!=='string')fail('Invalid command.');const s=stateOf(user,now);let result;
  const active=db.prepare('SELECT * FROM battles WHERE player_id=? AND settled=0 ORDER BY created_at DESC LIMIT 1').get(user.id);
  if(a.type==='battle-start'&&db.prepare('SELECT COUNT(*) AS n FROM battles WHERE settled=0').get().n>=128)fail('The battlefield is busy. Try again shortly.',503);
  if(a.type==='battle-start'&&a.mode&&a.mode!=='campaign'){
   if(active)fail('Finish your current battle first.');let b;if(['training','builder'].includes(a.mode)){const r=X.createModeBattle(s,a.mode,now);if(r.error)fail(r.error);b=r.battle;}else b=frontiers.startBattle(user,s,a,now);const funds=X.wallet(s,b);if(!b.practice&&M.armySize(funds.army)<1&&!Object.values(funds.heroes).some(h=>h.level&&!h.finishAt&&!(h.recoverAt>now)))fail('Train troops or prepare a hero first.');b.id=randomUUID();db.prepare('INSERT INTO battles(id,player_id,state,last_step,created_at) VALUES(?,?,?,?,?)').run(b.id,user.id,JSON.stringify(b),now,now);persist(user,s,now);return {state:s,battle:b,battleId:b.id,result:{ok:true},serverTime:now};
  }
  if(a.type==='battle-start'){
   if(active)fail('Finish your current battle first.');if(M.armySize(s.army)<1&&!Object.values(s.heroes).some(h=>h.level&&!h.finishAt&&h.recoverAt<=now))fail('Train an army or prepare a hero first.');
   let index=Number(a.index||0);if(!Number.isInteger(index)||index<0||index>10000)fail('Invalid stronghold.');
   if(!a.defender){const max=Object.keys(s.cleared).length?Math.max(...Object.keys(s.cleared).map(Number))+1:0;if(index>max)fail('Win the preceding stronghold first.');}
   const b=M.createBattle(s,index);b.id=randomUUID();let defenderId=null;
   if(a.defender){const defender=getUser(a.defender);if(!defender||defender.id===user.id)fail('Invalid opponent.');if(user.clan_id&&user.clan_id===defender.clan_id)fail('You cannot attack a clanmate.');const ds=stateOf(defender,now);if(ds.shieldUntil>now)fail('This village is protected by a shield.');if(db.prepare('SELECT id FROM battles WHERE defender_id=? AND settled=0').get(defender.id))fail('This village is already under attack.');
    defenderId=defender.id;b.pvp=true;b.bounds=15.2;b.enemy={index:0,name:defender.name,gold:Math.min(3000,Math.floor(ds.gold*.15)),elixir:Math.min(2500,Math.floor(ds.elixir*.15)),dark:0,glory:30};b.lootEscrow={gold:b.enemy.gold,elixir:b.enemy.elixir};ds.gold-=b.lootEscrow.gold;ds.elixir-=b.lootEscrow.elixir;persist(defender,ds,now);b.buildings=ds.buildings.filter(x=>!x.constructing).map(x=>({...x,hp:M.TYPES[x.type].hp*(1+(x.level-1)*.25),maxHp:M.TYPES[x.type].hp*(1+(x.level-1)*.25),cooldown:0}));
   }
   db.prepare('INSERT INTO battles(id,player_id,defender_id,state,last_step,created_at) VALUES(?,?,?,?,?,?)').run(b.id,user.id,defenderId,JSON.stringify(b),now,now);return {state:s,battle:b,battleId:b.id,result:{ok:true},serverTime:now};
  }
  if(a.type.startsWith('battle-')){
   const row=db.prepare('SELECT * FROM battles WHERE id=? AND player_id=?').get(String(a.battleId||''),user.id);if(!row)fail('Battle not found.',404);const b=advanceBattle(row,user,s,now);
   if(!b.ended){if(a.type==='battle-deploy')result=M.deploy(s,b,a.troop,a.x,a.z);else if(a.type==='battle-hero')result=M.deployHero(s,b,a.hero,a.x,a.z,now);else if(a.type==='battle-spell')result=M.castSpell(s,b,a.spell,a.x,a.z);else if(a.type==='battle-siege')result=X.deploySiege(s,b,a.siege,a.x,a.z);else if(a.type==='battle-ability')result=M.heroAbility(b,a.hero);else if(a.type==='battle-end'){b.ended=true;result=finishStoredBattle(row,b,user,s,now);}else fail('Unknown battle action.');if(result?.error)fail(result.error);}
   if(b.ended&&!b.settled)finishStoredBattle(row,b,user,s,now);db.prepare('UPDATE battles SET state=?,last_step=?,settled=? WHERE id=?').run(JSON.stringify(b),now,b.settled?1:0,row.id);persist(user,s,now);return {state:s,battle:b,battleId:b.id,result:result||b.result,serverTime:now};
  }
  if(active)fail('Return home before changing your village.');result=frontiers.handle(user,s,a,now)||M.applyAction(s,a,now,()=>randomInt(0,0x1000000)/0x1000000);if(result.error)fail(result.error);persist(user,s,now);return {state:s,result,serverTime:now};
 }
 function fulfill(event){
  if(!event||typeof event.id!=='string'||event.id.length>255||typeof event.type!=='string')fail('Malformed payment event.');
  if(db.prepare('SELECT id FROM payment_events WHERE id=?').get(event.id))return {duplicate:true};
  if(!['checkout.session.completed','checkout.session.async_payment_succeeded'].includes(event.type))return {ignored:true};
  const session=event.data?.object;if(session?.payment_status!=='paid')return {ignored:true};const order=db.prepare('SELECT * FROM orders WHERE id=?').get(String(session.metadata?.order_id||''));
  if(!order||session.id!==order.stripe_id||session.client_reference_id!==order.player_id||session.amount_total!==order.cents||session.currency!==order.currency)fail('Payment does not match the stored order.',400);
  if(order.status!=='paid'){const user=getUser(order.player_id),s=stateOf(user);s.gems+=order.gems;persist(user,s);db.prepare("UPDATE orders SET status='paid' WHERE id=?").run(order.id);}
  db.prepare('INSERT INTO payment_events VALUES(?,?)').run(event.id,Date.now());return {ok:true};
 }
 const server=http.createServer(async(req,res)=>{
  setSecurityHeaders(res,settings.secure);
  try{
   const url=new URL(req.url,'http://localhost'),p=url.pathname,now=Date.now();
   if(p==='/api/health')return json(res,200,{ok:true,version:'5.0.0'});
   if(p==='/api/payments/webhook'&&req.method==='POST'){let event;try{event=verifyWebhook(await body(req),req.headers['stripe-signature'],settings.webhookSecret);}catch{fail('Invalid payment signature.',400);}return json(res,200,tx(()=>fulfill(event)));}
   if(p.startsWith('/api/')){
    const ip=req.socket.remoteAddress||'unknown',rateIdentity=p.startsWith('/api/auth')||p==='/api/session'?ip:(sessionOf(req)?.player_id||ip),key=rateIdentity+':'+(p.startsWith('/api/auth')?'auth':p==='/api/session'?'session':'api');let bucket=rate.get(key);if(!bucket||now-bucket.start>60000){bucket={start:now,count:0};rate.set(key,bucket);}if(++bucket.count>(p.startsWith('/api/auth')?15:p==='/api/session'?25:700))fail('Too many requests. Try again shortly.',429);
    if(req.method==='POST')originCheck(req);if((p.startsWith('/api/auth/')||p==='/api/oauth/poll')&&!authTransportAllowed(req,settings.secure))fail('Account access requires HTTPS. Configure your HTTPS domain first.',403);
    if(p==='/api/config')return json(res,200,{server:true,payments:paymentEnabled,paymentTest:settings.stripeKey.startsWith('sk_test_'),packs:M.GEM_PACKS,oauth:oauth.publicConfig()});
    if(/^\/api\/auth\/oauth\/(google|facebook)\/callback$/.test(p)&&req.method==='GET'){const ok=await oauth.callback(p.split('/')[4],url.searchParams);res.writeHead(ok?200:400,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store','Referrer-Policy':'no-referrer'});return res.end(callbackHTML(ok));}
    if(p==='/api/session'&&req.method==='POST'){
     await jsonBody(req);
     let session=sessionOf(req);if(!session){const id=randomUUID(),s=M.initialState(now);db.prepare('INSERT INTO players(id,name,state,updated_at) VALUES(?,?,?,?)').run(id,'Chief '+randomInt(1000,9999),JSON.stringify(s),now);session=newSession(id,res);}return json(res,200,{...tx(()=>snapshot(getUser(session.player_id),now)),csrf:session.csrf});
    }
    if(p==='/api/auth/login'&&req.method==='POST'){
     const a=await jsonBody(req);if(typeof a.username!=='string'||typeof a.password!=='string'||a.password.length>256)fail('Invalid credentials.',401);const user=db.prepare('SELECT * FROM players WHERE login=?').get(a.username.toLowerCase());if(!user?.password_hash||!await passwordMatches(a.password,user.password_hash)||getUser(user.id)?.password_hash!==user.password_hash)fail('Invalid username or password.',401);
     const upgraded=user.password_hash.startsWith('scrypt$')?null:await passwordHash(a.password);const response=tx(()=>{if(getUser(user.id)?.password_hash!==user.password_hash)fail('Invalid username or password.',401);const old=sessionOf(req);if(old)db.prepare('DELETE FROM sessions WHERE token_hash=?').run(old.token_hash);if(upgraded)db.prepare('UPDATE players SET password_hash=? WHERE id=?').run(upgraded,user.id);const fresh=newSession(user.id,res);return {...snapshot(getUser(user.id),now),csrf:fresh.csrf};});return json(res,200,response);
    }
    const {user,session}=authenticate(req);
    if(p==='/api/auth/oauth/start'&&req.method==='POST')return json(res,200,oauth.start(user,session,await jsonBody(req)));
    if(p==='/api/oauth/poll'&&req.method==='POST')return json(res,200,oauth.poll(user,session,await jsonBody(req),res));
    if(p==='/api/state'&&req.method==='GET')return json(res,200,tx(()=>snapshot(user,now)));
    if(p==='/api/auth/register'&&req.method==='POST'){
     const a=await jsonBody(req);if(safeUser(user).registered)fail('This village already has an account.');if(typeof a.username!=='string'||!/^[A-Za-z0-9_]{3,24}$/.test(a.username)||typeof a.password!=='string'||a.password.length<10||a.password.length>128)fail('Use a 3–24 character username and a password of at least 10 characters.');if(db.prepare('SELECT id FROM players WHERE login=?').get(a.username.toLowerCase()))fail('That username is already taken.');const encoded=await passwordHash(a.password);const result=tx(()=>{if(safeUser(getUser(user.id)).registered)fail('This village already has an account.',409);if(db.prepare('SELECT id FROM players WHERE login=?').get(a.username.toLowerCase()))fail('That username is already taken.',409);db.prepare('UPDATE players SET name=?,login=?,password_hash=? WHERE id=?').run(a.username,a.username.toLowerCase(),encoded,user.id);db.prepare('DELETE FROM sessions WHERE player_id=?').run(user.id);const fresh=newSession(user.id,res);return {user:safeUser(getUser(user.id)),csrf:fresh.csrf};});return json(res,200,result);
    }
    if(p==='/api/auth/logout'&&req.method==='POST'){db.prepare('DELETE FROM sessions WHERE token_hash=?').run(session.token_hash);res.setHeader('Set-Cookie',`emberfall_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0${settings.secure?'; Secure':''}`);return json(res,200,{ok:true});}
    if(p==='/api/auth/password'&&req.method==='POST'){const a=await jsonBody(req);if(!user.password_hash||typeof a.currentPassword!=='string'||a.currentPassword.length>128||!validPassword(a.newPassword))fail('Use your current password and a new password of 10–128 characters.');if(!await passwordMatches(a.currentPassword,user.password_hash))fail('Current password is incorrect.',403);const encoded=await passwordHash(a.newPassword);const result=tx(()=>{if(getUser(user.id).password_hash!==user.password_hash)fail('Your password changed. Sign in again.',409);db.prepare('UPDATE players SET password_hash=? WHERE id=?').run(encoded,user.id);db.prepare('DELETE FROM sessions WHERE player_id=?').run(user.id);const fresh=newSession(user.id,res);return {ok:true,user:safeUser(getUser(user.id)),csrf:fresh.csrf};});return json(res,200,result);}
    if(p==='/api/command'&&req.method==='POST'){
     const a=await jsonBody(req);if(typeof a.requestId!=='string'||!/^[A-Za-z0-9_-]{8,80}$/.test(a.requestId))fail('A unique request ID is required.');const cached=db.prepare('SELECT response FROM commands WHERE player_id=? AND request_id=?').get(user.id,a.requestId);if(cached)return json(res,200,JSON.parse(cached.response));
     const response=tx(()=>{const result=command(user,a,now);db.prepare('INSERT INTO commands VALUES(?,?,?,?)').run(user.id,a.requestId,JSON.stringify(result),now);return result;});return json(res,200,response);
    }
    if(p==='/api/battle'&&req.method==='GET'){
     const row=db.prepare('SELECT * FROM battles WHERE id=? AND player_id=?').get(url.searchParams.get('id'),user.id);if(!row)fail('Battle not found.',404);return json(res,200,tx(()=>{const s=stateOf(user,now),b=advanceBattle(row,user,s,now);persist(user,s,now);return {battle:b,battleId:b.id,state:s,serverTime:now};}));
    }
    if(p==='/api/frontiers'&&req.method==='GET')return json(res,200,tx(()=>frontiers.read(user,now)));
    if(p==='/api/players'&&req.method==='GET')return json(res,200,{players:db.prepare('SELECT id,name,glory,clan_id,state FROM players WHERE id<>? ORDER BY glory DESC LIMIT 40').all(user.id).map(u=>{const s=JSON.parse(u.state);return {id:u.id,name:u.name,glory:u.glory,hall:M.hallLevel(s),shield:s.shieldUntil>now,clanId:u.clan_id};})});
    if(p==='/api/raids'&&req.method==='GET')return json(res,200,{raids:db.prepare('SELECT r.*,p.name AS attacker FROM raid_log r JOIN players p ON p.id=r.attacker_id WHERE r.attacker_id=? OR r.defender_id=? ORDER BY created_at DESC LIMIT 25').all(user.id,user.id).map(r=>({...r,result:JSON.parse(r.result)}))});
    if(p==='/api/clans'&&req.method==='GET'){
     const clans=db.prepare('SELECT c.id,c.name,COUNT(p.id) AS members,COALESCE(SUM(p.glory),0) AS glory FROM clans c LEFT JOIN players p ON p.clan_id=c.id GROUP BY c.id ORDER BY glory DESC LIMIT 40').all();const members=user.clan_id?db.prepare('SELECT id,name,glory FROM players WHERE clan_id=?').all(user.clan_id):[];const messages=user.clan_id?db.prepare('SELECT c.message,c.created_at,p.name FROM chat c JOIN players p ON p.id=c.player_id WHERE c.clan_id=? ORDER BY c.id DESC LIMIT 30').all(user.clan_id).reverse():[];return json(res,200,{clans,members,messages,clanId:user.clan_id});
    }
    if(p==='/api/clans'&&req.method==='POST'){
     const a=await jsonBody(req);const result=tx(()=>{
      Object.assign(user,getUser(user.id));if(a.action==='create'){if(user.clan_id)fail('Leave your current clan first.');if(typeof a.name!=='string'||a.name.trim().length<3||a.name.trim().length>24)fail('Clan names must be 3–24 characters.');if(db.prepare('SELECT id FROM clans WHERE name=?').get(a.name.trim()))fail('That clan name is taken.');const id=randomUUID();db.prepare('INSERT INTO clans VALUES(?,?,?,?)').run(id,a.name.trim(),user.id,now);db.prepare('UPDATE players SET clan_id=? WHERE id=?').run(id,user.id);}
      else if(a.action==='join'){if(user.clan_id)fail('Leave your current clan first.');if(!db.prepare('SELECT id FROM clans WHERE id=?').get(a.id))fail('Clan not found.');if(db.prepare('SELECT COUNT(*) AS n FROM players WHERE clan_id=?').get(a.id).n>=30)fail('Clan is full.');db.prepare('UPDATE players SET clan_id=? WHERE id=?').run(a.id,user.id);}
      else if(a.action==='leave'){if(user.clan_id)frontiers.canLeave(user,now);db.prepare('UPDATE players SET clan_id=NULL WHERE id=?').run(user.id);const left=db.prepare('SELECT id FROM players WHERE clan_id=? LIMIT 1').get(user.clan_id);if(left)db.prepare('UPDATE clans SET owner_id=? WHERE id=? AND owner_id=?').run(left.id,user.clan_id,user.id);else{db.prepare('DELETE FROM clans WHERE id=?').run(user.clan_id);db.prepare('DELETE FROM chat WHERE clan_id=?').run(user.clan_id);}}
      else if(a.action==='chat'){if(!user.clan_id)fail('Join a clan first.');if(typeof a.message!=='string'||a.message.trim().length<1||a.message.length>280)fail('Messages must be 1–280 characters.');db.prepare('INSERT INTO chat(clan_id,player_id,message,created_at) VALUES(?,?,?,?)').run(user.clan_id,user.id,a.message.trim(),now);}
      else if(a.action==='donate'){const recipient=getUser(a.id);if(!recipient||recipient.id===user.id||!user.clan_id||recipient.clan_id!==user.clan_id)fail('Choose a clanmate.');if(db.prepare('SELECT id FROM battles WHERE player_id IN (?,?) AND settled=0').get(user.id,recipient.id))fail('Both players must be at home.');const s=stateOf(user,now),other=stateOf(recipient,now),troop=M.TROOPS[a.troop];if(!troop||(s.army[a.troop]||0)<1||M.armySize(other.army)+M.queueSize(other)+troop.space>M.armyCapacity(other))fail('Troop unavailable or recipient camp is full.');s.army[a.troop]--;other.army[a.troop]=(other.army[a.troop]||0)+1;persist(user,s);persist(recipient,other);}
      else fail('Unknown clan action.');return {user:safeUser(getUser(user.id)),ok:true};});return json(res,200,result);
    }
    if(p==='/api/payments/checkout'&&req.method==='POST'){
     if(!paymentEnabled)fail('Gem purchases are not available yet.',503);if(!safeUser(user).registered)fail('Create an account to keep your purchased gems.',403);const a=await jsonBody(req),pack=packById(a.pack);if(!pack)fail('Unknown gem pack.');if(db.prepare("SELECT COUNT(*) AS n FROM orders WHERE player_id=? AND created_at>? AND status='pending'").get(user.id,now-60000).n>=3)fail('Please finish your pending checkout.',429);
     const orderId=randomUUID();db.prepare('INSERT INTO orders(id,player_id,pack,gems,cents,created_at) VALUES(?,?,?,?,?,?)').run(orderId,user.id,pack.id,pack.gems,pack.cents,now);const checkout=await createCheckout({key:settings.stripeKey,origin:settings.origin,userId:user.id,orderId,pack,fetcher:settings.fetcher});db.prepare('UPDATE orders SET stripe_id=? WHERE id=?').run(checkout.id,orderId);return json(res,200,{url:checkout.url,orderId});
    }
    fail('Endpoint not found.',404);
   }
   if(req.method!=='GET'&&req.method!=='HEAD')fail('Method not allowed.',405);let decoded;try{decoded=decodeURIComponent(p);}catch{fail('Invalid path.');}const file=path.resolve(root,'.'+(decoded==='/'?'/index.html':decoded));if(!file.startsWith(root+path.sep)||decoded.includes('\0')||decoded.split('/').some(part=>part.startsWith('.')))fail('Not found.',404);
   let data;try{data=await readFile(file);}catch{fail('Not found.',404);}if(file.endsWith('index.html'))data=Buffer.from(data.toString().replace('name="emberfall-runtime" content="auto"','name="emberfall-runtime" content="server"'));const mime={'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json','.webp':'image/webp','.png':'image/png','.txt':'text/plain','.webmanifest':'application/manifest+json','.woff2':'font/woff2'}[path.extname(file)]||'application/octet-stream';res.writeHead(200,{'Content-Type':mime+'; charset=utf-8','Cache-Control':file.endsWith('.html')?'no-cache':'public, max-age=600'});res.end(req.method==='HEAD'?undefined:data);
  }catch(e){if(e instanceof SyntaxError){e.status=400;e.message='Invalid JSON request.';}if(!res.headersSent)json(res,e.status||500,{error:e.status?e.message:'The server could not complete this request.'});else res.end();if(!e.status)console.error('Request error:',e.message);}
 });
 server.requestTimeout=15000;server.headersTimeout=10000;server.keepAliveTimeout=5000;server.maxRequestsPerSocket=1000;
 const battleTick=setInterval(()=>{const now=Date.now();for(const row of db.prepare('SELECT * FROM battles WHERE settled=0 LIMIT 100').all()){try{tx(()=>{const u=getUser(row.player_id),s=stateOf(u,now);advanceBattle(row,u,s,now);persist(u,s,now);});}catch(e){console.error('Battle update failed:',e.message);}}},2500);battleTick.unref();
 const cleanup=setInterval(()=>{const cutoff=Date.now();oauth.clean();db.prepare('DELETE FROM sessions WHERE expires_at<?').run(cutoff);db.prepare('DELETE FROM commands WHERE created_at<?').run(cutoff-86400000);for(const [k,v]of rate)if(cutoff-v.start>120000)rate.delete(k);},60000);cleanup.unref();
 const backups=config.backups?startBackups(path.resolve(dataDir),config.backupOptions):null;
 return {server,db,settings,backups,listen:()=>new Promise(resolve=>server.listen(port,config.host||process.env.HOST||'0.0.0.0',resolve)),close:()=>new Promise(resolve=>{clearInterval(cleanup);clearInterval(battleTick);server.close(async()=>{await backups?.close();db.close();resolve();});})};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){const app=await createApp({backups:process.env.BACKUP_ENABLED!=='false'});await app.listen();console.log('Emberfall is running on port '+app.server.address().port);for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>app.close().then(()=>process.exit(0)));}
