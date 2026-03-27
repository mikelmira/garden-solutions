# Dashboard Views

## 1. Admin Dashboard
**Purpose**: High-level oversight and exception management.
**Visible Data**:
- Metric cards: Pending Approvals (Count), Active Production Orders, Deliveries Today.
- Recent Activity feed (Audit Log summary).
**Actions**:
- Navigate to: Order Management, Product Catalogue, Client List, User Management.

## 2. Sales View (Mobile Optimized)
**Purpose**: Rapid order entry and history tracking.
**Visible Data**:
- My Clients list.
- Product Catalogue (Read-only, with Tier pricing).
- **Note**: Sales sees effective tier-discounted prices only (no base price/formulas).
- My Recent Orders (Status, Date, Total).
**Actions**:
- "New Order" (Main CTA).
- Sync Status indicator (Online/Offline/Syncing).

## 3. Manufacturing View (Tablet/Desktop)
**Purpose**: Production tracking without clutter.
**Visible Data**:
- **Kanban or List**:
  - *To Do* (Approved Orders).
  - *In Progress* (Started).
  - *Complete* (Ready for Delivery).
- Order Detail expansion: Shows SKU images, Color, Size, and Quantity progress bars.
**Actions**:
- "Update Progress" (Increment Manufactured Quantity).
- No pricing data is visible here.

## 4. Delivery View (Mobile Optimized)
**Purpose**: Route execution and proof of delivery.
**Visible Data**:
- "Today's Route" (List of DeliveryAssignments, where each = 1 Order).
- Delivery Assignment details (Client Name, Address, Contact).
- Order Manifest (Items to unload).
**Actions**:
- "Start Delivery" (Opens manifest).
- "Complete Item" (Input quantity).
- "Finalize Delivery" (Input Received By, Notes).
- Offline indicator strictly visible.
