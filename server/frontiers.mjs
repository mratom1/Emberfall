import {randomUUID} from 'node:crypto';
import * as X from '../dist/expansion.js';

export function createFrontiers({db,M,getUser,stateOf,persist,fail}){
 db.exec(`CREATE TABLE IF NOT EXISTS clan_worlds(clan_id TEXT PRIMARY KEY,state TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS wars(id TEXT PRIMARY KEY,clan_a TEXT NOT NULL,clan_b TEXT NOT NULL,state TEXT NOT NULL,status TEXT NOT NULL,created_at INTEGER NOT NULL);`);
 const getClan=id=>db.prepare('SELECT * FROM clans WHERE id=?').get(id);
 const members=id=>db.prepare('SELECT * FROM players WHERE clan_id=? ORDER BY glory DESC LIMIT 30').all(id);
 const putWorld=(id,c)=>db.prepare('INSERT INTO clan_worlds VALUES(?,?) ON CONFLICT(clan_id) DO UPDATE SET state=excluded.state').run(id,JSON.stringify(c));
 function world(id,now){
  let c;const row=db.prepare('SELECT state FROM clan_worlds WHERE clan_id=?').get(id);
  if(row)c=JSON.parse(row.state);else{const village=X.builderState(now);village.realm='capital';village.gold=3000;village.elixir=3000;village.builders=2;village.obstacles=[];village.heroes={};c={village,contributions:{},raid:{cycle:Math.floor(now/604800000),district:0,conquered:0,uses:{},buildings:null,active:null},league:null};}
  M.advance(c.village,now);const cycle=Math.floor(now/604800000);if(c.raid.cycle!==cycle&&!c.raid.active)c.raid={cycle,district:0,conquered:0,uses:{},buildings:null,active:null};return c;
 }
 const putWar=w=>db.prepare('UPDATE wars SET state=?,status=? WHERE id=?').run(JSON.stringify(w),w.status,w.id);
 function score(w,side){const values=Object.values(w.best[side]);return {stars:values.reduce((n,v)=>n+v.stars,0),percent:values.reduce((n,v)=>n+v.percent,0)};}
 function closeWar(w,now){if(w.status==='ended')return w;const spent=['a','b'].every(side=>w.rosters[side].every(p=>w.attacks.filter(a=>a.attacker===p.id).length>=Math.min(2,w.rosters[side==='a'?'b':'a'].length)));if((now>=w.endsAt||spent)&&!(w.pending||[]).length){w.status='ended';const a=score(w,'a'),b=score(w,'b');w.winner=a.stars===b.stars?(a.percent===b.percent?'draw':a.percent>b.percent?'a':'b'):a.stars>b.stars?'a':'b';putWar(w);}return w;}
 function readWar(id,now){const row=db.prepare('SELECT state FROM wars WHERE id=?').get(id);return row?closeWar(JSON.parse(row.state),now):null;}
 function roster(id,now){return members(id).slice(0,5).map(p=>{const s=stateOf(p,now);return {id:p.id,name:p.name,hall:M.hallLevel(s),buildings:structuredClone(s.buildings.filter(b=>!b.constructing))};});}
 function requireClan(user){if(!user.clan_id||!getClan(user.clan_id))fail('Join a clan first.');return getClan(user.clan_id);}
 function requireLeader(user){const clan=requireClan(user);if(clan.owner_id!==user.id)fail('Your clan leader controls this action.');return clan;}
 function activeWar(clanId,now){for(const row of db.prepare("SELECT id FROM wars WHERE (clan_a=? OR clan_b=?) AND status!='ended'").all(clanId,clanId)){const w=readWar(row.id,now);if(w.status!=='ended')return w;}return null;}
 function battleFrom(s,buildings,name,special){const b=M.createBattle(s,0);b.special=special;b.bounds=15.2;b.enemy={index:0,name,gold:0,elixir:0,dark:0,glory:0};b.buildings=buildings.map(v=>({...v,hp:v.hp??M.buildingHp(v),maxHp:v.maxHp??M.buildingHp(v),cooldown:0}));return b;}
 function district(c){if(!c.raid.buildings)c.raid.buildings=M.enemyBuildings(c.raid.district+2+c.raid.conquered).map(b=>({...b,hp:b.maxHp}));return c.raid.buildings;}
 function read(user,now){
  const clans=db.prepare('SELECT id,name,owner_id FROM clans ORDER BY name LIMIT 80').all();
  if(!user.clan_id)return {clans,clan:null,world:null,wars:[]};
  const c=world(user.clan_id,now);putWorld(user.clan_id,c);const wars=db.prepare('SELECT id FROM wars WHERE clan_a=? OR clan_b=? ORDER BY created_at DESC LIMIT 6').all(user.clan_id,user.clan_id).map(r=>readWar(r.id,now));return {clans,clan:getClan(user.clan_id),world:c,wars,serverTime:now};
 }
 function handle(user,s,a,now){
  if(a.type==='war-start'){
   const own=requireLeader(user),other=getClan(a.opponent);if(!other||other.id===own.id)fail('Choose another clan.');if(activeWar(own.id,now)||activeWar(other.id,now))fail('One of these clans is already at war.');
   const ra=roster(own.id,now),rb=roster(other.id,now);const size=Math.min(ra.length,rb.length);if(!size)fail('Both clans need members.');const w={id:randomUUID(),names:{a:own.name,b:other.name},clans:{a:own.id,b:other.id},rosters:{a:ra.slice(0,size),b:rb.slice(0,size)},best:{a:{},b:{}},used:{},pending:[],attacks:[],claimed:[],status:'active',readyAt:now+60000,endsAt:now+86460000};db.prepare('INSERT INTO wars VALUES(?,?,?,?,?,?)').run(w.id,own.id,other.id,JSON.stringify(w),w.status,now);return {ok:true};
  }
  if(a.type==='war-claim'){
   const w=readWar(a.warId,now);const side=w&&['a','b'].find(k=>w.rosters[k].some(p=>p.id===user.id));if(!w||!side||w.status!=='ended'||w.claimed.includes(user.id))fail('No unclaimed war reward.');const win=w.winner===side,medals=win?80:w.winner==='draw'?50:35,gems=win?25:10;s.expansion.medals+=medals;s.gems+=gems;w.claimed.push(user.id);putWar(w);return {ok:true,medals,gems};
  }
  if(a.type==='capital-donate'){
   requireClan(user);const n=Number(a.amount);if(!Number.isInteger(n)||n<1||n>100000||s.expansion.capitalGold<n)fail('Not enough capital gold.');const c=world(user.clan_id,now);s.expansion.capitalGold-=n;c.village.gold+=n;c.village.elixir=c.village.gold;c.contributions[user.id]=(c.contributions[user.id]||0)+n;putWorld(user.clan_id,c);return {ok:true};
  }
  if(a.realm==='capital'){
   requireLeader(user);if(!['build','move','upgrade'].includes(a.type))fail('Use capital gold contributions to develop the Capital.');const c=world(user.clan_id,now),v=c.village;
   if(a.type==='build'&&!X.BUILDER_TYPES.includes(a.building))fail('This building is not available in the Capital.');const selected=v.buildings.find(b=>b.id===a.id);if(a.type==='upgrade'&&selected?.level>=10)fail('Capital buildings have a maximum level of 10.');
   const cost=a.type==='build'?M.TYPES[a.building]:a.type==='upgrade'&&selected?M.upgradeCost(selected):{gold:0,elixir:0};if(!cost||v.gold<cost.gold+cost.elixir)fail('Donate more capital gold first.');const before=v.gold;v.elixir=before;const result=M.applyAction(v,{...a,realm:undefined},now);if(result.error)fail(result.error);v.gold=before-((before-v.gold)+(before-v.elixir));v.elixir=v.gold;putWorld(user.clan_id,c);return {...result,capital:v};
  }
  if(a.type==='league-start'){
   requireLeader(user);const c=world(user.clan_id,now),season=new Date(now).toISOString().slice(0,7);if(c.league&&!c.league.ended)fail('Finish the current league first.');if(c.league?.season===season)fail('Your clan has already entered this month’s league.');c.league={id:randomUUID(),season,round:0,roster:members(user.clan_id).slice(0,5).map(p=>({id:p.id,name:p.name})),used:{},scores:[],best:{},claimed:[],active:[],roundAt:now,ended:false};putWorld(user.clan_id,c);return {ok:true};
  }
  if(a.type==='league-next'){
   requireLeader(user);const c=world(user.clan_id,now),l=c.league;if(!l||l.ended)fail('No active league.');if(l.active.length)fail('Wait for current league attacks to finish.');if(!l.roster.every(p=>l.used[p.id])&&now-l.roundAt<900000)fail('Let each member attack, or wait 15 minutes.');const stars=Object.values(l.best).reduce((n,r)=>n+r.stars,0);l.scores.push({round:l.round+1,stars,max:l.roster.length*3});l.round++;l.used={};l.best={};l.roundAt=now;l.ended=l.round>=7;putWorld(user.clan_id,c);return {ok:true};
  }
  if(a.type==='league-claim'){
   requireClan(user);const c=world(user.clan_id,now),l=c.league;if(!l?.ended||!l.roster.some(p=>p.id===user.id)||l.claimed.includes(user.id))fail('No unclaimed league reward.');const stars=l.scores.reduce((n,r)=>n+r.stars,0),medals=70+Math.floor(stars/Math.max(1,l.roster.length))*10;s.expansion.medals+=medals;s.expansion.ore+=200;l.claimed.push(user.id);putWorld(user.clan_id,c);return {ok:true,medals};
  }
  return undefined;
 }
 function startBattle(user,s,a,now){
  const clan=requireClan(user);let b;
  if(a.mode==='war'){
   const w=readWar(a.warId,now),side=w&&['a','b'].find(k=>w.clans[k]===clan.id&&w.rosters[k].some(p=>p.id===user.id));if(!w||!side||w.status==='ended')fail('You are not in this active war roster.');if(now>=w.endsAt)fail('The war attack period has ended.');if(now<w.readyAt)fail('War preparation ends in '+Math.ceil((w.readyAt-now)/1000)+' seconds.');const other=side==='a'?'b':'a',target=w.rosters[other].find(p=>p.id===a.target);if(!target)fail('Choose an enemy war base.');const used=w.used[user.id]||[];if(used.length>=Math.min(2,w.rosters[other].length)||used.includes(target.id))fail('Two attacks per war; attack each target once.');used.push(target.id);w.used[user.id]=used;w.pending??=[];w.pending.push(user.id);putWar(w);b=battleFrom(s,target.buildings,'War · '+target.name,'war');b.war={id:w.id,side,target:target.id,attacker:user.id};
  }else if(a.mode==='capital'){
   const c=world(clan.id,now);if(c.raid.active)fail('A clanmate is attacking this district.');if((c.raid.uses[user.id]||0)>=5)fail('Your five Capital attacks are used for this raid week.');b=battleFrom(s,district(c),['Capital Peak','Dragon Cliffs','Forge Valley'][c.raid.district],'capital');b.capital={clanId:clan.id,cycle:c.raid.cycle,district:c.raid.district,previousDead:b.buildings.filter(x=>x.hp<=0).length};c.raid.uses[user.id]=(c.raid.uses[user.id]||0)+1;c.raid.active=user.id;putWorld(clan.id,c);
  }else if(a.mode==='league'){
   const c=world(clan.id,now),l=c.league;if(!l||l.ended||!l.roster.some(p=>p.id===user.id)||l.used[user.id])fail('No league attack is available.');b=battleFrom(s,M.enemyBuildings(1+l.round),'League · AI Stronghold '+(l.round+1),'league');b.bounds=8.7;b.league={clanId:clan.id,id:l.id,round:l.round,attacker:user.id};l.used[user.id]=true;l.active.push(user.id);putWorld(clan.id,c);
  }else fail('Unknown frontier battle.');return b;
 }
 function finish(user,s,b,now){
  if(b.frontierRecorded)return;b.frontierRecorded=true;
  if(b.war){const w=readWar(b.war.id,now);if(w){w.pending=(w.pending||[]).filter(id=>id!==user.id);const {side,target}=b.war,prior=w.best[side][target],r=b.result;if(!prior||r.stars>prior.stars||r.stars===prior.stars&&r.percent>prior.percent)w.best[side][target]={stars:r.stars,percent:r.percent};w.attacks.push({...b.war,stars:r.stars,percent:r.percent});putWar(w);closeWar(w,now);}}
  if(b.capital){const c=world(b.capital.clanId,now);if(c.raid.cycle===b.capital.cycle){c.raid.buildings=b.buildings.map(v=>({...v,cooldown:0,frozen:0}));c.raid.active=null;const n=b.buildings.filter(v=>v.hp<=0).length-b.capital.previousDead,capitalGold=Math.max(0,n)*100,medals=Math.max(0,n)*3;s.expansion.capitalGold+=capitalGold;s.expansion.medals+=medals;b.result.capitalGold=(b.result.capitalGold||0)+capitalGold;b.result.medals=medals;if(b.stats.percent===100){c.raid.district++;c.raid.buildings=null;if(c.raid.district===3){c.raid.district=0;c.raid.conquered++;}}putWorld(b.capital.clanId,c);}}
  if(b.league){const c=world(b.league.clanId,now),l=c.league;if(l?.id===b.league.id&&l.round===b.league.round){l.best[user.id]={stars:b.result.stars,percent:b.result.percent};l.active=l.active.filter(id=>id!==user.id);putWorld(b.league.clanId,c);}}
 }
 function canLeave(user,now){const w=activeWar(user.clan_id,now);if(w&&['a','b'].some(k=>w.rosters[k].some(p=>p.id===user.id)))fail('Finish your clan war before leaving.');const c=world(user.clan_id,now);if(c.league&&!c.league.ended&&c.league.roster.some(p=>p.id===user.id))fail('Finish your clan league before leaving.');if(c.raid.active===user.id)fail('Finish your Capital raid first.');}
 return {read,handle,startBattle,finish,canLeave,score};
}
