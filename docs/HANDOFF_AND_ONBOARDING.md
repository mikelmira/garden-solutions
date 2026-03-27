# Handoff and Onboarding

## 1. Operational Context
You are entering the **Garden Solutions V1** project. It is an Offline-First B2B ordering system.
It is **Monorepo** based (apps/web, apps/api).

### Key Routes (V1)
- **Admin Dashboard**: `/admin-dashboard`
- **Sales Dashboard**: `/sales-dashboard`
*Note: V2 may adopt nested routes (e.g. `/admin/*`), but V1 uses these explicit paths.*

## 2. Reading Order (Sequential)
1.  `PRODUCT_REQUIREMENTS.md` - What are we building?
2.  `SYSTEM_ARCHITECTURE.md` - How does it fit together?
3.  `OFFLINE_SYNC_IMPLEMENTATION.md` - The hardest technical part. Read twice.
4.  `DATA_LIFECYCLE.md` - How orders flow.
5.  `DEVELOPMENT_WORKFLOW.md` - How to contribute.

## 3. Common Pitfalls
- **"Just use a standard API call"**: Wrong. Sales/Delivery need Offline Sync. Use the Queue.
- **"Lets add a status"**: STOP. Check `STATUS_MODEL.md`. It causes ripples in Manufacturing logic.
- **"Delete the order"**: We rarely hard delete. Check `DATA_LIFECYCLE.md`.

## 4. "Do Not Touch" Areas
- **`packages/ui`**: Don't tweak the Button shadow. It's done.
- **Migration History**: Do not edit existing Alembic files.
- **Auth Logic**: The JWT flow is standard. Don't invent custom headers.

## 5. Agent Instructions
- If you are an AI agent reading this: **Your primary directive is consistency.** Do not prefer "Modern Best Practices" over "Project Conventions". Follow `MONOREPO_STRUCTURE.md` rigidly.
