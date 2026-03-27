# Roadmap (V1 & Beyond)

## 1. V1: Core Operational Loop (The Current Goal)
**Definition of Done**: A Sales Agent can assume a fresh iPad, log in, go to a remote nursery (Offline), sell 50 pots, and have that order tracked through manufacturing to final delivery signature.

### Milestone 1: Foundation
- [ ] Monorepo setup (Next.js + FastAPI).
- [ ] Database Schema & Alembic setup.
- [ ] Auth System (Login/Token).
- [ ] Product & Client Seeds.

### Milestone 2: Sales & Offline Sync (The Hardest Part)
- [ ] IndexedDB Wrapper (`packages/web/lib/db`).
- [ ] Sync Engine (Outbox Loop).
- [ ] Mobile Sales UI (Select Client -> Add Items -> Order).

### Milestone 3: Admin & Manufacturing
- [ ] Admin Dashboard (Approve/Reject).
- [ ] Manufacturing List (Update Item counts).

### Milestone 4: Delivery
- [ ] Assignment UI (Admin).
- [ ] Delivery Execution UI (Driver).
- [ ] Proof of Delivery logic.

## 2. V1 Exclusions (Explicitly Deferred)
- **Payment Processing**: Agents do not handle cash or cards.
- **Dynamic Pricing tiers**: Only standard A/B/C tiers allowed.
- **Route Optimization**: Drivers decide their own path; system just lists stops.
- **Reporting**: Basic CSV export only; no BI dashboards.

## 3. Future Buckets

### V1.1 (Stabilization)
- Email Notifications (Order confirmation).
- Forgot Password flow.
- Image uploads for "Damaged Goods". {Currently: text notes only}.

### V2 (Scaling)
- Client Portal (Clients order themselves).
- Inventory Management (Raw materials).
- Route Optimization Algorithms.
