# Security and Access

## 1. Authentication Strategy
- **Mechanism**: JWT (JSON Web Token).
- **Algorithm**: HS256 (HMAC SHA-256).
- **Secrets**: `JWT_SECRET` must be rotated in production.
- **Client Handling**:
  - Token stored in `LocalStorage` (for offline support) or `HttpOnly Cookie`.
  - **V1 Decision**: `LocalStorage` is acceptable *only* because this is an internal B2B app with controlled devices, and it simplifies the "Queue" mechanism (Queue worker needs to inject header without browser cookie magic).
  - **Risk Mitigation**: Short expiry (15 mins) + Refresh Token rotation.
  - **V1 Lock**: Token storage strategy is not to be refactored during V1 delivery.

## 2. Role Enforcement Points
Security is "Defense in Depth".

1.  **Frontend (UI)**:
    - *Utility*: Hides buttons users shouldn't see (`<RoleGuard allowed={['admin']} ...>`).
    - *Security Level*: **Zero**. (Client code can be manipulated).

2.  **API Gateway (Middleware)**:
    - *Utility*: Rejects requests without valid signatures.
    - *Security Level*: **High**.

3.  **Service Layer (Business Logic)**:
    - *Utility*: "A Sales user implies filtering queries by `sales_agent_id = user.id`".
    - *Security Level*: **Critical**. This is where data leakage is prevented.
    - **Rule**: Never trust the ID in the URL body alone; verify it matches the User's allowed scope.

## 3. Audit Relevance
- **Accountability**: Every mutation is traced to a `user_id`.
- **Non-Repudiation**: The `AuditLog` is immutable.
- **Security Alerts**: Multiple failed login attempts must be logged.

## 4. Secrets Management
- **Repo**: NO secrets in Git.
- **Dev**: `.env.local` (Gitignored).
- **Prod**: Injected via Docker Env Vars or Secret Manager (AWS/GCP).
- **Leak Prevention**: Backend Pydantic settings should forbid extra fields to prevent accidental dumping of config objects.
