#!/usr/bin/env sh
set -eu

api_base_url="${1:-http://127.0.0.1:8080}"
web_base_url="${2:-$api_base_url}"

curl --fail --silent "$api_base_url/api/health" >/dev/null
curl --fail --silent "$api_base_url/api/health/live" >/dev/null
curl --fail --silent "$api_base_url/api/health/ready" >/dev/null
curl --fail --silent "$api_base_url/api/openapi.json" >/dev/null
curl --fail --silent "$api_base_url/api/factors/top30?limit=2" >/dev/null
curl --fail --silent "$api_base_url/api/research/reports/002558" >/dev/null
curl --fail --silent "$api_base_url/api/industry/rotation" >/dev/null
curl --fail --silent "$api_base_url/api/market/dashboard" >/dev/null
curl --fail --silent "$api_base_url/api/market/funds" >/dev/null
curl --fail --silent "$api_base_url/api/system/status" >/dev/null

for route in dashboard market factors research funds compare review industry settings; do
  curl --fail --silent "$web_base_url/$route" >/dev/null
done

echo "API and nine-page smoke checks passed."
