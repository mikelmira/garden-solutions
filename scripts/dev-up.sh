#!/bin/bash
# ============================================
# Garden Solutions - Development Startup Script
# ============================================
# Starts all services: DB, API, Web
# Usage: ./scripts/dev-up.sh
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$ROOT_DIR/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Create log directory
mkdir -p "$LOG_DIR"

echo ""
echo "=========================================="
echo "  Garden Solutions - Dev Environment"
echo "=========================================="
echo ""

# --------------------------------------------
# 1. Kill existing processes on ports 3000 and 8000
# --------------------------------------------
log_info "Stopping existing processes..."

kill_port() {
    local port=$1
    local pids=$(lsof -ti :$port 2>/dev/null || true)
    if [ -n "$pids" ]; then
        log_warn "Killing processes on port $port: $pids"
        echo "$pids" | xargs kill 2>/dev/null || true
        sleep 1
        # Force kill if still running
        pids=$(lsof -ti :$port 2>/dev/null || true)
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -9 2>/dev/null || true
            sleep 1
        fi
    fi
}

kill_port 3000
kill_port 8000

# Also kill by process name as backup
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
sleep 2

log_success "Existing processes stopped"

# --------------------------------------------
# 2. Start Docker DB if not running
# --------------------------------------------
log_info "Checking Docker database..."

cd "$ROOT_DIR"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Check if the container exists and is running
if docker ps --format '{{.Names}}' | grep -q "gardensolutions-db-1"; then
    log_success "Database container already running"
elif docker ps -a --format '{{.Names}}' | grep -q "gardensolutions-db-1"; then
    log_info "Starting existing database container..."
    docker start gardensolutions-db-1 >/dev/null 2>&1
    sleep 3
    log_success "Database container started"
else
    log_info "Starting database with docker-compose..."
    docker-compose up -d db 2>/dev/null || docker compose up -d db 2>/dev/null
    sleep 5
    log_success "Database container created and started"
fi

# Wait for DB to be ready
log_info "Waiting for database to be ready..."
for i in {1..30}; do
    if docker exec gardensolutions-db-1 pg_isready -U admin -d garden_solutions >/dev/null 2>&1; then
        log_success "Database is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "Database failed to start"
        exit 1
    fi
    sleep 1
done

# --------------------------------------------
# 3. Start API (FastAPI on port 8000)
# --------------------------------------------
log_info "Starting API server..."

cd "$ROOT_DIR/apps/api"

# Activate venv and start uvicorn
(
    source venv/bin/activate 2>/dev/null || true
    uvicorn app.main:app --reload --port 8000 >> "$LOG_DIR/api.log" 2>&1
) &
API_PID=$!

log_info "API starting (PID: $API_PID, log: $LOG_DIR/api.log)"

# Wait for API to be healthy
log_info "Waiting for API to be ready..."
for i in {1..60}; do
    if curl -s --max-time 2 http://localhost:8000/api/v1/health | grep -q "healthy"; then
        log_success "API is ready"
        break
    fi
    if [ $i -eq 60 ]; then
        log_error "API failed to start. Check $LOG_DIR/api.log"
        tail -20 "$LOG_DIR/api.log"
        exit 1
    fi
    sleep 1
done

# --------------------------------------------
# 4. Clear Next.js cache and start Web
# --------------------------------------------
log_info "Preparing frontend..."

cd "$ROOT_DIR/apps/web"

# Remove .next cache
rm -rf .next 2>/dev/null || true
log_success "Next.js cache cleared"

# Start Next.js dev server
log_info "Starting Web server..."
(
    pnpm dev >> "$LOG_DIR/web.log" 2>&1
) &
WEB_PID=$!

log_info "Web starting (PID: $WEB_PID, log: $LOG_DIR/web.log)"

# Wait for Web to be ready
log_info "Waiting for Web to be ready..."
for i in {1..90}; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 http://localhost:3000 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" != "000" ]; then
        log_success "Web is ready (HTTP $HTTP_CODE)"
        break
    fi
    if [ $i -eq 90 ]; then
        log_error "Web failed to start. Check $LOG_DIR/web.log"
        tail -20 "$LOG_DIR/web.log"
        exit 1
    fi
    sleep 1
done

# --------------------------------------------
# 5. Final status
# --------------------------------------------
echo ""
echo "=========================================="
echo -e "  ${GREEN}All services are running!${NC}"
echo "=========================================="
echo ""
echo -e "  ${BLUE}Web:${NC}    http://localhost:3000"
echo -e "  ${BLUE}API:${NC}    http://localhost:8000/api/v1"
echo -e "  ${BLUE}Admin:${NC}  http://localhost:3000/admin/orders"
echo ""
echo -e "  ${YELLOW}Logs:${NC}"
echo "    API: $LOG_DIR/api.log"
echo "    Web: $LOG_DIR/web.log"
echo ""
echo -e "  ${YELLOW}To stop:${NC} pkill -f 'uvicorn|next dev'"
echo ""
