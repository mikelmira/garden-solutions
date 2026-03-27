# Product Requirements (V1)

## 1. Goal
To build a robust, offline-capable B2B ordering and fulfilment system for Garden Solutions that streamlines operations from sales capture to delivery.

## 2. V1 Scope
The V1 release focuses strictly on the core operational loop:
1.  **Sales Agents** capturing orders on-site at nurseries (often offline).
2.  **Admins** approving orders and managing exceptions.
3.  **Manufacturing** tracking production at the item level.
4.  **Delivery Teams** fulfilling orders (fully or partially) and recording proof of delivery.

## 3. Explicit Non-Goals (Out of Scope for V1)
- **No B2C Interface**: The system is strictly for internal staff and sales agents.
- **No Payments**: All financial transactions happen outside this system.
- **No Notifications**: Email/SMS notifications are not included in V1.
- **No Dynamic Pricing**: Prices are fixed per SKU with standard tier-based discounts.
- **No Customer Portal**: Clients do not log in.

## 4. User Roles
- **Admin**: Full system access; approves orders; manages master data (Products, Users, Clients).
- **Sales**: Creates orders; views own order history; view-only access to catalogue.
- **Manufacturing**: Views production queues; updates item status.
- **Delivery**: Views delivery schedules; updates delivery status; handles partial deliveries.

## 5. Key Success Criteria
- **data Integrity**: No lost orders, even if captured offline.
- **Inventory Accuracy**: Exact tracking of what has been delivered vs. what is outstanding.
- **Operational Efficiency**: Reduction in manual paperwork and phone coordination.
- **Usability**: Mobile-friendly interfaces for Sales and Delivery staff.
