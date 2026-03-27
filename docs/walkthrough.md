# Backend Walkthrough (Local Verification)

## Run Backend Locally
From `apps/api`:
1. `POSTGRES_PORT=5433 venv/bin/alembic -c alembic.ini upgrade head`
2. `POSTGRES_PORT=5433 venv/bin/python -m scripts.seed_admin`
3. `POSTGRES_PORT=5433 venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000`
4. `POSTGRES_PORT=5433 venv/bin/python -m scripts.smoke_test`

## Public Ordering Flow
- Resolve Sales Agent: `POST /api/v1/sales-agents/resolve`
- Resolve Store: `POST /api/v1/stores/resolve`
- Fetch Clients: `GET /api/v1/public/clients`
- Fetch Products: `GET /api/v1/public/products`
- Create Order: `POST /api/v1/public/orders`
  - Client order: include `sales_agent_code` + `client_id`
  - Store order: include `store_code` only

## Public Delivery Flow
- Resolve Delivery Team: `POST /api/v1/delivery-teams/resolve`
- Fetch Queue: `GET /api/v1/public/delivery/queue?team_code=...&date=YYYY-MM-DD`
- Record Outcome: `PATCH /api/v1/public/delivery/orders/{order_id}/outcome`
