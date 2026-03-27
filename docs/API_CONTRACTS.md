# API Contracts

## 1. REST Principles
- **Resources**: Nouns, pluralized (`/orders`, `/products`).
- **Verbs**:
  - `GET`: Retrieve. Idempotent.
  - `POST`: Create. Non-idempotent (unless Idempotency Key used).
  - `PUT`: Full Replace.
  - `PATCH`: Partial Update (Preferred for status changes).
  - `DELETE`: Remove (Soft delete for V1 entities like Orders/Products).

## 2. Naming Conventions
- **URL**: Kebab-case (`/order-items`).
- **JSON Fields**: Snake_case (`user_id`, `created_at`).
  - *Reasoning*: Matches Python/DB naming, avoids hydration mapping overhead. Frontend can handle snake_case easily.
- **Query Params**: Snake_case (`?delivery_date=2023-01-01`).

## 3. Standard Response Shapes

### Success (Single)
```json
{
  "data": { "id": "...", ... },
  "meta": { ... } // Optional
}
```

### Success (List)
```json
{
  "data": [ ... ],
  "pagination": {
    "total": 100,
    "page": 1,
    "size": 20
  }
}
```

### Error
All API errors conform to the format defined in `ERROR_HANDLING_AND_RECOVERY.md`.

```json
{
  "code": "STOCK_ERROR",
  "detail": "Product X is discontinued.",
  "trace_id": "abc-123"
}
```

## 4. Authentication
- **Header**: `Authorization: Bearer <token>`
- **401 Unauthorized**: Missing or invalid token.
- **403 Forbidden**: Valid token, but Role not allowed.

## 5. Versioning
- **URL Route**: `/api/v1/...`
- **Breaking Changes**: Require `/api/v2/...`.
- **Non-Breaking**: Additive fields allowed in V1.

## 6. Example Endpoints

### Orders
- `GET /api/v1/orders` (Filterable by status, date, client).
- `GET /api/v1/orders/{id}`
- `POST /api/v1/orders`
- `PATCH /api/v1/orders/{id}/status`
  - Body: `{ "status": "APPROVED" }`

### Sync
- `POST /api/v1/sync/outbox`
  - Processes a batch of offline mutations.
- `GET /api/v1/sync/inbox`
  - Returns entities changed since `?last_sync_timestamp`.
