# Delivery Public Views

## Overview
Delivery team uses a permanent team code to fetch assigned orders and record delivery outcomes.

## Endpoints
- Resolve Delivery Team: `POST /api/v1/delivery-teams/resolve`
  - Body: `{ "code": "D-XXXX" }`
- Delivery Queue: `GET /api/v1/public/delivery/queue?team_code=...&date=YYYY-MM-DD`
- Delivery Outcome: `PATCH /api/v1/public/delivery/orders/{order_id}/outcome`

## Outcomes
- `delivered`: Sets all items to delivered if fully manufactured.
- `partial`: Updates per-item delivered quantities (absolute), requires reason.
- `not_delivered`: No quantity updates; records reason.
