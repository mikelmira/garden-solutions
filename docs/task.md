# Sprint 4 Backend Task

## Goal
Implement delivery execution endpoints for V1 without changing frontend routes.

## Scope (Backend Only)
- Delivery queue endpoint.
- Order item delivered update endpoint.
- Delivery complete and partial endpoints (audit logged).
- Server-derived delivery readiness.

## Non-Goals
- No manufacturing changes.
- No new delivery tables unless required by docs.
- No order status mutations for delivery.

## Acceptance Checklist
- `GET /api/v1/delivery/queue` returns ready-for-delivery orders and item quantities.
- `PATCH /api/v1/order-items/{id}/delivered` updates delivered quantity with validation.
- `PATCH /api/v1/orders/{id}/delivery/complete` fails if not fully delivered.
- `PATCH /api/v1/orders/{id}/delivery/partial` records audit event.
- Smoke tests cover delivery flow.
