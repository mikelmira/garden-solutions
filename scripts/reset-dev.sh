#!/bin/bash
# Development Environment Reset Script
# Use this when experiencing:
# - Next.js chunk errors (Cannot find module ./xxx.js)
# - CORS errors after backend restart
# - 401 auth loops
# - Backend not responding

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Garden Solutions Dev Reset ==="

# 1. Stop any running servers
echo "[1/5] Stopping existing processes..."
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
sleep 2

# 2. Clear Next.js cache
echo "[2/5] Clearing Next.js cache..."
rm -rf "$ROOT_DIR/apps/web/.next" 2>/dev/null || true

# 3. Start backend
echo "[3/5] Starting backend..."
cd "$ROOT_DIR/apps/api"
source venv/bin/activate 2>/dev/null || true
nohup uvicorn app.main:app --reload --port 8000 > /tmp/uvicorn.log 2>&1 &
sleep 4

# 4. Verify backend
echo "[4/5] Verifying backend..."
if curl -s --max-time 5 http://localhost:8000/api/v1/health | grep -q "healthy"; then
    echo "  Backend: OK"
else
    echo "  Backend: FAILED - check /tmp/uvicorn.log"
    tail -20 /tmp/uvicorn.log
    exit 1
fi

# 5. Instructions for frontend
echo "[5/5] Ready!"
echo ""
echo "Backend is running on http://localhost:8000"
echo ""
echo "To start frontend:"
echo "  cd $ROOT_DIR/apps/web"
echo "  pnpm dev"
echo ""
echo "If you see chunk errors in browser:"
echo "  1. Stop the dev server (Ctrl+C)"
echo "  2. rm -rf .next"
echo "  3. pnpm dev"
