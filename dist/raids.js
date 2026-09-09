import * as M from './model.js?v=6.0.0';

export const WEEK = 7 * 86400000;
export const DEFENSE_INTERVAL = 6 * 3600000;
export const DEFENSE_GRACE = 5 * 60000;
export const GEM_BOX_REWARD = 25;
export const SHIELDS = [
  {id:'12h',name:'12-hour Shield',duration:12*3600000,gems:100},
  {id:'1d',name:'1-day Shield',duration:86400000,gems:180},
  {id:'2d',name:'2-day Shield',duration:2*86400000,gems:320}
];
const currencies = ['gold','elixir','dark'];
const botNames = ['Ashwood Keep','Silverpine Watch','Ravencrest','Copperleaf Hold','Frostmere','Sunstone Camp'];
const pick = (items, random) => items[Math.min(items.length-1,Math.floor(random()*items.length))];
export function ensure(s, now=Date.now()) {
  if(s.realm)return;
  s.raids??={};s.raids.history??=[];s.raids.nextDefenseAt??=now+DEFENSE_INTERVAL;
  s.raids.lastSeenAt??=now;s.raids.lastDefenseAt??=0;s.raids.recentOpponents??=[];
  s.nextGemBoxAt??=now;
}
export function availableLoot(s) {
  return Object.fromEntries(currencies.map(k=>[k,Math.floor(Math.max(0,Number(s[k])||0)/10)]));
}
export function buyShield(s, id, now=Date.now()) {
  const pack=SHIELDS.find(p=>p.id===id);if(!pack)return {error:'Choose a Shield from the shop.'};
  ensure(s,now);if(s.gems<pack.gems)return {error:'Not enough gems.'};
  const end=Math.max(now,s.shieldUntil||0)+pack.duration;
  if(end>now+WEEK)return {error:'A village can hold up to 7 days of Shield.'};
  s.gems-=pack.gems;s.shieldUntil=end;s.raids.nextDefenseAt=Math.max(s.raids.nextDefenseAt,end);
  return {ok:true,shieldUntil:end};
}
export function action(s,a,now) {
  if(a.type==='shield-buy')return s.realm?{error:'Shields protect the home village.'}:buyShield(s,a.shield,now);
  return null;
}
export function weeklyBox(s,now,events=[]) {
  if(s.realm)return;ensure(s,now);
  if(now<s.nextGemBoxAt||s.obstacles.some(o=>o.type==='gem-box'))return;
  // A single box waits until collected. Missed weeks never create a stack of claims.
  for(let z=10;z>=-13;z-=1.5)for(let x=-10;x<=13;x+=1.5)if(M.canPlace(s,'wall',x,z)){
    s.obstacles.push({id:'gem-box-'+s.nextGemBoxAt,type:'gem-box',x,z});
    events.push({kind:'regrow',gemBox:true});return;
  }
}
export function appearance(level=1) {
  level=Math.max(1,Math.min(50,Math.floor(level)||1));
  const tier=Math.min(4,Math.floor((level-1)/10));
  return {level,tier,name:['Bronze','Silver','Gold','Crystal','Royal'][tier],color:[0xc79258,0xbbd5df,0xf4cc76,0x94dbea,0xd5a8f7][tier],marks:1+(level-1)%10};
}
export function botVillage(player,random=Math.random,now=Date.now()) {
  const level=Math.max(1,Math.min(15,M.hallLevel(player)+pick([-1,0,0,0,1],random)));
  const s=M.initialState(now);s.obstacles=[];s.queue=[];
  for(const b of s.buildings){b.level=Math.max(1,level-(b.type==='hall'?0:Math.floor(random()*2)));delete b.finishAt;b.constructing=false;b.stored=0;}
  const additions=[['tower',2],['cannon',2],['storage',3],['mortar',3],['wizard',4],['tesla',5],['air',6],['inferno',8]];
  for(const [type,gate] of additions){if(level<gate)continue;let placed=false;
    for(const z of [-9,-5,0,5,9]){for(const x of [-9,-5,0,5,9])if(M.canPlace(s,type,x,z)){
      s.buildings.push({id:'bot-'+type+gate,type,x,z,level:Math.max(1,level-1)});placed=true;break;
    }if(placed)break;}
  }
  if(level>1)for(const x of [-10.5,-9,-7.5,-6,-4.5,-3,-1.5,0,1.5,3,4.5,6,7.5,9,10.5])for(const z of [-11,11])if(M.canPlace(s,'wall',x,z))s.buildings.push({id:'bw-'+x+'-'+z,type:'wall',x,z,level});
  const turn=pick([0,1,2,3],random);
  for(const b of s.buildings)for(let n=0;n<turn;n++){const x=b.x;b.x=-b.z;b.z=x;b.rotation=((b.rotation||0)+1)%4;}
  const cap=M.capacity(s);s.gold=Math.floor(cap*(.35+random()*.6));s.elixir=Math.floor(cap*(.35+random()*.6));s.dark=level<3?0:Math.floor(level*level*120*(.4+random()*.6));
  return {id:'bot-'+now+'-'+Math.floor(random()*1000000),name:pick(botNames,random),kind:'bot',hall:level,state:s};
}
export function configureBattle(b,defender) {
  const ds=defender.state;b.pvp=true;b.raid=true;b.bounds=15.2;
  b.enemy={index:0,name:defender.name,kind:defender.kind||'player',hall:M.hallLevel(ds),...availableLoot(ds),glory:30};
  b.defenderId=defender.id;b.defenderBalance=Object.fromEntries(currencies.map(k=>[k,ds[k]||0]));
  b.buildings=ds.buildings.filter(x=>!x.constructing).map(x=>({...x,hp:M.TYPES[x.type].hp*(1+(x.level-1)*.25),maxHp:M.TYPES[x.type].hp*(1+(x.level-1)*.25),cooldown:0}));
  return b;
}
export function createBotBattle(s,random=Math.random,now=Date.now()) {
  const b=configureBattle(M.createBattle(s,0),botVillage(s,random,now));
  b.id='raid-'+now+'-'+Math.floor(random()*1000000);return b;
}
export function reserveLoot(s,b) {
  b.lootEscrow=availableLoot(s);for(const k of currencies)s[k]=(s[k]||0)-b.lootEscrow[k];
}
export function settleDefender(s,b,result,now=Date.now()) {
  ensure(s,now);
  for(const k of currencies){
    if(b.lootEscrow)s[k]=(s[k]||0)+Math.max(0,(b.lootEscrow[k]||0)-(result[k]||0));
    else s[k]=Math.max(0,(s[k]||0)-(result[k]||0));
  }
  if(b.started){s.shieldUntil=Math.max(s.shieldUntil||0,now+DEFENSE_GRACE);s.raids.lastDefenseAt=now;s.raids.nextDefenseAt=now+DEFENSE_INTERVAL;}
}
export function record(s,entry) {
  if(s.realm)return;ensure(s,entry.created_at);
  if(s.raids.history.some(r=>r.id===entry.id&&r.direction===entry.direction))return;
  s.raids.history.unshift(entry);s.raids.history=s.raids.history.slice(0,100);
}
export function recordAttack(s,b,result,now=Date.now()) {
  if(b.practice||!b.started)return;
  record(s,{id:b.id||'battle-'+now,direction:'attack',opponent:b.enemy.name,opponentType:b.enemy.kind||(b.pvp?'player':'bot'),hall:b.enemy.hall||b.enemy.level||1,mode:b.raid?'raid':b.realm||'campaign',created_at:now,result:{...result}});
}
export function startAttack(s,b,now=Date.now()) {
  if(!b.raid||b.shieldBroken||!b.started)return;
  ensure(s,now);s.shieldUntil=0;b.shieldBroken=true;s.raids.nextDefenseAt=Math.max(s.raids.nextDefenseAt,now+DEFENSE_INTERVAL);
}
export function simulateDefense(s,random=Math.random,now=Date.now()) {
  ensure(s,now);
  if(s.realm||s.shieldUntil>now||s.raids.nextDefenseAt>now)return null;
  const bot=botVillage(s,random,now),attacker=bot.state,level=M.hallLevel(s);
  attacker.army={guardian:6+Math.min(8,level),ranger:4+Math.min(6,level),giant:Math.min(4,Math.floor(level/2))};
  attacker.research={guardian:Math.max(1,level-1),ranger:Math.max(1,level-1),giant:Math.max(1,level-1)};
  const b=configureBattle(M.createBattle(attacker,0),{id:'home',name:'Your village',state:s});b.id='defense-'+now;
  b.heroStock={};b.spellStock={};let i=0;const side=pick([0,1,2,3],random);
  for(const [type,count] of Object.entries({...attacker.army}))for(let n=0;n<count;n++){
    let x=-6+(i++%9)*1.5,z=16.8;for(let t=0;t<side;t++){const v=x;x=-z;z=v;}
    M.deploy(attacker,b,type,x,z);
  }
  // Run the same unit movement, wall blocking and defense damage rules as player raids.
  for(let tick=0;tick<1500&&!b.ended;tick++)M.stepBattle(b,.1);
  const stats=M.battleStats(b),loot=availableLoot(s),ratio=stats.percent/100;
  const result={...stats,won:stats.stars>0,glory:0,...Object.fromEntries(currencies.map(k=>[k,Math.floor(loot[k]*ratio)]))};
  settleDefender(s,b,result,now);
  const entry={id:b.id,direction:'defense',opponent:bot.name,opponentType:'bot',hall:bot.hall,mode:'raid',created_at:now,result};record(s,entry);
  return entry;
}
