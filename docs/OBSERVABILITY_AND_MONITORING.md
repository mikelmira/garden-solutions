# Observability and Monitoring

## 1. What Must Be Logged (Backend)
- **Application Logs**:
  - Startup/Shutdown events.
  - All Unhandled Exceptions (Include Stack Trace).
  - Warnings for "Soft Failures" (e.g., Sync Item Rejected).
- **Access Logs**:
  - HTTP Method, Path, Status Code, Duration.

## 2. Audit Logs vs Operational Logs
- **Audit Logs** (`audit_logs` table):
  - **Business Domain**: "Who changed Order price?"
  - **Permanent**: Lives in DB forever.
  - **Viewer**: Admin Users.
- **Operational Logs** (Stdout/CloudWatch):
  - **Tech Domain**: "Why did the DB connection timeout?"
  - **Ephemeral**: Retained for 30 days.
  - **Viewer**: DevOps/Engineers.

## 3. Critical Failure Signals
Monitor these signs of doom:
1.  **Queue depth backing up**: If `sync/outbox` calls drop to 0 but `orders` are not increasing.
2.  **500 Error Spikes**: Backend logic is broken.
3.  **Disk Space**: Database running out of storage.

## 4. Client-Side Monitoring
- **Sentry/LogRocket** (or equivalent):
  - Capture JS crashes in the field (Sales agents).
  - Capture "Failed Mutation" details (payloads that caused 400s).
