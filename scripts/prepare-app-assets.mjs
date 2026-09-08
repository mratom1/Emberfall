import {cp,mkdir,rm,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const destinations={android:'apps/android/app/src/main/assets/game',ios:'apps/ios/Emberfall/Game',windows:'apps/windows/Game'};
const platforms=process.argv.slice(2); for(const p of platforms.length?platforms:Object.keys(destinations)) {
 if(!Object.hasOwn(destinations,p))throw new Error('Choose android, ios or windows.');
 const dest=path.join(root,destinations[p]); await rm(dest,{recursive:true,force:true});await mkdir(dest,{recursive:true});await cp(path.join(root,'dist'),dest,{recursive:true});
 const index=path.join(dest,'index.html');await writeFile(index,(await readFile(index,'utf8')).replace('content="server"','content="auto"'));
 console.log('Bundled game assets: '+p);
}
