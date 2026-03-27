# API Reference

## 1. General Principles
- **Versioning**: All endpoints use `/api/v1/`. Breaking changes require `/api/v2/`.
- **Content-Type**: strictly `application/json`.
- **Date Format**: ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`).
- **Currency**: All monetary values are Decimals (e.g. `123.45`).

## 2. Authentication Groups
- **Public**: No token required.
- **Protected**: `Authorization: Bearer <token>` required.
- **Role-Gated**: Requires specific role claim in token.

## 3. Endpoint Groups

### Group: Auth
**Purpose**: System entry and token management.
- `POST /api/v1/auth/login`
  - *Public*. Returns Access + Refresh Token.
- `POST /api/v1/auth/refresh`
  - *Public*, requires Refresh Token. Returns new Access Token.
- `GET /api/v1/auth/me`
  - *Protected*. Returns current user profile.

### Group: Health
**Purpose**: Service liveness and DB connectivity.
- `GET /api/v1/health`
  - *Public*. Returns `{ status: "healthy" }` after a DB ping.

### Group: Clients
**Purpose**: Client management and listing.
- `GET /api/v1/clients`
  - *Protected*.
  - *Admin*: All clients.
  - *Sales*: Only clients assigned to them.
  - **Response includes**: `id`, `name`, `address` (optional), `tier_id`, `created_by`, `is_active`
- `GET /api/v1/clients/{id}`
  - *Protected*. Detail view.
- `POST /api/v1/clients`
  - *Admin Only*. Create new client.
  - **Body includes**: `name`, `tier_id`, `address` (optional)

### Group: Sales Agents
**Purpose**: Sales agent registry and resolve-by-code.
- `POST /api/v1/sales-agents`
  - *Admin Only*. Create sales agent.
- `GET /api/v1/sales-agents`
  - *Admin Only*. List sales agents.
- `GET /api/v1/sales-agents/{id}`
  - *Admin Only*. Sales agent detail.
- `PATCH /api/v1/sales-agents/{id}`
  - *Admin Only*. Update sales agent.
- `POST /api/v1/sales-agents/resolve`
  - *Public*. Resolve by code.
  - **Body**: `{ "code": "S-XXXX" }`

### Group: Delivery Teams
**Purpose**: Delivery team registry and resolve-by-code.
- `POST /api/v1/delivery-teams`
  - *Admin Only*. Create delivery team.
- `GET /api/v1/delivery-teams`
  - *Admin Only*. List delivery teams.
- `GET /api/v1/delivery-teams/{id}`
  - *Admin Only*. Delivery team detail.
- `PATCH /api/v1/delivery-teams/{id}`
  - *Admin Only*. Update delivery team.
- `POST /api/v1/delivery-teams/{id}/members`
  - *Admin Only*. Add team member.
- `PATCH /api/v1/delivery-teams/{team_id}/members/{member_id}`
  - *Admin Only*. Update team member.
- `DELETE /api/v1/delivery-teams/{team_id}/members/{member_id}`
  - *Admin Only*. Soft delete (sets `is_active=false`).
- `POST /api/v1/delivery-teams/resolve`
  - *Public*. Resolve by code.
  - **Body**: `{ "code": "D-XXXX" }`
### Group: Products & SKUs
**Purpose**: The sellable catalogue.
- `GET /api/v1/products`
  - *Protected*. List products (with SKUs).
  - **Query params**: `is_active` (default true), `category`
- `GET /api/v1/products/{id}`
  - *Protected*. Detail view including SKUs.
- `POST /api/v1/products`
  - *Admin Only*. Create Product.
- `POST /api/v1/products/{id}/skus`
  - *Admin Only*. Add variant.
- `PATCH /api/v1/products/{id}`
  - *Admin Only*. Update Product (soft delete via `is_active=false`).
- `POST /api/v1/products/{id}/image`
  - *Admin Only*. Upload/replace product image (multipart/form-data `file`).
- `DELETE /api/v1/products/{id}/image`
  - *Admin Only*. Remove product image.
- `PATCH /api/v1/products/{id}/skus/{sku_id}`
  - *Admin Only*. Update SKU under a product.
- `PATCH /api/v1/skus/{sku_id}`
  - *Admin Only*. Update SKU by ID (soft delete via `is_active=false`).
- `POST /api/v1/products/bulk`
  - *Admin Only*. Bulk upsert products and SKUs (JSON).
  - **Body**: `{ "products": [ { "name", "category", "description_html", "skus": [ { "code", "size", "color", "base_price_rands", "stock_quantity", "is_active?" } ] } ] }`
  - **Behavior**:
    - product match is case-insensitive trim on `name`
    - sku_code unique globally (conflict if it belongs to another product)
    - payload duplicates return 409
- `POST /api/v1/products/import-csv`
  - *Admin Only*. Bulk import products and SKUs (multipart/form-data file upload).
  - **CSV columns**:
    `product_name, product_description, product_category, product_is_active,
     sku_code, sku_size, sku_color, sku_base_price_rands, sku_stock_quantity, sku_is_active`
  - **Behavior**:
    - product match is case-insensitive trim on `product_name`
    - sku_code unique globally
    - per-row best-effort; failures are returned with row number and reason

### Group: Price Tiers
**Purpose**: Discount logic reference.
- `GET /api/v1/price-tiers`
  - *Protected*. List definitions (e.g., Tier A = 10%).

### Group: Orders
**Purpose**: Core transaction management.
- `GET /api/v1/orders`
  - *Protected*.
  - *Admin*: All.
  - *Sales*: Own (filtered by `created_by`). *(Sprint 1.1 alignment)*
  - *Mfg*: Approved+ only.
- `POST /api/v1/orders`
  - *Sales/Admin*. Create Order.
  - **Body optionally includes**: `sales_agent_id` or `sales_agent_code` (to attribute sales rep)
  - **Side Effect**: Creates `AuditLog`, sets status `Pending Approval` (or `Status` based on role).
- `GET /api/v1/orders/{id}`
  - *Protected*. Detailed view with Items.
  - **Response includes**: `sales_agent_id`, `store_id`, `order_source`, `delivery_team_id`, `delivery_status`, `delivery_status_reason`, `delivery_receiver_name`, `delivered_at`
- `PATCH /api/v1/orders/{id}/status`
  - *Admin Only*. Approve/Cancel.
  - **Side Effect**: `AuditLog`.
- `PATCH /api/v1/orders/{id}/assign-delivery-team`
  - *Admin Only*. Assign a delivery team.
  - **Body**: `{ "delivery_team_id": "UUID" }`
  - **Side Effect**: `AuditLog` (entity_type `delivery_assignment`)

### Group: Public Orders
**Purpose**: Sales agent order creation without login.
- `GET /api/v1/public/clients`
  - *Public*. List active clients for ordering.
  - **Response fields**: `id`, `name`, `address`
- `GET /api/v1/public/products`
  - *Public*. List active products with active SKUs for ordering.
  - **Response fields**: product `id`, `name`, `description`, `category`, `image_url`, `is_active`, `skus[]`
- `POST /api/v1/public/orders`
  - *Public*. Create order with **exactly one** of:
    - **Client order**: `sales_agent_code` **and** `client_id`
    - **Store order**: `store_code` (no `client_id`)
  - **Body**: same as `/orders` plus required `sales_agent_code` or `store_code`.
  - **Order source**: `order_source = "client"` for client orders, `order_source = "store"` for store orders.

### Group: Stores
**Purpose**: Internal nurseries and external store placeholders.
- `POST /api/v1/stores`
  - *Admin Only*. Create store.
- `GET /api/v1/stores`
  - *Admin Only*. List stores.
- `GET /api/v1/stores/{id}`
  - *Admin Only*. Store detail.
- `PATCH /api/v1/stores/{id}`
  - *Admin Only*. Update store (soft delete via `is_active=false`).
- `POST /api/v1/stores/resolve`
  - *Public*. Resolve store by code.
  - **Body**: `{ "code": "POT-001" }`
  - **Response**: `{ id, name, code, store_type }`

### Group: Manufacturing
**Purpose**: Manufacturing queue and progress.
- `GET /api/v1/manufacturing/queue`
  - *Manufacturing/Admin Only*. Returns approved orders with items and manufacturing counts.
  - **Response items include**: `id` (OrderItem.id), `order_id`, `sku_id`, `quantity_ordered`, `quantity_manufactured`, `remaining_to_manufacture`, `sku`

### Group: Order Items (Manufacturing)
**Purpose**: Tracking production.
- `PATCH /api/v1/order-items/{id}/manufactured`
  - *Manufacturing/Admin Only*. Set `quantity_manufactured` (absolute value).
  - **Path param**: `{id}` is `OrderItem.id` (NOT `sku_id`)
  - **Body**: `{ "quantity_manufactured": <integer> }`
  - **Rules** (enforced server-side):
    - `0 <= quantity_manufactured <= quantity_ordered`
    - Monotonically increasing (cannot decrease)
    - Does NOT change Order.status (derived per STATUS_MODEL.md)
  - **Side Effect**: Creates `AuditLog` entry atomically.

### Group: Order Items (Delivery)
**Purpose**: Tracking delivery quantities per item.
- `PATCH /api/v1/order-items/{id}/delivered`
  - *Delivery/Admin Only*. Set `quantity_delivered` (absolute value).
  - **Path param**: `{id}` is `OrderItem.id` (NOT `sku_id`)
  - **Body**: `{ "quantity_delivered": <integer> }`
  - **Rules** (enforced server-side):
    - `0 <= quantity_delivered <= quantity_manufactured`
    - Monotonically increasing (cannot decrease)
  - **Side Effect**: Creates `AuditLog` entry atomically.

### Group: Delivery Actions
**Purpose**: Logistics and proof of delivery.
- `GET /api/v1/delivery/queue`
  - *Delivery/Admin Only*. Returns ready-for-delivery orders with client details and items.
  - **Response items include**: `id` (OrderItem.id), `sku_id`, `quantity_ordered`, `quantity_manufactured`, `quantity_delivered`, `remaining_to_deliver`
- `PATCH /api/v1/delivery/orders/{order_id}/complete`
  - *Delivery/Admin Only*. Marks delivery complete **only** if all items are fully delivered.
  - **Body**: `{ "receiver_name": "string" }`
  - **Rules**: Fails if any item is not fully delivered; audit logged.
- `PATCH /api/v1/delivery/orders/{order_id}/partial`
  - *Delivery/Admin Only*. Records a partial delivery attempt and item quantities.
  - **Body**: `{ "receiver_name": "string", "reason": "string", "items": [{ "order_item_id": "UUID", "quantity_delivered": 1 }] }`
  - **Rules**: Requires `reason`; quantities are absolute and monotonically increasing; audit logged.

### Group: Public Delivery
**Purpose**: Delivery team mobile view without login.
- `GET /api/v1/public/delivery/queue?team_code=...&date=YYYY-MM-DD`
  - *Public*. Returns assigned orders for that team and date.
- `PATCH /api/v1/public/delivery/orders/{order_id}/outcome`
  - *Public*. Record delivery outcome.
  - **Body**: `{ "team_code": "D-XXXX", "outcome": "delivered|partial|not_delivered", "receiver_name": "...", "reason": "...", "items": [{ "order_item_id": "UUID", "quantity_delivered": 1 }] }`

### Group: Sync & Logs
**Purpose**: Offline support and Auditing.
- `POST /api/v1/sync/outbox`
  - *Protected*. Batch process offline mutations.
- `GET /api/v1/audit-logs`
  - *Admin Only*. View system history.
