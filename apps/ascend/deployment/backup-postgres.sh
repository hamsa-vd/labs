#!/bin/bash
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${ASCEND_BACKUP_DIR:?ASCEND_BACKUP_DIR is required}"
: "${ASCEND_BACKUP_KEY_FILE:?ASCEND_BACKUP_KEY_FILE is required}"

case "$ASCEND_BACKUP_DIR" in
  /*) ;;
  *) echo "ASCEND_BACKUP_DIR must be an absolute path" >&2; exit 1 ;;
esac

mkdir -p "$ASCEND_BACKUP_DIR"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
temporary="$ASCEND_BACKUP_DIR/.ascend-$timestamp.dump.enc.tmp"
destination="$ASCEND_BACKUP_DIR/ascend-$timestamp.dump.enc"

cleanup() { rm -f "$temporary"; }
trap cleanup EXIT

pg_dump "$DATABASE_URL" --format=custom \
  | openssl enc -aes-256-cbc -salt -pbkdf2 -iter 200000 -pass "file:$ASCEND_BACKUP_KEY_FILE" -out "$temporary"
chmod 600 "$temporary"
mv "$temporary" "$destination"
trap - EXIT

echo "$destination"
