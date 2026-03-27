# Frontend Implementation Guide

## 1. App Router Conventions

### Pages & Layouts
- **Structure**: `app/(role)/[flow]/page.tsx`
  - E.g., `app/(admin)/orders/page.tsx`, `app/(sales)/new-order/page.tsx`
  - *Exception*: Dashboards use `/admin-dashboard` and `/sales-dashboard` in V1. (V2 may nest them).
- **Route Groups**: Use `(group)` folders to segregate distinct layouts (e.g., Admin Sidebar vs. Mobile Bottom Nav).
- **Metadata**: Define `metadata` objects in `layout.tsx` for correct titles.

### Server vs. Client Components
- **Default**: Use Server Components (`RSC`) for all "Online-Only" views (Admin Dashboard, Reports).
- **Client Components**: Use `"use client"` for:
  - Interactive forms.
  - **All Offline-First Views** (Sales Order Capture, Delivery Execution) because they must rely on `IndexedDB` hooks (`useLiveQuery`).
  - Context Providers.

## 2. Component Architecture
- **Atoms/Molecules**: Use `packages/ui`.
- **Organisms**: Complex business components (e.g., `OrderSummaryCard`) live in `apps/web/components`.
- **Forms**: Use `react-hook-form` + `zod` for schema validation.
  - *Pattern*: Define the Zod schema in a separate file (e.g., `schemas/order.ts`) so it can be shared or inferred.

## 3. Data Fetching & State
- **Online Views**: `fetch` in RSC or `useQuery` (TanStack Query) in Client Components.
- **Offline Views**:
  - **Read**: Use `useLiveQuery` (Dexie) or equivalent to subscribe to local IndexedDB.
  - **Write**: typically `db.table.add({...})`.
  - **Sync**: A global `SyncProvider` detects online status and flushes the queue.

## 4. Styling
- **Tailwind CSS**: Utility-first.
- **cn()**: Always use the `cn` utility (from `shadcn/ui`) to merge class names.
  - `className={cn("text-sm", isActive && "font-bold", className)}`
- **Mobile First**: Write mobile styles first, then `md:`, `lg:`.
  - Sales/Delivery views must be tested at `375px` width.

## 5. Error & Loading States
- **Loading**: Every `page.tsx` must have a sibling `loading.tsx` (Suspense boundary) or handle internal loading states gracefully.
- **Error**: Every route group must have an `error.tsx` to act as an Error Boundary.
- **Not Found**: Use `notFound()` for missing resources.

## 6. Table & List Patterns
- **Desktop**: Use `shadcn/ui` **Table** component.
  - Features: Pagination, Sorting (Server-side URL params for Admin; Client-side for small offline lists).
- **Mobile**: Do **NOT** use tables. Use **Card Lists**.
  - *Pattern*: A vertical stack of `Card` components displaying key info (`CardHeader`, `CardContent`).

## 7. Troubleshooting
- **Stale Builds / 404 Loops**: If you encounter persistent 404 errors or missing chunks:
  1. Stop the dev server.
  2. Run `pnpm -C apps/web dev:clean` (or `npm run dev:clean` inside `apps/web`).
  3. This deletes `.next` cache and restarts the server cleanly.
