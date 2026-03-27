# Ordering Views (Public)

## Overview
Sales reps create orders without login using a permanent code.

## Endpoints
- Resolve Sales Agent: `POST /api/v1/sales-agents/resolve`
  - Body: `{ "code": "S-XXXX" }`
- Create Order: `POST /api/v1/public/orders`
  - Body includes `sales_agent_code` and standard order payload.

## Notes
- Orders created via public endpoint are set to `pending_approval`.
- Sales agent code is resolved to `sales_agent_id` server-side.
