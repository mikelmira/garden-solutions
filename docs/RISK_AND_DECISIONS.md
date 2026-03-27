# Risks and Decisions

## 1. Key Architectural Decisions (ADRs)

### ADR-001: LocalStorage for Auth Tokens
- **Context**: We need to attach Auth headers to background Sync requests when the browser tab is closed/inactive (PWA context) or simply when the `SyncManager` runs. Cookie-based checks with external domains or strictly `HttpOnly` complicates the custom `fetch` wrapper needed for the Sync Engine.
- **Decision**: Store JWT in `LocalStorage`.
- **Trade-off**: Slightly higher XSS risk vs. significant simplification of Offline/Background sync logic.
- **Mitigation**: Very short token usage; strict Content-Security-Policy (CSP).
- **V1 Constraint**: This decision is locked for V1. Revisit in V2 only.

### ADR-002: No Optimistic "Approved" Status
- **Context**: Sales Agent creates order. Should it show "Approved" immediately?
- **Decision**: No. It shows "Draft" (Offline) -> "Pending Approval" (Online).
- **Reason**: "Approved" implies a promise of stock/manufacturing capability. Only the Server/Admin can make that promise.
- **Benefit**: Red/Green logic remains strictly on Server.

### ADR-003: Poll-based Inbound Sync
- **Context**: How do we get updates (e.g., "Order Approved") to the device?
- **Decision**: Polling (`GET /sync/inbox` every 5 mins).
- **Reason**: WebSockets are complex to maintain for a V1 MVP and drain battery. Polling is robust and sufficient for the latency requirements (15 mins is fine).

## 2. Technical Risks

### Risk: IndexedDB Quota
- **Description**: Browser wipes storage if disk is full.
- **Mitigation**: Warn user if storage is low (using `navigator.storage`). Critical data (Unsynced Mutations) is prioritized.

### Risk: Mobile Browser Sleeping
- **Description**: iOS Safari aggressively suspends background tabs. Sync might not run.
- **Mitigation**: Sync logic must trigger *immediately* on `visibilitychange` (app foregrounded). We accept that background sync on iOS is limited without a native wrapper.

### Risk: Partial Delivery Complexity
- **Description**: Users might screw up the math (Ordered 10, Delivered 3, Remaining 7).
- **Mitigation**: UI must calculate the "Remaining" value automatically. User only types "Quantity Delivered". System prevents "Quantity Delivered > Quantity Outstanding".
