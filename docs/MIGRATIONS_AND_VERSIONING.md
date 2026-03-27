# Migrations and Versioning

## 1. Migration Rules (Alembic)
- **Never modify existing migrations**: Once merged to `main`, a migration file is immutable.
- **Down Revisions**: Every `upgrade()` must have a corresponding, tested `downgrade()`.
- **Naming**: `YYYYMMDD_HHMM_description_of_change.py`.

## 2. Backward Compatibility (The Offline Problem)
Sales agents might have an offline app with "Old Schema" logic while the server updates to "New Schema".
- **Rule**: New fields must be **Optional (Nullable)** in the database initially.
- **Rule**: Do not rename columns. Add new column -> Copy Data -> Deprecate old column.
- **Rule**: APIs must accept payloads missing the new field (defaulting safely).

## 3. Introducing New Statuses
If adding a status (e.g., `Returned`):
1.  Update `STATUS_MODEL.md`.
2.  Update Backend Enum definition.
3.  Add migration to update DB constraints (if using Postgres ENUM type).
    - *Tip*: Postgres ENUMs are hard to alter. Use `VARCHAR` with app-level validation or a Lookup Table for flexibility if statuses change often. **V1 Decision: App-level constants stored as VARCHAR**.

## 4. Rollback Principles
- **Code Rollback**: `git revert`.
- **DB Rollback**: `alembic downgrade -1`.
- **Data Protection**: If a migration destroys data (e.g., dropping a table), taking a snapshot (backup) immediately before deployment is mandatory.

## 5. Offline Sync Compatibility
- If the Server updates `orders` table structure:
  - Offline clients pushing old `CREATE_ORDER` payloads must still succeed.
  - The API Pydantic model must explicitly allow "missing" new fields and fill them with defaults.
