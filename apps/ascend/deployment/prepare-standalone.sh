#!/bin/bash
set -euo pipefail

project_root="$(cd "$(dirname "$0")/.." && pwd)"
standalone_app="$project_root/.next/standalone/apps/ascend"

test -f "$standalone_app/server.js"
mkdir -p "$standalone_app/.next"
cp -R "$project_root/public" "$standalone_app/public"
cp -R "$project_root/.next/static" "$standalone_app/.next/static"
