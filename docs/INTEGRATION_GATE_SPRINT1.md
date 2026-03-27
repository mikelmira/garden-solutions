# Integration Gate: Sprint 1 (Backend)

Date: 2026-01-31

## Commands Run (Exact)
1. `rg --files -g 'pyproject.toml' -g 'requirements*.txt'`
2. `sed -n '1,220p' apps/api/pyproject.toml`
3. `rg "5432|5433|postgres" -n docs`
4. `sed -n '1,200p' docker-compose.yml`
5. `lsof -nP -iTCP:5432 -sTCP:LISTEN`
6. `docker compose down -v`
7. `docker compose up -d db`
8. `docker compose exec -T db pg_isready -U admin`
9. `POSTGRES_PORT=5433 venv/bin/alembic -c alembic.ini upgrade head` (run from `apps/api`)
10. `docker compose exec -T db psql -U admin -d garden_solutions -c "\\d orders"`
11. `POSTGRES_PORT=5433 venv/bin/python -m scripts.seed_admin` (run from `apps/api`)
12. `docker compose exec -T db psql -U admin -d garden_solutions -c "SELECT id, name, created_by FROM clients ORDER BY name;"`
13. `lsof -nP -iTCP:8000 -sTCP:LISTEN`
14. `ps -fp 34781,34783`
15. `kill 34781`
16. `POSTGRES_PORT=5433 venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/gs_api.log 2>&1 & echo $!` (run from `apps/api`)
17. `sleep 1`
18. `venv/bin/python -m scripts.smoke_test` (run from `apps/api`)
19. `kill 36235`
20. `rg "sales_agent_id" apps/api/app`

## Step Results (Pass/Fail)
1) Dependency sanity check — **PASS**
   - Source of truth: `apps/api/pyproject.toml`.
   - Pin applied: `passlib[bcrypt]==1.7.4`, `bcrypt==4.0.1`.

2) Environment reproducibility — **PASS (Required port 5433)**
   - `lsof` confirmed port 5432 in use by Docker.
   - `docker-compose.yml` uses `5433:5432` and is required in this environment.

3) Database verification — **PASS**
   - Fresh DB via `docker compose down -v` and `up -d db`.
   - `alembic upgrade head` succeeded from empty DB to head.
   - `orders.created_by` exists; `orders.sales_agent_id` does not.
   - Index/FK names: `ix_orders_created_by` and `fk_orders_created_by` present.
   - Downgrade symmetry verified by code review (rename-only guards).

4) Seed script verification — **PASS**
   - `scripts.seed_admin` ran successfully.
   - Admin, Sales, Manufacturing, Delivery users created.
   - Clients created with `created_by` set.
   - Products + SKUs created.

5) API smoke tests — **PASS**
   - Login (admin & sales): OK.
   - `GET /clients`: Sales sees 2 (filtered).
   - `GET /products`: active products returned.
   - `POST /orders`: status `pending_approval`.
   - `PATCH /orders/{id}/status`: admin only (approved succeeded).
   - Status values are lowercase strings.

6) Final audit — **PASS**
   - No `sales_agent_id` references in `apps/api/app`.
   - Ownership logic uses `created_by`.
   - No frontend-breaking contract changes beyond documented `created_by` field.

## Files Changed
- `apps/api/pyproject.toml`
  - Pinned `passlib[bcrypt]==1.7.4` for bcrypt compatibility.

## Summary
- Integration-safe: **Yes**.
- Remaining risks: **Low**. Requires `POSTGRES_PORT=5433` for local Docker due to 5432 conflict in this environment.
