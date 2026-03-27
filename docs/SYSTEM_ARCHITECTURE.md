# System Architecture (Technical)

## 1. High-Level Diagram Description

The system implements a **Local-First, Sync-Based Architecture**.

1.  **Frontend Clients (Next.js)**: Act as the primary interface. For Sales and Delivery, they function as "Thick Clients" that maintain a local replica of necessary data (IndexedDB) and an operation queue for mutations.
2.  **API Gateway (FastAPI)**: The single entry point for all client requests. It handles authentication, request validation, and routes traffic to internal services (conceptually monolithic for V1, structured as modules).
3.  **Database (PostgreSQL)**: Truth source. Accessed solely via the API Layer.
4.  **Sync Engine**: A logical component spanning Frontend and Backend. Frontend pushes "Actions" (commands); Backend processes them and returns "Events" or "State Snapshots".

## 2. Frontend ↔ API Interaction

### Online Repositories (Admin/Mfg)
- **Pattern**: Standard REST (Request/Response).
- **Caching**: SWR / TanStack Query with standard invalidation.
- **Writes**: Direct POST/PUT/PATCH.
- **Optimistic UI**: Used for immediate feedback, rolled back on 4xx/5xx.

### Offline Repositories (Sales/Delivery)
- **Read**: Data is read from `IndexedDB` (using a wrapper like `Dexie.js` or `RxDB`).
- **Write**: Actions are written to a `MutationQueue` table in `IndexedDB`.
- **Sync Process**:
  1.  **Network Detected**: `SyncManager` wakes up.
  2.  **Push**: Iterates `MutationQueue`, sending items to `POST /api/sync/outbox`.
  3.  **Ack**: On 200 OK, item is removed from queue.
  4.  **Pull**: Client requests updates via `GET /api/sync/inbox?since_timestamp=X`.
  5.  **Merge**: Incoming data updates local `IndexedDB`.

## 3. Authentication & Authorization Flow

### Auth Strategy
1.  **Login**: `POST /api/auth/login` (email/password).
2.  **Token**: Server issues a specialized **JWT (JSON Web Token)**.
    - *Claims*: `user_id`, `role`, `schema_version`.
    - *Expiration*: Short-lived access token (15 mins), Long-lived refresh token (7 days).
3.  **Storage**:
    - Web: `HttpOnly` Secure Cookie (preferred for Admin).
    - Mobile/PWA: Secure Storage (or stored in IndexedDB if strictly necessary for offline headers, though Cookies preferred if PWA acts as browser). *Decision: Use Bearer Token stored in HttpOnly cookie for V1 simplicity, or standard Auth header if native wrapper used.* **V1 Decision: Bearer Token in LocalStorage to support offline request queuing easily.**

### Role Enforcement
- **Edge (Middleware)**: Checks for token presence.
- **Route Guard**: Helper `require_role(['admin'])` verifies token claims before executing logic.
- **Data Guard**: `get_orders(user)` filters SQL queries based on `user.role`.

## 4. System Boundaries

### App: `web`
- **Responsibility**: Rendering UI, routing, capturing user intent.
- **Forbidden**: Direct database access, business logic that bypasses the API.

### Package: `ui`
- **Responsibility**: "Dumb" components (Buttons, Inputs, Cards).
- **Forbidden**: Business logic, API calls, application state (Zustand/Redux), role checks.

### App: `api`
- **Responsibility**: Business rules, state transitions, data persistence.
- **Forbidden**: HTML generation, UI concerns.

## 5. Offline Sync Conceptual Flow
1.  **User Action**: "Submit Order #123".
2.  **Local Store**: `Order #123` saved with status `Draft`.
3.  **Queue**: `Action: CREATE_ORDER`, `Payload: { ... }`, `UUID: abc-123` saved to Queue.
4.  **Sync**:
    - POST `abc-123` to API.
    - API checks `UUID` (New?).
    - API validates Data.
    - API Transaction: Insert Order, Insert Audit Log.
    - API responds: `Success`.
5.  **Cleanup**: Client removes `abc-123` from Queue. Order status locally set to `Pending`.
