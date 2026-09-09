import * as R from '../dist/raids.js';
import * as M from '../dist/model.js';

export function createRaids({db,getUser,stateOf,persist,fail,random}) {
  function busy(id){return !!db.prepare('SELECT id FROM battles WHERE (defender_id=? OR player_id=?) AND settled=0 LIMIT 1').get(id,id);}
  function candidates(user,s,now,{attackers=false}={}) {
    return db.prepare('SELECT id,name,state,clan_id FROM players WHERE id<>? ORDER BY updated_at DESC LIMIT 500').all(user.id).filter(u=>{
      if(user.clan_id&&u.clan_id===user.clan_id||busy(u.id))return false;
      const other=JSON.parse(u.state);
      return Math.abs(M.hallLevel(other)-M.hallLevel(s))<=2 && (attackers ? now-(other.raids?.lastSeenAt||0)<15*60000 : !(other.shieldUntil>now));
    });
  }
  function choose(user,s,now,defenderId) {
    let defender;
    if(defenderId){
      defender=getUser(defenderId);
      if(!defender||defender.id===user.id)fail('Invalid opponent.');
      if(user.clan_id&&user.clan_id===defender.clan_id)fail('You cannot attack a clanmate.');
      if(busy(defender.id))fail('This village is already in a battle.');
      const ds=stateOf(defender,now);
      if(ds.shieldUntil>now)fail('This village is protected by a Shield.');
      if(Math.abs(M.hallLevel(ds)-M.hallLevel(s))>2)fail('Choose an opponent close to your Town Hall level.');
      return {user:defender,id:defender.id,name:defender.name,kind:'player',state:ds};
    }
    let pool=candidates(user,s,now);
    if(pool.length){
      const nearest=Math.min(...pool.map(u=>Math.abs(M.hallLevel(JSON.parse(u.state))-M.hallLevel(s))));
      pool=pool.filter(u=>Math.abs(M.hallLevel(JSON.parse(u.state))-M.hallLevel(s))===nearest);
      const fresh=pool.filter(u=>!s.raids.recentOpponents.includes(u.id));if(fresh.length)pool=fresh;
      defender=getUser(pool[Math.min(pool.length-1,Math.floor(random()*pool.length))].id);
      s.raids.recentOpponents=[defender.id,...s.raids.recentOpponents.filter(id=>id!==defender.id)].slice(0,5);
      return {user:defender,id:defender.id,name:defender.name,kind:'player',state:stateOf(defender,now)};
    }
    return R.botVillage(s,random,now);
  }
  function start(user,s,a,now) {
    R.ensure(s,now);
    if(busy(user.id))fail('Finish your current battle before searching again.');
    const defender=choose(user,s,now,a.defender),b=R.configureBattle(M.createBattle(s,0),defender);
    b.attackerName=user.name;b.attackerHall=M.hallLevel(s);
    if(defender.user){R.reserveLoot(defender.state,b);persist(defender.user,defender.state,now);}
    return {battle:b,defenderId:defender.user?.id||null};
  }
  function defend(user,s,now) {
    R.ensure(s,now);
    if(s.raids.nextDefenseAt>now||s.shieldUntil>now||busy(user.id)||now-s.raids.lastSeenAt<5*60000)return null;
    if(candidates(user,s,now,{attackers:true}).length)return null;
    const entry=R.simulateDefense(s,random,now);if(!entry)return null;
    const result={...entry.result,attackerName:entry.opponent,attackerHall:entry.hall,defenderName:user.name,defenderHall:M.hallLevel(s),opponentType:'bot',mode:'raid'};
    db.prepare('INSERT OR IGNORE INTO raid_log VALUES(?,?,?,?,?)').run(entry.id+':'+user.id,'bot:'+entry.opponent,user.id,JSON.stringify(result),now);
    persist(user,s,now);return entry;
  }
  function history(user) {
    return db.prepare('SELECT r.*,a.name AS attacker,d.name AS defender FROM raid_log r LEFT JOIN players a ON a.id=r.attacker_id LEFT JOIN players d ON d.id=r.defender_id WHERE r.attacker_id=? OR r.defender_id=? ORDER BY created_at DESC LIMIT 100').all(user.id,user.id).map(row=>{
      const result=JSON.parse(row.result),attack=row.attacker_id===user.id;
      return {id:row.id,direction:attack?'attack':'defense',opponent:attack?(result.defenderName||row.defender||'Wilds stronghold'):(result.attackerName||row.attacker||'AI raider'),opponentType:result.opponentType||(!row.defender_id?'bot':'player'),hall:attack?result.defenderHall:result.attackerHall,mode:result.mode||'campaign',created_at:row.created_at,result};
    });
  }
  return {start,defend,history,busy};
}
