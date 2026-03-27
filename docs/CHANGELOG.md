# Changelog - Documentation Refinement

## 2026-01-30: V1 Constraints & Consistency Lock

### Data Model & Flows
- **DATA_MODEL.md**: Added strict V1 constraint: `DeliveryAssignment` is 1-to-1 with `Order`. Added `order_id` FK.
- **USER_FLOWS.md**: Updated Delivery Assignment flow to reflect single-order assignment.
- **API_REFERENCE.md**: Clarified that `/deliveries/today` returns Order Assignments, not multi-order runs.

### Status Logic
- **STATUS_MODEL.md**: Added "Server Authority" section. Explicitly banned clients from setting derived statuses (`In Production`, `Ready for Delivery`, etc.).
- **BACKEND_IMPLEMENTATION_GUIDE.md**: Restricted status endpoints to Admin-only (Approve/Cancel).
- **API_CONTRACTS.md**: Aligned status endpoint constraints with Backend Guide.

### Roles & Visibility
- **ROLES_AND_PERMISSIONS.md**: Explicitly restricted Sales pricing visibility to "Effective Price Only".
- **DASHBOARD_VIEWS.md**: Added pricing visibility notes for Sales View and Assignment linkage for Delivery View.

### Architecture & Security
- **RISK_AND_DECISIONS.md**: Locked `LocalStorage` decision for V1 (ADR-001).
- **SECURITY_AND_ACCESS.md**: Added V1 Lock on token storage strategy.

### Standardization
- **API_CONTRACTS.md**: Removed inline error definition; redirected to `ERROR_HANDLING_AND_RECOVERY.md` as the canonical source.
