# Data Lifecycle

## 1. Order Lifecycle
An `Order` is the central aggregate root.

1.  **Creation**: Born as `Draft` (Offline) or `Pending Approval` (Online).
    - Immutable Snapshot: `unit_price_rands` is copied from Catalogue to OrderItem at this moment. Future price changes do **not** affect existing orders.
2.  **Approval**: Admin validates. Status -> `Approved`.
    - **Edit Lock**: Once `Approved`, Line Items (Quantity/SKU) cannot be changed effortlessly. To change, Admin must revert to `Pending Approval` first (if manufacturing hasn't started).
3.  **Production**: As items are made, `quantity_manufactured` increases.
    - Status -> `In Production` (Any item > 0).
    - Status -> `Ready for Delivery` (All items == ordered).
4.  **Delivery**:
    - **Partial**: Driver delivers 5/10. Status -> `Partially Delivered`. Remaining 5 are "Outstanding".
    - **Final**: Driver delivers remaining 5. Status -> `Completed`.

## 2. Order Item Lifecycle
Items are stateful counters, not just rows.
- `quantity_ordered`: Rigid after approval.
- `quantity_manufactured`: Monotonically increasing. Cannot exceed `quantity_ordered`.
- `quantity_delivered`: Monotonically increasing. Cannot exceed `quantity_manufactured`.

## 3. Delivery Event Lifecycle
A `DeliveryEvent` is an **append-only** record.
- We do not "update" a delivery record. We create a new event.
- If a driver makes a mistake, they (or Admin) create a *correction* event (negative quantity adjustments are rare; usually Admin fixes via direct database intervention in V1, or we rely on explicit "Return" flows in V2).
- **V1 Rule**: Drivers cannot "Undo". They must call Admin to fix data entry errors.

## 4. Deletion Rules
- **Hard Delete**: Permitted for `Draft` orders that were never synced.
- **Soft Delete**:
  - `Products` (marked `is_active=False`).
  - `Users` (marked `is_active=False`).
  - `Clients` (marked `is_active=False`).
- **Never Delete**:
  - `Orders` (Once synced/approved).
  - `AuditLogs`.
  - `DeliveryEvents`.

## 5. Rescheduling
If a delivery fails:
1.  Assignment Status -> `Failed`.
2.  Order Status remains `Ready for Delivery` (or `Partially Delivered`).
3.  Admin creates **New Assignment** for a future date.
4.  Data is preserved; history shows one failed attempt and one pending attempt.
