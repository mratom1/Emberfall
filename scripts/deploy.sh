#!/usr/bin/env bash
# Run from /opt/emberfall. Never sources .env as shell code or deletes data volumes.
set -euo pipefail
image=${1:?Usage: deploy.sh emberfall:COMMIT_SHA}
[[ "$image" =~ ^emberfall:[a-f0-9]{40}$ ]] || { printf 'Expected an immutable Emberfall commit image.\n' >&2; exit 2; }
[[ -f .env && -f deploy/runtime.compose.yml ]] || { printf 'Create /opt/emberfall/.env and install the deployment files first.\n' >&2; exit 2; }
mkdir -p .deploy
chmod 700 .deploy
exec 9>.deploy/lock
flock -n 9 || { printf 'Another deployment is already running.\n' >&2; exit 2; }
export GAME_IMAGE="$image"
compose=(docker compose --project-directory "$PWD" --env-file .env -f deploy/runtime.compose.yml)
# Parse configuration without printing environment secrets.
project=$("${compose[@]}" config --format json | python3 -c 'import json,sys; print(json.load(sys.stdin)["name"])')
if ! docker volume inspect "${project}_emberfall_data" >/dev/null 2>&1; then
  legacy=$(docker volume ls --format '{{.Name}}' | awk '/_emberfall_data$/ {print}')
  if [[ -n "$legacy" ]]; then
    printf 'Existing village volumes found. Set COMPOSE_PROJECT_NAME in .env to the existing project before migration.\n' >&2
    exit 2
  fi
fi
previous=$("${compose[@]}" ps -a -q game | head -n 1)
old_image=''
if [[ -n "$previous" ]]; then
  old_image=$(docker inspect --format '{{.Config.Image}}' "$previous")
  if [[ $(docker inspect --format '{{.State.Running}}' "$previous") == true ]]; then
    "${compose[@]}" exec -T game node scripts/backup.mjs
  else
    # Back up a stopped deployment without publishing ports or starting a server.
    GAME_IMAGE="$old_image" "${compose[@]}" run --rm --no-deps game node scripts/backup.mjs
  fi
fi
if "${compose[@]}" up -d --wait --wait-timeout 120; then
  printf '%s\n' "$old_image" > .deploy/previous-image
  printf '%s\n' "$image" > .deploy/current-image
  printf 'Deployment healthy: %s\n' "$image"
else
  printf 'New release failed its health check.\n' >&2
  if [[ -n "$old_image" ]]; then
    export GAME_IMAGE="$old_image"
    "${compose[@]}" up -d --wait --wait-timeout 120
    printf 'Previous image restored; village data retained.\n' >&2
  fi
  exit 1
fi
