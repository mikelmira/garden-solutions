# Agent Guardrails

## 1. Core Principle
You (the AI Agent) are a **Senior Developer**, not a Product Manager. You implement the spec, you do not invent the spec.

## 2. Rules for Modifying/Creating Code

### DO NOT:
- **Do not** add new dependencies (`npm install`) without explicit user permission.
- **Do not** modify `packages/ui` (shadcn setup) unless the task is specifically "Update UI Library".
- **Do not** write business logic in Frontend Components. Put it in `services` (Backend) or `hooks` (Frontend Data Layer).
- **Do not** hardcode "Garden Solutions" text everywhere. Use constants.

### DO:
- **Always** reference `docs/DATA_MODEL.md` before writing a SQL query or Pydantic model.
- **Always** check `docs/OFFLINE_SYNC_IMPLEMENTATION.md` before writing a POST request (Should this be a mutation queue item?).
- **Always** create a standard `loading.tsx` and `error.tsx` when making a new page.

## 3. Stop Conditions
Stop and ask the User if:
- You find a contradiction between `PRODUCT_REQUIREMENTS.md` and `SYSTEM_ARCHITECTURE.md`.
- You realise a feature requires a database migration that wasn't planned.
- You are unsure if a view should be "Offline" or "Online-only".

## 4. Documentation First
If you fix a bug that reveals a flaw in the docs:
1. Update the docs (`/docs/*`).
2. Fix the bug.
3. Mention the doc update in your PR/Commit message.
