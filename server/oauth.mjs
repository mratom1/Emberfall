import {randomBytes, randomUUID, createHash, createHmac, createPublicKey, verify} from 'node:crypto';

const digest = value => createHash('sha256').update(value).digest('hex');
const secret = () => randomBytes(32).toString('base64url');
const fail = (message, status = 400) => { throw Object.assign(new Error(message), {status}); };
const subject = value => typeof value === 'string' && value.length > 0 && value.length <= 255;
const label = value => typeof value === 'string' ? value.replace(/[\u0000-\u001f\u007f]/g, '').trim().slice(0, 60) : '';
const fields = (url, data) => {const u = new URL(url); for (const [k,v] of Object.entries(data)) u.searchParams.set(k, v); return u;};

// This is an application session handoff. Provider tokens never go to a WebView,
// URL fragment, localStorage, app bridge, log, or persistent identity record.
export function createOAuth({db, settings, config = {}, tx, getUser, newSession, snapshot}) {
  db.exec(`CREATE TABLE IF NOT EXISTS auth_identities (
    provider TEXT NOT NULL, subject TEXT NOT NULL, player_id TEXT NOT NULL REFERENCES players(id),
    created_at INTEGER NOT NULL, PRIMARY KEY(provider, subject));
    CREATE INDEX IF NOT EXISTS identity_player ON auth_identities(player_id);
    CREATE TABLE IF NOT EXISTS oauth_attempts (
    id TEXT PRIMARY KEY, state_hash TEXT UNIQUE NOT NULL, poll_hash TEXT NOT NULL,
    provider TEXT NOT NULL, mode TEXT NOT NULL, owner_session TEXT NOT NULL,
    owner_player TEXT NOT NULL, verifier TEXT NOT NULL, nonce TEXT NOT NULL,
    expires_at INTEGER NOT NULL, status TEXT NOT NULL, result TEXT);
    CREATE INDEX IF NOT EXISTS oauth_owner ON oauth_attempts(owner_session, expires_at);
    CREATE INDEX IF NOT EXISTS oauth_expiry ON oauth_attempts(expires_at);`);
  const providers = {
    google: {id: config.googleId ?? process.env.GOOGLE_CLIENT_ID ?? '', key: config.googleSecret ?? process.env.GOOGLE_CLIENT_SECRET ?? ''},
    facebook: {id: config.facebookId ?? process.env.FACEBOOK_APP_ID ?? '', key: config.facebookSecret ?? process.env.FACEBOOK_APP_SECRET ?? ''}
  };
  const version = config.facebookVersion ?? process.env.FACEBOOK_GRAPH_VERSION ?? 'v25.0';
  if (!/^v\d{2}\.0$/.test(version)) throw new Error('FACEBOOK_GRAPH_VERSION must look like v25.0.');
  let origin;
  try {const u = new URL(settings.origin); if(u.protocol === 'https:' && u.origin === settings.origin && !u.username && !u.password && settings.secure) origin = u.origin;} catch {}
  const enabled = id => !!(origin && providers[id]?.id && providers[id]?.key);
  const publicConfig = () => Object.fromEntries(Object.keys(providers).map(p => [p, {enabled: enabled(p)}]));
  const redirect = p => origin + '/api/auth/oauth/' + p + '/callback';
  let jwks = {keys: [], until: 0, fetchedAt: 0};
  async function fetchJSON(url, init = {}) {
    const response = await settings.fetcher(url, {...init, redirect: 'error', signal: AbortSignal.timeout(10000)});
    if (!response.ok) fail('The sign-in provider could not complete this request.', 502);
    if (Number(response.headers.get('content-length')) > 65536) fail('Invalid sign-in response.', 502);
    const reader = response.body.getReader(); const chunks = []; let size = 0;
    try {while(true) {const r = await reader.read(); if (r.done) break; size += r.value.length; if(size > 65536) {await reader.cancel(); fail('Invalid sign-in response.', 502);} chunks.push(Buffer.from(r.value));}}
    finally {reader.releaseLock();}
    let data; try {data = JSON.parse(Buffer.concat(chunks).toString());} catch {fail('Invalid sign-in response.', 502);}
    if(!data || typeof data !== 'object' || Array.isArray(data)) fail('Invalid sign-in response.', 502);
    return data;
  }
  async function googleIdentity(code, attempt) {
    const token = await fetchJSON('https://oauth2.googleapis.com/token', {method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: new URLSearchParams({code, client_id: providers.google.id, client_secret: providers.google.key, redirect_uri: redirect('google'), grant_type: 'authorization_code', code_verifier: attempt.verifier}).toString()});
    if (typeof token.id_token !== 'string' || token.id_token.length > 16000) fail('Invalid Google identity.', 401);
    const parts = token.id_token.split('.'); if(parts.length !== 3 || parts.some(p => !/^[A-Za-z0-9_-]+$/.test(p))) fail('Invalid Google identity.', 401);
    let header, claims; try {header = JSON.parse(Buffer.from(parts[0], 'base64url')); claims = JSON.parse(Buffer.from(parts[1], 'base64url'));} catch {fail('Invalid Google identity.', 401);}
    if(header?.alg !== 'RS256' || typeof header.kid !== 'string' || header.kid.length > 200) fail('Invalid Google signature.', 401);
    const now = Date.now();
    if (jwks.until <= now || (!jwks.keys.some(k => k.kid === header.kid) && now - jwks.fetchedAt > 60000)) {
      const result = await fetchJSON('https://www.googleapis.com/oauth2/v3/certs');
      if(!Array.isArray(result.keys) || result.keys.length > 20) fail('Google signing keys unavailable.', 502);
      jwks = {keys: result.keys, fetchedAt: now, until: now + 1800000};
    }
    const key = jwks.keys.find(k => k.kid === header.kid && k.kty === 'RSA' && (!k.use || k.use === 'sig') && (!k.alg || k.alg === 'RS256'));
    let valid = false;
    try {valid = !!key && verify('RSA-SHA256', Buffer.from(parts[0] + '.' + parts[1]), createPublicKey({key, format: 'jwk'}), Buffer.from(parts[2], 'base64url'));} catch {}
    const seconds = now / 1000;
    if(!valid || !claims || !['accounts.google.com', 'https://accounts.google.com'].includes(claims.iss) || claims.aud !== providers.google.id || (claims.azp && claims.azp !== providers.google.id) || !Number.isFinite(claims.exp) || claims.exp <= seconds || !Number.isFinite(claims.iat) || claims.iat > seconds + 60 || claims.iat < seconds - 600 || claims.nonce !== attempt.nonce || !subject(claims.sub)) fail('Google identity verification failed.', 401);
    return {subject: claims.sub, name: label(claims.name)};
  }
  async function facebookIdentity(code) {
    const base = 'https://graph.facebook.com/' + version;
    const result = await fetchJSON(base + '/oauth/access_token', {method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: new URLSearchParams({client_id: providers.facebook.id, client_secret: providers.facebook.key, redirect_uri: redirect('facebook'), code}).toString()});
    const token = result.access_token;
    if(typeof token !== 'string' || token.length > 16000) fail('Invalid Facebook identity.', 401);
    const checked = await fetchJSON(fields(base + '/debug_token', {input_token: token}), {headers: {Authorization: 'Bearer ' + providers.facebook.id + '|' + providers.facebook.key}});
    const d = checked.data, now = Date.now()/1000;
    if(d?.is_valid !== true || String(d.app_id) !== providers.facebook.id || !subject(d.user_id) || !Number.isFinite(d.expires_at) || d.expires_at <= now || (d.data_access_expires_at && d.data_access_expires_at <= now)) fail('Facebook identity verification failed.', 401);
    const proof = createHmac('sha256', providers.facebook.key).update(token).digest('hex');
    const profile = await fetchJSON(fields(base + '/me', {fields: 'id,name', appsecret_proof: proof}), {headers: {Authorization: 'Bearer ' + token}});
    if(profile.id !== d.user_id) fail('Facebook identity verification failed.', 401);
    return {subject: profile.id, name: label(profile.name)};
  }
  function start(user, session, data) {
    if(!['google','facebook'].includes(data.provider) || !enabled(data.provider)) fail('This sign-in provider is not configured on this server.', 503);
    if(!['signin','link'].includes(data.mode)) fail('Choose sign in or link account.');
    if(data.mode === 'link' && !user.password_hash && !user.providers?.length) fail('Save your village account before linking another sign-in method.');
    if(db.prepare('SELECT id FROM battles WHERE player_id=? AND settled=0').get(user.id)) fail('Return home before signing in.');
    const now = Date.now();
    if(db.prepare("SELECT COUNT(*) AS n FROM oauth_attempts WHERE owner_session=? AND expires_at>? AND status IN ('pending','processing','ready')").get(session.token_hash, now).n >= 3) fail('Complete or cancel your open sign-in window first.', 429);
    const id = randomUUID(), state = secret(), pollToken = secret(), verifier = secret(), nonce = secret(), expiresAt = now + 600000, p = data.provider;
    db.prepare('INSERT INTO oauth_attempts VALUES(?,?,?,?,?,?,?,?,?,?,?,NULL)').run(id, digest(state), digest(pollToken), p, data.mode, session.token_hash, user.id, verifier, nonce, expiresAt, 'pending');
    const authorizationUrl = p === 'google' ? fields('https://accounts.google.com/o/oauth2/v2/auth', {client_id: providers[p].id, redirect_uri: redirect(p), response_type: 'code', scope: 'openid profile', state, nonce, code_challenge: createHash('sha256').update(verifier).digest('base64url'), code_challenge_method: 'S256', prompt: 'select_account'}) : fields('https://www.facebook.com/' + version + '/dialog/oauth', {client_id: providers[p].id, redirect_uri: redirect(p), response_type: 'code', scope: 'public_profile', state});
    return {id, pollToken, authorizationUrl: authorizationUrl.href, expiresAt};
  }
  async function callback(provider, params) {
    const state = params.get('state');
    if(!enabled(provider) || typeof state !== 'string' || !/^[A-Za-z0-9_-]{43}$/.test(state)) fail('This sign-in request is invalid or expired.', 400);
    const attempt = db.prepare('SELECT * FROM oauth_attempts WHERE state_hash=? AND provider=?').get(digest(state), provider);
    if(!attempt || attempt.expires_at <= Date.now() || attempt.status !== 'pending') fail('This sign-in request was used or expired. Start again in the game.', 400);
    // Claim before network I/O; a replay cannot exchange a second code.
    db.prepare("UPDATE oauth_attempts SET status='processing' WHERE id=? AND status='pending'").run(attempt.id);
    try {
      const code = params.get('code');
      if(params.has('error') || typeof code !== 'string' || code.length < 1 || code.length > 4096) fail('Sign-in was cancelled. You can try again in the game.');
      const identity = provider === 'google' ? await googleIdentity(code, attempt) : await facebookIdentity(code);
      if(!db.prepare('SELECT 1 FROM sessions WHERE token_hash=? AND player_id=? AND expires_at>?').get(attempt.owner_session, attempt.owner_player, Date.now()) || attempt.expires_at <= Date.now()) fail('The game session expired. Start again in the game.');
      db.prepare("UPDATE oauth_attempts SET status='ready',result=?,verifier='',nonce='' WHERE id=? AND status='processing'").run(JSON.stringify(identity), attempt.id);
      return true;
    } catch {
      db.prepare("UPDATE oauth_attempts SET status='failed',result=NULL,verifier='',nonce='' WHERE id=?").run(attempt.id);
      return false;
    }
  }
  function poll(user, session, data, res) {
    if(typeof data.id !== 'string' || typeof data.pollToken !== 'string' || data.pollToken.length !== 43) fail('Invalid sign-in handoff.', 403);
    const row = db.prepare('SELECT * FROM oauth_attempts WHERE id=? AND owner_session=? AND owner_player=? AND poll_hash=?').get(data.id, session.token_hash, user.id, digest(data.pollToken));
    if(!row || row.expires_at <= Date.now()) fail('Sign-in expired. Please start again.', 410);
    if(data.cancel === true) {db.prepare('DELETE FROM oauth_attempts WHERE id=?').run(row.id); return {status: 'cancelled'};}
    if(row.status === 'failed') fail('Sign-in was cancelled or could not be verified. Please try again.', 401);
    if(row.status !== 'ready') return {status: 'pending'};
    const identity = JSON.parse(row.result);
    return tx(() => {
      const saved = db.prepare('SELECT player_id FROM auth_identities WHERE provider=? AND subject=?').get(row.provider, identity.subject);
      if(row.mode === 'link' && saved && saved.player_id !== user.id) fail('That sign-in belongs to another village. Its villages cannot be merged.', 409);
      if(db.prepare('SELECT id FROM battles WHERE player_id=? AND settled=0').get(user.id)) fail('Return home before completing sign-in.', 409);
      if(!saved && row.mode === 'signin' && (user.password_hash || user.providers?.length)) fail('No village is saved to that account. Choose Connect to link it, or sign out to start a new village.',409);
      const target = saved?.player_id || user.id;
      if(!saved) {
        db.prepare('INSERT INTO auth_identities VALUES(?,?,?,?)').run(row.provider, identity.subject, target, Date.now());
        if(!user.password_hash && !user.providers?.length && identity.name) db.prepare('UPDATE players SET name=? WHERE id=?').run(identity.name, target);
        db.prepare('DELETE FROM sessions WHERE player_id=?').run(target);
      } else db.prepare('DELETE FROM sessions WHERE token_hash=?').run(session.token_hash);
      db.prepare('DELETE FROM oauth_attempts WHERE owner_session=?').run(session.token_hash);
      const fresh = newSession(target, res);
      return {status: 'complete', ...snapshot(getUser(target)), csrf: fresh.csrf};
    });
  }
  const clean = () => db.prepare('DELETE FROM oauth_attempts WHERE expires_at<?').run(Date.now());
  return {publicConfig, start, callback, poll, clean};
}

export function callbackHTML(success) {
  return `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Emberfall account</title><link rel="stylesheet" href="/theme.css"><body class="auth-callback"><main><span class="auth-emblem">E</span><p>EMBERFALL · ACCOUNT</p><h1>${success ? 'You are signed in.' : 'Sign-in could not finish.'}</h1><p>${success ? 'Return to Emberfall in your app or the original game tab. Your village will open there.' : 'Return to the game and try again. Your village has not changed.'}</p><p>You can close this browser tab.</p></main></body></html>`;
}
