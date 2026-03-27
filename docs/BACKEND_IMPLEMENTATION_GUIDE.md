# Backend Implementation Guide

## 1. API Structure
- **Framework**: FastAPI.
- **Directory**:
  ```
  api/
  ├── main.py            # App entrypoint
  ├── routers/           # Route definitions (e.g. orders.py, auth.py)
  ├── services/          # Business logic (e.g. OrderService.place_order)
  ├── schemas/           # Pydantic models (DTOs)
  ├── models/            # SQLAlchemy database models
  └── core/              # Config, Security, Database connection
  ```

## 2. Layered Architecture Rules
1.  **Router**: Handles HTTP request, extracts params, calls Service. **NO Business Logic**.
2.  **Service**: Contains all business rules, orchestration, and commits transactions.
    - *Example*: `create_order` checks stock, calculates price, saves to DB.
3.  **Repository (Optional)**: Direct DB access. For V1, simple SQLAlchemy queries within Services is acceptable if DRY.

## 3. Validation
- **Input**: Strictly validated by **Pydantic Schemas**.
  - Reject unknown fields (`extra="forbid"`).
  - Use specific types (`EmailStr`, `PositiveInt`, `Decimal`).
- **Business Rule Validation**: Occurs in Service Layer.
  - E.g., "Cannot approve an order that is already cancelled."
  - Raise `HTTPException(400, detail="...")`.

## 4. Status Transition Enforcement
- **State Machine**: Status transitions must be strictly controlled.
- **Pattern**:
  - `verify_transition(current_status, new_status) -> bool`
  - If invalid, raise 400.
  - If invalid, raise 400.
  - Do NOT manually update status strings in random places. Use a dedicated `update_status` method.
  - **Constraint**: Status endpoints are Admin-only (Approve/Cancel). All other updates are derived from Item quantities.

## 5. Audit Logging Strategy
- **Requirement**: ALL write operations (POST, PUT, PATCH, DELETE) must create an `AuditLog` entry.
- **Mechanism**:
  - **Explicit**: `OrderService.update(...)` calls `AuditService.log(...)` within the same transaction.
  - **Context**: Pass the `current_user` to every service method to ensure authorship is recorded.
  - **Middleware**: Avoid generic middleware logging for business audits; it lacks context. Use explicit logging.

## 6. Idempotency for Offline Sync
- **Header**: Clients submitting offline actions send `X-Idempotency-Key` (UUID).
- **Check**:
  - Before processing, query `AuditLog` or a dedicated `IdempotencyStore`.
  - If Key exists: Return the *original* response (200 OK) without re-executing.
  - If Key new: Execute, then store Key.
