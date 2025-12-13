#!/usr/bin/env bash
# Vérifie /health et envoie une alerte Discord si KO.

API_URL="${API_URL:-http://127.0.0.1:8500/health}"
WEBHOOK="${FRE_DISCORD_WEBHOOK:-}"

fail() {
  echo "[WATCHDOG] API KO : $1"
  if [ -n "$WEBHOOK" ]; then
    curl -s -X POST -H "Content-Type: application/json" \
      -d "{\"content\":\"[FRE_NODE] Watchdog: échec health (${API_URL}) : $1\"}" \
      "$WEBHOOK" >/dev/null 2>&1
  fi
}

resp=$(curl -s -m 5 -w "%{http_code}" "$API_URL")
code=${resp: -3}
body=${resp:0:${#resp}-3}

if [ "$code" != "200" ]; then
  fail "HTTP $code"
  exit 1
fi

status=$(echo "$body" | grep -o '"status":"[^"]*"' | cut -d':' -f2 | tr -d '"')
if [ "$status" != "ok" ]; then
  fail "status=$status"
  exit 1
fi

echo "[WATCHDOG] OK"
exit 0
