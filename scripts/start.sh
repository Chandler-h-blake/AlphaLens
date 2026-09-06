#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
# Direct builds avoid Compose Bake's non-ASCII path session-header bug.
docker build -t alphalens-backend -f infra/backend.Dockerfile .
docker build -t alphalens-frontend -f infra/frontend.Dockerfile .
docker compose up -d --no-build --wait
