#!/bin/bash

# Proof of Skill - Development Startup Script
# Usage: ./start.sh [docker|local]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║           Proof of Skill - Development Setup              ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Determine mode
MODE="${1:-docker}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for a service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=${3:-30}
    local attempt=1

    echo -n "  Waiting for $name"
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    echo -e " ${RED}✗${NC}"
    return 1
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"

    local missing=()

    if [ "$MODE" = "docker" ]; then
        if ! command_exists docker; then
            missing+=("docker")
        fi
        # Check for docker-compose (v1) or docker compose (v2)
        if ! command_exists docker-compose; then
            if ! docker compose version >/dev/null 2>&1; then
                echo -e "${RED}Docker Compose not found.${NC}"
                echo ""
                echo "Options:"
                echo "  1. Install Docker Compose: sudo pacman -S docker-compose"
                echo "  2. Run locally instead: ./start.sh local"
                echo ""
                exit 1
            fi
        fi
    else
        if ! command_exists python3; then
            missing+=("python3")
        fi
        if ! command_exists node; then
            missing+=("node")
        fi
        if ! command_exists npm; then
            missing+=("npm")
        fi
    fi

    if [ ${#missing[@]} -ne 0 ]; then
        echo -e "${RED}Missing prerequisites: ${missing[*]}${NC}"
        echo "Please install the missing tools and try again."
        exit 1
    fi

    echo -e "  Prerequisites: ${GREEN}✓${NC}"
}

# Function to start with Docker
start_docker() {
    echo -e "\n${YELLOW}Starting services with Docker...${NC}"

    cd "$PROJECT_ROOT"

    # Check if docker compose (v2) or docker-compose (v1)
    if docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker compose"
    else
        DOCKER_COMPOSE="docker-compose"
    fi

    # Stop any existing containers
    echo "  Stopping existing containers..."
    $DOCKER_COMPOSE down >/dev/null 2>&1 || true

    # Build and start
    echo "  Building and starting containers..."
    $DOCKER_COMPOSE up --build -d

    echo -e "  Containers started: ${GREEN}✓${NC}"
}

# Function to start locally
start_local() {
    echo -e "\n${YELLOW}Starting services locally...${NC}"

    # Create logs directory
    mkdir -p "$PROJECT_ROOT/logs"

    # Start MongoDB (check if already running)
    if ! pgrep -x mongod >/dev/null; then
        echo "  ${YELLOW}Note: MongoDB not detected. Please start MongoDB manually or use Docker mode.${NC}"
        echo "  You can install MongoDB or run: docker run -d -p 27017:27017 mongo:7"
    fi

    # Setup and start API
    echo "  Setting up API..."
    cd "$PROJECT_ROOT/apps/api"
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -q -r requirements.txt

    echo "  Starting API server..."
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload > "$PROJECT_ROOT/logs/api.log" 2>&1 &
    echo $! > "$PROJECT_ROOT/logs/api.pid"

    # Setup and start Sandbox Runner
    echo "  Setting up Sandbox Runner..."
    cd "$PROJECT_ROOT/apps/sandbox-runner"
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -q -r requirements.txt

    echo "  Starting Sandbox Runner..."
    python server.py > "$PROJECT_ROOT/logs/sandbox.log" 2>&1 &
    echo $! > "$PROJECT_ROOT/logs/sandbox.pid"

    # Setup and start Web
    echo "  Setting up Web frontend..."
    cd "$PROJECT_ROOT/apps/web"
    if [ ! -d "node_modules" ]; then
        npm install --silent
    fi

    echo "  Starting Web server..."
    npm run dev > "$PROJECT_ROOT/logs/web.log" 2>&1 &
    echo $! > "$PROJECT_ROOT/logs/web.pid"

    cd "$PROJECT_ROOT"
    echo -e "  Local services started: ${GREEN}✓${NC}"
}

# Function to seed database
seed_database() {
    echo -e "\n${YELLOW}Seeding database...${NC}"

    cd "$PROJECT_ROOT/scripts"

    # Create virtual environment if needed
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -q motor passlib pymongo

    # Wait a moment for MongoDB to be ready
    sleep 2

    # Run seed scripts
    echo "  Seeding tasks and jobs..."
    python seed_tasks.py 2>/dev/null || echo "    (some warnings are normal)"

    echo "  Seeding demo users..."
    python seed_demo_data.py 2>/dev/null || echo "    (some warnings are normal)"

    cd "$PROJECT_ROOT"
    echo -e "  Database seeded: ${GREEN}✓${NC}"
}

# Function to validate services
validate_services() {
    echo -e "\n${YELLOW}Validating services...${NC}"

    local all_ok=true

    # Check API
    if ! wait_for_service "http://localhost:8000/health" "API" 30; then
        all_ok=false
    fi

    # Check Sandbox
    if ! wait_for_service "http://localhost:8080/health" "Sandbox" 30; then
        all_ok=false
    fi

    # Check Web
    if ! wait_for_service "http://localhost:3000" "Web" 60; then
        all_ok=false
    fi

    if [ "$all_ok" = true ]; then
        echo -e "\n${GREEN}All services are running!${NC}"
        return 0
    else
        echo -e "\n${RED}Some services failed to start.${NC}"
        return 1
    fi
}

# Function to run quick tests
run_tests() {
    echo -e "\n${YELLOW}Running quick validation tests...${NC}"

    # Test API health
    echo -n "  API health check: "
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
    fi

    # Test user registration
    echo -n "  User registration: "
    REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8000/auth/register \
        -H "Content-Type: application/json" \
        -d '{"email":"test'$(date +%s)'@example.com","password":"password123","display_name":"Test User","role":"candidate"}')

    if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
        echo -e "${GREEN}✓${NC}"
        TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    else
        echo -e "${RED}✗${NC}"
        TOKEN=""
    fi

    # Test tasks endpoint
    if [ -n "$TOKEN" ]; then
        echo -n "  Tasks endpoint: "
        if curl -s http://localhost:8000/tasks \
            -H "Authorization: Bearer $TOKEN" | grep -q "tasks"; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
        fi
    fi

    # Test sandbox execution
    echo -n "  Sandbox execution: "
    SANDBOX_RESPONSE=$(curl -s -X POST http://localhost:8080/run \
        -H "Content-Type: application/json" \
        -d '{"code":"print(1+1)","language":"python","input":{},"timeout":5}')

    if echo "$SANDBOX_RESPONSE" | grep -q '"output"'; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
    fi
}

# Function to print access info
print_access_info() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Proof of Skill is running!${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${YELLOW}Web App:${NC}      http://localhost:3000"
    echo -e "  ${YELLOW}API:${NC}          http://localhost:8000"
    echo -e "  ${YELLOW}API Docs:${NC}     http://localhost:8000/docs"
    echo -e "  ${YELLOW}Sandbox:${NC}      http://localhost:8080"
    echo ""
    echo -e "${BLUE}Demo Credentials:${NC}"
    echo "  alice@example.com / password123 (candidate - fast iterator)"
    echo "  bob@example.com / password123 (candidate - careful tester)"
    echo "  carol@example.com / password123 (candidate - debugger)"
    echo "  recruiter@example.com / password123 (recruiter)"
    echo ""
    if [ "$MODE" = "docker" ]; then
        echo -e "${YELLOW}To stop:${NC} docker compose down"
        echo -e "${YELLOW}To view logs:${NC} docker compose logs -f [service]"
    else
        echo -e "${YELLOW}To stop:${NC} ./stop.sh"
        echo -e "${YELLOW}Logs:${NC} logs/*.log"
    fi
    echo ""
}

# Function to show help
show_help() {
    echo "Usage: ./start.sh [docker|local|help]"
    echo ""
    echo "Commands:"
    echo "  docker  - Start all services using Docker Compose (default)"
    echo "  local   - Start services locally (requires Python, Node, MongoDB)"
    echo "  help    - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./start.sh          # Start with Docker"
    echo "  ./start.sh docker   # Start with Docker"
    echo "  ./start.sh local    # Start locally"
}

# Main execution
main() {
    case "$MODE" in
        help|-h|--help)
            show_help
            exit 0
            ;;
        docker)
            check_prerequisites
            start_docker
            sleep 5  # Give containers time to initialize
            validate_services
            seed_database
            run_tests
            print_access_info
            ;;
        local)
            check_prerequisites
            start_local
            sleep 3
            validate_services
            seed_database
            run_tests
            print_access_info
            ;;
        *)
            echo -e "${RED}Unknown mode: $MODE${NC}"
            show_help
            exit 1
            ;;
    esac
}

main
