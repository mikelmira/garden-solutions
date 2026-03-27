# Offline Sync Implementation

## 1. Client-Side Queue Model
We use **IndexedDB** to persist mutations when offline.
**Table**: `mutation_queue`
- `id`: Auto-incrementing Integer (Ensures FIFO ordering).
- `uuid`: String (UUID v4) - **Idempotency Key**.
- `type`: String (e.g., "CREATE_ORDER", "UPDATE_DELIVERY").
- `payload`: JSON Object.
- `createdAt`: Timestamp.
- `retryCount`: Integer (Default 0).

## 2. Sync Triggers
1.  **Network Event**: `window.addEventListener('online', ...)`
2.  **User Trigger**: "Sync Now" button in UI.
3.  **Background Interval**: Every 5 minutes (if tab active).
4.  **Immediate**: Attempt to sync immediately after a mutation is added (optimistic attempt).

## 3. The Outbound Sync Loop
The `SyncManager` executes strictly serially:
1.  **Peppering**: Check if queue has items.
2.  **Lock**: Ensure only one sync process runs at a time.
3.  **Process Item**:
    - Take the *oldest* item (`id: min`).
    - Send `POST /api/v1/sync/outbox` with `{ type, payload, uuid }`.
    - **Success (2xx)**: Delete item from queue. Repeat loop.
    - **Transient Failure (5xx, Network Error)**: Increment `retryCount`. Backoff. **Stop Queue Processing**.
    - **Terminal Failure (400 Bad Request)**:
        - **Quarantine**: Move item to a `failed_mutations` table.
        - **Alert**: Show user "Action Failed".
        - **Continue**: Proceed to next item. (Critical decision: Don't block valid subsequent actions if an isolated 400 occurs, but be careful of dependencies).

## 4. Conflict Resolution
- **Strategy**: Server Authority.
- **Scenario**: Two users edit same Order.
  - User A is Online: Updates Status to `Approved`.
  - User B is Offline: Updates Status to `Cancelled`.
  - User B syncs later.
- **Handling**:
  - API receives User B's "Cancel".
  - Service Logic checks: "Is current status transitionable to Cancelled from Approved?"
  - If No: Returns 400. Sync Engine treats as **Terminal Failure**. User B is notified "Update Rejected: Order is already Approved".

## 5. Blocked Offline Actions
Some actions strictly require a connection and are disabled in the UI when `!isOnline`:
- User Login (Initial).
- Admin Approvals (Require real-time stock check).
- User Management (Creating new users).
