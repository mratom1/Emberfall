import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

// VACUUM and integrity checks run in a child so gameplay stays responsive.
export function startBackups(dataDir, {intervalMs = Number(process.env.BACKUP_INTERVAL_HOURS || 6) * 3600000, keep = Number(process.env.BACKUP_KEEP || 28), report = message => console.error(message)} = {}) {
  if (!Number.isFinite(intervalMs) || intervalMs < 60000 || intervalMs > 7 * 86400000) throw new Error('Backup interval must be 1 minute–7 days.');
  if (!Number.isInteger(keep) || keep < 1 || keep > 1000) throw new Error('Backup retention must be 1–1000 files.');
  const script = fileURLToPath(new URL('../scripts/backup.mjs', import.meta.url));
  let active = null, stopped = false;
  const run = () => {
    if (stopped) return Promise.resolve(null);
    if (active) return active;
    active = new Promise((resolve, reject) => {
      const child = spawn(process.execPath, [script, path.join(dataDir, 'backups'), '--automatic'], {env: {...process.env, DATA_DIR: dataDir, BACKUP_KEEP: String(keep)}, stdio: ['ignore', 'pipe', 'pipe'], timeout: 60000});
      let result = '', error = '';
      child.stdout.on('data', data => { result = (result + data).slice(-4096); });
      child.stderr.on('data', data => { error = (error + data).slice(-4096); });
      child.once('error', reject);
      child.once('close', code => code === 0 ? resolve(result.trim()) : reject(new Error(error.trim() || 'Backup process failed.')));
    }).finally(() => { active = null; });
    return active;
  };
  const scheduled = () => run().catch(error => report('Automatic backup failed: ' + error.message));
  const timer = setInterval(scheduled, intervalMs);
  timer.unref();
  scheduled();
  return {run, close: async () => { stopped = true; clearInterval(timer); if (active) await active.catch(() => {}); }};
}
