import assert from 'node:assert/strict';
import {mkdtemp, mkdir, writeFile, readFile, copyFile, rm, access} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
import path from 'node:path';
import os from 'node:os';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('..',import.meta.url)),dir=await mkdtemp(path.join(os.tmpdir(),'emberfall-deploy-'));
let count=0;const pass=message=>{count++;console.log('PASS',message);};
const image='emberfall:'+'a'.repeat(40),oldImage='emberfall:'+'b'.repeat(40);
try {
 await mkdir(path.join(dir,'bin'));await mkdir(path.join(dir,'deploy'));
 await copyFile(path.join(root,'deploy/runtime.compose.yml'),path.join(dir,'deploy/runtime.compose.yml'));
 await writeFile(path.join(dir,'.env'),'DOMAIN=$(touch DO_NOT_EXECUTE)\n');
 const fake=`#!/usr/bin/env python3
import sys,os,json
args=sys.argv[1:]
with open(os.environ['DOCKER_LOG'],'a') as f: f.write(json.dumps({'args':args,'image':os.environ.get('GAME_IMAGE')})+'\\n')
if args[0]=='compose':
 if 'config' in args: print(json.dumps({'name':'emberfall'}))
 elif 'ps' in args: print('old-container')
 elif 'exec' in args and os.environ.get('FAIL_BACKUP')=='1': sys.exit(1)
 elif 'up' in args and os.environ.get('FAIL_NEW')=='1' and os.environ.get('GAME_IMAGE')==os.environ['NEW_IMAGE']: sys.exit(1)
elif args[0]=='inspect':
 print('true' if '.State.Running' in args[2] else os.environ['OLD_IMAGE'])
elif args[:2]==['volume','inspect'] and os.environ.get('LEGACY_VOLUME')=='1': sys.exit(1)
elif args[:2]==['volume','ls']: print('oldproject_emberfall_data')
`;
 await writeFile(path.join(dir,'bin/docker'),fake,{mode:0o755});
 const log=path.join(dir,'commands.log'),env={...process.env,PATH:path.join(dir,'bin')+':'+process.env.PATH,DOCKER_LOG:log,NEW_IMAGE:image,OLD_IMAGE:oldImage};
 const run=async(extra={},argument=image)=>{await writeFile(log,'');const result=spawnSync('bash',[path.join(root,'scripts/deploy.sh'),argument],{cwd:dir,env:{...env,...extra},encoding:'utf8'});const calls=(await readFile(log,'utf8')).trim().split('\n').filter(Boolean).map(JSON.parse);return {...result,calls};};
 let r=await run();assert.equal(r.status,0,r.stderr);assert.equal((await readFile(path.join(dir,'.deploy/current-image'),'utf8')).trim(),image);
 assert.ok(r.calls.findIndex(c=>c.args.includes('exec'))<r.calls.findIndex(c=>c.args.includes('up')));
 await assert.rejects(access(path.join(dir,'DO_NOT_EXECUTE')));
 pass('Deployment backs up before replacement and never executes .env as shell code');
 r=await run({FAIL_NEW:'1'});assert.equal(r.status,1);const changes=r.calls.filter(c=>c.args.includes('up'));assert.deepEqual(changes.map(c=>c.image),[image,oldImage]);
 assert.ok(r.calls.every(c=>!c.args.includes('down')&&!c.args.includes('rm')));
 pass('A failed health gate restores the old image without deleting player volumes');
 r=await run({FAIL_BACKUP:'1'});assert.notEqual(r.status,0);assert.ok(!r.calls.some(c=>c.args.includes('up')));
 r=await run({LEGACY_VOLUME:'1'});assert.notEqual(r.status,0);assert.ok(!r.calls.some(c=>c.args.includes('up')));
 pass('Backup failure and ambiguous legacy volumes stop before replacing the running game');
 r=await run({},'emberfall:latest;touch invalid');assert.equal(r.status,2);assert.equal(r.calls.length,0);
 const ssh=spawnSync('bash',[path.join(root,'scripts/deploy-over-ssh.sh')],{cwd:dir,env:{...process.env,VPS_HOST:'bad;touch DO_NOT_EXECUTE',VPS_USER:'deploy',VPS_SSH_KEY:'test',VPS_KNOWN_HOSTS:'test',GITHUB_SHA:'a'.repeat(40),IMAGE_ARCHIVE:'test'},encoding:'utf8'});
 assert.equal(ssh.status,2);await assert.rejects(access(path.join(dir,'DO_NOT_EXECUTE')));
 pass('Deployment rejects injected hosts and mutable or malformed image references before external commands');
 console.log(`${count} deployment safety checks passed (Docker/SSH simulated).`);
} finally {await rm(dir,{recursive:true,force:true});}
