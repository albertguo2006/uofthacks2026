#!/bin/bash

# Proof of Skill - Test Script
# Runs comprehensive tests against running services

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_URL="http://localhost:8000"
SANDBOX_URL="http://localhost:8080"
WEB_URL="http://localhost:3000"

PASSED=0
FAILED=0

# Test function
test_endpoint() {
    local name="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    local expected="$5"
    local auth="$6"

    echo -n "  $name: "

    local curl_args=(-s -X "$method" "$url" -H "Content-Type: application/json")

    if [ -n "$auth" ]; then
        curl_args+=(-H "Authorization: Bearer $auth")
    fi

    if [ -n "$data" ]; then
        curl_args+=(-d "$data")
    fi

    local response
    response=$(curl "${curl_args[@]}" 2>/dev/null)

    if echo "$response" | grep -q "$expected"; then
        echo -e "${GREEN}PASS${NC}"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        echo "    Expected: $expected"
        echo "    Got: $response"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              Proof of Skill - Test Suite                  ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if services are running
echo -e "${YELLOW}Checking service availability...${NC}"

if ! curl -s "$API_URL/health" >/dev/null 2>&1; then
    echo -e "${RED}API is not running at $API_URL${NC}"
    echo "Run ./start.sh first"
    exit 1
fi

if ! curl -s "$SANDBOX_URL/health" >/dev/null 2>&1; then
    echo -e "${RED}Sandbox is not running at $SANDBOX_URL${NC}"
    exit 1
fi

echo -e "  Services available: ${GREEN}✓${NC}"

# ====================
# Health Checks
# ====================
echo -e "\n${YELLOW}Health Checks${NC}"

test_endpoint "API health" "GET" "$API_URL/health" "" "healthy"
test_endpoint "Sandbox health" "GET" "$SANDBOX_URL/health" "" "healthy"

# ====================
# Authentication Tests
# ====================
echo -e "\n${YELLOW}Authentication Tests${NC}"

# Generate unique email
TEST_EMAIL="testuser$(date +%s)@example.com"

# Register
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"password123\",\"display_name\":\"Test User\",\"role\":\"candidate\"}")

if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    echo -e "  User registration: ${GREEN}PASS${NC}"
    PASSED=$((PASSED + 1))
    TOKEN=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")
else
    echo -e "  User registration: ${RED}FAIL${NC}"
    FAILED=$((FAILED + 1))
    TOKEN=""
fi

# Login
test_endpoint "User login" "POST" "$API_URL/auth/login" \
    "{\"email\":\"$TEST_EMAIL\",\"password\":\"password123\"}" \
    "access_token"

# Login with demo user
DEMO_LOGIN=$(curl -s -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"alice@example.com","password":"password123"}')

DEMO_TOKEN=$(echo "$DEMO_LOGIN" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")

if [ -n "$DEMO_TOKEN" ]; then
    echo -e "  Demo user login: ${GREEN}PASS${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "  Demo user login: ${RED}FAIL${NC} (run seed_demo_data.py first)"
    FAILED=$((FAILED + 1))
fi

# ====================
# Tasks Tests
# ====================
echo -e "\n${YELLOW}Tasks Tests${NC}"

if [ -n "$TOKEN" ]; then
    test_endpoint "List tasks" "GET" "$API_URL/tasks" "" "tasks" "$TOKEN"
    test_endpoint "Get task detail" "GET" "$API_URL/tasks/bugfix-null-check" "" "starter_code" "$TOKEN"
else
    echo -e "  ${YELLOW}Skipping (no auth token)${NC}"
fi

# ====================
# Jobs Tests
# ====================
echo -e "\n${YELLOW}Jobs Tests${NC}"

if [ -n "$TOKEN" ]; then
    test_endpoint "List jobs" "GET" "$API_URL/jobs" "" "jobs" "$TOKEN"
    test_endpoint "List jobs with locked" "GET" "$API_URL/jobs?include_locked=true" "" "jobs" "$TOKEN"
else
    echo -e "  ${YELLOW}Skipping (no auth token)${NC}"
fi

# ====================
# Passport Tests
# ====================
echo -e "\n${YELLOW}Passport Tests${NC}"

if [ -n "$DEMO_TOKEN" ]; then
    test_endpoint "Get passport" "GET" "$API_URL/passport/demo-candidate-1" "" "user_id" "$DEMO_TOKEN"
else
    echo -e "  ${YELLOW}Skipping (no demo token)${NC}"
fi

# ====================
# Sandbox Tests
# ====================
echo -e "\n${YELLOW}Sandbox Execution Tests${NC}"

# Python execution
echo -n "  Python execution: "
PYTHON_RESULT=$(curl -s -X POST "$SANDBOX_URL/run" \
    -H "Content-Type: application/json" \
    -d '{"code":"def solution(x): return x * 2","language":"python","input":{"x": 21},"timeout":5}')

if echo "$PYTHON_RESULT" | grep -q "42"; then
    echo -e "${GREEN}PASS${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}FAIL${NC}"
    echo "    Response: $PYTHON_RESULT"
    FAILED=$((FAILED + 1))
fi

# JavaScript execution
echo -n "  JavaScript execution: "
JS_RESULT=$(curl -s -X POST "$SANDBOX_URL/run" \
    -H "Content-Type: application/json" \
    -d '{"code":"function processUser(user) { return user ? user.name.toUpperCase() : null; }","language":"javascript","input":{"user":{"name":"alice"}},"timeout":5}')

if echo "$JS_RESULT" | grep -qi "alice"; then
    echo -e "${GREEN}PASS${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}FAIL${NC}"
    echo "    Response: $JS_RESULT"
    FAILED=$((FAILED + 1))
fi

# Timeout handling
echo -n "  Timeout handling: "
TIMEOUT_RESULT=$(curl -s -X POST "$SANDBOX_URL/run" \
    -H "Content-Type: application/json" \
    -d '{"code":"import time; time.sleep(10)","language":"python","input":{},"timeout":2}')

if echo "$TIMEOUT_RESULT" | grep -qi "timeout\|error"; then
    echo -e "${GREEN}PASS${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}FAIL${NC}"
    FAILED=$((FAILED + 1))
fi

# ====================
# Event Tracking Tests
# ====================
echo -e "\n${YELLOW}Event Tracking Tests${NC}"

if [ -n "$TOKEN" ]; then
    TRACK_RESULT=$(curl -s -X POST "$API_URL/track" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{"event_type":"test_event","session_id":"test-session","task_id":"test-task","timestamp":'$(date +%s000)',"properties":{"test":true}}')

    if echo "$TRACK_RESULT" | grep -q "event_id"; then
        echo -e "  Track event: ${GREEN}PASS${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "  Track event: ${RED}FAIL${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "  ${YELLOW}Skipping (no auth token)${NC}"
fi

# ====================
# Summary
# ====================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
TOTAL=$((PASSED + FAILED))
echo -e "Tests: $TOTAL | ${GREEN}Passed: $PASSED${NC} | ${RED}Failed: $FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${YELLOW}Some tests failed. Check the output above.${NC}"
    exit 1
fi
