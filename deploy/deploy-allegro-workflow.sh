#!/usr/bin/env bash
set -euo pipefail

# Deploy Allegro -> WMS + AI Email Workflow to VPS
# Prerequisites:
#   - SSH access to VPS
#   - Docker images rebuilt and pushed to GHCR
#   - API_KEY set as environment variable

API_URL="${API_URL:-http://localhost:80/api/v1}"
API_KEY="${API_KEY:?ERROR: API_KEY environment variable is required}"

echo "=== Step 1: Pull latest images ==="
docker compose -f docker-compose.vps.yml pull

echo "=== Step 2: Restart services (Kafka first, then platform, then connectors) ==="
docker compose -f docker-compose.vps.yml up -d kafka
sleep 15
docker compose -f docker-compose.vps.yml up -d

echo "=== Step 3: Wait for platform health ==="
for i in $(seq 1 30); do
  if curl -sf http://localhost:80/api/health > /dev/null 2>&1; then
    echo "Platform is healthy"
    break
  fi
  echo "Waiting for platform... ($i/30)"
  sleep 5
done

echo "=== Step 4: Create workflow ==="
curl -s -X POST "${API_URL}/workflows" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d @docs/workflows/allegro_wms_ai_email.json | python3 -m json.tool

echo ""
echo "=== Done ==="
echo ""
echo "Next steps:"
echo "  1. Configure Allegro credentials:  POST ${API_URL}/credentials (connector: allegro, fields: client_id, client_secret)"
echo "  2. Configure WMS credentials:      POST ${API_URL}/credentials (connector: pinquark-wms, fields: api_url, username, password)"
echo "  3. Configure Email credentials:    POST ${API_URL}/credentials (connector: email-client, fields: email_address, username, password, imap_host, smtp_host, smtp_port)"
echo "  4. Configure AI Agent credentials: POST ${API_URL}/credentials (connector: ai-agent, fields: gemini_api_key)"
echo "  5. Enable the workflow in the dashboard"
