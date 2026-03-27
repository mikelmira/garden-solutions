# Data Model

## 1. Overview
This document defines the logical entities and relationships for the V1 Garden Solutions system. It is implementation-agnostic but maps directly to the PostgreSQL schema.

## 2. Core Entities

### User
Represents a system user (staff).
- **id** (PK): UUID
- **email**: String (Unique, Required)
- **full_name**: String (Required)
- **role**: Enum (Admin, Sales, Manufacturing, Delivery) (Required)
- **is_active**: Boolean (Default: true)
- **hashed_password**: String (Required)

### PriceTier
Defines the global discount structures.
- **id** (PK): UUID
- **name**: String (e.g., "Tier A", "Tier B", "Tier C") (Unique, Required)
- **discount_percentage**: Decimal (Required) — A value of 0.10 means 10% discount.

### Client
Represents the B2B customer.
- **id** (PK): UUID
- **name**: String (Required)
- **contact_person**: String (Optional)
- **contact_number**: String (Optional)
- **address**: Text (Required)
- **price_tier_id**: FK -> PriceTier.id (Required)
- **sales_agent_id**: FK -> User.id (Optional) — Assigned sales rep.

### Product
Top-level product definition (e.g., "Classic Pot").
- **id** (PK): UUID
- **name**: String (Required)
- **description**: Text (Optional)
- **category**: String (Optional)
- **is_active**: Boolean (Default: true)

### SKU (Variant)
Specific sellable unit (e.g., "Classic Pot - Large - Terracotta").
- **id** (PK): UUID
- **product_id**: FK -> Product.id (Required)
- **code**: String (Unique, Required) — e.g., "CP-L-TC"
- **size**: String (Required)
- **color**: String (Required)
- **base_price_rands**: Decimal (Required) — The standard price before discount.
- **stock_quantity**: Integer (Required) — Current physical stock.

### Order
The header record for a B2B sale.
- **id** (PK): UUID
- **client_id**: FK -> Client.id (Required)
- **created_by**: FK -> User.id (Required) — Who created the order. *(Sprint 1.1 alignment)*
- **created_at**: Timestamp (Required)
- **delivery_date**: Date (Required) — default: created_at + 14 days.
- **status**: Enum (Use StatusModel) (Required)
- **total_price_rands**: Decimal (Required) — Snapshot of total value at time of order.
- **notes**: Text (Optional)

### OrderItem
Line items within an order.
- **id** (PK): UUID
- **order_id**: FK -> Order.id (Required)
- **sku_id**: FK -> SKU.id (Required)
- **quantity_ordered**: Integer (Required)
- **quantity_manufactured**: Integer (Default: 0)
- **quantity_delivered**: Integer (Default: 0)
- **unit_price_rands**: Decimal (Required) — Snapshot of price after tier discount.

### DeliveryAssignment
Grouping of specific item quantities for a delivery run.
- **id** (PK): UUID
- **order_id**: FK -> Order.id (Required) — **V1 Constraint**: One assignment = One Order.
- **user_id**: FK -> User.id (Required) — The driver/delivery agent.
- **scheduled_date**: Date (Required)
- **status**: Enum (Scheduled, In Transit, Completed, Failed)
- **vehicle_reg**: String (Optional)

### DeliveryEvent
Record of a physical delivery or partial delivery action.
- **id** (PK): UUID
- **delivery_assignment_id**: FK -> DeliveryAssignment.id (Required)
- **order_id**: FK -> Order.id (Required)
- **sku_id**: FK -> SKU.id (Required)
- **quantity_delivered**: Integer (Required)
- **received_by_name**: String (Required)
- **notes**: Text (Optional) — Reason for partial/shortage.
- **timestamp**: Timestamp (Required)

### AuditLog
System-wide audit trail.
- **id** (PK): UUID
- **user_id**: FK -> User.id (Optional) — System actions may be null.
- **action**: String (Required) — e.g., "ORDER_UPDATE", "PRICE_CHANGE".
- **entity_type**: String (Required) — e.g., "Order".
- **entity_id**: UUID (Required)
- **changes**: JSON (Optional) — Diff of before/after.
- **timestamp**: Timestamp (Required)
