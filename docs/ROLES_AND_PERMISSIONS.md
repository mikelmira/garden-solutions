# Roles and Permissions

## 1. Role Definitions
There are four distinct roles in the system. A user can hold only one role.

### Admin
- **Scope**: Superuser access.
- **Purpose**: Manage the business, master data, and exceptions.

### Sales
- **Scope**: Field agents.
- **Purpose**: Capture orders and manage client relationships.

### Manufacturing
- **Scope**: Factory floor.
- **Purpose**: View production requirements and update manufacturing progress.

### Delivery
- **Scope**: Logistics.
- **Purpose**: View assigned routes and record successful deliveries.

## 2. Permissions Matrix

| Feature / Resource       | Admin         | Sales                  | Manufacturing | Delivery               |
| ------------------------ | ------------- | ---------------------- | ------------- | ---------------------- |
| **All Orders**           | View / Edit   | View (Own Only)        | View (Read-Only) | View (Assigned Only) |
| **Order Creation**       | Yes           | Yes                    | No            | No                     |
| **Order Approval**       | Yes           | No                     | No            | No                     |
| **Cancel Order**         | Yes           | Yes (Draft/Pending Only) | No            | No                     |
| **View Pricing**         | Yes           | Yes                    | No            | No                     |
| **Edit Pricing/Tiers**   | Yes           | No                     | No            | No                     |
| **Client Management**    | Create / Edit | View List              | No            | View (Assigned delivery) |
| **Product/SKU Catalogue**| Create / Edit | View                   | View          | View                   |
| **Update Manufacturing** | Yes           | No                     | Yes           | No                     |
| **Assign Delivery**      | Yes           | No                     | No            | No                     |
| **Update Delivery**      | Yes           | No                     | No            | Yes                    |
| **User Management**      | Yes           | No                     | No            | No                     |
| **Audit Logs**           | View          | No                     | No            | No                     |

## 3. Explicit Restrictions
- **Sales** agents strictly cannot see orders belonging to other agents.
- **Sales** cannot see or modify delivery assignments.
- **Sales** can only see effective prices (no base price or formulas).
- **Manufacturing** has no visibility of pricing or client discounts.
- **Delivery** agents cannot alter the contents of an order, only the status of the delivered items.
