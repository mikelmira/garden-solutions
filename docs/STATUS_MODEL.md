# Status Model

## 1. Order Status Lifecycle
The `Order` entity tracks the high-level progress of a sale.

### Statuses
1.  **Draft**: Locally created on device, not yet synced or finalized.
2.  **Pending Approval**: Synced to server, waiting for Admin review.
3.  **Approved**: Confirmed by Admin. Ready for manufacturing.
4.  **In Production**: Manufacturing has marked at least one item as started/complete.
5.  **Ready for Delivery**: All items are manufactured.
6.  **Out for Delivery**: Handover to delivery team.
7.  **Partially Delivered**: Some items delivered, others outstanding details recorded.
8.  **Completed**: All items delivered.
9.  **Cancelled**: Terminated by Sales (if Draft/Pending) or Admin.

### Valid Transitions
- `Draft` -> `Pending Approval`
- `Pending Approval` -> `Approved` OR `Cancelled`
- `Approved` -> `In Production` (Automatic trigger when mfg starts)
- `In Production` -> `Ready for Delivery` (Automatic when all items mfg complete)
- `Ready for Delivery` -> `Out for Delivery`
- `Out for Delivery` -> `Partially Delivered` OR `Completed`
- `Partially Delivered` -> `Completed`

**V1 Backend Note**: In the current backend, delivery readiness and delivery completion are **derived** from `OrderItem` counters. No automatic status mutation is performed for manufacturing or delivery.

## 2. OrderItem Status / Tracking
Items are not just "status labels"; they track numeric progress. Status is derived from quantities.

### Logic
- **Pending**: `quantity_manufactured` = 0
- **Manufacturing**: `quantity_manufactured` > 0 AND `quantity_manufactured` < `quantity_ordered`
- **Manufactured**: `quantity_manufactured` == `quantity_ordered`
- **Delivered**: `quantity_delivered` == `quantity_ordered`

**Critical Rule**: An item is considered "Outstanding" if `quantity_ordered` > `quantity_delivered`.

## 3. Delivery Status
The `DeliveryAssignment` entity tracks the logistics event.
- **Scheduled**: Assigned to a driver.
- **In Transit**: Driver has left the depot.
- **Completed**: Delivery run finished (successfully or with issues).
- **Failed**: Could not complete run (e.g., breakdown).

## 4. Server Authority (V1)
- **Admin Only**: Only Admin can change status to `Approved` or `Cancelled` via explicit endpoints.
- **System Only**: `In Production`, `Ready for Delivery`, `Partially Delivered`, and `Completed` are **derived statuses**.
    - Clients cannot set these directly.
    - The Server calculates them based on `OrderItem` counters (`manufactured`, `delivered`).
