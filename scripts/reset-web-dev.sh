#!/bin/bash
#
# reset-web-dev.sh - Reset Next.js dev server for Garden Solutions
# Fixes: .next corruption, port conflicts, stale processes
#

set -e

# Ensure we are in the project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT" || exit 1

echo "========================================="
echo "  Garden Solutions - Web Dev Reset"
echo "========================================="
echo ""

# Step 1: Kill Next.js processes
echo "[1/5] Killing any running Next.js processes..."
pkill -f "next-server" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
sleep 1
echo "      Done."

# Step 2: Free port 3000
echo "[2/5] Freeing port 3000..."
PORT_PIDS=$(lsof -ti:3000 2>/dev/null || true)
if [ -n "$PORT_PIDS" ]; then
    echo "$PORT_PIDS" | xargs kill -9 2>/dev/null || true
    echo "      Killed processes on port 3000."
    sleep 1
else
    echo "      Port 3000 already free."
fi

# Step 3: Remove .next cache
echo "[3/5] Removing .next build cache..."
if [ -d "apps/web/.next" ]; then
    rm -rf apps/web/.next
    echo "      Removed apps/web/.next"
else
    echo "      No .next folder found."
fi

# Step 4: Remove node_modules cache (NOT node_modules itself)
echo "[4/5] Removing node_modules cache..."
if [ -d "apps/web/node_modules/.cache" ]; then
    rm -rf apps/web/node_modules/.cache
    echo "      Removed node_modules/.cache"
else
    echo "      No cache folder found."
fi

# Step 5: Start dev server
echo "[5/5] Starting Next.js dev server..."
echo ""
echo "========================================="
echo "  Starting pnpm dev in apps/web"
echo "  Press Ctrl+C to stop"
echo "========================================="
echo ""

cd apps/web || exit 1
exec pnpm dev
