import {COUNTRY_CODES,FLAG_COST} from './flags.js?v=8.0.0';
import {EXTRA_HEROES,unlockedLand,landContains} from './content.js?v=8.0.0';
import * as R from './raids.js?v=8.0.0';
import * as Q from './quality.js?v=8.0.0';
import * as X from './expansion.js?v=8.0.0';
export const SAVE_KEY = 'emberfall.kingdom.v1';
export const TYPES = {
  hall: {name:'Town Hall',icon:'castle',desc:'The heart of your village. Upgrade to unlock stronger buildings and a larger army.',gold:0,elixir:0,size:3.7,hp:1600,max:1,time:30},
  mine: {name:'Gold Mine',icon:'pickaxe',desc:'Brings gold up from the deep. Collect its earnings to build and upgrade.',gold:450,elixir:0,size:2.3,hp:550,max:4,time:12},
  well: {name:'Elixir Spring',icon:'flask-conical',desc:'Draws magical elixir from the earth. Keep your army well supplied.',gold:400,elixir:0,size:2.3,hp:550,max:4,time:12},
  barracks: {name:'Barracks',icon:'swords',desc:'Upgrade to unlock new troop types. Use the Laboratory to improve troop levels.',gold:850,elixir:150,size:3,hp:850,max:2,time:18},
  tower: {name:'Watchtower',icon:'tower-control',desc:'Rangers watch over the village from above, firing at enemies in range.',gold:650,elixir:0,size:1.8,hp:700,max:5,time:15},
  cannon: {name:'Iron Cannon',icon:'crosshair',desc:'A hard-hitting defense against ground troops. Protect your resource buildings.',gold:800,elixir:100,size:2,hp:850,max:4,time:18},
  storage: {name:'Storehouse',icon:'warehouse',desc:'Safely holds your supplies. Upgrades greatly increase gold and elixir capacity.',gold:500,elixir:0,size:2.6,hp:750,max:3,time:13},
  camp: {name:'Army Camp',icon:'tent',desc:'A place for your army to gather. Each camp level adds 6 troop spaces.',gold:550,elixir:100,size:2.6,hp:600,max:3,time:15},
  cottage: {name:'Builder Lodge',icon:'house',desc:'A home for your builders. Hire up to five builders with gems.',gold:0,elixir:0,size:2,hp:500,max:1,time:0}
};
export const TROOPS = {
  guardian:{name:'Guardian',icon:'sword',desc:'Fearless frontline fighter. Leads the charge into battle.',cost:45,time:2,hp:190,damage:35,speed:2.1,range:1.1,rate:.82,space:1,color:0xb95540},
  ranger:{name:'Ranger',icon:'bow-arrow',desc:'Quick-footed archer. Strikes safely from a distance.',cost:70,time:3,hp:115,damage:28,speed:2.3,range:4.2,rate:1,space:1,color:0x4f7764},
  giant:{name:'Stone Giant',icon:'mountain',desc:'A towering tank that targets defenses first.',cost:180,time:5,hp:920,damage:75,speed:1.4,range:1.2,rate:1.3,space:3,color:0x9d9989}
};
Object.assign(TYPES,{
 flag:{name:'Country Flag',icon:'flag',desc:'A country flag on a decorative pole.',gold:200,elixir:0,size:.65,hp:1,max:30,time:0,decoration:true},
 laboratory:{name:'Laboratory',icon:'microscope',desc:'Research permanent troop upgrades. One research project at a time.',gold:1200,elixir:400,size:2.6,hp:850,max:1,time:20,unlock:2},
 forge:{name:'Spell Forge',icon:'wand-sparkles',desc:'Brew Thunder, Heal, Rage, and Freeze spells for battle.',gold:1500,elixir:500,size:2.4,hp:900,max:1,time:25,unlock:2},
 altar:{name:'Hero Hall',icon:'crown',desc:'Unlock and upgrade 20 original heroes. Town Hall and Barracks upgrades open the roster.',gold:1800,elixir:600,size:2.8,hp:1400,max:1,time:30,unlock:2},
 mortar:{name:'Mortar',icon:'target',desc:'Long-range shells damage groups of ground troops.',gold:1100,elixir:100,size:2,hp:900,max:4,time:20,unlock:2},
 wizard:{name:'Arcane Tower',icon:'sparkles',desc:'Magic blasts damage nearby groups on the ground and in the air.',gold:1900,elixir:450,size:2,hp:1000,max:4,time:25,unlock:3},
 air:{name:'Sky Defender',icon:'radar',desc:'Powerful bolts target flying enemies.',gold:1300,elixir:200,size:1.8,hp:850,max:4,time:20,unlock:3},
 tesla:{name:'Storm Coil',icon:'zap',desc:'Rapid electric strikes against ground and flying enemies.',gold:2300,elixir:500,size:1.8,hp:1100,max:4,time:30,unlock:4},
 inferno:{name:'Inferno Spire',icon:'flame',desc:'A searing beam cuts down tough troops.',gold:4500,elixir:1500,size:2,hp:1800,max:3,time:45,unlock:6},
 drill:{name:'Dark Elixir Drill',icon:'fuel',desc:'Produces dark elixir for hero upgrades.',gold:1700,elixir:500,size:2.3,hp:800,max:3,time:25,unlock:3},
 wall:{name:'Fortress Wall',icon:'brick-wall',desc:'Blocks ground troops until destroyed. Flying units pass over.',gold:75,elixir:0,size:.8,hp:550,max:160,time:0,unlock:1},
 bomb:{name:'Burst Trap',icon:'bomb',desc:'Triggers once when ground troops approach. Automatically rearms after each defense.',gold:220,elixir:0,size:.7,hp:1,max:12,time:5,unlock:2}
});
Object.assign(TROOPS,{
 raider:{name:'Gold Raider',icon:'footprints',desc:'Fast, inexpensive raider. Runs through weak defenses.',cost:85,time:3,hp:130,damage:34,speed:3.1,range:1,rate:.65,space:1,color:0x86a251,unlock:2},
 mage:{name:'Ember Mage',icon:'flame',desc:'A fragile ranged caster with powerful fire attacks.',cost:160,time:4,hp:155,damage:78,speed:1.8,range:4.5,rate:1.1,space:2,color:0x8f65b4,unlock:3},
 breaker:{name:'Siege Breaker',icon:'axe',desc:'Armored assault unit that targets defenses.',cost:240,time:5,hp:550,damage:90,speed:1.8,range:1.1,rate:1.2,space:3,color:0x627c89,unlock:4,target:'defense'},
 wyvern:{name:'Sky Wyvern',icon:'bird',desc:'Flying attacker that ignores walls and ground-only defenses.',cost:420,time:7,hp:1050,damage:115,speed:2,range:3.2,rate:1.25,space:5,color:0x81749d,unlock:5,flying:true},
 colossus:{name:'Iron Colossus',icon:'bot',desc:'A heavily armored siege unit built to outlast defenses.',cost:650,time:9,hp:2100,damage:155,speed:1.15,range:1.2,rate:1.45,space:7,color:0x7f9a98,unlock:6,target:'defense'}
});
export const DEFENSES={tower:{range:8.3,damage:24,rate:.9},cannon:{range:7,damage:45,rate:1.25,groundOnly:true},mortar:{range:11,damage:65,rate:2.8,splash:2.6,groundOnly:true},wizard:{range:7,damage:40,rate:1.3,splash:2},air:{range:10,damage:105,rate:1.1,airOnly:true},tesla:{range:7,damage:33,rate:.5},inferno:{range:8.5,damage:65,rate:.35}};
export const HEROES={
 ...EXTRA_HEROES,
 king:{name:'Ember King',icon:'crown',desc:'Frontline hero. Royal Fury heals and empowers nearby allies.',hp:2000,damage:100,speed:1.7,range:1.3,rate:1,unlock:2,color:0xc98544},
 queen:{name:'Moon Ranger',icon:'bow-arrow',desc:'Ranged hero. Moon Volley damages every standing defense.',hp:1300,damage:140,speed:2.1,range:5.6,rate:1,unlock:3,color:0x8768aa},
 prince:{name:'Dusk Prince',icon:'moon',desc:'Flying hero. Nightfall damages and freezes nearby defenses.',hp:1750,damage:125,speed:2.1,range:4.4,rate:1.1,unlock:4,color:0x6d619c,flying:true},
 champion:{name:'Dawn Champion',icon:'shield',desc:'Defense hunter. Sun Shield strikes the four nearest defenses.',hp:2200,damage:160,speed:2.4,range:3.5,rate:1,unlock:7,color:0xdba253,target:'defense'},
 machine:{name:'Battle Machine',icon:'bot',desc:'Builder Base hero. Overdrive heals and empowers nearby troops.',hp:2400,damage:130,speed:1.5,range:1.4,rate:1.2,unlock:1,color:0x8daba6,builderOnly:true},
 warden:{name:'Storm Warden',icon:'wand-sparkles',desc:'Flying support hero. Renewal restores the whole army.',hp:1600,damage:90,speed:1.8,range:5,rate:1.1,unlock:5,color:0x668aa2,flying:true}
};
export const SPELLS={thunder:{name:'Thunder',icon:'zap',cost:120,time:3,unlock:1,desc:'350 damage in a 3.5-tile radius.'},heal:{name:'Healing Circle',icon:'heart-pulse',cost:150,time:4,unlock:1,desc:'Restores nearby troops for 8 seconds.'},rage:{name:'Rage',icon:'flame',cost:180,time:4,unlock:2,desc:'Boosts movement and damage for 8 seconds.'},freeze:{name:'Freeze',icon:'snowflake',cost:180,time:4,unlock:3,desc:'Stops nearby defenses for 6 seconds.'}};
export const GEM_PACKS=[{id:'pouch',name:'Pouch of Gems',gems:500,cents:499},{id:'chest',name:'Chest of Gems',gems:1200,cents:999},{id:'vault',name:'Vault of Gems',gems:2500,cents:1999}];
function heroState(){return Object.fromEntries(X.HOME_HEROES.map(k=>[k,{level:0,recoverAt:0}]));}
export function seedObstacles(){return Array.from({length:22},(_,i)=>{const a=i/22*Math.PI*2,r=11.2+(i%3)*.65;return {id:'tree-'+i,type:i%5===0?'rock':'tree',x:Math.round(Math.cos(a)*r*2)/2,z:Math.round(Math.sin(a)*r*2)/2};});}
export function troopUnlocked(s,type){return Object.hasOwn(TROOPS,type)&&troopLevel(s)>=(TROOPS[type]?.unlock||1);}
export function heroMaxLevel(s,type){const d=HEROES[type];if(!d||hallLevel(s)<d.unlock||troopLevel(s)<(d.barracks||1))return 0;return d.barracks?Math.min(50,hallLevel(s)*5,troopLevel(s)*5):Math.min(50,(hallLevel(s)-d.unlock+1)*5);}
export function heroUnlocked(s,type){const d=HEROES[type];return !!d&&hallLevel(s)>=d.unlock&&troopLevel(s)>=(d.barracks||1)&&s.buildings.some(b=>b.type==='altar'&&!b.constructing);}
export function unitDefinition(u){return u.hero?HEROES[u.type]:u.pet?X.PETS[u.type]:u.siege?X.SIEGE[u.type]:TROOPS[u.type];}
export function heroCost(h){return {dark:80+Math.round(65*Math.pow(Math.max(1,h.level),1.4)),time:20+Math.max(1,h.level)*8};}
export function skipCost(finishAt,now=Date.now()){return Math.max(1,Math.ceil((finishAt-now)/10000));}
export function beginResearch(s,type,now=Date.now()){
 const lab=s.buildings.find(b=>b.type==='laboratory'&&!b.finishAt);if(!lab)return {error:'Build a Laboratory first.'};if(!troopUnlocked(s,type))return {error:'Unlock this troop in the Barracks first.'};
 if(s.researchQueue.length)return {error:'Your Laboratory is already researching.'};const level=s.research[type]||1;if(level>=Math.min(15,lab.level+2))return {error:'Upgrade the Laboratory to research further.'};const cost=250*level*level;if(s.elixir<cost)return {error:'Not enough elixir.'};s.elixir-=cost;s.researchQueue.push({type,finishAt:now+(20+level*12)*1000});return {ok:true};
}
export function upgradeHero(s,type,now=Date.now()){
 const def=HEROES[type],h=s.heroes[type];if(!Object.hasOwn(HEROES,type)||!h)return {error:'Unknown hero.'};if(!heroUnlocked(s,type))return {error:'Requires Hero Hall, Town Hall '+def.unlock+' and Barracks '+(def.barracks||1)+'.'};
 if(h.finishAt)return {error:'Hero upgrade already in progress.'};if(h.recoverAt>now)return {error:'Your hero is recovering.'};if(h.level>=heroMaxLevel(s,type))return {error:'Upgrade Town Hall and Barracks to raise this hero further.'};const c=heroCost(h);if(s.dark<c.dark)return {error:'Not enough dark elixir.'};s.dark-=c.dark;h.startedAt=now;h.finishAt=now+c.time*1000;return {ok:true};
}
export function brew(s,type,now=Date.now()){
 const d=SPELLS[type],forge=s.buildings.find(b=>b.type==='forge'&&!b.finishAt);if(!Object.hasOwn(SPELLS,type)||!forge||forge.level<d.unlock)return {error:'Upgrade your Spell Forge to unlock this spell.'};if(Object.values(s.spells).reduce((a,b)=>a+b,0)+s.spellQueue.length>=12)return {error:'Spell storage is full (12).'};if(s.elixir<d.cost)return {error:'Not enough elixir.'};s.elixir-=d.cost;s.spellQueue.push({type,finishAt:Math.max(now,s.spellQueue.at(-1)?.finishAt||0)+d.time*1000});return {ok:true};
}
export function clearObstacle(s,id,now=Date.now(),random=Math.random){const o=s.obstacles.find(o=>o.id===id);if(!o||o.finishAt)return {error:'Choose an uncleared obstacle.'};if(freeBuilders(s)<1)return {error:'A free builder is needed.'};const cost=o.type==='gem-box'?0:o.type==='tree'?75:120;if(s.gold<cost)return {error:'Not enough gold.'};s.gold-=cost;o.finishAt=now+(o.type==='tree'?8:12)*1000;o.gemReward=o.type==='gem-box'?R.GEM_BOX_REWARD:o.type==='tree'&&random()<.42?1+Math.floor(random()*6):0;return {ok:true};}
export function advanceProgression(s,now,events=[]){
 s.obstacles??=seedObstacles();s.heroes??=heroState();s.research??={};s.researchQueue??=[];s.spells??={thunder:2,heal:0,rage:0,freeze:0};s.spellQueue??=[];s.gems??=100;s.dark??=0;s.builders??=2;
 for(const o of s.obstacles.filter(o=>o.finishAt&&o.finishAt<=now)){s.gems+=o.gemReward||0;if(o.type==='gem-box')s.nextGemBoxAt=now+R.WEEK;events.push({kind:'obstacle',gems:o.gemReward||0});}s.obstacles=s.obstacles.filter(o=>!o.finishAt||o.finishAt>now);R.weeklyBox(s,now,events);
 for(const [type,h]of Object.entries(s.heroes))if(h.finishAt&&h.finishAt<=now){h.level++;delete h.finishAt;delete h.startedAt;events.push({kind:'hero',type});}
 for(const q of s.researchQueue.filter(q=>q.finishAt<=now)){s.research[q.type]=(s.research[q.type]||1)+1;events.push({kind:'research',type:q.type});}s.researchQueue=s.researchQueue.filter(q=>q.finishAt>now);
 for(const q of s.spellQueue.filter(q=>q.finishAt<=now)){s.spells[q.type]=(s.spells[q.type]||0)+1;events.push({kind:'spell',type:q.type});}s.spellQueue=s.spellQueue.filter(q=>q.finishAt>now);
 if(now>=(s.nextObstacleAt||now+1)){if(s.obstacles.length<28){for(let i=0;i<40;i++){const a=Math.random()*Math.PI*2,r=11+Math.random()*2.5,x=Math.round(Math.cos(a)*r*2)/2,z=Math.round(Math.sin(a)*r*2)/2;if(canPlace(s,'bomb',x,z)){s.obstacles.push({id:'tree-'+now,type:'tree',x,z});events.push({kind:'regrow'});break;}}}s.nextObstacleAt=now+1800000;}
}
export function deployHero(s,battle,type,x,z,now=Date.now()){
 const root=s;s=X.wallet(s,battle);const level=battle.heroStock?.[type],def=HEROES[type];if(!level||!Object.hasOwn(HEROES,type)||battle.ended)return {error:'Hero is not ready.'};if(!canDeploy(battle,x,z))return {error:'Deploy outside standing buildings or inside a cleared area.'};
 const stats=X.heroStats(s,type,level),u={id:'u'+battle.units.length,type,hero:true,level,x,z,hp:stats.hp,maxHp:stats.hp,damage:stats.damage,speed:stats.speed,range:stats.range,regen:stats.regen,freeze:stats.freeze,wardPower:stats.ward,cooldown:0,phase:0,abilityUsed:false};battle.units.push(u);X.addPet(root,battle,u);battle.heroStock[type]=0;battle.started=true;s.heroes[type].recoverAt=now+180000;return {unit:u};
}
export function heroAbility(battle,type){const u=battle.units.find(u=>u.hero&&u.type===type&&u.hp>0&&!u.abilityUsed);if(!u||battle.ended)return {error:'Deploy a living hero before using this ability.'};u.abilityUsed=true;X.extraAbility(battle,u);const ability=HEROES[type].ability||({champion:'shield',prince:'freeze',queen:'volley',warden:'heal'}[type]);if(ability==='shield'){const targets=battle.buildings.filter(b=>b.hp>0&&DEFENSES[b.type]).sort((a,b)=>Math.hypot(a.x-u.x,a.z-u.z)-Math.hypot(b.x-u.x,b.z-u.z)).slice(0,4);for(const b of targets)b.hp=Math.max(0,b.hp-u.damage*3);}else if(ability==='freeze'||ability==='burst'){for(const b of battle.buildings)if(Math.hypot(b.x-u.x,b.z-u.z)<7){b.hp=Math.max(0,b.hp-u.damage*2);if(ability==='freeze')b.frozen=8;}}else if(ability==='volley'){for(const b of battle.buildings)if(DEFENSES[b.type])b.hp=Math.max(0,b.hp-260);}else if(ability==='heal'){for(const a of battle.units)if(a.hp>0)a.hp=Math.min(a.maxHp,a.hp+a.maxHp*.5);}else{for(const a of battle.units)if(a.hp>0&&Math.hypot(a.x-u.x,a.z-u.z)<5){a.hp=Math.min(a.maxHp,a.hp+250);a.rage=10;}}return {ok:true};}
export function castSpell(s,battle,type,x,z){s=X.wallet(s,battle);if(!Object.hasOwn(SPELLS,type)||battle.ended||!Number.isFinite(x)||!Number.isFinite(z)||!(battle.land||[{x1:-(battle.bounds||8.7),x2:battle.bounds||8.7,z1:-(battle.bounds||8.7),z2:battle.bounds||8.7}]).some(r=>x>=r.x1-3&&x<=r.x2+3&&z>=r.z1-3&&z<=r.z2+3))return {error:'Choose a target in the village.'};if((battle.spellStock[type]||0)<1)return {error:'No spell remaining.'};battle.spellStock[type]--;s.spells[type]--;battle.started=true;
 if(type==='thunder'){strike(battle,x,z);}else if(type==='freeze'){for(const b of battle.buildings)if(Math.hypot(b.x-x,b.z-z)<3.8)b.frozen=6;}else battle.effects.push({type,x,z,remaining:8});return {ok:true};}
function tickEffects(b,dt){for(const u of b.units)u.rage=Math.max(0,(u.rage||0)-dt);for(const s of b.buildings)s.frozen=Math.max(0,(s.frozen||0)-dt);for(const e of b.effects||[]){e.remaining-=dt;for(const u of b.units)if(u.hp>0&&Math.hypot(u.x-e.x,u.z-e.z)<4){if(e.type==='heal')u.hp=Math.min(u.maxHp,u.hp+65*dt);if(e.type==='rage')u.rage=.2;}}b.effects=(b.effects||[]).filter(e=>e.remaining>0);}
function segmentNear(a,b,p,r){const dx=b.x-a.x,dz=b.z-a.z,d=dx*dx+dz*dz;if(d<.01)return false;const t=((p.x-a.x)*dx+(p.z-a.z)*dz)/d;return t>0&&t<1&&Math.hypot(a.x+t*dx-p.x,a.z+t*dz-p.z)<r;}
export function applyAction(s,a,now=Date.now(),random=Math.random){
 advance(s,now);if(!a||typeof a.type!=='string')return {error:'Invalid action.'};const raidAction=R.action(s,a,now);if(raidAction)return raidAction;const expanded=X.action(s,a,now);if(expanded)return expanded;const quality=Q.action(s,a,now);if(quality)return quality;
 if(a.type.startsWith('flag-'))return flagAction(s,a,now);
 if(a.type==='build'){const r=build(s,a.building,a.x,a.z,now);if(r.building)r.building.rotation=(a.rotation||0)%4;return r;}
 if(a.type==='move'){const b=s.buildings.find(b=>b.id===a.id);if(!b||b.finishAt||!canPlace(s,b.type,a.x,a.z,b.id))return {error:'This placement is blocked.'};b.x=a.x;b.z=a.z;b.rotation=(a.rotation||0)%4;return {ok:true};}
 if(a.type==='upgrade'){const target=s.buildings.find(b=>b.id===a.id);if(target?.type==='wall')return Q.action(s,{type:'wall-upgrade',ids:[target.id],currency:a.currency||'gold'},now);return upgrade(s,target,now);}
 if(a.type==='train')return train(s,a.troop,now);
 if(a.type==='collect'){const result=collect(s,a.id);for(const b of s.buildings.filter(b=>b.type==='drill'&&(!a.id||b.id===a.id))){const n=Math.floor(b.stored||0);s.dark+=n;b.stored-=n;}return result;}
 if(a.type==='research')return beginResearch(s,a.troop,now);
 if(a.type==='hero-upgrade')return upgradeHero(s,a.hero,now);
 if(a.type==='brew')return brew(s,a.spell,now);
 if(a.type==='clear')return clearObstacle(s,a.id,now,random);
 if(a.type==='claim')return claimQuest(s,a.id)?{ok:true}:{error:'Quest is not ready.'};
 if(a.type==='builder'){const cost=[0,0,250,500,1000][s.builders]||1000;if(s.builders>=5)return {error:'All 5 builders are hired.'};if(s.gems<cost)return {error:'Not enough gems.'};s.gems-=cost;s.builders++;return {ok:true};}
 if(a.type==='exchange'){if(!['gold','elixir','dark'].includes(a.resource))return {error:'Unknown resource.'};if(s.gems<20)return {error:'Not enough gems.'};if(a.resource!=='dark'&&s[a.resource]>=capacity(s))return {error:'Your stores are full.'};s.gems-=20;s[a.resource]=a.resource==='dark'?s.dark+200:Math.min(capacity(s),s[a.resource]+1500);return {ok:true};}
 if(a.type==='skip'){const target=a.kind==='hero'?s.heroes[a.id]:a.kind==='research'?s.researchQueue[0]:a.kind==='training'?s.queue[0]:a.kind==='spell'?s.spellQueue[0]:a.kind==='obstacle'?s.obstacles.find(o=>o.id===a.id):s.buildings.find(b=>b.id===a.id);if(!target?.finishAt)return {error:'Nothing to finish.'};const cost=skipCost(target.finishAt,now);if(s.gems<cost)return {error:'Not enough gems.'};s.gems-=cost;const shift=target.finishAt-now;if(a.kind==='training')for(const q of s.queue)q.finishAt-=shift;if(a.kind==='spell')for(const q of s.spellQueue)q.finishAt-=shift;target.finishAt=now;advance(s,now);return {ok:true};}
 return {error:'Unknown action.'};
}
export const QUESTS=[
  {id:'build',title:'A growing village',desc:'Build one more resource building',icon:'hammer',reward:400,goal:1,value:s=>s.stats.built},
  {id:'train',title:'Strength in numbers',desc:'Train 5 troops',icon:'users',reward:450,goal:5,value:s=>s.stats.trained},
  {id:'raid',title:'Into the wilds',desc:'Win your first battle',icon:'swords',reward:800,goal:1,value:s=>s.stats.wins},
  {id:'upgrade',title:'Built to last',desc:'Complete 3 building upgrades',icon:'castle',reward:650,goal:3,value:s=>s.stats.upgraded},
  {id:'conquer',title:'A name to remember',desc:'Win 5 battles',icon:'trophy',reward:1500,goal:5,value:s=>s.stats.wins}
];
export function initialState(now=Date.now()){
  return {version:2,gold:4000,elixir:3000,dark:200,gems:100,builders:2,glory:0,heroes:heroState(),research:{},researchQueue:[],spells:{thunder:2,heal:0,rage:0,freeze:0},spellQueue:[],obstacles:seedObstacles(),nextObstacleAt:now+1800000,shieldUntil:0,lastTick:now,army:{...Object.fromEntries(Object.keys(TROOPS).map(k=>[k,0])),guardian:9,ranger:5,giant:1},queue:[],cleared:{},claimed:[],stats:{built:0,trained:0,wins:0,upgraded:0},settings:{sound:false,quality:'auto'},buildings:[
    {id:'hall',type:'hall',x:0,z:0,level:1},
    {id:'barracks',type:'barracks',x:5,z:-3,level:1},
    {id:'mine',type:'mine',x:-6,z:2.5,level:1,stored:160},
    {id:'well',type:'well',x:5.5,z:3,level:1,stored:130},
    {id:'tower1',type:'tower',x:-5,z:-5,level:1},
    {id:'tower2',type:'tower',x:1,z:-7,level:1},
    {id:'cannon',type:'cannon',x:7,z:0,level:1},
    {id:'storage',type:'storage',x:-2.5,z:5.6,level:1},
    {id:'camp',type:'camp',x:3,z:7,level:1},
    {id:'cottage',type:'cottage',x:-6.5,z:-1,level:1}
  ]};
}
export function capacity(s){return 5000+s.buildings.filter(b=>b.type==='storage'&&!b.constructing).reduce((n,b)=>n+b.level*b.level*3000*Math.max(1,(b.level-1)/3),0);}
export function armyCapacity(s){return 24+s.buildings.filter(b=>b.type==='camp'&&!b.constructing).reduce((n,b)=>n+b.level*6,0);}
export function armySize(army){return Object.entries(TROOPS).reduce((n,[k,v])=>n+(army[k]||0)*v.space,0);}
export function queueSize(s){return s.queue.reduce((n,q)=>n+TROOPS[q.type].space,0);}
export function hallLevel(s){return s.buildings.find(b=>b.type==='hall')?.level||1;}
export function troopLevel(s){return Math.max(1,...s.buildings.filter(b=>b.type==='barracks'&&!b.constructing).map(b=>b.level));}
export function freeBuilders(s){return (s.builders||2)-s.buildings.filter(b=>b.finishAt&&b.type!=='wall').length-(s.obstacles||[]).filter(o=>o.finishAt).length;}
export function producerRate(b){return b.type==='mine'?1.7*b.level:b.type==='well'?1.35*b.level:b.type==='drill'?.12*b.level:0;}
export function productionCapacity(b){return b.level*600;}
export function upgradeCost(b){if(b.type==='wall')return {gold:Math.round(TYPES.wall.gold*Math.pow(1.7,b.level)),elixir:0,time:0};return {gold:Math.round((TYPES[b.type].gold||850)*Math.pow(1.7,b.level)),elixir:b.type==='hall'?500*b.level:Math.round((TYPES[b.type].elixir||50)*Math.pow(1.6,b.level)),time:(b.type==='hall'?30:15)*b.level};}
export function canPlace(s,type,x,z,ignoreId){
  if(!Object.hasOwn(TYPES,type))return false;const size=TYPES[type].size;
  return Number.isFinite(x)&&Number.isFinite(z)&&landContains(unlockedLand(s),x,z,size/2)&&!s.buildings.some(b=>b.id!==ignoreId&&Math.abs(b.x-x)<(TYPES[b.type].size+size)/2+(type==='wall'&&b.type==='wall'?.02:.25)&&Math.abs(b.z-z)<(TYPES[b.type].size+size)/2+(type==='wall'&&b.type==='wall'?.02:.25))&&!(s.flags||[]).some(f=>f.id!==ignoreId&&Math.abs(f.x-x)<size/2+.4&&Math.abs(f.z-z)<size/2+.4)&&!(s.obstacles||[]).some(o=>Math.abs(o.x-x)<size/2+.75&&Math.abs(o.z-z)<size/2+.75);
}
export function nextWallSpot(s,x,z,rotation=0){
 const directions=rotation%2?[[0,1],[1,0],[0,-1],[-1,0]]:[[1,0],[0,1],[-1,0],[0,-1]];
 for(const [dx,dz]of directions)if(canPlace(s,'wall',x+dx,z+dz))return {x:x+dx,z:z+dz};return null;
}
export function build(s,type,x,z,now=Date.now()){
  const def=TYPES[type];
  if(!Object.hasOwn(TYPES,type)||['hall','cottage','flag'].includes(type))return {error:'That building cannot be placed.'};
  if(hallLevel(s)<(def.unlock||1))return {error:'Requires Town Hall level '+def.unlock+'.'};
  if(s.buildings.filter(b=>b.type===type).length>=def.max)return {error:'You have reached the building limit.'};
  if(type!=='wall'&&freeBuilders(s)<1)return {error:'Both builders are busy. An upgrade will finish soon.'};
  if(!canPlace(s,type,x,z))return {error:'Choose an empty tile inside the clearing.'};
  if(s.gold<def.gold||s.elixir<def.elixir)return {error:'Not enough resources. Collect from your village or win a raid.'};
  s.gold-=def.gold;s.elixir-=def.elixir;
  const b={id:'b'+now.toString(36)+Math.floor(Math.random()*9999).toString(36),type,x,z,level:1,stored:0,constructing:type!=='wall',...(type==='wall'?{}:{startedAt:now,finishAt:now+def.time*1000})};
  s.buildings.push(b);s.stats.built++;
  return {building:b};
}
export function upgrade(s,b,now=Date.now()){
  if(!b||b.finishAt)return {error:'This building is already under construction.'};

  if(b.level>=(b.type==='hall'?15:15))return {error:'Maximum level reached.'};
  if(b.type!=='hall'&&b.level>=hallLevel(s)+1)return {error:'Upgrade your Town Hall first.'};
  if(b.type!=='wall'&&freeBuilders(s)<1)return {error:'All builders are busy.'};
  const c=upgradeCost(b);if(s.gold<c.gold||s.elixir<c.elixir)return {error:'Not enough resources for this upgrade.'};
  s.gold-=c.gold;s.elixir-=c.elixir;if(b.type==='wall'){b.level++;s.stats.upgraded++;}else{b.startedAt=now;b.finishAt=now+c.time*1000;b.constructing=false;}
  return {ok:true};
}
export function train(s,type,now=Date.now()){
  const def=TROOPS[type];if(!Object.hasOwn(TROOPS,type))return {error:'Choose a troop.'};
  if(!troopUnlocked(s,type))return {error:'Upgrade Barracks to level '+(def.unlock||1)+' to unlock this troop.'};
  if(!s.buildings.some(b=>b.type==='barracks'&&!b.finishAt))return {error:'Your barracks is being upgraded. Training will reopen soon.'};
  if(armySize(s.army)+queueSize(s)+def.space>armyCapacity(s))return {error:'Army camp is full. Raid with your troops or upgrade your camp.'};
  if(s.elixir<def.cost)return {error:'Not enough elixir to train this troop.'};
  s.elixir-=def.cost;
  const startAt=Math.max(now,s.queue.at(-1)?.finishAt||0);
  s.queue.push({id:'q'+now.toString(36)+s.queue.length,type,finishAt:startAt+def.time*1000});
  return {ok:true};
}
export function advance(s,now=Date.now()){
  const events=[];const from=s.lastTick||now;const elapsed=Math.min(8*3600,Math.max(0,(now-from)/1000));
  for(const b of s.buildings){
    if(b.finishAt&&now>=b.finishAt){if(!b.constructing){b.level++;s.stats.upgraded++;}b.constructing=false;delete b.finishAt;delete b.startedAt;events.push({kind:'building',building:b});}
    if(producerRate(b)&&!b.finishAt)b.stored=Math.min(productionCapacity(b),(b.stored||0)+producerRate(b)*elapsed);
  }
  const done=s.queue.filter(q=>q.finishAt<=now);s.queue=s.queue.filter(q=>q.finishAt>now);
  for(const q of done){s.army[q.type]=(s.army[q.type]||0)+1;s.stats.trained++;events.push({kind:'troop',type:q.type});}
  advanceProgression(s,now,events);X.advance(s,now,events);s.lastTick=now;return events;
}
export function collect(s,only){let gold=0,elixir=0;const cap=capacity(s);for(const b of s.buildings){if(only&&b.id!==only)continue;if(b.type==='mine'){const n=Math.max(0,Math.min(Math.floor(b.stored||0),cap-s.gold));s.gold+=n;b.stored=(b.stored||0)-n;gold+=n;}if(b.type==='well'){const n=Math.max(0,Math.min(Math.floor(b.stored||0),cap-s.elixir));s.elixir+=n;b.stored=(b.stored||0)-n;elixir+=n;}}return {gold,elixir};}
export function claimQuest(s,id){const q=QUESTS.find(q=>q.id===id);if(!q||s.claimed.includes(id)||q.value(s)<q.goal)return false;s.gold=Math.min(capacity(s),s.gold+q.reward);s.claimed.push(id);return true;}
export function loadState(storage,now=Date.now()){
  try{
    const raw=JSON.parse(storage.getItem(SAVE_KEY));if(!raw||![1,2,3].includes(raw.version)||!Array.isArray(raw.buildings)||!raw.buildings.some(b=>b.type==='hall'))return initialState(now);
    const base=initialState(now),s={...base,...raw,version:2,heroes:{...base.heroes,...raw.heroes},research:{...raw.research},spells:{...base.spells,...raw.spells},settings:{...base.settings,...raw.settings},stats:{...base.stats,...raw.stats},army:{...base.army,...raw.army}};
    s.buildings=s.buildings.filter(b=>TYPES[b.type]&&Number.isFinite(b.x)&&Number.isFinite(b.z)).map(b=>({...b,level:Math.max(1,Math.min(15,Number(b.level)||1)),stored:Math.max(0,Number(b.stored)||0)}));
    s.queue=Array.isArray(s.queue)?s.queue.filter(q=>TROOPS[q.type]&&Number.isFinite(q.finishAt)):[];
    for(const k of ['gold','elixir','glory'])s[k]=Math.max(0,Number(s[k])||0);
    for(const k of Object.keys(TROOPS))s.army[k]=Math.max(0,Math.min(200,Math.floor(Number(s.army[k])||0)));
    advance(s,now);return s;
  }catch{return initialState(now);}
}
const ENEMY_NAMES=['Bramble Outpost','Redstone Crossing','The Hollow Keep','Ironwood Watch','Ashen Citadel','Frostgate Hold','Stormbreak Fortress','The Ember Throne'];
export function enemyDef(index){return {index,name:ENEMY_NAMES[index%ENEMY_NAMES.length]+(index>=8?' '+(Math.floor(index/8)+1):''),gold:700+index*240,elixir:450+index*150,glory:20+index*5,level:1+Math.floor(index/2),difficulty:index<2?'Scout territory':index<5?'Guarded territory':'Hostile territory'};}
export function enemyBuildings(index){
  const level=1+Math.floor(index/3);const list=[
    {id:'e-hall',type:'hall',x:0,z:-2,level},
    {id:'e-mine',type:'mine',x:-4.5,z:1,level},
    {id:'e-well',type:'well',x:4.5,z:1,level},
    {id:'e-cannon',type:'cannon',x:0,z:3.5,level},
    {id:'e-storage',type:'storage',x:0,z:7,level},
    {id:'e-tower',type:'tower',x:5,z:-4,level}
  ];
  if(index>=1)list.push({id:'e-tower2',type:'tower',x:-5,z:-4,level});
  if(index>=2)list.push({id:'e-barracks',type:'barracks',x:-5,z:5,level});
  if(index>=3)list.push({id:'e-cannon2',type:'cannon',x:5,z:5,level});
  if(index>=5)list.push({id:'e-cannon3',type:'cannon',x:0,z:-6.5,level});
  return list.map(b=>({...b,maxHp:Math.round(TYPES[b.type].hp*(.67+index*.085)),hp:Math.round(TYPES[b.type].hp*(.67+index*.085)),cooldown:Math.random()*.8}));
}
export function createBattle(s,index){return X.enrichBattle(s,{enemy:enemyDef(index),buildings:enemyBuildings(index),units:[],remaining:{...s.army},deployed:{guardian:0,ranger:0,giant:0},started:false,elapsed:0,duration:150,bounds:8.7,spells:s.spells?.thunder||0,spellStock:{...s.spells},heroStock:Object.fromEntries(Object.entries(s.heroes||{}).filter(([k,h])=>h.level>0&&!h.finishAt&&!(h.recoverAt>Date.now())).map(([k,h])=>[k,h.level])),effects:[],ended:false,stats:{destroyed:0,stars:0,percent:0}});}
export function canDeploy(battle,x,z){
 if(!Number.isFinite(x)||!Number.isFinite(z)||battle.ended)return false;
 const regions=battle.land||[{x1:-(battle.bounds||8.7),x2:battle.bounds||8.7,z1:-(battle.bounds||8.7),z2:battle.bounds||8.7}];
 if(!regions.some(r=>x>=r.x1-4.8&&x<=r.x2+4.8&&z>=r.z1-4.8&&z<=r.z2+4.8))return false;
 if(battle.buildings.some(b=>b.hp>0&&Math.abs(b.x-x)<TYPES[b.type].size/2+1&&Math.abs(b.z-z)<TYPES[b.type].size/2+1))return false;
 return !landContains(regions,x,z)||battle.buildings.some(b=>b.hp<=0&&Math.abs(b.x-x)<=TYPES[b.type].size/2+1&&Math.abs(b.z-z)<=TYPES[b.type].size/2+1);
}
export function deploy(s,battle,type,x,z){
  s=X.wallet(s,battle);
  if(battle.ended||!Object.hasOwn(TROOPS,type)||!(battle.remaining[type]>0))return {error:'No troops of this type remaining.'};
  if(!canDeploy(battle,x,z))return {error:'Deploy outside standing buildings or inside a cleared area.'};
  const def=TROOPS[type],boost=1+((s.research?.[type]||1)-1)*.18;
  const unit={id:'u'+battle.units.length,type,level:s.research?.[type]||1,x,z,hp:def.hp*boost,maxHp:def.hp*boost,damage:def.damage*boost,cooldown:Math.random()*.3,phase:Math.random()*6.28};
  battle.units.push(unit);battle.remaining[type]--;battle.deployed[type]=(battle.deployed[type]||0)+1;s.army[type]--;battle.started=true;
  return {unit};
}
export function strike(battle,x,z){if(battle.spells<=0||battle.ended)return false;battle.spells--;battle.started=true;for(const b of battle.buildings)if(b.hp>0&&Math.hypot(b.x-x,b.z-z)<3.5)b.hp=Math.max(0,b.hp-350);return true;}
export function battleStats(battle){const targets=battle.buildings.filter(b=>!['wall','bomb'].includes(b.type));const dead=targets.filter(b=>b.hp<=0);const percent=Math.round(dead.length/Math.max(1,targets.length)*100);const stars=(percent>=50?1:0)+(dead.some(b=>b.type==='hall')?1:0)+(percent===100?1:0);return {destroyed:dead.length,percent,stars};}
export function stepBattle(battle,dt,onEvent=()=>{}){
  if(battle.ended||!battle.started)return;
  battle.elapsed+=dt;tickEffects(battle,dt);X.combatTick(battle,dt);const alive=()=>battle.buildings.filter(b=>b.hp>0&&b.type!=='bomb');
  for(const u of battle.units){
    if(u.hp<=0||u.pet&&X.PETS[u.type].heal)continue;const base=unitDefinition(u),def={...base,speed:u.speed||base.speed,range:u.range||base.range};const candidates=alive();if(!candidates.length)break;
    let targets=def.target==='defense'||u.type==='giant'?candidates.filter(b=>DEFENSES[b.type]):candidates.filter(b=>b.type!=='wall');if(!targets.length)targets=candidates;
    let target=targets.reduce((a,b)=>Math.hypot(a.x-u.x,a.z-u.z)<Math.hypot(b.x-u.x,b.z-u.z)?a:b);
    if(!def.flying){const wall=candidates.filter(b=>b.type==='wall'&&segmentNear(u,target,b,.9)).sort((a,b)=>Math.hypot(a.x-u.x,a.z-u.z)-Math.hypot(b.x-u.x,b.z-u.z))[0];if(wall)target=wall;}
    const dx=target.x-u.x,dz=target.z-u.z,d=Math.hypot(dx,dz),stop=def.range+TYPES[target.type].size*.4;
    u.target=target.id;u.cooldown=Math.max(0,u.cooldown-dt);
    if(d>stop){
      let vx=dx/d,vz=dz/d;
      for(const obstacle of candidates){if(obstacle.id===target.id)continue;const odx=u.x-obstacle.x,odz=u.z-obstacle.z;const od=Math.hypot(odx,odz),radius=TYPES[obstacle.type].size*.56+.35;if(od<radius&&od>.01){const strength=(radius-od)/radius*3;vx+=odx/od*strength;vz+=odz/od*strength;}}
      const len=Math.hypot(vx,vz)||1;u.x+=vx/len*Math.min(def.speed*(u.rage?1.4:1)*dt,d-stop);u.z+=vz/len*Math.min(def.speed*(u.rage?1.4:1)*dt,d-stop);u.moving=true;u.facing=Math.atan2(dx,dz);
    }else{u.moving=false;u.facing=Math.atan2(dx,dz);if(u.cooldown<=0){const beforeHp=target.hp;target.hp=Math.max(0,target.hp-u.damage*(u.rage?1.6:1)*(target.type==='wall'?(def.wallPower||1):1));if(def.splash)for(const other of candidates)if(other!==target&&Math.hypot(other.x-target.x,other.z-target.z)<def.splash)other.hp=Math.max(0,other.hp-u.damage*.5);u.cooldown=def.rate;u.swing=.24;onEvent({kind:'hit',unit:u,target,damage:beforeHp-target.hp,ranged:def.range>2});}}
    u.swing=Math.max(0,(u.swing||0)-dt);
  }
  for(const b of battle.buildings){
    if(b.hp<=0)continue;
    if(b.type==='bomb'&&!b.triggered){const nearby=battle.units.filter(u=>u.hp>0&&Math.hypot(u.x-b.x,u.z-b.z)<1.6);if(nearby.length){for(const u of battle.units)if(Math.hypot(u.x-b.x,u.z-b.z)<2.8)u.hp=Math.max(0,u.hp-130*b.level);b.triggered=true;b.hp=0;onEvent({kind:'trap',building:b});}continue;}
    const def=DEFENSES[b.type];if(!def||b.frozen>0)continue;b.cooldown=Math.max(0,b.cooldown-dt);if(b.cooldown>0)continue;
    const targets=battle.units.filter(u=>u.hp>0&&Math.hypot(u.x-b.x,u.z-b.z)<def.range&&(!def.airOnly||unitDefinition(u).flying)&&(!def.groundOnly||!unitDefinition(u).flying));if(!targets.length)continue;
    const u=targets.reduce((a,c)=>Math.hypot(a.x-b.x,a.z-b.z)<Math.hypot(c.x-b.x,c.z-b.z)?a:c);
    const damage=def.damage*(1+(b.level-1)*.15);u.hp=Math.max(0,u.hp-damage*(u.ward>0?.15:1));if(def.splash)for(const other of targets)if(other!==u&&Math.hypot(other.x-u.x,other.z-u.z)<def.splash)other.hp=Math.max(0,other.hp-damage*.65*(other.ward>0?.15:1));
    b.cooldown=def.rate;b.facing=Math.atan2(u.x-b.x,u.z-b.z);onEvent({kind:'defend',building:b,unit:u});
  }
  battle.stats=battleStats(battle);
  const empty=Object.values(battle.remaining).every(n=>n<=0)&&Object.values(battle.heroStock||{}).every(n=>n<=0)&&battle.units.every(u=>u.hp<=0);
  if(battle.stats.percent===100||battle.elapsed>=battle.duration||empty){battle.ended=true;onEvent({kind:'end'});}
}
export function settleBattle(s,battle){
  const root=s;s=X.wallet(s,battle);
  if(battle.settled)return battle.result;if(battle.practice){battle.ended=true;battle.settled=true;battle.stats=battleStats(battle);return battle.result={gold:0,elixir:0,dark:0,glory:0,...battle.stats,won:battle.stats.stars>0,practice:true};}battle.ended=true;battle.settled=true;battle.stats=battleStats(battle);
  const ratio=battle.stats.percent/100;const gold=Math.min(Math.max(0,capacity(s)-s.gold),Math.floor(battle.enemy.gold*ratio)),elixir=Math.min(Math.max(0,capacity(s)-s.elixir),Math.floor(battle.enemy.elixir*ratio)),glory=battle.stats.stars?Math.floor(battle.enemy.glory*battle.stats.stars/3):0;
  s.gold+=gold;s.elixir+=elixir;s.glory+=glory;
  if(battle.stats.stars){s.stats.wins++;if(!battle.pvp&&!battle.special)s.cleared[battle.enemy.index]=Math.max(s.cleared[battle.enemy.index]||0,battle.stats.stars);}
  const dark=battle.raid?Math.floor((battle.enemy.dark||0)*ratio):battle.stats.stars?Math.floor((battle.enemy.dark??30)*ratio):0;s.dark=(s.dark||0)+dark;for(const u of battle.units.filter(u=>u.hero)){const h=s.heroes[u.type];if(h)h.recoverAt=Date.now()+30000;}
  battle.result={gold,elixir,dark,glory,...battle.stats,won:battle.stats.stars>0};X.reward(root,battle,battle.result);R.recordAttack(root,battle,battle.result);return battle.result;
}

export function flagAction(s,a,now=Date.now()){
 if(s.realm)return {error:'Flags belong in the home village.'};s.flags??=[];
 if(a.type==='flag-buy'){if(!COUNTRY_CODES.has(a.code))return {error:'Choose a country from the flag shop.'};if(s.flags.length>=30)return {error:'A village can display 30 flags.'};if(!canPlace(s,'flag',a.x,a.z))return {error:'Choose an open tile for the flag.'};if(s.gold<FLAG_COST)return {error:'Not enough gold.'};s.gold-=FLAG_COST;const flag={id:'flag-'+now+'-'+Math.floor(Math.random()*1e8),code:a.code,x:a.x,z:a.z};s.flags.push(flag);return {ok:true,flag};}
 if(a.type==='flag-move'){const flag=s.flags.find(f=>f.id===a.id);if(!flag||!canPlace(s,'flag',a.x,a.z,flag.id))return {error:'Choose an open tile for the flag.'};flag.x=a.x;flag.z=a.z;return {ok:true,flag};}
 return {error:'Unknown flag action.'};
}
