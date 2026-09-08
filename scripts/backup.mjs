import {DatabaseSync} from 'node:sqlite';
import {mkdirSync, readdirSync, renameSync, rmSync, chmodSync, existsSync} from 'node:fs';
import {randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

export function backupDatabase({dataDir, outputDir, automatic = false, keep = 28, now = new Date()} = {}) {
  const data = path.resolve(dataDir || process.env.DATA_DIR || 'data');
  const out = path.resolve(outputDir || path.join(data, 'backups'));
  const source = path.join(data, 'emberfall.sqlite');
  if (!existsSync(source)) throw new Error('No existing database found. Start the game server before backing it up.');
  if (!Number.isInteger(keep) || keep < 1 || keep > 1000) throw new Error('Backup retention must be 1–1000 files.');
  mkdirSync(out, {recursive: true, mode: 0o700});
  chmodSync(out, 0o700);
  const file = path.join(out, `emberfall-${automatic ? 'auto' : 'manual'}-${now.toISOString().replace(/[:.]/g, '-')}-${randomUUID()}.sqlite`);
  const temporary = file + '.partial';
  const db = new DatabaseSync(source, {readOnly: true});
  try {
    db.exec('PRAGMA busy_timeout=10000;');
    db.prepare('VACUUM INTO ?').run(temporary);
    chmodSync(temporary, 0o600);
    const check = new DatabaseSync(temporary, {readOnly: true});
    try {
      const integrity = check.prepare('PRAGMA integrity_check').get();
      if (Object.values(integrity)[0] !== 'ok') throw new Error('Backup integrity check failed.');
      if (check.prepare('PRAGMA foreign_key_check').all().length) throw new Error('Backup foreign key check failed.');
    } finally { check.close(); }
    renameSync(temporary, file);
    if (automatic) {
      const own = readdirSync(out).filter(name => /^emberfall-auto-\d{4}-\d{2}-\d{2}T[0-9TZ-]+-[a-f0-9-]{36}\.sqlite$/.test(name)).sort().reverse();
      for (const name of own.slice(keep)) rmSync(path.join(out, name));
    }
    return file;
  } catch (error) { rmSync(temporary, {force: true}); throw error; }
  finally { db.close(); }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    console.log(backupDatabase({outputDir: process.argv[2], automatic: process.argv.includes('--automatic'), keep: Number(process.env.BACKUP_KEEP || 28)}));
  } catch (error) { console.error('Backup failed:', error.message); process.exitCode = 1; }
}
