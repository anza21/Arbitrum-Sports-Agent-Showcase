#!/bin/bash
echo "=== Dashboard API Curl Tests ==="
echo "Testing all endpoints with curl..."

echo ""
echo "=== Testing /api/health ==="
curl -s "http://localhost:5000/api/health" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(json.dumps(data, indent=2))
except:
    print('Failed to parse JSON or server not responding')
"

echo ""
echo "=== Testing /api/status ==="
curl -s "http://localhost:5000/api/status" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(json.dumps(data, indent=2))
except:
    print('Failed to parse JSON or server not responding')
"

echo ""
echo "=== Testing /api/bets ==="
curl -s "http://localhost:5000/api/bets" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(json.dumps(data, indent=2))
except:
    print('Failed to parse JSON or server not responding')
"

echo ""
echo "=== Testing /api/summary ==="
curl -s "http://localhost:5000/api/summary" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(json.dumps(data, indent=2))
except:
    print('Failed to parse JSON or server not responding')
"

echo ""
echo "=== Testing / (API documentation) ==="
curl -s "http://localhost:5000/" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(json.dumps(data, indent=2))
except:
    print('Failed to parse JSON or server not responding')
"

echo ""
echo "=== Curl tests completed! ==="
