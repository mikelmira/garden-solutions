# Error Handling and Recovery

## 1. API Error Standards
Rest API returns **Problem Details for HTTP APIs (RFC 7807)** style responses where possible, or a simplified JSON.

```json
{
  "code": "STOCK_ERROR",
  "detail": "Product X is discontinued.",
  "trace_id": "abc-123"
}
```

- **400**: Bad Request (Client Logic Error).
- **401**: Unauthorized (Not logged in).
- **403**: Forbidden (Role mismatch).
- **404**: Not Found.
- **409**: Conflict (Optimistic lock failure / State mismatch).
- **500**: Internal Server Error (Bug).

## 2. Offline Failure Scenarios
- **Transient**: Network timeout.
  - **Action**: Retry exponentially (2s, 4s, 8s...). Keep in Queue.
- **Terminal**: Logic Error (e.g. invalid SKU ID).
  - **Action**:
    - Remove from active queue.
    - Move to "Dead Letter Queue" (Failed Mutations).
    - **Alert User**: "Order #123 failed to sync. Please contact support."

## 3. Sync Failure Recovery
If a Sync Batch fails mid-way:
- **Atomic Batches**: Not implemented in V1. Requests are individual.
- **Recovery**:
  - Item 1 succeeds (Removed from Q).
  - Item 2 fails (Remains in Q).
  - Item 3 is blocked (FIFO rule).
- **Unlock**: User must be prompted to "Delete Failed Item" or "Retry" to unblock the queue.

## 4. User-Visible Errors
- **Principle**: Never show raw SQL errors or Stack Traces.
- **UI**: Show toast notifications ("Saved successfully", "Connection lost", "Error submitting order").
