#!/bin/bash
# Synapse Health Check Script
# Verifies all services are running and accessible

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0
PASSED=0

echo "================================"
echo "Synapse Health Check"
echo "================================"
echo ""

# Function to check service
check_service() {
    local name=$1
    local port=$2
    local path=${3:-""}
    
    echo -n "Checking $name... "
    
    if nc -z localhost $port 2>/dev/null; then
        if [ -z "$path" ]; then
            echo -e "${GREEN}✓${NC}"
            ((PASSED++))
        else
            # Try to access the endpoint
            if curl -s http://localhost:$port$path > /dev/null 2>&1; then
                echo -e "${GREEN}✓${NC}"
                ((PASSED++))
            else
                echo -e "${RED}✗${NC} (port open but endpoint failed)"
                ((FAILED++))
            fi
        fi
    else
        echo -e "${RED}✗${NC} (connection refused)"
        ((FAILED++))
    fi
}

# Function to check docker compose services
check_docker_status() {
    local service=$1
    local expected_state=$2
    
    echo -n "Docker service $service... "
    
    local status=$(docker-compose ps | grep $service | awk '{print $NF}')
    
    if [ "$status" = "$expected_state" ]; then
        echo -e "${GREEN}✓${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} (status: $status)"
        ((FAILED++))
    fi
}

# Check Docker Compose services
echo "🐳 Docker Services:"
check_docker_status "postgres" "healthy"
check_docker_status "redis" "healthy"
check_docker_status "qdrant" "Up"
check_docker_status "backend" "healthy"
check_docker_status "frontend" "healthy"
echo ""

# Check Service Connectivity
echo "🌐 Service Connectivity:"
check_service "PostgreSQL" "5432"
check_service "Redis" "6379"
check_service "Qdrant" "6333"
check_service "Backend" "8000" "/health"
check_service "Frontend" "3000"
echo ""

# Check API Endpoints
echo "🔌 API Endpoints:"

echo -n "GET /health... "
if curl -s http://localhost:8000/health | grep -q '"status":"ok"'; then
    echo -e "${GREEN}✓${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} (response check failed)"
    ((FAILED++))
fi

echo -n "GET /docs... "
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} (endpoint not responding)"
    ((FAILED++))
fi

echo -n "Frontend page... "
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} (endpoint not responding)"
    ((FAILED++))
fi

echo ""

# Check Database Connection
echo "💾 Database Status:"

echo -n "PostgreSQL connection... "
if docker-compose exec -T postgres pg_isready -U synapse > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} (connection failed)"
    ((FAILED++))
fi

echo -n "Table creation... "
TABLES=$(docker-compose exec -T postgres psql -U synapse -d synapse -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null || echo "0")
if [ "$TABLES" -gt "0" ]; then
    echo -e "${GREEN}✓${NC} ($TABLES tables)"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} (no tables found)"
    ((FAILED++))
fi

echo ""

# Check Redis Connection
echo "📦 Cache Status:"

echo -n "Redis connection... "
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} (connection failed)"
    ((FAILED++))
fi

echo ""

# Summary
echo "================================"
echo "Health Check Summary"
echo "================================"
echo -e "Passed: ${GREEN}${PASSED}${NC}"
echo -e "Failed: ${RED}${FAILED}${NC}"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All systems operational!${NC}"
    echo ""
    echo "🚀 You can now access:"
    echo "   Frontend:  http://localhost:3000"
    echo "   Backend:   http://localhost:8000"
    echo "   API Docs:  http://localhost:8000/docs"
    exit 0
else
    echo ""
    echo -e "${YELLOW}⚠️  Some checks failed. See details above.${NC}"
    echo ""
    echo "🔍 Troubleshooting steps:"
    echo "   1. View logs: docker-compose logs -f"
    echo "   2. Check service status: docker-compose ps"
    echo "   3. Restart services: docker-compose restart"
    echo "   4. See DOCKER_SETUP.md for detailed help"
    exit 1
fi
