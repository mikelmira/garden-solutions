# User Flows

## 1. Sales Order Capture (Mobile/Offline)
**Actor**: Sales Agent

1.  **Select Client**: Agent selects a client from the cached list on their device.
2.  **View Catalogue**: Agent browses products. Pricing displayed is specific to the selected Client's `PriceTier`.
3.  **Build Cart**: Agent adds SKUs and quantities to the cart.
4.  **Confirm Details**: Agent sets the requested Delivery Date (default: today + 14 days).
5.  **Submit**:
    - *If Online*: Order is posted to API immediately. Status -> `Pending Approval`.
    - *If Offline*: Order is saved to local Outbox. Status -> `Draft` (locally).
6.  **Sync (Automatic)**: When connectivity returns, app posts the order. Status -> `Pending Approval`.

## 2. Order Approval
**Actor**: Admin

1.  **Review**: Admin opens the "Pending Orders" list.
2.  **Inspect**: Admin views Order details, checks Client credit standing (manual process outside system), and validates stock feasibility.
3.  **Decision**:
    - *Approve*: Status -> `Approved`. Manufacturing dashboard receives visibility.
    - *Reject/Clarify*: Admin contacts Sales Agent (offline comms) or edits order details, then Approves.
    - *Cancel*: Status -> `Cancelled`.

## 3. Manufacturing Completion
**Actor**: Manufacturing Staff

1.  **View Queue**: Staff views "Production Queue" (Orders with Status `Approved` or `In Production`).
2.  **Update Item**: Staff selects an Order, expands the Item list.
3.  **Log Output**: Staff increments `quantity_manufactured` for a specific SKU.
    - *Transition*: If this is the first item made, Order Status -> `In Production`.
4.  **Complete Order**: When all items have `quantity_manufactured == quantity_ordered`, Order Status -> `Ready for Delivery`.

## 4. Delivery Assignment
**Actor**: Admin / Logistics Manager

1.  **Plan Run**: Admin views "Ready for Delivery" orders.
2.  **Create Assignment**: Admin creates a new Delivery Assignment for a **single order**.
3.  **Assign Driver**: Admin sets Driver and Date.
4.  **Dispatch**: Admin marks Assignment as `In Transit`.

## 5. Delivery Execution (Mobile/Offline)
**Actor**: Delivery Driver

1.  **View Run**: Driver opens "My Deliveries" for the day.
2.  **Arrive**: Driver arrives at Client site.
3.  **Confirm Quantities**: For each item, Driver confirms the quantity physically handing over.
    - *Full*: Inputs full Expected Quantity.
    - *Partial*: Inputs lower quantity. **MUST** select a Reason (e.g., "Damaged", "Refused", "Shortage") and add Note.
4.  **Proof of Delivery**: Driver enters "Received By" name (Required).
5.  **Submit**:
    - Status updates to `Completed` if full delivery.
    - Status updates to `Partially Delivered` if items remain outstanding.
    - Syncs when online.
