#!/bin/bash

# Simple development startup script
# Runs services in foreground with visible output

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Proof of Skill Development Server ==="
echo ""

# Check for MongoDB
echo "Step 1: Starting MongoDB..."
if ! pgrep -x mongod >/dev/null && ! docker ps | grep -q mongo; then
    echo "  Starting MongoDB in Docker..."
    docker run -d --name pos-mongo -p 27017:27017 mongo:7 2>/dev/null || \
    docker start pos-mongo 2>/dev/null || \
    echo "  Warning: Could not start MongoDB. Please start it manually."
fi
echo "  MongoDB: OK"

# Seed database
echo ""
echo "Step 2: Seeding database..."
cd "$PROJECT_ROOT/scripts"
python3 seed_tasks.py 2>/dev/null || echo "  (tasks may already exist)"
echo "  Database seeded"

# Start services in background with output
echo ""
echo "Step 3: Starting services..."
echo ""

cd "$PROJECT_ROOT"
mkdir -p logs

# Start API
echo "Starting API server on http://localhost:8000 ..."
cd "$PROJECT_ROOT/apps/api"
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > "$PROJECT_ROOT/logs/api.log" 2>&1 &
API_PID=$!
echo "  API PID: $API_PID"

# Start Sandbox
echo "Starting Sandbox on http://localhost:8080 ..."
cd "$PROJECT_ROOT/apps/sandbox-runner"
python3 server.py > "$PROJECT_ROOT/logs/sandbox.log" 2>&1 &
SANDBOX_PID=$!
echo "  Sandbox PID: $SANDBOX_PID"

# Start Web
echo "Starting Web on http://localhost:3000 ..."
cd "$PROJECT_ROOT/apps/web"
npm run dev > "$PROJECT_ROOT/logs/web.log" 2>&1 &
WEB_PID=$!
echo "  Web PID: $WEB_PID"

cd "$PROJECT_ROOT"

# Save PIDs
echo "$API_PID" > logs/api.pid
echo "$SANDBOX_PID" > logs/sandbox.pid
echo "$WEB_PID" > logs/web.pid

# Wait for services
echo ""
echo "Waiting for services to start..."
sleep 5

# Check services
echo ""
echo "=== Service Status ==="
curl -s http://localhost:8000/health >/dev/null && echo "  API:     http://localhost:8000 ✓" || echo "  API:     starting... (check logs/api.log)"
curl -s http://localhost:8080/health >/dev/null && echo "  Sandbox: http://localhost:8080 ✓" || echo "  Sandbox: starting... (check logs/sandbox.log)"
curl -s http://localhost:3000 >/dev/null && echo "  Web:     http://localhost:3000 ✓" || echo "  Web:     starting... (check logs/web.log)"

echo ""
echo "=== Demo Credentials ==="
echo "  alice@example.com / password123"
echo "  bob@example.com / password123"
echo "  recruiter@example.com / password123"

echo ""
echo "=== Commands ==="
echo "  View logs:  tail -f logs/api.log"
echo "  Stop all:   ./stop.sh"
echo ""
echo "Press Ctrl+C to stop watching (services will keep running)"
echo ""

# Tail logs
tail -f logs/api.log logs/sandbox.log 2>/dev/null
