#!/bin/bash

# Proof of Skill - Stop Services Script

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${YELLOW}Stopping Proof of Skill services...${NC}"

# Stop Docker containers if running
if docker compose version >/dev/null 2>&1; then
    docker compose down 2>/dev/null || true
elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose down 2>/dev/null || true
fi

# Stop local processes if PID files exist
if [ -f "$PROJECT_ROOT/logs/api.pid" ]; then
    kill $(cat "$PROJECT_ROOT/logs/api.pid") 2>/dev/null || true
    rm "$PROJECT_ROOT/logs/api.pid"
    echo "  Stopped API server"
fi

if [ -f "$PROJECT_ROOT/logs/sandbox.pid" ]; then
    kill $(cat "$PROJECT_ROOT/logs/sandbox.pid") 2>/dev/null || true
    rm "$PROJECT_ROOT/logs/sandbox.pid"
    echo "  Stopped Sandbox runner"
fi

if [ -f "$PROJECT_ROOT/logs/web.pid" ]; then
    kill $(cat "$PROJECT_ROOT/logs/web.pid") 2>/dev/null || true
    rm "$PROJECT_ROOT/logs/web.pid"
    echo "  Stopped Web server"
fi

# Kill any remaining processes on the ports
for port in 3000 8000 8080; do
    pid=$(lsof -t -i:$port 2>/dev/null || true)
    if [ -n "$pid" ]; then
        kill $pid 2>/dev/null || true
        echo "  Killed process on port $port"
    fi
done

echo -e "${GREEN}All services stopped.${NC}"
