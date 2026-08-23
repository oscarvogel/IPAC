#!/usr/bin/env bash
set -Eeuo pipefail

TARGET_REF="${1:-main}"
BACKUP_DIR="${IPAC_BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"

previous_commit="$(git rev-parse HEAD)"
timestamp="$(date +%Y%m%d-%H%M%S)"
backup_file="$BACKUP_DIR/ipac-predeploy-$timestamp.dump"

rollback() {
  echo "El deploy falló. Restaurando código $previous_commit..."
  git checkout --detach "$previous_commit"
  docker compose build
  docker compose up -d
}
trap rollback ERR

echo "Creando backup previo en $backup_file..."
docker compose exec -T db sh -c 'pg_dump -Fc -U "$POSTGRES_USER" "$POSTGRES_DB"' > "$backup_file"

git fetch --prune origin
git checkout "$TARGET_REF"
git pull --ff-only origin "$TARGET_REF"

docker compose build --pull
docker compose up -d --remove-orphans
docker compose ps

curl --fail --retry 12 --retry-delay 5 http://127.0.0.1:8005/api/health/
curl --fail --retry 12 --retry-delay 5 http://127.0.0.1:8084/healthz

trap - ERR
echo "Deploy finalizado. Commit: $(git rev-parse HEAD)"
