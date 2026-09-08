#!/usr/bin/env bash
set -euo pipefail
: "${VPS_HOST:?Set VPS_HOST in the production environment}"
: "${VPS_USER:?Set VPS_USER in the production environment}"
: "${VPS_SSH_KEY:?Set VPS_SSH_KEY in the production environment}"
: "${VPS_KNOWN_HOSTS:?Set verified VPS_KNOWN_HOSTS in the production environment}"
: "${GITHUB_SHA:?Missing commit SHA}"
: "${IMAGE_ARCHIVE:?Missing image archive}"
VPS_PORT=${VPS_PORT:-22}
[[ "$VPS_HOST" =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]*$ && "$VPS_USER" =~ ^[a-z_][a-z0-9_-]*$ && "$VPS_PORT" =~ ^[0-9]{1,5}$ && "$GITHUB_SHA" =~ ^[a-f0-9]{40}$ ]] || { printf 'Invalid deployment destination or commit.\n' >&2; exit 2; }
(( 10#$VPS_PORT >= 1 && 10#$VPS_PORT <= 65535 )) || exit 2
umask 077
keys=$(mktemp -d)
trap 'rm -rf "$keys"' EXIT
printf '%s\n' "$VPS_SSH_KEY" > "$keys/key"
printf '%s\n' "$VPS_KNOWN_HOSTS" > "$keys/known_hosts"
ssh_opts=(-i "$keys/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$keys/known_hosts" -o ConnectTimeout=15)
remote="$VPS_USER@$VPS_HOST"
release="/opt/emberfall/releases/$GITHUB_SHA"
# Only validated hexadecimal IDs are interpolated into remote shell commands.
ssh "${ssh_opts[@]}" -p "$VPS_PORT" "$remote" "test -f /opt/emberfall/.env && mkdir -p '$release/deploy' '$release/scripts'"
scp "${ssh_opts[@]}" -P "$VPS_PORT" "$IMAGE_ARCHIVE" "$remote:$release/image.tar.gz"
scp "${ssh_opts[@]}" -P "$VPS_PORT" deploy/runtime.compose.yml deploy/Caddyfile "$remote:$release/deploy/"
scp "${ssh_opts[@]}" -P "$VPS_PORT" scripts/deploy.sh "$remote:$release/scripts/"
ssh "${ssh_opts[@]}" -p "$VPS_PORT" "$remote" "bash -s -- '$GITHUB_SHA'" <<'REMOTE'
set -euo pipefail
commit=$1
cd /opt/emberfall
release="releases/$commit"
docker load -i "$release/image.tar.gz"
mkdir -p deploy scripts
cp "$release/deploy/runtime.compose.yml" deploy/runtime.compose.yml
cp "$release/deploy/Caddyfile" deploy/Caddyfile
cp "$release/scripts/deploy.sh" scripts/deploy.sh
bash scripts/deploy.sh "emberfall:$commit"
# Remove only the transferred copy after a healthy deployment, never player data.
rm "$release/image.tar.gz"
REMOTE
