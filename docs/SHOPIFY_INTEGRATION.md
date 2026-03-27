# Shopify Integration — Pot Shack

Operational integration layer connecting the Pot Shack Shopify storefront to Garden Solutions internal order management. Designed to be webhook-driven, admin-manageable, diagnosable, retry-safe, and operationally trustworthy.

---

## Architecture Overview

```
Shopify Store (Pot Shack)
    │
    ├── Webhooks ──────────► /api/v1/webhooks/shopify/*
    │                            │
    │                            ▼
    │                     ShopifyService
    │                    (shared core logic)
    │                            │
    │                     ┌──────┴──────┐
    │                     │             │
    │               Products/       Orders
    │               Variants        Ingestion
    │                     │             │
    │                Auto-Map      Create Internal
    │               Variants       Order (pending)
    │
    └── Admin UI ──────────► /api/v1/shopify/*
         (manual sync,           │
          mapping,               ▼
          reconciliation)   ShopifyService
                           (same core logic)
```

All sync flows — webhooks, manual sync, and reconciliation — share the same `ShopifyService` to guarantee identical behavior.

---

## Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SHOPIFY_SHOP_DOMAIN` | Yes (prod) | Shopify store domain | `pot-shack.myshopify.com` |
| `SHOPIFY_ACCESS_TOKEN` | Yes (prod) | Shopify Admin API access token | `shpat_xxxxx` |
| `SHOPIFY_WEBHOOK_SECRET` | Yes (prod) | HMAC secret for webhook signature verification | `whsec_xxxxx` |
| `SHOPIFY_API_VERSION` | No | Shopify API version (default: `2024-01`) | `2024-01` |

**Dev mode:** When `SHOPIFY_WEBHOOK_SECRET` is empty, HMAC verification is skipped — webhooks are accepted without signature checks. This is for local development only.

Set these in `apps/api/.env` (see `apps/api/.env.example`).

---

## Database Tables

### `shopify_products`
Synced Shopify product records. One row per Shopify product.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | Internal ID |
| `shopify_product_id` | BigInteger | Shopify's product ID (unique, indexed) |
| `store_id` | UUID FK → stores | Links to internal store record |
| `title` | String(500) | Product title |
| `product_type` | String(255) | Shopify product type |
| `vendor` | String(255) | Shopify vendor |
| `shopify_handle` | String(500) | URL handle |
| `shopify_status` | String(50) | active / draft / archived |
| `raw_payload` | JSONB | Full Shopify product JSON |
| `last_synced_at` | DateTime | Last sync timestamp |

### `shopify_variants`
Synced Shopify variants with optional mapping to internal SKUs.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | Internal ID |
| `shopify_variant_id` | BigInteger | Shopify's variant ID (unique, indexed) |
| `shopify_product_id` | BigInteger | Parent Shopify product ID |
| `product_id_fk` | UUID FK → shopify_products | Parent product |
| `shopify_sku` | String(255) | Shopify SKU code (indexed) |
| `sku_id` | UUID FK → skus | Mapped internal SKU (nullable) |
| `mapping_status` | String(20) | `mapped` / `unmapped` / `ignored` (indexed) |
| `price`, `option1-3`, etc. | Various | Shopify variant details |

### `shopify_orders`
Synced Shopify orders with mapping to internal orders.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | Internal ID |
| `shopify_order_id` | BigInteger | Shopify's order ID (unique, indexed) |
| `shopify_order_number` | String(100) | Display number (e.g. #1042) |
| `store_id` | UUID FK → stores | Links to internal store |
| `internal_order_id` | UUID FK → orders | Linked internal order (nullable) |
| `sync_status` | String(20) | `synced` / `partial` / `failed` / `pending` / `cancelled` |
| `error_message` | Text | Error details if failed |
| `unmapped_items` | JSONB | List of items that couldn't be mapped |
| `raw_payload` | JSONB | Full Shopify order JSON |

### `shopify_webhook_events`
Raw webhook payload storage for diagnostics and replay.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | Internal ID |
| `shopify_webhook_id` | String(255) | X-Shopify-Webhook-Id header (indexed) |
| `topic` | String(100) | e.g. `orders/create` (indexed) |
| `store_id` | UUID FK → stores | Resolved store |
| `status` | String(20) | `received` / `processed` / `failed` / `duplicate` |
| `processing_time_ms` | Integer | Processing time in milliseconds |
| `raw_payload` | JSONB | Full webhook payload |
| `headers` | JSONB | Relevant Shopify headers |

**Migration:** `apps/api/alembic/versions/20260310_1000_add_shopify_integration_tables.py`

---

## Webhook Endpoints

Public endpoints (no JWT auth) verified via HMAC-SHA256 signature.

| Endpoint | Shopify Topic | What It Does |
|----------|--------------|--------------|
| `POST /api/v1/webhooks/shopify/orders/create` | `orders/create` | Ingests new Shopify order → creates internal order |
| `POST /api/v1/webhooks/shopify/orders/updated` | `orders/updated` | Updates existing order metadata (respects lifecycle guards) |
| `POST /api/v1/webhooks/shopify/orders/cancelled` | `orders/cancelled` | Cancels internal order + returns inventory |
| `POST /api/v1/webhooks/shopify/products/create` | `products/create` | Syncs new product + auto-maps variants |
| `POST /api/v1/webhooks/shopify/products/update` | `products/update` | Updates product/variant data + re-attempts unmapped |

### Shopify Webhook Setup

In the Shopify Admin → Settings → Notifications → Webhooks, register these:

```
Event: Order creation      → https://your-api.com/api/v1/webhooks/shopify/orders/create
Event: Order update        → https://your-api.com/api/v1/webhooks/shopify/orders/updated
Event: Order cancellation  → https://your-api.com/api/v1/webhooks/shopify/orders/cancelled
Event: Product creation    → https://your-api.com/api/v1/webhooks/shopify/products/create
Event: Product update      → https://your-api.com/api/v1/webhooks/shopify/products/update
```

Format: JSON. API version: 2024-01. Copy the webhook signing secret to `SHOPIFY_WEBHOOK_SECRET`.

### Webhook Processing Flow

1. Receive raw body + headers
2. Verify HMAC-SHA256 signature (or skip in dev mode)
3. Parse JSON payload
4. Resolve internal store (type=shopify, is_active)
5. Log raw event to `shopify_webhook_events` (idempotency check via `X-Shopify-Webhook-Id`)
6. If duplicate → return 200 immediately
7. Dispatch to `ShopifyService` for processing
8. Mark event as `processed` or `failed`
9. Always return 200 to Shopify (even on error — we've logged it)

---

## Admin API Endpoints

All admin endpoints require JWT auth with `admin` role. Prefix: `/api/v1/shopify/`.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status` | GET | Integration overview: sync counts, last sync times, webhook activity |
| `/products` | GET | List synced Shopify products with variant counts |
| `/variants` | GET | List variants (filter by `status`: mapped/unmapped/ignored) |
| `/variants/{id}/map` | POST | Manually map a variant to an internal SKU |
| `/variants/{id}/ignore` | POST | Mark a variant as intentionally ignored |
| `/orders` | GET | List synced orders (filter by `sync_status`) |
| `/sync/products` | POST | Manual product sync (accepts Shopify JSON payloads) |
| `/sync/orders` | POST | Manual order sync (accepts Shopify JSON payloads) |
| `/reconcile/mappings` | POST | Re-attempt auto-mapping for all unmapped variants |
| `/reconcile/orders` | POST | Reprocess failed/partial orders |
| `/webhooks/recent` | GET | Recent webhook events for diagnostics |
| `/internal-skus` | GET | Search internal SKUs (for mapping dropdown) |

---

## Admin Shopify Screen

Located at `/admin/shopify` in the web app. Five tabs:

### Overview Tab
- Sync status cards: products synced, variants (mapped/unmapped/ignored), orders (synced/partial/failed)
- Last sync timestamps for products, orders, and webhooks
- Action buttons: Reconcile Mappings, Reprocess Failed Orders
- Webhook endpoint reference (copy-pastable URLs)

### Unmapped Variants Tab
- Lists all Shopify variants that don't have a corresponding internal SKU
- Each variant shows: Shopify SKU, product title, price, options
- Suggested matches (partial SKU code match) displayed as quick-select buttons
- Manual SKU search field with dropdown for exact mapping
- "Ignore" button for variants that are not relevant (e.g. gift cards, bundles)

### Mapped Variants Tab
- Table of all successfully mapped variants
- Shows: Shopify SKU → Internal SKU Code → Product Name
- Confirms mapping integrity at a glance

### Orders Tab
- Table of all synced Shopify orders
- Columns: Shopify #, customer, total, Shopify status, sync status, errors
- Filterable by sync_status (synced/partial/failed/pending/cancelled)
- Links to internal order detail where applicable

### Webhooks Tab
- Event log of recent webhook activity
- Shows: topic, status, processing time, received timestamp
- Failed events show error messages for debugging

---

## Variant Mapping

### How It Works

Shopify variants must be mapped to internal SKUs before their orders can be fully synced. Three mapping states:

| Status | Meaning |
|--------|---------|
| `mapped` | Variant is linked to an internal SKU — orders with this variant are fully processable |
| `unmapped` | No match found — orders containing this variant will be `partial` (created but items missing) |
| `ignored` | Admin explicitly marked as not relevant — excluded from sync counts |

### Auto-Mapping Strategy

When a product/variant is synced (via webhook or manual), the system attempts auto-mapping:

1. **Exact match**: `shopify_variant.shopify_sku == sku.code` (case-sensitive)
2. **Case-insensitive match**: `lower(shopify_sku) == lower(sku.code)`

If a match is found, the variant is automatically set to `mapped` with the corresponding `sku_id`.

### Manual Mapping

For variants that can't be auto-mapped:
1. Admin goes to the Unmapped Variants tab
2. System suggests partial matches based on first 6 characters of SKU code
3. Admin can search all internal SKUs by code
4. Admin selects the correct SKU and clicks "Map"
5. Mapping is recorded in the audit log with the admin's user ID

### Reconciliation

After creating new internal SKUs, run **Reconcile Mappings** to re-attempt auto-mapping for all unmapped variants. This is safe to run repeatedly — it only updates variants that match.

---

## Order Lifecycle Integration

### How Shopify Orders Enter the Platform

```
Shopify order created
    │
    ▼
Webhook received → shopify_orders record created
    │
    ▼
Line items resolved via variant mapping
    │
    ├── All items mapped → Internal order created (PENDING_APPROVAL) → sync_status = "synced"
    ├── Some items mapped → Internal order created (partial items) → sync_status = "partial"
    ├── No items mapped → No internal order → sync_status = "failed"
    └── Shopify order already cancelled → No internal order → sync_status = "cancelled"
    │
    ▼
Admin reviews and approves internal order
    │
    ▼
Standard order lifecycle: approved → manufacturing → delivery → completed
```

### Key Rules

| Rule | Description |
|------|-------------|
| **New orders always start as `pending_approval`** | Shopify orders require admin approval before entering the pipeline |
| **Approved+ orders: items are FROZEN** | Once an order is approved, Shopify updates cannot modify order items. Only metadata (status, timestamps) is updated. |
| **Shopify cancellations are ALWAYS respected** | Even after internal approval. Triggers internal cancellation + inventory deallocation. |
| **Unmapped items don't block order creation** | Orders are created with whatever items can be mapped; unmapped items are recorded for later resolution. |
| **Reprocessing is safe** | Failed/partial orders can be reprocessed after fixing mappings. Only pending_approval orders are recreated. |

### What Happens on Shopify Order Update

| Internal Order Status | Shopify Update Behavior |
|-----------------------|------------------------|
| Not yet created | Full order creation attempted |
| `pending_approval` | Items can be updated |
| `approved` or later | Metadata update only; item changes blocked |
| Any status (except completed/cancelled) | Cancellation respected |
| `completed` or `cancelled` | No changes applied |

### What Happens on Shopify Order Cancellation

1. Internal order status set to `CANCELLED`
2. If inventory was allocated, `InventoryService.deallocate_order()` returns stock
3. Audit log entry created with trigger: `shopify_cancellation`
4. Shopify order record updated to `sync_status = "cancelled"`

---

## Reconciliation Tools

### Reconcile Mappings (`POST /api/v1/shopify/reconcile/mappings`)

- Re-runs auto-mapping for every variant with `mapping_status = "unmapped"`
- Safe to run any time — especially after creating new internal SKUs
- Returns: `{ total_unmapped, resolved, remaining }`

### Reprocess Failed Orders (`POST /api/v1/shopify/reconcile/orders`)

- Re-attempts ingestion for all orders with `sync_status = "failed"` or `"partial"`
- If a partial order's internal order is still `pending_approval`, it is deleted and recreated
- If the internal order has been approved, it is NOT touched (only Shopify metadata updated)
- Returns: `{ total_attempted, reprocessed, still_failed }`

Both tools are available via the admin UI Overview tab or directly via API.

---

## Diagnostics & Logging

### Webhook Event Log

Every incoming webhook is stored in `shopify_webhook_events` with:
- Full raw payload (JSONB)
- Request headers (webhook ID, topic, shop domain)
- Processing status: `received` → `processed` | `failed` | `duplicate`
- Processing time in milliseconds
- Error message if failed

### Structured Lifecycle Logging

All Shopify operations emit structured JSON logs via the `app.lifecycle` logger:

| Event | Description |
|-------|-------------|
| `shopify.product_synced` | Product upserted with variant count |
| `shopify.variant_mapped` | Variant auto or manually mapped to SKU |
| `shopify.variant_unmapped` | Auto-mapping failed for variant |
| `shopify.order_ingested` | New order created with sync status |
| `shopify.order_updated` | Existing order updated (metadata or blocked) |
| `shopify.order_cancelled_internally` | Shopify cancellation triggered internal cancel |
| `shopify.mappings_reconciled` | Bulk mapping reconciliation results |
| `shopify.orders_reconciled` | Bulk order reprocessing results |

### Audit Trail

Admin actions (manual mapping, ignore, order creation from Shopify) are recorded in the immutable `audit_log` table with:
- Action performed
- Entity type and ID
- User who performed it
- JSONB payload with before/after state

---

## Safety & Guardrails

| Guardrail | Implementation |
|-----------|---------------|
| **Webhook HMAC verification** | SHA-256 signature check on every webhook (skipped in dev) |
| **Webhook idempotency** | Duplicate `X-Shopify-Webhook-Id` detected and skipped |
| **Order idempotency** | Duplicate `shopify_order_id` triggers update, not duplicate creation |
| **Lifecycle protection** | Approved+ orders cannot have items modified by Shopify updates |
| **Cancellation safety** | Cancellations always respected; inventory deallocated |
| **Reprocessing safety** | Only `pending_approval` orders are recreated during reprocessing |
| **Admin-only API** | All management endpoints require admin JWT |
| **Always 200 to Shopify** | Webhooks return 200 even on error (prevents Shopify retry storms) |

---

## Files Reference

| File | Purpose |
|------|---------|
| `apps/api/app/models/shopify.py` | Database models (4 tables) |
| `apps/api/app/services/shopify.py` | Core integration service (~500 lines) |
| `apps/api/app/routers/shopify_webhooks.py` | Public webhook endpoints (5 routes) |
| `apps/api/app/routers/shopify.py` | Admin API endpoints (12 routes) |
| `apps/api/app/core/config.py` | Shopify env var configuration |
| `apps/api/alembic/versions/20260310_1000_*.py` | Database migration |
| `apps/web/app/(admin)/admin/shopify/page.tsx` | Admin Shopify management UI |
| `apps/web/lib/api.ts` | Frontend API client (12 Shopify methods) |

---

## Known Limitations

1. **No Shopify Admin API client**: The current integration is webhook-driven and manual-sync only. There is no active polling or pull-based sync from the Shopify Admin API. Products/orders must arrive via webhooks or be manually pasted as JSON.
2. **Single Shopify store**: The system resolves the first active store with `store_type = "shopify"`. Multi-store support would require domain-based resolution.
3. **No webhook retry queue**: If webhook processing fails, the event is logged but not automatically retried. Use the Reconcile Orders tool to reprocess.
4. **No real-time inventory sync**: Shopify inventory levels are stored but not pushed back to Shopify. Internal inventory is the source of truth.
5. **Delivery date defaulted**: Shopify orders get a default delivery date of 14 days from ingestion. Admin can adjust after approval.
6. **No fulfillment callback**: When an internal order is completed/delivered, fulfillment status is not pushed back to Shopify.
