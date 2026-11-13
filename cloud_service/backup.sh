#!/usr/bin/env sh
# Usage: sh cloud_service/backup.sh /absolute/private/backup-directory
set -eu
umask 077
out=${1:?Provide an existing private backup directory}
[ -d "$out" ] || { echo 'Backup directory does not exist.' >&2; exit 1; }
repo=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
file="$out/beesky-$(date -u +%Y%m%dT%H%M%SZ).dump"
[ ! -e "$file" ] || { echo 'Backup file already exists.' >&2; exit 1; }
docker compose --env-file "$repo/cloud_service/.env.production" -f "$repo/cloud_service/compose.production.yaml" exec -T db pg_dump -U beesky -d beesky -Fc > "$file.partial"
# Verify archive readability before publishing its final name.
docker compose --env-file "$repo/cloud_service/.env.production" -f "$repo/cloud_service/compose.production.yaml" exec -T db pg_restore --list < "$file.partial" > /dev/null
mv "$file.partial" "$file"
printf 'Created backup: %s\n' "$file"
