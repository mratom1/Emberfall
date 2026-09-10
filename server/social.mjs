import {randomInt} from 'node:crypto';
export function playerCode(n){if(!Number.isSafeInteger(n)||n<1||n>676*99999)throw Error('Player ID space exhausted');const block=Math.floor((n-1)/99999);return 'EF'+String.fromCharCode(65+Math.floor(block/26),65+block%26)+String((n-1)%99999+1).padStart(5,'0');}
export function createSocial({db,fail}){
 db.exec(`CREATE TABLE IF NOT EXISTS player_codes(sequence INTEGER PRIMARY KEY AUTOINCREMENT,player_id TEXT NOT NULL UNIQUE REFERENCES players(id),code TEXT UNIQUE);
 CREATE TABLE IF NOT EXISTS clan_codes(clan_id TEXT PRIMARY KEY REFERENCES clans(id) ON DELETE CASCADE,code TEXT NOT NULL UNIQUE);
 CREATE TABLE IF NOT EXISTS friendships(sender TEXT NOT NULL REFERENCES players(id),recipient TEXT NOT NULL REFERENCES players(id),status TEXT NOT NULL DEFAULT 'pending',PRIMARY KEY(sender,recipient));
 CREATE INDEX IF NOT EXISTS friends_recipient ON friendships(recipient,status);
 CREATE TABLE IF NOT EXISTS clan_invites(clan_id TEXT NOT NULL REFERENCES clans(id) ON DELETE CASCADE,recipient TEXT NOT NULL REFERENCES players(id),sender TEXT NOT NULL REFERENCES players(id),PRIMARY KEY(clan_id,recipient));`);
 function code(id){let row=db.prepare('SELECT sequence,code FROM player_codes WHERE player_id=?').get(id);if(!row){const r=db.prepare('INSERT INTO player_codes(player_id) VALUES(?)').run(id);row={sequence:Number(r.lastInsertRowid)};}if(!row.code){row.code=playerCode(row.sequence);db.prepare('UPDATE player_codes SET code=? WHERE player_id=?').run(row.code,id);}return row.code;}
 function clanCode(id){let row=db.prepare('SELECT code FROM clan_codes WHERE clan_id=?').get(id);if(row)return row.code;for(let i=0;i<20;i++){const value=Array.from({length:10},()=>String(randomInt(10))).join('');if(!db.prepare('SELECT code FROM clan_codes WHERE code=?').get(value)){db.prepare('INSERT INTO clan_codes VALUES(?,?)').run(id,value);return value;}}fail('Please try creating the clan again.');}
 for(const p of db.prepare('SELECT id FROM players ORDER BY rowid').all())code(p.id);
 for(const c of db.prepare('SELECT id FROM clans').all())clanCode(c.id);
 const profile=p=>{const s=JSON.parse(p.state);return {id:p.id,code:code(p.id),name:p.name,glory:p.glory,hall:s.buildings.find(b=>b.type==='hall')?.level||1,clanId:p.clan_id};};
 function read(user,q=''){
 q=String(q).trim().slice(0,40);const players=q?db.prepare('SELECT p.* FROM players p JOIN player_codes c ON c.player_id=p.id WHERE c.code=? OR p.name LIKE ? LIMIT 30').all(q.toUpperCase(),'%'+q+'%').map(profile):[];
 const clans=db.prepare('SELECT c.*,x.code,(SELECT count(*) FROM players p WHERE p.clan_id=c.id) AS members FROM clans c JOIN clan_codes x ON x.clan_id=c.id WHERE x.code=? OR c.name LIKE ? ORDER BY c.name LIMIT 40').all(q,'%'+q+'%');
 const friends=db.prepare('SELECT f.sender,f.recipient,f.status,p.* FROM friendships f JOIN players p ON p.id=CASE WHEN f.sender=? THEN f.recipient ELSE f.sender END WHERE f.sender=? OR f.recipient=? LIMIT 200').all(user.id,user.id,user.id).map(p=>({...profile(p),status:p.status,incoming:p.recipient===user.id}));
 const invites=db.prepare('SELECT i.clan_id,c.name,x.code FROM clan_invites i JOIN clans c ON c.id=i.clan_id JOIN clan_codes x ON x.clan_id=c.id WHERE i.recipient=? LIMIT 100').all(user.id);
 return {profile:profile(user),players,clans,friends,invites};
 }
 function action(user,a){
 const target=db.prepare('SELECT p.* FROM players p LEFT JOIN player_codes c ON c.player_id=p.id WHERE p.id=? OR c.code=?').get(String(a.target||''),String(a.target||'').toUpperCase());
 if(['request','accept','remove','invite'].includes(a.action)&&(!target||target.id===user.id))fail('Choose another player.');
 if(a.action==='request'){if(db.prepare('SELECT 1 FROM friendships WHERE (sender=? AND recipient=?) OR (sender=? AND recipient=?)').get(user.id,target.id,target.id,user.id))fail('A friendship or request already exists.');if(db.prepare('SELECT count(*) n FROM friendships WHERE sender=? OR recipient=?').get(user.id,user.id).n>=100)fail('Friend list is full.');db.prepare('INSERT INTO friendships(sender,recipient) VALUES(?,?)').run(user.id,target.id);}
 else if(a.action==='accept'){const r=db.prepare("UPDATE friendships SET status='accepted' WHERE sender=? AND recipient=? AND status='pending'").run(target.id,user.id);if(!r.changes)fail('No incoming request.');}
 else if(a.action==='remove')db.prepare('DELETE FROM friendships WHERE (sender=? AND recipient=?) OR (sender=? AND recipient=?)').run(user.id,target.id,target.id,user.id);
 else if(a.action==='invite'){const clan=db.prepare('SELECT * FROM clans WHERE id=? AND owner_id=?').get(user.clan_id,user.id);if(!clan)fail('Only your clan leader can invite players.');if(target.clan_id)fail('This player already belongs to a clan.');db.prepare('INSERT OR IGNORE INTO clan_invites VALUES(?,?,?)').run(clan.id,target.id,user.id);}
 else if(a.action==='join-invite'){if(user.clan_id)fail('Leave your current clan first.');const invite=db.prepare('SELECT * FROM clan_invites WHERE clan_id=? AND recipient=?').get(a.clanId,user.id);if(!invite)fail('Invitation not found.');if(db.prepare('SELECT count(*) n FROM players WHERE clan_id=?').get(a.clanId).n>=30)fail('Clan is full.');db.prepare('UPDATE players SET clan_id=? WHERE id=?').run(a.clanId,user.id);db.prepare('DELETE FROM clan_invites WHERE recipient=?').run(user.id);}
 else if(a.action==='decline-invite')db.prepare('DELETE FROM clan_invites WHERE clan_id=? AND recipient=?').run(a.clanId,user.id);
 else fail('Unknown social action.');return {ok:true};
 }
 return {code,clanCode,read,action};
}
