import {randomBytes,scrypt,timingSafeEqual} from 'node:crypto';
import {promisify} from 'node:util';
const derive=promisify(scrypt),PARAMS={N:32768,r:8,p:3,maxmem:64*1024*1024};
let inFlight=0;
async function bounded(fn){if(inFlight>=4)throw Object.assign(new Error('Authentication is busy. Try again shortly.'),{status:429});inFlight++;try{return await fn();}finally{inFlight--;}}
export async function passwordHash(password){return bounded(async()=>{const salt=randomBytes(16).toString('hex'),key=await derive(password,salt,64,PARAMS);return `scrypt$32768$8$3$${salt}$${key.toString('hex')}`;});}
export async function passwordMatches(password,stored){return bounded(async()=>{
 try{let salt,expected,options;if(stored.startsWith('scrypt$')){const parts=stored.split('$');if(parts.length!==6||parts[1]!=='32768'||parts[2]!=='8'||parts[3]!=='3')return false;[, , , ,salt,expected]=parts;options=PARAMS;}else{[salt,expected]=stored.split(':');options={N:16384,r:8,p:1,maxmem:64*1024*1024};}if(!/^[a-f0-9]{32}$/.test(salt)||!/^[a-f0-9]{128}$/.test(expected))return false;const key=await derive(password,salt,64,options);return timingSafeEqual(key,Buffer.from(expected,'hex'));}catch{return false;}
 });}
export function setSecurityHeaders(res,secure){
 res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','same-origin');res.setHeader('X-Frame-Options','DENY');res.setHeader('Permissions-Policy','camera=(), microphone=(), geolocation=(), fullscreen=(self)');
 res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'");
 if(secure)res.setHeader('Strict-Transport-Security','max-age=31536000');
}
export function validPassword(value){return typeof value==='string'&&value.length>=10&&value.length<=128;}
export function authTransportAllowed(req,secure){const host=(req.headers.host||'').split(':')[0],remote=req.socket.remoteAddress||'';return secure||(['127.0.0.1','localhost'].includes(host)&&['127.0.0.1','::1','::ffff:127.0.0.1'].includes(remote));}
