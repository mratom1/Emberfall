#!/usr/bin/env bash
set -euo pipefail
image=${1:?Supply a local Docker image}
name="emberfall-smoke-$$"
cleanup() { docker rm -f "$name" >/dev/null 2>&1 || true; }
trap cleanup EXIT
# Run as the image's non-root user; only a temporary data volume is writable.
docker run -d --name "$name" --read-only --cap-drop ALL --security-opt no-new-privileges:true --tmpfs /tmp --tmpfs /app/data:uid=1000,gid=1000,mode=0700 -e BACKUP_ENABLED=false "$image" >/dev/null
for attempt in $(seq 1 30); do
  if docker exec "$name" node -e "fetch('http://127.0.0.1:8080/api/health').then(async r=>{const d=await r.json();if(!r.ok||!d.ok)process.exit(1)}).catch(()=>process.exit(1))" >/dev/null 2>&1; then
    docker exec "$name" node -e "if(process.getuid()===0)process.exit(1);fetch('http://127.0.0.1:8080/').then(async r=>{if(!r.ok||!(await r.text()).includes('content=\"server\"'))process.exit(1)})"
    printf 'Container starts, serves the game, and runs without root.\n'
    exit 0
  fi
  sleep 1
done
docker logs --tail 30 "$name"
exit 1
