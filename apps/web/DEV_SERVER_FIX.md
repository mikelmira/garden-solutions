# Next.js Dev Server Troubleshooting

## Common Issue: "Cannot find module ./XXX.js" or build errors

When you see errors like:
- `Cannot find module './616.js'`
- `ENOENT: no such file or directory, open '.../.next/package.json'`
- 404 errors for `/_next/static/*` chunks
- Build fails with cryptic module errors

### Quick Fix

Run this from the repository root:

```bash
./scripts/reset-web-dev.sh
```

This script will:
1. Kill any running Next.js processes
2. Free port 3000
3. Remove `.next` build cache
4. Remove `node_modules/.cache`
5. Start `pnpm dev`

### Manual Steps

If the script doesn't work or you prefer manual steps:

```bash
# From repository root:

# 1. Kill any running Next.js processes
pkill -f "next-server" || true
pkill -f "next dev" || true

# 2. Kill anything on port 3000
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# 3. Remove .next cache
rm -rf apps/web/.next

# 4. Remove node_modules cache (optional but thorough)
rm -rf apps/web/node_modules/.cache

# 5. Restart dev server
cd apps/web && pnpm dev
```

### Prevention

- Don't force-kill the dev server (Ctrl+C is fine)
- If you switch git branches with significant changes, clean the cache
- After major dependency updates, clean and rebuild

### Verification

After restart, check these work:
- http://localhost:3000 (frontend)
- http://localhost:8000/api/v1/health (backend API)
