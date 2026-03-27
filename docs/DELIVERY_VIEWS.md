# Delivery Views Documentation

## Overview
The delivery system now includes a dedicated mobile-first web app at `/delivery` for logistics teams.

## Routes
- **`/delivery`**: Public Logistics App. Protected by Delivery Team Code (e.g., `DT-ALPHA`).

## Workflow
1. **Gate**: User enters Team Code. Validated via `POST /api/v1/delivery-teams/resolve`.
2. **Queue List**: Shows orders for the selected date (default: Today).
   - Filter by date supported.
   - Status indicators: Pending (Default), Delivered, Partial, Not Delivered.
3. **Action**: User updates status.
   - **Delivered**: Optional receiver name.
   - **Partial**: Requires reason + per-item confirmed quantities.
   - **Not Delivered**: Requires failure reason.

## API Requirements
- `POST /delivery-teams/resolve`: Returns `{ id, name, code }`.
- `GET /public/delivery/queue?team_code=...&date=...`: Returns list of assigned orders.
- `PATCH /public/delivery/orders/{id}/outcome`: payload `{ team_code, outcome, reason, items... }`.
