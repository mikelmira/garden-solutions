# Manufacturing Views Implementation Guide

## Overview
This document outlines the implementation of the Manufacturing UI for Sprint 2. The goal is to allow factory users to view approved orders and track manufacturing progress.

## Routes
- `/manufacturing-dashboard` (Protected, Role: Manufacturing)

## Views

### 1. Dashboard (`/manufacturing-dashboard`)
#### Summary Widgets
- **Total Outstanding Items**: Sum of (quantity_ordered - quantity_manufactured) for all items in "Approved" orders.
- **Active Orders Count**: Count of orders with status "Approved" or "In Production".

#### Filters
- **Search**: Client Name
- **Date**: Delivery Date range
- **StatusFilter**: "Approved", "In Production" (default: "Approved")

#### Order List (Accordion/Card Layout)
Display orders matching filters.
- **Header**:
  - Client Name
  - Delivery Date (formatted)
  - Order ID (short)
  - Status Badge
  - Progress Bar (Manufactured / Total Items)

- **Expanded Content (Items Table)**:
  - Columns:
    - Product / SKU (Code + Name + Size/Color)
    - Ordered (Qty)
    - Manufactured (Current Qty)
    - Remaining (Calculated)
    - Actions:
      - Input: Increment Qty (or Absolute Set - TBD based on API)
      - Button: "Mark Manufactured" / "Update"

## Components
- `ManufacturingDashboard`: Main container, fetching data and managing state.
- `ManufacturingStats`: Widget component.
- `ManufacturingOrderList`: List of orders.
- `ManufacturingOrderItem`: Row for an individual item with update logic.

## API Integration
- **Fetch Queue**: `GET /api/v1/manufacturing/queue`
  - Returns approved orders with items including `item.id`
  - Status values are lowercase (e.g., `approved`, `pending_approval`)
  - Frontend maps to display format via `api.ts`
- **Update Item**: `PATCH /api/v1/order-items/{id}/manufactured`
  - Uses `item.id` (NOT `sku_id`) as the path parameter
  - Body: `{ "quantity_manufactured": <new absolute total> }`
  - Rules (enforced server-side):
    - `0 <= quantity_manufactured <= quantity_ordered`
    - Monotonically increasing (cannot decrease)
    - Does NOT change Order.status
    - Creates AuditLog entry atomically

## Design System
- Use `shadcn/ui` components: `Card`, `Table`, `Badge`, `Progress`, `Button`, `Input`, `Accordion` (or Collapsible).
