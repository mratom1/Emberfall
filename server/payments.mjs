import {createHmac,timingSafeEqual} from 'node:crypto';
import {GEM_PACKS} from '../dist/model.js';

export function verifyWebhook(raw,signature,secret,now=Date.now()){
 if(!secret||typeof signature!=='string')throw new Error('Webhook is not configured.');
 const fields=signature.split(',').map(x=>x.split('=')),timestamp=fields.find(x=>x[0]==='t')?.[1];
 if(!timestamp||!/^\d+$/.test(timestamp)||Math.abs(now/1000-Number(timestamp))>300)throw new Error('Expired webhook signature.');
 const expected=createHmac('sha256',secret).update(timestamp+'.').update(raw).digest();
 const matches=fields.filter(x=>x[0]==='v1').some(([,v])=>{if(!/^[a-f0-9]{64}$/i.test(v||''))return false;return timingSafeEqual(expected,Buffer.from(v,'hex'));});
 if(!matches)throw new Error('Invalid webhook signature.');return JSON.parse(raw.toString('utf8'));
}
export function packById(id){return GEM_PACKS.find(p=>p.id===id);}
export async function createCheckout({key,origin,userId,orderId,pack,fetcher=fetch}){
 const params=new URLSearchParams({mode:'payment',client_reference_id:userId,success_url:origin+'/?purchase=success',cancel_url:origin+'/?purchase=cancelled','line_items[0][price_data][currency]':'usd','line_items[0][price_data][unit_amount]':String(pack.cents),'line_items[0][price_data][product_data][name]':pack.name+' · '+pack.gems+' gems','line_items[0][quantity]':'1','metadata[order_id]':orderId,'metadata[user_id]':userId,'metadata[pack_id]':pack.id});
 const response=await fetcher('https://api.stripe.com/v1/checkout/sessions',{method:'POST',headers:{Authorization:'Bearer '+key,'Content-Type':'application/x-www-form-urlencoded','Idempotency-Key':orderId},body:params,signal:AbortSignal.timeout(15000)});
 const data=await response.json();if(!response.ok||!data.id||!data.url)throw new Error('Payment provider is unavailable. Please try again.');
 if(new URL(data.url).hostname!=='checkout.stripe.com'||new URL(data.url).protocol!=='https:')throw new Error('Invalid checkout destination.');return data;
}
