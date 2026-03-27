# Garden Solutions Platform Guide

Internal reference document for the Garden Solutions B2B order management and manufacturing operations platform.

---

## System Overview

Garden Solutions is a full-stack platform for managing the lifecycle of garden product orders — from sales through manufacturing, inventory allocation, and delivery. It serves four user roles across admin dashboards, public portals, and operational interfaces.

**Tech Stack:** Next.js 14 (frontend) + FastAPI (backend) + PostgreSQL

---

## User Roles & Access

| Role | Login | Access |
|------|-------|--------|
| **Admin** | admin@gardensolutions.com | Full platform access: products, orders, clients, stores, teams, manufacturing, delivery, analytics |
| **Sales** | sales@gardensolutions.com | Create orders, view own clients and orders, sales dashboard |
| **Manufacturing** | manufacturing@gardensolutions.com | View manufacturing queue, record production completion |
| **Delivery** | delivery@gardensolutions.com | View delivery queue, record delivery outcomes |

**Public Access (no login required):**
- Sales agents enter orders using their agent code (e.g., `4500`)
- Stores place orders using their store code (e.g., `POTSHACK`)
- Factory workers access moulding page using factory team code (e.g., `FACTORY-A`)
- Delivery teams access delivery page using team code (e.g., `JHB-N`)

---

## Product Lifecycle

### Products
Products are top-level catalog items (e.g., "Classic Pot"). Each product has:
- Name, description, category
- Optional image (uploaded via admin)
- Active/inactive status (soft delete)

### SKUs (Stock Keeping Units)
Each product has one or more SKU variants. A SKU represents a specific size + colour combination:
- Unique code (e.g., `CP-M-TC` = Classic Pot, Medium, Terracotta)
- Base price in Rands
- Stock quantity tracking
- Active/inactive status

### Categories
Products are grouped by category: Pots, Planters, Garden Beds, Accessories.

---

## Order Lifecycle

### Order Sources
Orders can be created from three entry points:
1. **Admin panel** — Admin creates orders directly
2. **Sales agent portal** — Public page, agent authenticates with their code
3. **Store portal** — Public page, store authenticates with their code

### Pricing
- Each SKU has a `base_price_rands`
- Clients and stores can be assigned a **Price Tier**
- Price tiers apply a discount percentage (e.g., Trade = 10%, Wholesale = 20%)
- Unit price at order time = `base_price × (1 - discount_percentage)`
- The unit price is snapshotted on the order item at creation time

### Order Statuses

```
pending_approval → approved → [in_production] → ready_for_delivery → out_for_delivery → completed
                 ↘ cancelled                                       → partially_delivered → completed
```

| Status | Description | Who triggers |
|--------|-------------|-------------|
| `pending_approval` | Order just created, awaiting review | Automatic on creation |
| `approved` | Order accepted, enters manufacturing demand | Admin |
| `in_production` | Manufacturing has started (informational) | System |
| `ready_for_delivery` | All items manufactured AND allocated | System |
| `out_for_delivery` | Dispatched to delivery team | Admin assigns team |
| `partially_delivered` | Some items delivered, some outstanding | Delivery team |
| `completed` | All items fully delivered | Delivery team |
| `cancelled` | Order cancelled, inventory returned | Admin |

### Order Items
Each order contains line items with these quantity fields:
- `quantity_ordered` — How many the customer wants
- `quantity_manufactured` — How many have been produced
- `quantity_allocated` — How many are reserved from inventory (FIFO)
- `quantity_delivered` — How many have been physically delivered

---

## Manufacturing Lifecycle

### Outstanding Demand
When an order is **approved**, its items become **outstanding demand**. The admin manufacturing page aggregates demand by SKU across all approved orders.

Outstanding for a SKU = `SUM(quantity_ordered - quantity_allocated)` across approved orders.

### Daily Manufacturing Plan
The admin creates a daily manufacturing plan:
1. View outstanding demand (aggregated by SKU)
2. Select which SKUs to manufacture and how many
3. Create the day's plan

The plan is a **snapshot** — it doesn't auto-update during the day.

### Moulding (Factory Floor)
Factory workers access the moulding page using their team code:
1. See today's plan items
2. Record completed quantities for each SKU
3. Completion triggers:
   - Inventory is added (`quantity_on_hand` increases)
   - FIFO allocation runs (allocates new inventory to oldest approved orders)
   - `quantity_manufactured` updates on corresponding order items

### Legacy Manufacturing Endpoint
Individual order items can also have `quantity_manufactured` updated directly via the manufacturing queue. This is used for order-level tracking alongside the daily plan approach.

---

## Inventory & FIFO Allocation

### Inventory Model
Each SKU has a global `InventoryItem` record with `quantity_on_hand`.

### When Inventory Increases
Manufacturing completion (via daily plan or direct update) adds to inventory.

### FIFO Allocation Algorithm
When new inventory is available:
1. Get all **approved** orders, sorted by `created_at` ascending (oldest first)
2. For each order item matching the SKU:
   - Calculate `need = quantity_ordered - quantity_allocated`
   - Allocate `min(need, available_inventory)`
   - Update `order_item.quantity_allocated`
   - Decrement `inventory.quantity_on_hand`

### When Inventory Decreases
Order cancellation returns allocated inventory:
- `quantity_allocated` is reset to 0 on all items
- Returned quantity is added back to `inventory.quantity_on_hand`
- FIFO allocation re-runs to redistribute

---

## Delivery Lifecycle

### Readiness Check
An order is **ready for delivery** when ALL items satisfy:
- `quantity_manufactured >= quantity_ordered`
- `quantity_allocated >= quantity_ordered`

### Delivery Queue
The delivery queue shows orders that are:
- In status: `approved`, `ready_for_delivery`, or `partially_delivered`
- Pass the readiness check
- Have remaining items to deliver

### Delivery Teams
- Teams are managed by admin (e.g., "Johannesburg North")
- Each team has members and a unique code
- Teams are assigned to orders by admin

### Delivery Outcomes

| Outcome | Effect |
|---------|--------|
| **Delivered** | All items set to `quantity_delivered = quantity_ordered`. Order → `completed`. |
| **Partial** | Specific items updated with partial quantities. Order → `partially_delivered`. Reason recorded. |
| **Not Delivered** | No quantity changes. Reason recorded. Order stays in queue. |

### Delivery Status (on order)
- `outstanding` — Not yet delivered
- `delivered` — Fully delivered
- `partial` — Some items delivered
- `not_delivered` — Delivery attempted but failed

---

## Entities Reference

### Price Tiers
Discount levels assigned to clients and stores:
- **Retail** (0%) — No discount
- **Trade** (10%) — Small trade customers
- **Wholesale** (20%) — Bulk orders
- **VIP Partner** (25%) — Long-term partners

### Clients
B2B customers who place orders through sales agents. Each client has:
- Name, address
- Assigned price tier
- Created by (user who added them)

### Stores
Retail/online stores that place orders independently:
- Name, code (for authentication)
- Store type (shopify, nursery, etc.)
- Optional price tier

### Sales Agents
Field sales representatives with unique codes:
- Used for public order entry authentication
- Linked to orders they create

### Delivery Teams
Logistics teams with members:
- Unique team code (for public delivery portal)
- Multiple members per team

### Factory Teams
Manufacturing floor teams:
- Unique team code (for moulding portal)
- Members have individual codes for authentication

---

## Key Workflows

### Admin: Approve an Order
1. Navigate to Orders → find pending order
2. Click Approve
3. Order moves to `approved`, items enter manufacturing demand

### Admin: Create Manufacturing Plan
1. Navigate to Manufacturing
2. View outstanding demand by SKU
3. Add SKUs to today's plan
4. Factory workers can now see the plan on the moulding page

### Factory Worker: Complete Moulding
1. Enter factory code on moulding page
2. See today's plan items
3. Update completed quantities
4. Backend auto-updates inventory + allocation

### Admin: Assign Delivery
1. Navigate to order detail
2. Select delivery team
3. Set delivery date if needed

### Delivery Team: Record Delivery
1. Enter team code on delivery page
2. See assigned orders for today
3. Mark as Delivered, Partial, or Not Delivered
4. Order status updates automatically

---

## API Structure

All endpoints under `/api/v1/`:

| Group | Prefix | Auth | Description |
|-------|--------|------|-------------|
| Auth | `/auth` | Mixed | Login, refresh, profile |
| Products | `/products` | Protected | CRUD + image upload + SKU management |
| Orders | `/orders` | Protected | CRUD + status + delivery assignment |
| Clients | `/clients` | Protected | CRUD |
| Stores | `/stores` | Admin | CRUD |
| Price Tiers | `/price-tiers` | Protected | CRUD + usage check |
| Manufacturing | `/manufacturing` | Mfg/Admin | Queue, outstanding, daily plans |
| Moulding | `/moulding` | Mfg | Today's plan, completion recording |
| Delivery | `/delivery` | Del/Admin | Queue, complete, partial |
| Sales Agents | `/sales-agents` | Admin | CRUD |
| Delivery Teams | `/delivery-teams` | Admin | CRUD + members |
| Factory Teams | `/factory-teams` | Admin | CRUD + members |
| Public | `/public` | None | Orders, products, moulding, delivery |

### Response Envelope
All responses use: `{ "data": T, "pagination": { "total", "page", "size" } }`

### Authentication
- JWT tokens (access: 15 min, refresh: 7 days)
- Access token in `Authorization: Bearer <token>` header
- Public endpoints require team/agent codes instead

---

## Database Schema (Key Relationships)

```
User ──→ Client (created_by)
       ──→ Order (created_by)

PriceTier ──→ Client (tier_id)
           ──→ Store (price_tier_id)

Product ──→ SKU[] (product_id)

SKU ──→ OrderItem (sku_id)
     ──→ InventoryItem (sku_id, unique)
     ──→ ManufacturingDayItem (sku_id)

Order ──→ OrderItem[] (order_id, cascade delete)
       ──→ Client (client_id, nullable)
       ──→ Store (store_id, nullable)
       ──→ SalesAgent (sales_agent_id, nullable)
       ──→ DeliveryTeam (delivery_team_id, nullable)

ManufacturingDay ──→ ManufacturingDayItem[] (manufacturing_day_id, cascade delete)
```

---

## Development Reference

### Running Locally
```bash
# Start database
docker compose up -d

# Start API (from apps/api)
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude '.venv'

# Start frontend (from apps/web)
pnpm dev

# Seed demo data (from apps/api)
python -m scripts.seed_full_demo
```

### Key Files
| File | Purpose |
|------|---------|
| `apps/api/app/models/` | SQLAlchemy models |
| `apps/api/app/services/` | Business logic |
| `apps/api/app/routers/` | API endpoints |
| `apps/api/app/schemas/` | Pydantic validation |
| `apps/web/lib/api.ts` | Frontend API client |
| `apps/web/lib/auth.tsx` | Auth context & hooks |
| `apps/web/types/index.ts` | TypeScript interfaces |
