#!/usr/bin/env sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if [ ! -f .env ]; then cp .env.example .env; fi
if ! command -v docker >/dev/null 2>&1; then
  printf '%s\n' 'Docker is required for this launcher. Install Docker Engine with the Compose plugin, or use Node.js 24 and run npm start.'
  exit 1
fi
docker compose version >/dev/null
exec docker compose up -d --build
