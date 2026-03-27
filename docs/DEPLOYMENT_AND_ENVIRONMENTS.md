# Deployment and Environments

## 1. Local Development Setup
- **Prerequisites**: Docker Desktop, Node.js 20+, Python 3.11+.
- **Command**: `pnpm dev`
  - Starts Next.js (Port 3000).
  - Starts FastAPI (Port 8000).
  - Starts Postgres (Docker, Port 5432).
- **Database**:
  - `pnpm db:up`: Runs Docker Compose for DB.
  - `pnpm db:migrate`: Runs Alembic migrations.
  - `pnpm db:seed`: Populates local DB with dummy Tier/Product data.

## 2. Environment Separation

### Development (Local)
- `NODE_ENV=development`
- Database: Local Docker.
- Auth: Dummy seed users.

### Staging (Remote)
- `NODE_ENV=production`
- Replica of Production.
- Data: Anonymized dump of Prod or Synthetic data.
- Purpose: Final verification of V1 release candidates.

### Production (Remote)
- `NODE_ENV=production`
- Database: Managed PostgreSQL (e.g., RDS, Cloud SQL).
- Logging: Structured JSON logs sent to aggregator.

## 3. Docker Strategy
- **Containerization**:
  - `apps/web/Dockerfile`: Multi-stage build (Install -> Build -> Runner).
  - `apps/api/Dockerfile`: Python-slim based.
- **Orchestration**:
  - Local: `docker-compose.yml`.
  - Prod: Container runtime (ECS, Cloud Run, Kubernetes, or simple Coolify/Dokku).

## 4. Production Readiness Checklist
- [ ] No hardcoded secrets.
- [ ] `NEXT_PUBLIC_API_URL` points to prod API.
- [ ] Database backups configured (Daily).
- [ ] Alembic migrations applied successfully.
- [ ] Admin user seeded (bootstrap).
- [ ] HTTPS enforced (TLS termination at Load Balancer).
