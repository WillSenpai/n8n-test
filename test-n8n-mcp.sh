#!/bin/bash
# Test script for n8n MCP Server
# Usage: ./test-n8n-mcp.sh

set -e

source_config() {
  N8N_API_URL=$(python3 -c "import json; print(json.load(open('.mcp.json'))['mcpServers']['n8n']['env']['N8N_API_URL'])")
  N8N_API_KEY=$(python3 -c "import json; print(json.load(open('.mcp.json'))['mcpServers']['n8n']['env']['N8N_API_KEY'])")
}

echo "=== n8n MCP Server Test ==="
echo ""

# 1. Check .mcp.json exists
if [ ! -f .mcp.json ]; then
  echo "FAIL: .mcp.json not found"
  exit 1
fi
echo "PASS: .mcp.json exists"

# 2. Parse config
source_config
echo "PASS: Config parsed - API URL: $N8N_API_URL"

# 3. Test API connectivity
echo ""
echo "--- Testing n8n API connectivity ---"
HTTP_CODE=$(curl -s -o /tmp/n8n-test-response.json -w "%{http_code}" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "$N8N_API_URL/api/v1/workflows?limit=1" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
  echo "PASS: API reachable (HTTP $HTTP_CODE)"
  echo "Response: $(cat /tmp/n8n-test-response.json | head -c 500)"
elif [ "$HTTP_CODE" = "000" ]; then
  echo "FAIL: Cannot reach n8n API (network error)"
else
  echo "FAIL: API returned HTTP $HTTP_CODE"
  cat /tmp/n8n-test-response.json 2>/dev/null
fi

# 4. Test MCP server startup
echo ""
echo "--- Testing MCP server startup ---"
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}' | \
  timeout 30 npx -y @leonardsellem/n8n-mcp-server 2>/tmp/n8n-mcp-stderr.log | head -c 2000 > /tmp/n8n-mcp-stdout.log

if [ -s /tmp/n8n-mcp-stdout.log ]; then
  echo "PASS: MCP server responded"
  echo "Response: $(cat /tmp/n8n-mcp-stdout.log)"
else
  echo "WARN: No stdout from MCP server"
  echo "Stderr: $(cat /tmp/n8n-mcp-stderr.log | tail -5)"
fi

echo ""
echo "=== Test complete ==="
