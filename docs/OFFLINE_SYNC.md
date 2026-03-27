# Offline & Sync Strategy

## 1. Principles
The system follows an "Offline-First" approach for Sales and Delivery roles. This means the UI reads from a local cache by default and writes to a local queue, regardless of network status.

## 2. What Can Be Done Offline
- **Sales**:
  - View Client list (cached).
  - View Product Catalogue (cached).
  - Create new Orders.
  - View "My Orders" history (cached snapshot).
- **Delivery**:
  - View today's assigned manifest (cached upon morning sync).
  - Execute deliveries (record quantities, names, notes).

## 3. What Cannot Be Done Offline
- **Admin Functions**: Approvals, User management, Catalogue edits require an active connection.
- **Real-time Stock Checks**: Sales agents see "Last Known" stock, but cannot guarantee reservation until sync.

## 4. Sync Rules
1.  **Outbound Sync** (Client -> Server):
    - Triggered automatically when network creates connection.
    - Triggered manually via "Sync Now" button.
    - Queue is processed serially (FIFO) to maintain order of operations.
2.  **Inbound Sync** (Server -> Client):
    - Occurs on Login.
    - Occurs periodically (e.g., every 15 mins) when online.
    - Fetches Status updates on Orders.

## 5. Conflict Resolution
- **Last Write Wins** is NOT used for Status.
- **Server Authority**: If an Order was Cancelled by Admin while Sales Agent was offline editing it, the Server rejects the update with a specific error code ("Order Closed"). The Agent acts on the error manually.
- **Idempotency**: All offline actions carry a UUID generated on the client. If the network drops during a POST, retrying the same UUID ensures the server processes it only once.
