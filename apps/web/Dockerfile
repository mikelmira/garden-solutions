FROM node:20-alpine AS base

# Install pnpm
RUN corepack enable

# ── Build stage ────────────────────────────────────────────────
FROM base AS builder
WORKDIR /app

# Copy workspace config
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml turbo.json ./
COPY apps/web/package.json ./apps/web/
COPY packages/ ./packages/

# Install all dependencies (dev + prod) for the build
RUN pnpm install --frozen-lockfile

# Copy source and build
COPY apps/web/ ./apps/web/
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm --filter web build

# ── Production stage ───────────────────────────────────────────
# We install production deps fresh in the runner stage instead of relying on
# Next's standalone output, because Next's standalone tracing has long-standing
# issues with pnpm workspaces (node_modules symlinks dangle, `.pnpm` store is
# not bundled). Installing prod deps with pnpm in a clean runner is the
# reliable, well-documented workaround for this codebase shape.
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Workspace manifests so pnpm understands the workspace
COPY --from=builder /app/package.json /app/pnpm-lock.yaml /app/pnpm-workspace.yaml /app/turbo.json ./
COPY --from=builder /app/apps/web/package.json ./apps/web/
COPY --from=builder /app/packages ./packages

# Install ONLY production dependencies for the web filter
RUN pnpm install --frozen-lockfile --prod --filter web

# Copy the Next.js build output and public assets
COPY --from=builder /app/apps/web/.next ./apps/web/.next
COPY --from=builder /app/apps/web/public ./apps/web/public

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

# Run from the web app directory; pnpm-defined "start" script calls `next start`
WORKDIR /app/apps/web
CMD ["pnpm", "start"]
